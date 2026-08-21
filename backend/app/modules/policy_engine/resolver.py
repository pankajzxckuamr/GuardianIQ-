from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime, timezone
import hashlib
import json
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.relationship.models import PolicyBinding, GenericRelationship
from app.modules.policy_engine.models import (
    GovernancePolicy,
    PolicyVersion,
    PolicyRule,
)
from app.modules.agent.models import Agent
from app.modules.relationship.repository import RelationshipRepository
from app.modules.policy_engine.repository import (
    PolicyRepository,
    PolicyVersionRepository,
    PolicyRuleRepository,
    PolicyBindingRepository,
)


@dataclass
class ResolvedPolicy:
    policy: GovernancePolicy
    version: PolicyVersion
    rules: List[PolicyRule]
    binding: PolicyBinding
    resolved_scope: str  # DIRECT, WORKFLOW, DEPARTMENT, GLOBAL
    source_target_type: str
    source_target_id: str
    precedence_rank: int


@dataclass
class ResolvedPolicySet:
    resolved_policies: List[ResolvedPolicy] = field(default_factory=list)
    resolution_hash: str = ""
    resolution_trace: List[Dict[str, Any]] = field(default_factory=list)


class BindingResolver:
    """
    Enterprise Policy Binding Resolution Engine.
    Resolves multi-level hierarchical policy bindings across Direct, Graph-related,
    Workflow, Department, and Global scopes with deterministic specificity ordering.
    """

    SCOPE_SPECIFICITY = {
        "DIRECT": 1,
        "WORKFLOW": 2,
        "DEPARTMENT": 3,
        "GLOBAL": 4,
        "TENANT": 4,
    }

    def __init__(self, db: Session):
        self.db = db

    def resolve_runtime_policies(
        self,
        tenant_id: UUID,
        agent_id: Optional[str] = None,
        tool_ids: Optional[List[str]] = None,
        data_source_ids: Optional[List[str]] = None,
        model_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        as_of: Optional[datetime] = None,
    ) -> ResolvedPolicySet:
        now = as_of or datetime.now(timezone.utc)
        candidate_bindings: List[Dict[str, Any]] = []

        # 1. Direct Bindings
        if agent_id:
            for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "AGENT", str(agent_id), now):
                candidate_bindings.append({
                    "binding": b,
                    "scope": "DIRECT",
                    "source_type": "AGENT",
                    "source_id": str(agent_id),
                })

        if tool_ids:
            for tid in tool_ids:
                for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "TOOL", str(tid), now):
                    candidate_bindings.append({
                        "binding": b,
                        "scope": "DIRECT",
                        "source_type": "TOOL",
                        "source_id": str(tid),
                    })

        if data_source_ids:
            for dsid in data_source_ids:
                for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "DATA_SOURCE", str(dsid), now):
                    candidate_bindings.append({
                        "binding": b,
                        "scope": "DIRECT",
                        "source_type": "DATA_SOURCE",
                        "source_id": str(dsid),
                    })

        if model_id:
            for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "MODEL", str(model_id), now):
                candidate_bindings.append({
                    "binding": b,
                    "scope": "DIRECT",
                    "source_type": "MODEL",
                    "source_id": str(model_id),
                })

        if workflow_id:
            for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "WORKFLOW", str(workflow_id), now):
                candidate_bindings.append({
                    "binding": b,
                    "scope": "WORKFLOW",
                    "source_type": "WORKFLOW",
                    "source_id": str(workflow_id),
                })

        # 2. Graph Relationship Inferred Bindings (Agent -> Tools, DataSources, Models, Workflows)
        if agent_id:
            graph_bindings = self._resolve_graph_relationships(tenant_id, agent_id, now)
            candidate_bindings.extend(graph_bindings)

        # 3. Department & Global / Tenant-Wide Mandatory Bindings
        global_bindings = self._resolve_global_and_tenant_bindings(tenant_id, agent_id, now)
        candidate_bindings.extend(global_bindings)

        # 4. Deduplicate & Apply Scope Specificity Override (DIRECT > WORKFLOW > DEPARTMENT > GLOBAL)
        # and Priority Ordering (Lower integer priority = higher precedence)
        policy_map: Dict[UUID, Dict[str, Any]] = {}
        for item in candidate_bindings:
            b: PolicyBinding = item["binding"]
            p_id = b.policy_id
            scope_rank = self.SCOPE_SPECIFICITY.get(item["scope"], 5)

            if p_id not in policy_map:
                policy_map[p_id] = {**item, "scope_rank": scope_rank}
            else:
                existing = policy_map[p_id]
                # If new item is more specific (lower scope_rank), replace
                if scope_rank < existing["scope_rank"]:
                    policy_map[p_id] = {**item, "scope_rank": scope_rank}
                elif scope_rank == existing["scope_rank"]:
                    # If same scope, prefer higher priority (lower numerical priority)
                    if b.priority < existing["binding"].priority:
                        policy_map[p_id] = {**item, "scope_rank": scope_rank}

        # 5. Load Active Policies, Versions, and Rules
        resolved_list: List[ResolvedPolicy] = []
        resolution_trace: List[Dict[str, Any]] = []

        # Sort candidate items by (scope_rank ASC, binding.priority ASC)
        sorted_candidates = sorted(
            list(policy_map.values()),
            key=lambda x: (x["scope_rank"], x["binding"].priority)
        )

        for rank_idx, item in enumerate(sorted_candidates, start=1):
            b: PolicyBinding = item["binding"]
            policy = PolicyRepository.get_by_id(self.db, b.policy_id, tenant_id)
            if not policy or policy.status != "ACTIVE":
                continue

            # Select Version
            version: Optional[PolicyVersion] = None
            if b.version_strategy == "PINNED" and b.pinned_policy_version_id:
                version = PolicyVersionRepository.get_by_id(self.db, b.pinned_policy_version_id, tenant_id)
            else:
                version = PolicyVersionRepository.get_active_version(self.db, policy.id, tenant_id)

            if not version:
                continue

            # Load Rules
            rules = PolicyRuleRepository.list_rules_by_version(self.db, version.id, tenant_id)

            resolved_policy = ResolvedPolicy(
                policy=policy,
                version=version,
                rules=rules,
                binding=b,
                resolved_scope=item["scope"],
                source_target_type=item["source_type"],
                source_target_id=item["source_id"],
                precedence_rank=rank_idx,
            )
            resolved_list.append(resolved_policy)

            resolution_trace.append({
                "precedence_rank": rank_idx,
                "policy_id": str(policy.id),
                "policy_code": policy.policy_code,
                "version_number": version.version_number,
                "version_status": version.status,
                "version_strategy": b.version_strategy,
                "resolved_scope": item["scope"],
                "source_target_type": item["source_type"],
                "source_target_id": item["source_id"],
                "priority": b.priority,
                "rules_count": len(rules),
            })

        # 6. Compute Deterministic SHA-256 Resolution Hash
        res_hash = self._compute_resolution_hash(resolved_list)

        return ResolvedPolicySet(
            resolved_policies=resolved_list,
            resolution_hash=res_hash,
            resolution_trace=resolution_trace,
        )

    def _resolve_graph_relationships(
        self, tenant_id: UUID, agent_id: str, as_of: datetime
    ) -> List[Dict[str, Any]]:
        """
        Resolves indirect relationships: USES_TOOL/USES, USES_DATA_SOURCE/USES,
        USES_MODEL/USES, PARTICIPATES_IN_WORKFLOW/GOVERNED_BY.
        """
        results: List[Dict[str, Any]] = []

        rels = RelationshipRepository.find_active(
            db=self.db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=agent_id,
            as_of=as_of,
        )

        for rel in rels:
            r_type = rel.relationship_type
            t_type = rel.target_type
            t_id = rel.target_id

            # 1. Workflow Relationships
            if r_type in ["PARTICIPATES_IN_WORKFLOW", "GOVERNED_BY"] or (r_type == "USES" and t_type == "WORKFLOW"):
                for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "WORKFLOW", t_id, as_of):
                    results.append({
                        "binding": b,
                        "scope": "WORKFLOW",
                        "source_type": "WORKFLOW",
                        "source_id": t_id,
                    })

            # 2. Tool Relationships (USES_TOOL or USES)
            elif r_type == "USES_TOOL" or (r_type == "USES" and t_type == "TOOL"):
                for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "TOOL", t_id, as_of):
                    results.append({
                        "binding": b,
                        "scope": "DIRECT",
                        "source_type": "TOOL",
                        "source_id": t_id,
                    })

            # 3. Data Source Relationships (USES_DATA_SOURCE or USES)
            elif r_type == "USES_DATA_SOURCE" or (r_type == "USES" and t_type in ["DATA_SOURCE", "DATASOURCE"]):
                for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "DATA_SOURCE", t_id, as_of):
                    results.append({
                        "binding": b,
                        "scope": "DIRECT",
                        "source_type": "DATA_SOURCE",
                        "source_id": t_id,
                    })

            # 4. Model Relationships (USES_MODEL or USES)
            elif r_type == "USES_MODEL" or (r_type == "USES" and t_type in ["MODEL", "AI_MODEL"]):
                for b in PolicyBindingRepository.find_active_bindings(self.db, tenant_id, "MODEL", t_id, as_of):
                    results.append({
                        "binding": b,
                        "scope": "DIRECT",
                        "source_type": "MODEL",
                        "source_id": t_id,
                    })

        return results

    def _resolve_global_and_tenant_bindings(
        self, tenant_id: UUID, agent_id: Optional[str], as_of: datetime
    ) -> List[Dict[str, Any]]:
        """Resolves department/BU bindings and tenant/global mandatory bindings."""
        results: List[Dict[str, Any]] = []

        # 1. Department Bindings
        if agent_id:
            try:
                agent = self.db.query(Agent).filter(Agent.id == UUID(agent_id), Agent.tenant_id == tenant_id).first()
                if agent and agent.department_id:
                    dept_bindings = PolicyBindingRepository.find_active_bindings(
                        self.db, tenant_id, "DEPARTMENT", str(agent.department_id), as_of
                    )
                    for b in dept_bindings:
                        results.append({
                            "binding": b,
                            "scope": "DEPARTMENT",
                            "source_type": "DEPARTMENT",
                            "source_id": str(agent.department_id),
                        })
            except Exception:
                pass

        # 2. Global / Tenant Mandatory Bindings
        global_bindings = (
            self.db.query(PolicyBinding)
            .filter(
                PolicyBinding.tenant_id == tenant_id,
                PolicyBinding.status == "ACTIVE",
                or_(PolicyBinding.binding_scope == "GLOBAL", PolicyBinding.binding_scope == "TENANT"),
            )
            .all()
        )
        for b in global_bindings:
            results.append({
                "binding": b,
                "scope": "GLOBAL",
                "source_type": "TENANT",
                "source_id": str(tenant_id),
            })

        return results

    @staticmethod
    def _compute_resolution_hash(resolved_policies: List[ResolvedPolicy]) -> str:
        """Computes deterministic SHA-256 hash across sorted resolved policies, versions, and rules."""
        elements = []
        for rp in resolved_policies:
            rule_ids = [str(r.id) for r in rp.rules]
            elements.append({
                "policy_id": str(rp.policy.id),
                "version_id": str(rp.version.id),
                "version_number": rp.version.version_number,
                "rule_ids": rule_ids,
                "scope": rp.resolved_scope,
                "priority": rp.binding.priority,
            })

        serialized = json.dumps(elements, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
