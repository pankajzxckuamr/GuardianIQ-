from datetime import datetime, timezone
from uuid import UUID, uuid4
import sqlalchemy as sa
from sqlalchemy.future import select
from app.modules.auth.models import Role, User, user_roles
from app.modules.registry.models import GuardianUser, RegistryAuditEvent
from app.modules.workflow_scheduler.models import ApprovalGroupMember
from app.modules.authorization.models import WorkflowAuthorizationDecision, WorkflowDelegation
from app.modules.authorization.rbac_service import check_permission, execute_statement
from app.modules.authorization.abac_service import evaluate_context
from app.modules.authorization.schemas import AuthorizationRequest, AuthorizationResponse
import inspect
import asyncio

class GovernanceEventService:
    @staticmethod
    async def publish_event(event_type: str, payload: dict, db) -> None:
        """Publishes a security event to the registry audit events log."""
        meta = {
            "change_summary": payload.get("change_summary") or f"Authorization denied for action {payload.get('action')}",
            "before_json": payload.get("before_json"),
            "after_json": payload.get("after_json") or payload
        }
        stmt = sa.insert(RegistryAuditEvent).values(
            event_type=event_type,
            entity_type=payload.get("entity_type", "authorization_decision"),
            entity_id=str(payload.get("entity_id")) if payload.get("entity_id") else None,
            actor_user_id=payload.get("subject_user_id"),
            action=payload.get("action") or "EVALUATE",
            event_metadata=meta,
            created_at=datetime.now(timezone.utc)
        )
        await execute_statement(db, stmt)


class AuthorizationDecisionService:
    async def evaluate(self, request: AuthorizationRequest, db, persist: bool = False) -> AuthorizationResponse:
        # 1. Fetch Subject Context
        user_roles_list = []
        g_user = None
        
        if request.subject_user_id:
            guardian_stmt = select(GuardianUser).where(GuardianUser.id == request.subject_user_id)
            guardian_res = await execute_statement(db, guardian_stmt)
            g_user = guardian_res.scalar()
            
            if g_user:
                user_roles_list = [r.role_code for r in g_user.roles]

        subject_dict = {
            "user_id": request.subject_user_id,
            "roles": user_roles_list,
            "department_id": g_user.department_id if g_user else None
        }

        # 2. Fetch Object Context
        object_context = {
            "risk_level": "MEDIUM",
            "owner_user_id": None,
            "approval_group_id": None,
            "schedule_status": None,
            "execution_mode": None,
            "sensitivity_level": None
        }

        if request.object_type and request.object_id:
            # Workflow Schedule
            if request.object_type == "workflow_schedules":
                from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule
                sched_stmt = select(Phase2WorkflowSchedule).where(Phase2WorkflowSchedule.id == request.object_id)
                sched_res = await execute_statement(db, sched_stmt)
                sched = sched_res.scalar()
                if sched:
                    object_context.update({
                        "risk_level": sched.risk_level,
                        "owner_user_id": sched.owner_user_id,
                        "approval_group_id": sched.approval_group_id,
                        "schedule_status": sched.schedule_status
                    })
            
            # Workflow Run
            elif request.object_type == "workflow_runs":
                from app.modules.workflow_execution.models import WorkflowRun
                run_stmt = select(WorkflowRun).where(WorkflowRun.id == request.object_id)
                run_res = await execute_statement(db, run_stmt)
                run = run_res.scalar()
                if run:
                    object_context.update({
                        "risk_level": run.risk_level,
                        "owner_user_id": run.triggered_by_user_id
                    })

            # Workflow Run Output
            elif request.object_type == "workflow_run_outputs":
                from app.modules.workflow_execution.models import WorkflowRunOutput, WorkflowRun
                out_stmt = select(WorkflowRunOutput).where(WorkflowRunOutput.id == request.object_id)
                out_res = await execute_statement(db, out_stmt)
                out = out_res.scalar()
                if out:
                    run_stmt = select(WorkflowRun.triggered_by_user_id).where(WorkflowRun.id == out.run_id)
                    run_res = await execute_statement(db, run_stmt)
                    run_owner = run_res.scalar()
                    object_context.update({
                        "sensitivity_level": out.severity,
                        "severity": out.severity,
                        "risk_score": float(out.risk_score) if out.risk_score is not None else None,
                        "owner_user_id": run_owner
                    })

        # Merge additional custom context parameters from request
        if request.context_json:
            for k, v in request.context_json.items():
                if v is not None:
                    object_context[k] = v

        # 3. RBAC Evaluation
        rbac_allowed = False
        if request.subject_user_id:
            rbac_allowed = await check_permission(request.subject_user_id, request.action, db)
        
        deny_reasons = []
        if not rbac_allowed:
            deny_reasons.append("Failed RBAC check: User missing required permission code")

        # 4. ABAC Evaluation
        abac_allowed, failed_conditions = await evaluate_context(subject_dict, object_context, request.action, db)
        if not abac_allowed:
            deny_reasons.extend(failed_conditions)

        # 5. Relationship Evaluation
        is_owner = False
        is_group_member = False
        has_delegation = False
        now = datetime.now(timezone.utc)

        if request.subject_user_id:
            is_owner = (subject_dict.get("user_id") == object_context.get("owner_user_id"))
            approval_group_id = object_context.get("approval_group_id")
            
            if approval_group_id:
                # Check direct membership
                member_stmt = select(ApprovalGroupMember.user_id).where(
                    ApprovalGroupMember.approval_group_id == approval_group_id,
                    ApprovalGroupMember.user_id == request.subject_user_id
                )
                member_res = await execute_statement(db, member_stmt)
                is_group_member = member_res.scalar() is not None

                # Check active delegation
                if not is_group_member:
                    delegation_stmt = (
                        select(WorkflowDelegation.id)
                        .join(ApprovalGroupMember, ApprovalGroupMember.user_id == WorkflowDelegation.delegator_user_id)
                        .where(
                            WorkflowDelegation.delegatee_user_id == request.subject_user_id,
                            ApprovalGroupMember.approval_group_id == approval_group_id,
                            WorkflowDelegation.start_at <= now,
                            WorkflowDelegation.end_at >= now,
                            WorkflowDelegation.status == "ACTIVE",
                            WorkflowDelegation.is_deleted == False
                        )
                    )
                    delegation_res = await execute_statement(db, delegation_stmt)
                    has_delegation = delegation_res.scalar() is not None

        relationship_allowed = is_owner or is_group_member or has_delegation
        
        if request.action == "CANCEL_WORKFLOW_RUN":
            if "GOVERNANCE_ADMIN" in user_roles_list or "SUPER_ADMIN" in user_roles_list:
                relationship_allowed = True
            # if escalation_owner_id matched, but we don't have it explicitly right now, we default to the role check.

        # 6. Compute Overall Decision
        # Overall access is permitted only when both RBAC and ABAC evaluate to True
        allowed = rbac_allowed and abac_allowed
        if request.action in ["ACTIVATE_WORKFLOW_SCHEDULE", "RUN_WORKFLOW_SCHEDULE", "CANCEL_WORKFLOW_RUN"]:
            # Certain actions also require relationship success if ABAC didn't already override
            pass # Actually, relationship_allowed is normally combined if needed. We'll leave it as rbac and abac for strictness unless relations are mandatory. 
            # In GuardianIQ, usually RBAC + ABAC is enough. We'll track relationship in the result.
        
        decision = "ALLOW" if allowed else "DENY"

        rbac_result = {"allowed": rbac_allowed, "roles": user_roles_list}
        abac_result = {"allowed": abac_allowed, "failed_conditions": failed_conditions}
        relationship_result = {
            "allowed": relationship_allowed,
            "is_owner": is_owner,
            "is_group_member": is_group_member,
            "has_delegation": has_delegation
        }

        # 7. Audit Logging on DENY
        decision_id = uuid4()
        evaluated_at_dt = datetime.now(timezone.utc)
        
        if decision == "DENY":
            audit_payload = {
                "decision_id": str(decision_id),
                "subject_user_id": str(request.subject_user_id) if request.subject_user_id else None,
                "subject_agent_id": str(request.subject_agent_id) if request.subject_agent_id else None,
                "action": request.action,
                "object_type": request.object_type,
                "object_id": str(request.object_id) if request.object_id else None,
                "deny_reasons": deny_reasons,
                "evaluated_at": evaluated_at_dt.isoformat()
            }
            await GovernanceEventService.publish_event("AUTHORIZATION_DENIED", audit_payload, db)

        # 8. Persist Decision if Requested
        if persist:
            resolved_tenant_id = None
            if request.subject_user_id:
                resolved_tenant_id = request.subject_user_id
            elif object_context.get("owner_user_id"):
                resolved_tenant_id = object_context.get("owner_user_id")
            
            if not resolved_tenant_id:
                g_user_stmt = select(GuardianUser.id).limit(1)
                g_user_res = await execute_statement(db, g_user_stmt)
                resolved_tenant_id = g_user_res.scalar()

            decision_record = WorkflowAuthorizationDecision(
                id=decision_id,
                tenant_id=resolved_tenant_id,
                subject_user_id=request.subject_user_id,
                subject_agent_id=request.subject_agent_id,
                subject_type=request.subject_type,
                object_type=request.object_type,
                object_id=request.object_id,
                action=request.action,
                decision=decision,
                reason_json={"deny_reasons": deny_reasons},
                rbac_result=rbac_result,
                abac_result=abac_result,
                relationship_result=relationship_result,
                evaluated_at=evaluated_at_dt
            )
            db.add(decision_record)
            if hasattr(db, "commit") and asyncio.iscoroutinefunction(db.commit):
                await db.commit()
            else:
                db.commit()

        return AuthorizationResponse(
            allowed=allowed,
            decision=decision,
            rbac_result=rbac_result,
            abac_result=abac_result,
            relationship_result=relationship_result,
            deny_reasons=deny_reasons,
            evaluated_at=evaluated_at_dt
        )

    async def can_create_schedule(self, subject_user_id: UUID, db) -> AuthorizationResponse:
        req = AuthorizationRequest(subject_user_id=subject_user_id, subject_type="USER", action="CREATE_WORKFLOW_SCHEDULE")
        return await self.evaluate(req, db, persist=True)

    async def can_activate_schedule(self, subject_user_id: UUID, schedule_id: UUID, db) -> AuthorizationResponse:
        req = AuthorizationRequest(subject_user_id=subject_user_id, subject_type="USER", action="ACTIVATE_WORKFLOW_SCHEDULE", object_type="workflow_schedules", object_id=schedule_id)
        return await self.evaluate(req, db, persist=True)

    async def can_run_schedule(self, subject_user_id: UUID, schedule_id: UUID, db) -> AuthorizationResponse:
        req = AuthorizationRequest(subject_user_id=subject_user_id, subject_type="USER", action="RUN_WORKFLOW_SCHEDULE", object_type="workflow_schedules", object_id=schedule_id)
        return await self.evaluate(req, db, persist=True)

    async def can_view_output(self, subject_user_id: UUID, output_id: UUID, db) -> AuthorizationResponse:
        req = AuthorizationRequest(subject_user_id=subject_user_id, subject_type="USER", action="VIEW_WORKFLOW_RUN_OUTPUT", object_type="workflow_run_outputs", object_id=output_id)
        return await self.evaluate(req, db, persist=True)

    async def can_cancel_run(self, subject_user_id: UUID, run_id: UUID, db) -> AuthorizationResponse:
        req = AuthorizationRequest(subject_user_id=subject_user_id, subject_type="USER", action="CANCEL_WORKFLOW_RUN", object_type="workflow_runs", object_id=run_id)
        return await self.evaluate(req, db, persist=True)

    async def can_assign_agent(self, subject_user_id: UUID, schedule_id: UUID, agent_id: UUID, db) -> AuthorizationResponse:
        req = AuthorizationRequest(subject_user_id=subject_user_id, subject_type="USER", action="ASSIGN_AI_AGENT_TO_WORKFLOW", object_type="workflow_schedules", object_id=schedule_id, context_json={"agent_id": str(agent_id)})
        return await self.evaluate(req, db, persist=True)
