from uuid import UUID
import pytz
from croniter import croniter
import sqlalchemy as sa
from sqlalchemy.future import select

from app.shared.enums import RiskLevel, ExecutionMode, ScheduleType
from app.modules.registry.models import RegistryWorkflow, RegistryAIAgent, RegistryAIModel, RegistryTool
from app.modules.workflow_scheduler.models import ApprovalGroup

from app.shared.db_compat import db_get, execute_statement

import inspect


class ValidationError:
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message

    def __repr__(self):
        return f"ValidationError(field={self.field!r}, message={self.message!r})"


class WorkflowScheduleValidationService:
    @classmethod
    async def validate_create(cls, payload, db) -> list[ValidationError]:
        errors = []

        def get_val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        def set_val(obj, key, val):
            if isinstance(obj, dict):
                obj[key] = val
            else:
                setattr(obj, key, val)

        workflow_id = get_val(payload, "workflow_id")
        agent_assignments = get_val(payload, "agent_assignments") or []
        schedule_type = get_val(payload, "schedule_type")
        cron_expression = get_val(payload, "cron_expression")
        timezone = get_val(payload, "timezone")
        start_at = get_val(payload, "start_at")
        end_at = get_val(payload, "end_at")
        risk_level = get_val(payload, "risk_level")
        approval_required = get_val(payload, "approval_required", False)
        approval_group_id = get_val(payload, "approval_group_id")

        # 1. Check workflow is ACTIVE in registry_workflows
        if workflow_id:
            try:
                w_id = UUID(str(workflow_id)) if not isinstance(workflow_id, UUID) else workflow_id
                workflow = await db_get(db, RegistryWorkflow, w_id)
                if not workflow:
                    errors.append(ValidationError("workflow_id", f"Workflow with ID {workflow_id} does not exist"))
                elif workflow.status != "ACTIVE":
                    errors.append(ValidationError("workflow_id", f"Workflow with ID {workflow_id} is not ACTIVE"))
            except ValueError:
                errors.append(ValidationError("workflow_id", f"Invalid workflow UUID format: {workflow_id}"))
        else:
            errors.append(ValidationError("workflow_id", "workflow_id is required"))

        # Map execution mode ranks
        EXECUTION_MODE_RANK = {
            "READ_ONLY": 1,
            "RECOMMEND_ONLY": 2,
            "APPROVAL_REQUIRED": 3,
            "LIMITED_EXECUTION": 4,
            "FULLY_BLOCKED": 5
        }

        # 2. Check all agent_ids and model_ids and execution modes
        all_allowed_tools = []
        has_write_execute_tool = False
        exec_mode_auto_approve = False

        for idx, assignment in enumerate(agent_assignments):
            agent_id = get_val(assignment, "agent_id")
            model_id = get_val(assignment, "model_id")
            assignment_mode = get_val(assignment, "execution_mode")

            # Check agent status
            if agent_id:
                try:
                    a_id = UUID(str(agent_id)) if not isinstance(agent_id, UUID) else agent_id
                    agent = await db_get(db, RegistryAIAgent, a_id)
                    if not agent:
                        errors.append(ValidationError(f"agent_assignments[{idx}].agent_id", f"Agent with ID {agent_id} does not exist"))
                    elif agent.status != "ACTIVE":
                        errors.append(ValidationError(f"agent_assignments[{idx}].agent_id", f"Agent with ID {agent_id} is not ACTIVE"))
                    else:
                        # check execution_mode does not exceed agent's registered max
                        agent_mode = agent.execution_mode
                        agent_mode_str = agent_mode.value if hasattr(agent_mode, "value") else str(agent_mode)
                        assignment_mode_str = assignment_mode.value if hasattr(assignment_mode, "value") else str(assignment_mode)
                        if EXECUTION_MODE_RANK.get(assignment_mode_str, 0) > EXECUTION_MODE_RANK.get(agent_mode_str, 0):
                            errors.append(ValidationError(
                                f"agent_assignments[{idx}].execution_mode",
                                f"Execution mode {assignment_mode_str} exceeds agent's max registered mode {agent_mode_str}"
                            ))
                except ValueError:
                    errors.append(ValidationError(f"agent_assignments[{idx}].agent_id", f"Invalid agent UUID format: {agent_id}"))
            else:
                errors.append(ValidationError(f"agent_assignments[{idx}].agent_id", "agent_id is required"))

            # Check model status
            if model_id:
                try:
                    m_id = UUID(str(model_id)) if not isinstance(model_id, UUID) else model_id
                    model = await db_get(db, RegistryAIModel, m_id)
                    if not model:
                        errors.append(ValidationError(f"agent_assignments[{idx}].model_id", f"Model with ID {model_id} does not exist"))
                    elif model.status != "ACTIVE":
                        errors.append(ValidationError(f"agent_assignments[{idx}].model_id", f"Model with ID {model_id} is not ACTIVE"))
                except ValueError:
                    errors.append(ValidationError(f"agent_assignments[{idx}].model_id", f"Invalid model UUID format: {model_id}"))

            # Track allowed tools
            allowed_tools = get_val(assignment, "allowed_tools") or get_val(assignment, "allowed_tools_json") or []
            all_allowed_tools.extend(allowed_tools)

            # Check execution mode trigger
            assignment_mode_str = assignment_mode.value if hasattr(assignment_mode, "value") else str(assignment_mode)
            if assignment_mode_str in ["APPROVAL_REQUIRED", "LIMITED_EXECUTION"]:
                exec_mode_auto_approve = True

        # Check tools capability in database
        if all_allowed_tools:
            stmt = select(RegistryTool).where(RegistryTool.tool_code.in_(all_allowed_tools))
            res = await execute_statement(db, stmt)
            db_tools = res.scalars().all()
            for tool in db_tools:
                if tool.access_mode in ["WRITE", "EXECUTE", "ADMIN"]:
                    has_write_execute_tool = True

        # 3. Cron validity via croniter
        sched_type_str = schedule_type.value if hasattr(schedule_type, "value") else str(schedule_type)
        if sched_type_str == "CRON":
            if not cron_expression:
                errors.append(ValidationError("cron_expression", "cron_expression is required when schedule_type is CRON"))
            elif not croniter.is_valid(cron_expression):
                errors.append(ValidationError("cron_expression", f"Invalid cron expression: {cron_expression}"))

        # 4. Timezone validity via pytz
        if timezone:
            try:
                pytz.timezone(timezone)
            except Exception:
                errors.append(ValidationError("timezone", f"Invalid timezone: {timezone}"))

        # 5. end_at > start_at
        if start_at and end_at:
            if end_at <= start_at:
                errors.append(ValidationError("end_at", "end_at must be greater than start_at"))

        # 6. Auto-set approval_required=True
        risk_str = risk_level.value if hasattr(risk_level, "value") else str(risk_level)
        risk_trigger = risk_str in ["HIGH", "CRITICAL"]

        if risk_trigger or has_write_execute_tool or exec_mode_auto_approve:
            set_val(payload, "approval_required", True)
            approval_required = True

        # 7. Require approval_group_id when approval_required=True
        if approval_required:
            if not approval_group_id:
                errors.append(ValidationError("approval_group_id", "approval_group_id is required when approval_required is True"))
            else:
                try:
                    ag_id = UUID(str(approval_group_id)) if not isinstance(approval_group_id, UUID) else approval_group_id
                    group = await db_get(db, ApprovalGroup, ag_id)
                    if not group:
                        errors.append(ValidationError("approval_group_id", f"Approval group with ID {approval_group_id} does not exist"))
                except ValueError:
                    errors.append(ValidationError("approval_group_id", f"Invalid approval group UUID format: {approval_group_id}"))

        return errors
