import os
import json
import httpx
from datetime import datetime, timezone
from uuid import UUID, uuid4
import sqlalchemy as sa
from sqlalchemy.future import select

from app.modules.agent_runtime.boundary_checker import BoundaryChecker
from app.modules.workflow_execution.models import WorkflowRun, WorkflowRunStep, WorkflowRunOutput
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule
from app.modules.workflow_notifications.service import ScheduleNotificationService
from app.modules.audit.event_service import GovernanceEventService
from app.modules.audit.event_codes import WorkflowEventCode
from app.shared.db_compat import db_get, db_flush, execute_statement

from app.modules.policy_engine.enums import Decision
from app.modules.enforcement.context_builder import GovernedRuntimeContextBuilder
from app.modules.enforcement.engine import RuntimeEnforcementEngine


class BoundaryViolationError(Exception):
    pass


class AgentRuntimeService:
    def __init__(self):
        self.boundary_checker = BoundaryChecker()
        self.event_service = GovernanceEventService()

    async def invoke_agent(self, run_id: UUID, assignment, context: dict, db) -> dict:
        # 1. Unified Runtime Enforcement Gateway Check (Context -> Boundaries -> Policies -> Combiner)
        tenant_id = getattr(assignment, "tenant_id", None) or getattr(getattr(assignment, "schedule", None), "tenant_id", None)
        workflow_id = str(assignment.schedule.workflow_id) if getattr(assignment, "schedule", None) and getattr(assignment.schedule, "workflow_id", None) else None
        model_id = str(assignment.model_id) if getattr(assignment, "model_id", None) else None
        requested_tool = context.get("requested_tool")
        tool_id = context.get("tool_id")
        tool_params = context.get("tool_parameters", {})
        data_reqs = context.get("data_requests", [])
        facts = dict(context.get("facts", context))

        if tenant_id:
            gov_req = GovernedRuntimeContextBuilder.build_request(
                tenant_id=tenant_id,
                agent_id=str(assignment.agent_id) if getattr(assignment, "agent_id", None) else None,
                workflow_id=workflow_id,
                model_id=model_id,
                tool_id=str(tool_id) if tool_id else None,
                tool_name=requested_tool,
                tool_parameters=tool_params,
                data_requests=data_reqs,
                facts=facts,
                operation=context.get("operation") or requested_tool or "invoke",
                environment=context.get("environment") or "PRODUCTION",
            )
            enforcement_engine = RuntimeEnforcementEngine(db)
            enforce_res = enforcement_engine.enforce(gov_req, tenant_id=tenant_id)

            # Route DENY -> Block execution
            if enforce_res.decision == Decision.DENY:
                reason = enforce_res.reason or "Execution blocked by runtime governance enforcement"
                if enforce_res.violations:
                    v_msgs = [v.message if hasattr(v, "message") else str(v) for v in enforce_res.violations]
                    reason = f"{reason} - {'; '.join(v_msgs)}"
                raise BoundaryViolationError(reason)

            # Route REQUIRE_APPROVAL -> Intercept before execution
            if enforce_res.decision == Decision.REQUIRE_APPROVAL:
                return {
                    "status": "APPROVAL_REQUIRED",
                    "execution_permitted": False,
                    "approval_requirements": [a.model_dump() for a in (enforce_res.approval_requirements or [])],
                    "reason": enforce_res.reason,
                    "trace": enforce_res.trace,
                }

            # Route ESCALATE -> Security escalation
            if enforce_res.decision == Decision.ESCALATE:
                return {
                    "status": "ESCALATED",
                    "execution_permitted": False,
                    "reason": enforce_res.reason,
                    "trace": enforce_res.trace,
                }
        else:
            # Fallback to procedural boundary check if no tenant context
            passed, reason = await self.boundary_checker.check(assignment, requested_tool, db)
            if not passed:
                raise BoundaryViolationError(reason)

        # 2. Add run step or update existing: AGENT_INVOCATION, status=RUNNING
        stmt = select(WorkflowRunStep).where(
            WorkflowRunStep.run_id == run_id,
            WorkflowRunStep.step_code == "AGENT_INVOCATION"
        )
        res = await execute_statement(db, stmt)
        step = res.scalar()
        if not step:
            step = WorkflowRunStep(
                id=uuid4(),
                run_id=run_id,
                step_code="AGENT_INVOCATION",
                step_order=3,
                step_type="INVOCATION",
                tenant_id=assignment.tenant_id
            )
            db.add(step)
        
        step.step_status = "RUNNING"
        step.started_at = datetime.now(timezone.utc)
        step.input_json = context
        await db_flush(db)

        # 3. Publish AGENT_EXECUTION_STARTED
        run = await db_get(db, WorkflowRun, run_id)
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_EXECUTION_STARTED,
            entity_type="workflow_runs",
            entity_id=run_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="INVOKE_AGENT",
            event_summary=f"Agent invocation started for run {run.run_code}",
            event_payload={"agent_id": str(assignment.agent_id)},
            db=db
        )

        # 4. Call Claude if ANTHROPIC_API_KEY set, else return mock structured output
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        raw_output = None
        if api_key:
            try:
                system_prompt = (
                    "You are a GuardianIQ governance compliance LLM. You must evaluate the context and return a valid JSON object. "
                    "Response schema must be EXACTLY: "
                    '{"findings": [{"severity": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL", "title": "string", "description": "string"}], '
                    '"recommendations": ["string"], "evidence": {}, "risk_score": 0-100}'
                )
                user_msg = f"Evaluate execution context: {json.dumps(context)}"
                
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 1000,
                            "system": system_prompt,
                            "messages": [{"role": "user", "content": user_msg}]
                        },
                        timeout=30.0
                    )
                    resp.raise_for_status()
                    resp_json = resp.json()
                    content_text = resp_json["content"][0]["text"]
                    raw_output = json.loads(content_text)
            except Exception as e:
                # If API call fails, log error and fall back to mock
                raw_output = {
                    "findings": [
                        {
                            "severity": "MEDIUM",
                            "title": "Claude Invocation Failure",
                            "description": f"Failed to call Anthropic API: {str(e)}. Fallback occurred."
                        }
                    ],
                    "recommendations": ["Check Anthropic API key configuration."],
                    "evidence": {"error": str(e)},
                    "risk_score": 50
                }
        
        if not raw_output:
            # Mock structured output for demo mode
            assign_mode = assignment.execution_mode.value if hasattr(assignment.execution_mode, "value") else str(assignment.execution_mode)
            mock_score = 35
            if context.get("requested_tool") == "TL-WRITE":
                mock_score = 80
            elif assign_mode == "LIMITED_EXECUTION":
                mock_score = 78

            mock_findings = []
            if mock_score > 75:
                mock_findings.append({
                    "severity": "HIGH",
                    "title": "High Risk Execution Path Detected",
                    "description": f"Agent invoked with tool {context.get('requested_tool')} in mode {assign_mode}."
                })
            else:
                mock_findings.append({
                    "severity": "LOW",
                    "title": "Standard Run Completed",
                    "description": "No immediate compliance violations observed in execution context."
                })

            raw_output = {
                "findings": mock_findings,
                "recommendations": [
                    "Ensure secondary reviewer review if mode exceeds RECOMMEND_ONLY.",
                    "Log all direct database manipulations."
                ],
                "evidence": {
                    "agent_id": str(assignment.agent_id),
                    "execution_mode": assign_mode,
                    "requested_tool": context.get("requested_tool")
                },
                "risk_score": mock_score
            }

        # Update step to completed
        step.step_status = "COMPLETED"
        step.completed_at = datetime.now(timezone.utc)
        step.output_json = raw_output
        await db_flush(db)

        # Publish AGENT_EXECUTION_COMPLETED
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.AGENT_EXECUTION_COMPLETED,
            entity_type="workflow_runs",
            entity_id=run_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="INVOKE_AGENT",
            event_summary=f"Agent invocation completed for run {run.run_code}",
            event_payload={"risk_score": raw_output.get("risk_score")},
            db=db
        )

        return raw_output

    async def parse_output(self, raw_output: dict, run_id: UUID, db) -> WorkflowRunOutput:
        # Load run
        run = await db_get(db, WorkflowRun, run_id)
        schedule = await db_get(db, Phase2WorkflowSchedule, run.schedule_id)

        # Parse output fields
        findings = raw_output.get("findings", [])
        recommendations = raw_output.get("recommendations", [])
        evidence = raw_output.get("evidence", {})
        risk_score = raw_output.get("risk_score", 0)

        # Determine severity from findings/risk
        has_high_critical_finding = any(f.get("severity") in ["HIGH", "CRITICAL"] for f in findings)
        severity = "MEDIUM"
        if risk_score > 75 or has_high_critical_finding:
            severity = "HIGH"

        # If risk_score > 75 or any finding severity in [HIGH, CRITICAL]:
        escalation_required = False
        if risk_score > 75 or has_high_critical_finding:
            escalation_required = True
            
            # Send notification to schedule owner
            if schedule.owner_user_id:
                await ScheduleNotificationService.create_notification(
                    db=db,
                    tenant_id=run.tenant_id,
                    recipient_user_id=schedule.owner_user_id,
                    notification_type="RISK_ESCALATION",
                    title="High-Risk Run Output Escalation",
                    message=f"Run {run.run_code} executed with high compliance risk (Score: {risk_score}%). Escalation required.",
                    severity="CRITICAL",
                    entity_type="workflow_runs",
                    entity_id=run_id,
                    actor_id=None
                )

        # Insert output record
        out_rec = WorkflowRunOutput(
            id=uuid4(),
            tenant_id=run.tenant_id,
            run_id=run_id,
            output_type="COMPLIANCE_ASSESSMENT",
            severity=severity,
            risk_score=risk_score,
            findings_json=findings,
            recommendations_json=recommendations,
            evidence_json=evidence,
            raw_output_json=raw_output,
            parse_status="PARSED",
            created_by=run.created_by,
            updated_by=run.updated_by
        )
        db.add(out_rec)
        await db_flush(db)

        # Update run failure escalations if a failure occurred
        if escalation_required:
            from app.modules.workflow_execution.models import WorkflowRunFailure
            stmt = select(WorkflowRunFailure).where(WorkflowRunFailure.run_id == run_id)
            res = await execute_statement(db, stmt)
            failures = res.scalars().all()
            for f in failures:
                f.escalation_required = True
                f.escalation_sent_at = datetime.now(timezone.utc)
            if failures:
                await db_flush(db)

        # Publish WORKFLOW_OUTPUT_GENERATED
        await self.event_service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_OUTPUT_GENERATED,
            entity_type="workflow_runs",
            entity_id=run_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="PARSE_OUTPUT",
            event_summary=f"Workflow run output generated for run {run.run_code}",
            event_payload={"risk_score": risk_score, "escalation_required": escalation_required},
            db=db
        )

        return out_rec
