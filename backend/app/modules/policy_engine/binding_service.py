from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.modules.relationship.models import PolicyBinding
from app.modules.policy_engine.models import GovernancePolicy, PolicyVersion
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool, Workflow
from app.modules.datasource.models import DataSource
from app.modules.ai_model.models import AIModel
from app.modules.relationship.cache_service import MemoryCacheService
from app.modules.policy_engine.repository import (
    PolicyRepository,
    PolicyVersionRepository,
    PolicyBindingRepository,
)
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate


class PolicyBindingService:
    def __init__(self, db: Session):
        self.db = db
        self.cache = MemoryCacheService()
        self.publisher = EventPublisherService()

    def validate_target_exists(self, tenant_id: UUID, target_type: str, target_id: str) -> bool:
        """
        Validates target entity existence and same-tenant ownership.
        Returns True if valid, raises ValueError if missing or belongs to another tenant.
        """
        try:
            target_uuid = UUID(target_id)
        except (ValueError, TypeError):
            # Target might be wildcard '*' or non-UUID identifier
            if target_id == "*":
                return True
            raise ValueError(f"Invalid target_id '{target_id}', must be a valid UUID or '*'")

        if target_type == "AGENT":
            target = (
                self.db.query(Agent)
                .filter(Agent.id == target_uuid, Agent.tenant_id == tenant_id)
                .first()
            )
            if not target:
                raise ValueError(f"Agent '{target_id}' not found for tenant")
            return True

        elif target_type == "TOOL":
            target = (
                self.db.query(Tool)
                .filter(Tool.id == target_uuid, Tool.tenant_id == tenant_id)
                .first()
            )
            if not target:
                raise ValueError(f"Tool '{target_id}' not found for tenant")
            return True

        elif target_type in ["DATA_SOURCE", "DATASOURCE"]:
            target = (
                self.db.query(DataSource)
                .filter(DataSource.id == target_uuid, DataSource.tenant_id == tenant_id)
                .first()
            )
            if not target:
                raise ValueError(f"Data source '{target_id}' not found for tenant")
            return True

        elif target_type == "WORKFLOW":
            target = (
                self.db.query(Workflow)
                .filter(Workflow.id == target_uuid, Workflow.tenant_id == tenant_id)
                .first()
            )
            if not target:
                raise ValueError(f"Workflow '{target_id}' not found for tenant")
            return True

        elif target_type in ["MODEL", "AI_MODEL"]:
            target = (
                self.db.query(AIModel)
                .filter(AIModel.id == target_uuid, AIModel.tenant_id == tenant_id)
                .first()
            )
            if not target:
                raise ValueError(f"AI Model '{target_id}' not found for tenant")
            return True

        elif target_type in ["PROMPT", "RUNTIME"]:
            # Allowed virtual target types
            return True

        else:
            raise ValueError(f"Unsupported target_type '{target_type}'")

    def check_duplicate_overlap(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        target_type: str,
        target_id: str,
        effective_from: Optional[datetime],
        effective_to: Optional[datetime],
        exclude_binding_id: Optional[UUID] = None,
    ):
        """
        Prevents overlapping active bindings for the same (tenant, policy, target) tuple.
        """
        query = self.db.query(PolicyBinding).filter(
            PolicyBinding.tenant_id == tenant_id,
            PolicyBinding.policy_id == policy_id,
            PolicyBinding.target_type == target_type,
            PolicyBinding.target_id == target_id,
            PolicyBinding.status == "ACTIVE",
        )
        if exclude_binding_id:
            query = query.filter(PolicyBinding.id != exclude_binding_id)

        existing = query.all()
        for b in existing:
            b_from = b.effective_from or datetime.min.replace(tzinfo=timezone.utc)
            b_to = b.effective_to or datetime.max.replace(tzinfo=timezone.utc)

            n_from = effective_from or datetime.min.replace(tzinfo=timezone.utc)
            n_to = effective_to or datetime.max.replace(tzinfo=timezone.utc)

            # Check overlap: (n_from <= b_to) and (n_to >= b_from)
            if n_from <= b_to and n_to >= b_from:
                raise ValueError(
                    f"Conflicting active binding already exists (ID: {b.id}) covering overlapping dates"
                )

    def create_binding(
        self,
        tenant_id: UUID,
        user_id: UUID,
        binding_data: Dict[str, Any],
        correlation_id: Optional[UUID] = None,
    ) -> PolicyBinding:
        policy_id = binding_data["policy_id"]
        target_type = binding_data["target_type"]
        target_id = str(binding_data["target_id"])

        # 1. Validate Policy belongs to tenant
        policy = PolicyRepository.get_by_id(self.db, policy_id, tenant_id)
        if not policy:
            raise ValueError("Policy not found for tenant")

        # 2. Validate Target exists in tenant
        self.validate_target_exists(tenant_id, target_type, target_id)

        # 3. Validate Version Strategy
        version_strategy = binding_data.get("version_strategy", "LATEST")
        pinned_version_id = binding_data.get("pinned_policy_version_id")
        if version_strategy == "PINNED":
            if not pinned_version_id:
                raise ValueError("pinned_policy_version_id is required when version_strategy is PINNED")
            p_ver = PolicyVersionRepository.get_by_id(self.db, pinned_version_id, tenant_id)
            if not p_ver or p_ver.policy_id != policy_id:
                raise ValueError("pinned_policy_version_id does not belong to this policy")

        # 4. Check Date Overlap
        now = datetime.now(timezone.utc)
        effective_from = binding_data.get("effective_from", now)
        effective_to = binding_data.get("effective_to")
        self.check_duplicate_overlap(tenant_id, policy_id, target_type, target_id, effective_from, effective_to)

        # 5. Insert Binding
        binding = PolicyBinding(
            tenant_id=tenant_id,
            policy_id=policy_id,
            target_type=target_type,
            target_id=target_id,
            binding_scope=binding_data.get("binding_scope", "GLOBAL"),
            priority=binding_data.get("priority", policy.priority),
            is_mandatory=binding_data.get("is_mandatory", True),
            effective_from=effective_from,
            effective_to=effective_to,
            status="ACTIVE",
            version_strategy=version_strategy,
            pinned_policy_version_id=pinned_version_id,
            condition_json=binding_data.get("condition_json"),
        )
        PolicyBindingRepository.create(self.db, binding)

        # 6. Invalidate Cache
        self.cache.invalidate_tenant(str(tenant_id))

        # 7. Emit POLICY_BINDING_CREATED Event
        evt = GovernanceEventCreate(
            event_type="POLICY_BINDING_CREATED",
            event_category="POLICY_BINDING",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(user_id)},
            subject_json={
                "entity_type": "POLICY_BINDING",
                "entity_id": str(binding.id),
                "policy_id": str(policy_id),
                "target_type": target_type,
                "target_id": target_id,
            },
            correlation_id=correlation_id or uuid4(),
            payload_json={
                "policy_code": policy.policy_code,
                "target_type": target_type,
                "target_id": target_id,
                "version_strategy": version_strategy,
            },
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()
        return binding

    def suspend_binding(
        self,
        tenant_id: UUID,
        binding_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
        correlation_id: Optional[UUID] = None,
    ) -> PolicyBinding:
        binding = self.db.query(PolicyBinding).filter(
            PolicyBinding.id == binding_id, PolicyBinding.tenant_id == tenant_id
        ).first()
        if not binding:
            raise ValueError("Policy binding not found")

        binding.status = "SUSPENDED"
        self.cache.invalidate_tenant(str(tenant_id))

        now = datetime.now(timezone.utc)
        evt = GovernanceEventCreate(
            event_type="POLICY_BINDING_UPDATED",
            event_category="POLICY_BINDING",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(user_id)},
            subject_json={
                "entity_type": "POLICY_BINDING",
                "entity_id": str(binding.id),
                "policy_id": str(binding.policy_id),
            },
            correlation_id=correlation_id or uuid4(),
            payload_json={"status": "SUSPENDED", "reason": reason},
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()
        return binding

    def revoke_binding(
        self,
        tenant_id: UUID,
        binding_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
        correlation_id: Optional[UUID] = None,
    ) -> PolicyBinding:
        binding = self.db.query(PolicyBinding).filter(
            PolicyBinding.id == binding_id, PolicyBinding.tenant_id == tenant_id
        ).first()
        if not binding:
            raise ValueError("Policy binding not found")

        now = datetime.now(timezone.utc)
        binding.status = "DEACTIVATED"
        binding.effective_to = now
        self.cache.invalidate_tenant(str(tenant_id))

        evt = GovernanceEventCreate(
            event_type="POLICY_BINDING_DEACTIVATED",
            event_category="POLICY_BINDING",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(user_id)},
            subject_json={
                "entity_type": "POLICY_BINDING",
                "entity_id": str(binding.id),
                "policy_id": str(binding.policy_id),
            },
            correlation_id=correlation_id or uuid4(),
            payload_json={"status": "DEACTIVATED", "reason": reason},
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()
        return binding

    def resolve_effective_bindings(
        self,
        tenant_id: UUID,
        target_type: str,
        target_id: str,
        as_of: Optional[datetime] = None,
    ) -> List[PolicyBinding]:
        """
        Resolves effective bindings for a target with thread-locked in-process memory caching.
        """
        cache_key = f"bindings:{tenant_id}:{target_type}:{target_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if target_type == "AGENT":
            bindings = PolicyBindingRepository.resolve_effective_bindings_for_agent(
                self.db, tenant_id, target_id, as_of
            )
        else:
            bindings = PolicyBindingRepository.find_active_bindings(
                self.db, tenant_id, target_type, target_id, as_of
            )

        self.cache.set(cache_key, bindings, ttl_seconds=300)
        return bindings
