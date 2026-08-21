from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc, asc

from app.modules.policy_engine.models import (
    GovernancePolicy,
    PolicyVersion,
    PolicyRule,
    PolicyException,
    PolicyEvaluation,
    PolicyRuleEvaluation,
    EnforcementDecision,
    PolicyApproval,
)
from app.modules.relationship.models import PolicyBinding
from app.modules.relationship.repository import RelationshipRepository
from app.modules.policy_engine.query_utils import (
    apply_tenant_filter,
    apply_effective_date_filter,
    apply_pagination,
)


class PolicyRepository:
    @staticmethod
    def get_by_id(db: Session, policy_id: UUID, tenant_id: UUID) -> Optional[GovernancePolicy]:
        return (
            db.query(GovernancePolicy)
            .filter(GovernancePolicy.id == policy_id, GovernancePolicy.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def get_by_code(db: Session, policy_code: str, tenant_id: UUID) -> Optional[GovernancePolicy]:
        return (
            db.query(GovernancePolicy)
            .filter(GovernancePolicy.policy_code == policy_code, GovernancePolicy.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def list_policies(
        db: Session,
        tenant_id: UUID,
        category: Optional[str] = None,
        status: Optional[str] = None,
        as_of: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[GovernancePolicy]:
        query = db.query(GovernancePolicy)
        query = apply_tenant_filter(query, GovernancePolicy, tenant_id)

        if category:
            query = query.filter(GovernancePolicy.category == category)
        if status:
            query = query.filter(GovernancePolicy.status == status)
        if as_of:
            query = apply_effective_date_filter(query, GovernancePolicy, as_of)

        query = query.order_by(GovernancePolicy.priority.asc(), GovernancePolicy.created_at.desc())
        return apply_pagination(query, limit, offset).all()

    @staticmethod
    def create(db: Session, policy: GovernancePolicy) -> GovernancePolicy:
        db.add(policy)
        db.flush()
        return policy

    @staticmethod
    def update(db: Session, policy: GovernancePolicy) -> GovernancePolicy:
        db.flush()
        return policy


class PolicyVersionRepository:
    @staticmethod
    def get_by_id(db: Session, version_id: UUID, tenant_id: UUID) -> Optional[PolicyVersion]:
        return (
            db.query(PolicyVersion)
            .filter(PolicyVersion.id == version_id, PolicyVersion.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def get_active_version(db: Session, policy_id: UUID, tenant_id: UUID) -> Optional[PolicyVersion]:
        return (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.tenant_id == tenant_id,
                PolicyVersion.status == "ACTIVE",
            )
            .order_by(PolicyVersion.version_number.desc())
            .first()
        )

    @staticmethod
    def list_versions(
        db: Session, policy_id: UUID, tenant_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[PolicyVersion]:
        query = db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy_id, PolicyVersion.tenant_id == tenant_id
        )
        query = query.order_by(PolicyVersion.version_number.desc())
        return apply_pagination(query, limit, offset).all()

    @staticmethod
    def create_draft(db: Session, version: PolicyVersion) -> PolicyVersion:
        version.status = "DRAFT"
        db.add(version)
        db.flush()
        return version

    @staticmethod
    def update_draft(db: Session, version: PolicyVersion) -> PolicyVersion:
        # Strict immutability check
        if version.status not in ["DRAFT", "IN_REVIEW"]:
            raise ValueError(
                f"Cannot modify immutable policy version with status '{version.status}'. Only DRAFT versions are mutable."
            )
        db.flush()
        return version

    @staticmethod
    def activate_version(db: Session, version_id: UUID, tenant_id: UUID, activated_by_user_id: UUID) -> PolicyVersion:
        target = PolicyVersionRepository.get_by_id(db, version_id, tenant_id)
        if not target:
            raise ValueError("Policy version not found")

        now = datetime.now(timezone.utc)
        # Supersede any currently active version for this policy
        active_versions = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_id == target.policy_id,
                PolicyVersion.tenant_id == tenant_id,
                PolicyVersion.status == "ACTIVE",
                PolicyVersion.id != target.id,
            )
            .all()
        )
        for v in active_versions:
            v.status = "SUPERSEDED"

        target.status = "ACTIVE"
        target.activated_at = now
        target.activated_by = activated_by_user_id
        db.flush()
        return target


class PolicyRuleRepository:
    @staticmethod
    def list_rules_by_version(db: Session, version_id: UUID, tenant_id: UUID) -> List[PolicyRule]:
        return (
            db.query(PolicyRule)
            .filter(PolicyRule.policy_version_id == version_id, PolicyRule.tenant_id == tenant_id)
            .order_by(PolicyRule.execution_order.asc())
            .all()
        )

    @staticmethod
    def create(db: Session, rule: PolicyRule) -> PolicyRule:
        db.add(rule)
        db.flush()
        return rule

    @staticmethod
    def bulk_create(db: Session, rules: List[PolicyRule]) -> List[PolicyRule]:
        for r in rules:
            db.add(r)
        db.flush()
        return rules


class PolicyBindingRepository:
    @staticmethod
    def find_active_bindings(
        db: Session,
        tenant_id: UUID,
        target_type: str,
        target_id: str,
        as_of: Optional[datetime] = None,
    ) -> List[PolicyBinding]:
        """
        Finds active direct bindings for a target entity respecting temporal validity windows.
        """
        query = db.query(PolicyBinding).filter(
            PolicyBinding.tenant_id == tenant_id,
            PolicyBinding.target_type == target_type,
            PolicyBinding.target_id == target_id,
            PolicyBinding.status == "ACTIVE",
        )
        query = apply_effective_date_filter(query, PolicyBinding, as_of)
        return query.order_by(PolicyBinding.priority.asc()).all()

    @staticmethod
    def resolve_effective_bindings_for_agent(
        db: Session,
        tenant_id: UUID,
        agent_id: str,
        as_of: Optional[datetime] = None,
    ) -> List[PolicyBinding]:
        """
        Resolves both direct bindings on the agent and transitive bindings from parent workflows
        or departments using RelationshipRepository.find_active (strictly respecting effective dates).
        """
        bindings_map: Dict[UUID, PolicyBinding] = {}

        # 1. Direct Agent Bindings
        direct = PolicyBindingRepository.find_active_bindings(db, tenant_id, "AGENT", agent_id, as_of)
        for b in direct:
            bindings_map[b.policy_id] = b

        # 2. Transitive Workflow Bindings (Agent GOVERNED_BY Workflow or USES_WORKFLOW)
        parent_rels = RelationshipRepository.find_active(
            db=db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=agent_id,
            relationship_type="GOVERNED_BY",
            as_of=as_of,
        )
        for rel in parent_rels:
            wf_bindings = PolicyBindingRepository.find_active_bindings(
                db, tenant_id, rel.target_type, rel.target_id, as_of
            )
            for b in wf_bindings:
                if b.policy_id not in bindings_map:
                    bindings_map[b.policy_id] = b

        return sorted(list(bindings_map.values()), key=lambda x: x.priority)

    @staticmethod
    def create(db: Session, binding: PolicyBinding) -> PolicyBinding:
        db.add(binding)
        db.flush()
        return binding

    @staticmethod
    def list_by_policy(
        db: Session, policy_id: UUID, tenant_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[PolicyBinding]:
        query = db.query(PolicyBinding).filter(
            PolicyBinding.policy_id == policy_id, PolicyBinding.tenant_id == tenant_id
        )
        return apply_pagination(query, limit, offset).all()


class PolicyExceptionRepository:
    @staticmethod
    def find_active_exceptions(
        db: Session,
        tenant_id: UUID,
        policy_id: UUID,
        target_type: str,
        target_id: str,
        as_of: Optional[datetime] = None,
    ) -> List[PolicyException]:
        ts = as_of or datetime.now(timezone.utc)
        return (
            db.query(PolicyException)
            .filter(
                PolicyException.tenant_id == tenant_id,
                PolicyException.policy_id == policy_id,
                PolicyException.target_type == target_type,
                PolicyException.target_id == target_id,
                PolicyException.status == "ACTIVE",
                PolicyException.valid_from <= ts,
                PolicyException.valid_to >= ts,
            )
            .all()
        )

    @staticmethod
    def create(db: Session, exception: PolicyException) -> PolicyException:
        db.add(exception)
        db.flush()
        return exception


class PolicyEvaluationRepository:
    @staticmethod
    def log_evaluation(
        db: Session,
        evaluation: PolicyEvaluation,
        rule_evaluations: Optional[List[PolicyRuleEvaluation]] = None,
    ) -> PolicyEvaluation:
        db.add(evaluation)
        db.flush()

        if rule_evaluations:
            for re in rule_evaluations:
                re.evaluation_id = evaluation.id
                re.tenant_id = evaluation.tenant_id
                db.add(re)
            db.flush()
        return evaluation
