from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.agent_boundary.models import DataSourceField, AgentDataPermission
from app.modules.data_governance.repository import DataGovernanceRepository


class DataGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def list_fields(self, data_source_id: UUID, tenant_id: UUID) -> List[DataSourceField]:
        return DataGovernanceRepository.list_fields_by_data_source(self.db, data_source_id, tenant_id)

    def add_field(self, tenant_id: UUID, data: Dict[str, Any]) -> DataSourceField:
        field = DataSourceField(
            tenant_id=tenant_id,
            data_source_id=data["data_source_id"],
            field_name=data["field_name"],
            data_type=data.get("data_type", "STRING"),
            classification=data.get("classification", "INTERNAL"),
            sensitivity_level=data.get("sensitivity_level", "MEDIUM"),
            is_pii=data.get("is_pii", False),
            masking_strategy=data.get("masking_strategy"),
            is_active=data.get("is_active", True),
        )
        DataGovernanceRepository.create_field(self.db, field)
        self.db.commit()
        return field

    def list_agent_permissions(self, agent_id: UUID, tenant_id: UUID) -> List[AgentDataPermission]:
        return DataGovernanceRepository.list_permissions_by_agent(self.db, agent_id, tenant_id)

    def grant_permission(self, tenant_id: UUID, data: Dict[str, Any]) -> AgentDataPermission:
        perm = AgentDataPermission(
            tenant_id=tenant_id,
            agent_id=data["agent_id"],
            data_source_id=data["data_source_id"],
            field_id=data.get("field_id"),
            allowed_operations_json=data.get("allowed_operations_json", ["READ"]),
            max_classification=data.get("max_classification", "CONFIDENTIAL"),
            max_sensitivity=data.get("max_sensitivity", "HIGH"),
            is_active=data.get("is_active", True),
        )
        DataGovernanceRepository.create_or_update_permission(self.db, perm)
        self.db.commit()
        return perm

    def evaluate_data_access(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data_source_id: UUID,
        operation: str = "READ",
        requested_fields: Optional[List[str]] = None,
        records: Optional[List[Dict[str, Any]]] = None,
        record_count: Optional[int] = None,
    ):
        from app.modules.data_governance.guard import DataPermissionGuard
        guard = DataPermissionGuard(self.db)
        return guard.evaluate_data_access(
            tenant_id=tenant_id,
            agent_id=agent_id,
            data_source_id=data_source_id,
            operation=operation,
            requested_fields=requested_fields,
            records=records,
            record_count=record_count,
        )

