from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.modules.policy_engine.enums import DataClassification, SensitivityLevel, DataOperation


class DataSourceFieldCreate(BaseModel):
    data_source_id: UUID
    field_name: str
    data_type: str = "STRING"
    classification: DataClassification = DataClassification.INTERNAL
    sensitivity_level: SensitivityLevel = SensitivityLevel.MEDIUM
    is_pii: bool = False
    masking_strategy: Optional[str] = None
    is_active: bool = True


class AgentDataPermissionCreate(BaseModel):
    agent_id: UUID
    data_source_id: UUID
    field_id: Optional[UUID] = None
    allowed_operations_json: List[DataOperation] = [DataOperation.READ]
    max_classification: DataClassification = DataClassification.CONFIDENTIAL
    max_sensitivity: SensitivityLevel = SensitivityLevel.HIGH
    is_active: bool = True
