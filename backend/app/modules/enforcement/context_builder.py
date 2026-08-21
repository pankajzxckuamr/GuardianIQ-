from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.modules.policy_engine.schemas import (
    GovernedRuntimeRequest,
    ActorContext,
    AgentContext,
    WorkflowContext,
    ModelContext,
    ToolContext,
    DataRequestContext,
)
from app.modules.policy_engine.enums import EnforcementMode, AccessMode, DataOperation, DataClassification, SensitivityLevel


class GovernedRuntimeContextBuilder:
    """Constructs and normalizes canonical GovernedRuntimeRequest envelopes from runtime parameters."""

    @staticmethod
    def build_request(
        tenant_id: Optional[UUID] = None,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        autonomy_level: Optional[str] = None,
        workflow_id: Optional[str] = None,
        workflow_run_id: Optional[str] = None,
        workflow_name: Optional[str] = None,
        model_id: Optional[str] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        operation: Optional[str] = None,
        tool_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_parameters: Optional[Dict[str, Any]] = None,
        tool_access_mode: Optional[AccessMode] = None,
        data_requests: Optional[List[Dict[str, Any]]] = None,
        environment: Optional[str] = None,
        facts: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
        idempotency_key: Optional[str] = None,
        enforcement_mode: EnforcementMode = EnforcementMode.BLOCKING,
    ) -> GovernedRuntimeRequest:
        req_id = uuid4()
        corr_id = correlation_id or uuid4()

        actor = ActorContext(user_id=actor_id, role=role) if actor_id else None
        agent = (
            AgentContext(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_type=agent_type,
                autonomy_level=autonomy_level,
            )
            if agent_id
            else None
        )
        workflow = (
            WorkflowContext(
                workflow_id=workflow_id,
                workflow_run_id=workflow_run_id,
                workflow_name=workflow_name,
            )
            if workflow_id
            else None
        )
        model = (
            ModelContext(
                model_id=model_id,
                model_name=model_name,
                model_version=model_version,
            )
            if model_id
            else None
        )
        tool = (
            ToolContext(
                tool_id=tool_id,
                tool_name=tool_name,
                operation=operation,
                parameters=tool_parameters or {},
                access_mode=tool_access_mode,
            )
            if (tool_id or tool_name or tool_parameters)
            else None
        )

        parsed_data_reqs: List[DataRequestContext] = []
        if data_requests:
            for dr in data_requests:
                parsed_data_reqs.append(
                    DataRequestContext(
                        data_source_id=dr["data_source_id"],
                        table_name=dr.get("table_name"),
                        columns=dr.get("columns", []),
                        operation=dr.get("operation", DataOperation.READ),
                        classification=dr.get("classification"),
                        sensitivity_level=dr.get("sensitivity_level"),
                        record_count=dr.get("record_count"),
                        query=dr.get("query"),
                        filter_criteria=dr.get("filter_criteria", {}),
                    )
                )

        eval_facts = dict(facts or {})
        if environment:
            eval_facts["environment"] = environment
        if operation:
            eval_facts["operation"] = operation

        return GovernedRuntimeRequest(
            request_id=req_id,
            correlation_id=corr_id,
            tenant_id=tenant_id,
            actor=actor,
            agent=agent,
            workflow=workflow,
            model=model,
            tool=tool,
            data_requests=parsed_data_reqs,
            facts=eval_facts,
            idempotency_key=idempotency_key,
            enforcement_mode=enforcement_mode,
        )
