from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.modules.policy_engine.models import (
    GovernancePolicy,
    PolicyVersion,
    PolicyRule,
    PolicyException,
)
from app.modules.relationship.models import PolicyBinding, ObjectResponsibility
from app.modules.policy_engine.repository import (
    PolicyRepository,
    PolicyVersionRepository,
    PolicyRuleRepository,
    PolicyBindingRepository,
    PolicyExceptionRepository,
)
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate


class PolicyVersionService:
    def __init__(self, db: Session):
        self.db = db
        self.publisher = EventPublisherService()

    @staticmethod
    def validate_rules(rules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validates syntax and structural requirements of policy rules."""
        if not isinstance(rules_data, list):
            raise ValueError("rules_data must be a list of rule definitions")

        validated = []
        valid_actions = {"ALLOW", "DENY", "REQUIRE_APPROVAL", "MODIFY"}
        valid_targets = {"AGENT", "TOOL", "DATA_SOURCE", "WORKFLOW", "PROMPT", "RUNTIME"}

        for idx, r in enumerate(rules_data):
            rule_code = r.get("rule_code")
            name = r.get("name")
            action = r.get("action", "DENY")
            target_type = r.get("target_type", "AGENT")

            if not rule_code:
                raise ValueError(f"Rule at index {idx} is missing required 'rule_code'")
            if not name:
                raise ValueError(f"Rule at index {idx} is missing required 'name'")
            if action not in valid_actions:
                raise ValueError(f"Invalid rule action '{action}'. Must be one of {valid_actions}")
            if target_type not in valid_targets:
                raise ValueError(f"Invalid rule target_type '{target_type}'. Must be one of {valid_targets}")

            validated.append(
                {
                    "rule_code": rule_code,
                    "name": name,
                    "description": r.get("description"),
                    "rule_type": r.get("rule_type", "GENERAL"),
                    "target_type": target_type,
                    "target_id": str(r.get("target_id", "*")),
                    "condition_expression": r.get("condition_expression", "true"),
                    "condition_json": r.get("condition_json", {}),
                    "action": action,
                    "severity": r.get("severity", "MEDIUM"),
                    "execution_order": r.get("execution_order", idx + 1),
                    "is_active": r.get("is_active", True),
                }
            )
        return validated

    def create_draft_version(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        user_id: UUID,
        changelog: Optional[str] = None,
        rules_data: Optional[List[Dict[str, Any]]] = None,
        correlation_id: Optional[UUID] = None,
    ) -> PolicyVersion:
        policy = PolicyRepository.get_by_id(self.db, policy_id, tenant_id)
        if not policy:
            raise ValueError("Policy not found")

        # Determine next version number
        existing_versions = PolicyVersionRepository.list_versions(self.db, policy_id, tenant_id)
        next_ver_num = (existing_versions[0].version_number + 1) if existing_versions else 1

        validated_rules = self.validate_rules(rules_data or [])

        version = PolicyVersion(
            tenant_id=tenant_id,
            policy_id=policy_id,
            version_number=next_ver_num,
            status="DRAFT",
            changelog=changelog or f"Draft version {next_ver_num}",
            rules_count=len(validated_rules),
        )
        PolicyVersionRepository.create_draft(self.db, version)

        # Insert rules
        for r_dict in validated_rules:
            rule = PolicyRule(
                tenant_id=tenant_id,
                policy_version_id=version.id,
                rule_code=r_dict["rule_code"],
                name=r_dict["name"],
                description=r_dict.get("description"),
                rule_type=r_dict["rule_type"],
                target_type=r_dict["target_type"],
                target_id=r_dict["target_id"],
                condition_expression=r_dict["condition_expression"],
                condition_json=r_dict["condition_json"],
                action=r_dict["action"],
                severity=r_dict["severity"],
                execution_order=r_dict["execution_order"],
                is_active=r_dict["is_active"],
            )
            PolicyRuleRepository.create(self.db, rule)

        # Emit POLICY_VERSION_CREATED event
        now = datetime.now(timezone.utc)
        evt = GovernanceEventCreate(
            event_type="POLICY_VERSION_CREATED",
            event_category="POLICY",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(user_id)},
            subject_json={
                "entity_type": "POLICY_VERSION",
                "entity_id": str(version.id),
                "policy_id": str(policy_id),
                "version_number": next_ver_num,
            },
            correlation_id=correlation_id or uuid4(),
            payload_json={"policy_code": policy.policy_code, "version_number": next_ver_num, "rules_count": len(validated_rules)},
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()
        return version

    def update_draft_version(
        self,
        tenant_id: UUID,
        version_id: UUID,
        changelog: Optional[str] = None,
        rules_data: Optional[List[Dict[str, Any]]] = None,
    ) -> PolicyVersion:
        version = PolicyVersionRepository.get_by_id(self.db, version_id, tenant_id)
        if not version:
            raise ValueError("Policy version not found")

        # Repository-level immutability enforcement
        if changelog is not None:
            version.changelog = changelog

        PolicyVersionRepository.update_draft(self.db, version)

        if rules_data is not None:
            validated_rules = self.validate_rules(rules_data)
            # Remove existing draft rules
            self.db.query(PolicyRule).filter(
                PolicyRule.policy_version_id == version.id,
                PolicyRule.tenant_id == tenant_id,
            ).delete()
            # Re-insert rules
            for r_dict in validated_rules:
                rule = PolicyRule(
                    tenant_id=tenant_id,
                    policy_version_id=version.id,
                    rule_code=r_dict["rule_code"],
                    name=r_dict["name"],
                    description=r_dict.get("description"),
                    rule_type=r_dict["rule_type"],
                    target_type=r_dict["target_type"],
                    target_id=r_dict["target_id"],
                    condition_expression=r_dict["condition_expression"],
                    condition_json=r_dict["condition_json"],
                    action=r_dict["action"],
                    severity=r_dict["severity"],
                    execution_order=r_dict["execution_order"],
                    is_active=r_dict["is_active"],
                )
                PolicyRuleRepository.create(self.db, rule)
            version.rules_count = len(validated_rules)

        self.db.commit()
        return version

    def activate_version(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        version_id: UUID,
        user_id: UUID,
        correlation_id: Optional[UUID] = None,
    ) -> PolicyVersion:
        policy = PolicyRepository.get_by_id(self.db, policy_id, tenant_id)
        if not policy:
            raise ValueError("Policy not found")

        version = PolicyVersionRepository.activate_version(self.db, version_id, tenant_id, user_id)
        policy.status = "ACTIVE"

        # Emit POLICY_VERSION_ACTIVATED event
        now = datetime.now(timezone.utc)
        evt = GovernanceEventCreate(
            event_type="POLICY_VERSION_ACTIVATED",
            event_category="POLICY",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(user_id)},
            subject_json={
                "entity_type": "POLICY_VERSION",
                "entity_id": str(version.id),
                "policy_id": str(policy_id),
                "version_number": version.version_number,
            },
            correlation_id=correlation_id or uuid4(),
            payload_json={"policy_code": policy.policy_code, "version_number": version.version_number},
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()
        return version


class PolicyService:
    def __init__(self, db: Session):
        self.db = db
        self.publisher = EventPublisherService()
        self.version_service = PolicyVersionService(db)

    def list_policies(
        self,
        tenant_id: UUID,
        category: Optional[str] = None,
        status: Optional[str] = None,
        as_of: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[GovernancePolicy]:
        return PolicyRepository.list_policies(self.db, tenant_id, category, status, as_of, limit, offset)

    def get_policy(self, policy_id: UUID, tenant_id: UUID) -> Optional[GovernancePolicy]:
        return PolicyRepository.get_by_id(self.db, policy_id, tenant_id)

    def create_policy(
        self,
        tenant_id: UUID,
        owner_user_id: UUID,
        policy_data: Dict[str, Any],
        initial_rules: Optional[List[Dict[str, Any]]] = None,
        correlation_id: Optional[UUID] = None,
    ) -> GovernancePolicy:
        now = datetime.now(timezone.utc)
        policy = GovernancePolicy(
            tenant_id=tenant_id,
            owner_user_id=owner_user_id,
            policy_code=policy_data["policy_code"],
            name=policy_data["name"],
            description=policy_data.get("description"),
            category=policy_data.get("category", "GENERAL"),
            enforcement_mode=policy_data.get("enforcement_mode", "BLOCKING"),
            priority=policy_data.get("priority", 100),
            effective_from=policy_data.get("effective_from", now),
            effective_to=policy_data.get("effective_to"),
            status="DRAFT",
        )
        PolicyRepository.create(self.db, policy)

        # Synchronize into object_responsibilities
        resp = ObjectResponsibility(
            tenant_id=tenant_id,
            object_type="POLICY",
            object_id=str(policy.id),
            actor_type="USER",
            actor_id=str(owner_user_id),
            responsibility_type="OWNER",
            is_primary=True,
            effective_from=now,
            status="ACTIVE",
        )
        self.db.add(resp)

        # Emit POLICY_CREATED event
        corr_id = correlation_id or uuid4()
        evt = GovernanceEventCreate(
            event_type="POLICY_CREATED",
            event_category="POLICY",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(owner_user_id)},
            subject_json={
                "entity_type": "POLICY",
                "entity_id": str(policy.id),
                "policy_code": policy.policy_code,
            },
            correlation_id=corr_id,
            payload_json={
                "policy_code": policy.policy_code,
                "name": policy.name,
                "category": policy.category,
                "enforcement_mode": policy.enforcement_mode,
            },
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()

        # Optionally create initial draft version
        if initial_rules is not None:
            self.version_service.create_draft_version(
                tenant_id=tenant_id,
                policy_id=policy.id,
                user_id=owner_user_id,
                changelog="Initial baseline draft",
                rules_data=initial_rules,
                correlation_id=corr_id,
            )

        return policy

    def suspend_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
        correlation_id: Optional[UUID] = None,
    ) -> GovernancePolicy:
        policy = PolicyRepository.get_by_id(self.db, policy_id, tenant_id)
        if not policy:
            raise ValueError("Policy not found")

        policy.status = "SUSPENDED"

        # Emit POLICY_SUSPENDED event
        now = datetime.now(timezone.utc)
        evt = GovernanceEventCreate(
            event_type="POLICY_SUSPENDED",
            event_category="POLICY",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(user_id)},
            subject_json={
                "entity_type": "POLICY",
                "entity_id": str(policy.id),
                "policy_code": policy.policy_code,
            },
            correlation_id=correlation_id or uuid4(),
            payload_json={"policy_code": policy.policy_code, "reason": reason},
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()
        return policy

    def retire_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
        correlation_id: Optional[UUID] = None,
    ) -> GovernancePolicy:
        policy = PolicyRepository.get_by_id(self.db, policy_id, tenant_id)
        if not policy:
            raise ValueError("Policy not found")

        policy.status = "RETIRED"

        # Mark active versions as RETIRED
        active_versions = (
            self.db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_id == policy.id,
                PolicyVersion.tenant_id == tenant_id,
                PolicyVersion.status == "ACTIVE",
            )
            .all()
        )
        for v in active_versions:
            v.status = "RETIRED"

        # Emit POLICY_RETIRED event
        now = datetime.now(timezone.utc)
        evt = GovernanceEventCreate(
            event_type="POLICY_RETIRED",
            event_category="POLICY",
            occurred_at=now,
            source_service="policy_engine",
            actor_json={"user_id": str(user_id)},
            subject_json={
                "entity_type": "POLICY",
                "entity_id": str(policy.id),
                "policy_code": policy.policy_code,
            },
            correlation_id=correlation_id or uuid4(),
            payload_json={"policy_code": policy.policy_code, "reason": reason},
        )
        self.publisher.publish_event(self.db, evt, tenant_id=tenant_id)
        self.db.commit()
        return policy

    def list_versions(self, policy_id: UUID, tenant_id: UUID) -> List[PolicyVersion]:
        return PolicyVersionRepository.list_versions(self.db, policy_id, tenant_id)

    def get_active_version(self, policy_id: UUID, tenant_id: UUID) -> Optional[PolicyVersion]:
        return PolicyVersionRepository.get_active_version(self.db, policy_id, tenant_id)

    def list_bindings(self, policy_id: UUID, tenant_id: UUID) -> List[PolicyBinding]:
        return PolicyBindingRepository.list_by_policy(self.db, policy_id, tenant_id)

    def bind_policy(self, tenant_id: UUID, binding_data: Dict[str, Any]) -> PolicyBinding:
        binding = PolicyBinding(
            tenant_id=tenant_id,
            policy_id=binding_data["policy_id"],
            target_type=binding_data["target_type"],
            target_id=str(binding_data["target_id"]),
            binding_scope=binding_data.get("binding_scope", "GLOBAL"),
            priority=binding_data.get("priority", 100),
            is_mandatory=binding_data.get("is_mandatory", True),
            effective_from=binding_data.get("effective_from", datetime.now(timezone.utc)),
            effective_to=binding_data.get("effective_to"),
            status="ACTIVE",
            version_strategy=binding_data.get("version_strategy", "LATEST"),
            pinned_policy_version_id=binding_data.get("pinned_policy_version_id"),
            condition_json=binding_data.get("condition_json"),
        )
        PolicyBindingRepository.create(self.db, binding)
        self.db.commit()
        return binding
