"""
Audit Export Service for generating JSON and CSV export packages with cryptographic manifest & audit logs.
"""
import uuid
import json
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.events.models import GovernanceEvent, EventExportLog
from app.shared.hashing import compute_sha256_hash

class AuditExportService:
    @staticmethod
    def generate_manifest(
        events: List[GovernanceEvent],
        filter_params: Dict[str, Any],
        export_format: str
    ) -> Dict[str, Any]:
        """Generates a cryptographic manifest dictionary for the audit package."""
        event_ids = [str(ev.event_id) for ev in events]
        return {
            "manifest_version": "1.0",
            "export_format": export_format.upper(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(events),
            "scope_json": filter_params,
            "event_ids": event_ids,
            "hash_algorithm": "SHA-256"
        }

    @classmethod
    def create_export(
        cls,
        db: Session,
        tenant_id: uuid.UUID,
        requested_by: uuid.UUID,
        filter_params: Optional[Dict[str, Any]] = None,
        export_format: str = "JSON"
    ) -> Dict[str, Any]:
        """
        Creates an audit export package for the specified scope, computes SHA-256 manifest hash,
        and logs the export event in `event_export_log`.
        """
        filter_params = filter_params or {}
        fmt = export_format.upper()
        if fmt not in ["JSON", "CSV"]:
            fmt = "JSON"

        query = db.query(GovernanceEvent).filter(GovernanceEvent.tenant_id == tenant_id)

        if filter_params.get("event_type"):
            query = query.filter(GovernanceEvent.event_type == filter_params["event_type"])
        if filter_params.get("event_category"):
            query = query.filter(GovernanceEvent.event_category == filter_params["event_category"])
        if filter_params.get("classification"):
            query = query.filter(GovernanceEvent.classification == filter_params["classification"])

        events = query.order_by(GovernanceEvent.occurred_at.asc()).all()

        manifest = cls.generate_manifest(events, filter_params, fmt)

        # Build Export Content
        serialized_events = []
        for ev in events:
            serialized_events.append({
                "event_id": str(ev.event_id),
                "tenant_id": str(ev.tenant_id),
                "event_type": ev.event_type,
                "event_category": ev.event_category,
                "event_version": ev.event_version,
                "occurred_at": ev.occurred_at.isoformat() if ev.occurred_at else None,
                "recorded_at": ev.recorded_at.isoformat() if ev.recorded_at else None,
                "source_service": ev.source_service,
                "actor_json": ev.actor_json,
                "subject_json": ev.subject_json,
                "correlation_id": str(ev.correlation_id) if ev.correlation_id else None,
                "causation_id": str(ev.causation_id) if ev.causation_id else None,
                "risk_context_json": ev.risk_context_json,
                "policy_context_json": ev.policy_context_json,
                "payload_json": ev.payload_json,
                "classification": ev.classification,
                "retention_class": ev.retention_class,
                "event_hash": ev.event_hash
            })

        export_package = {
            "manifest": manifest,
            "events": serialized_events
        }

        package_str = json.dumps(export_package, sort_keys=True)
        export_hash = compute_sha256_hash(package_str)

        # Log into event_export_log
        export_log = EventExportLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            exported_by=requested_by,
            filter_params_json=filter_params,
            format=fmt,
            record_count=len(events),
            file_hash=export_hash
        )
        db.add(export_log)
        db.commit()
        db.refresh(export_log)

        return {
            "export_id": str(export_log.id),
            "tenant_id": str(tenant_id),
            "requested_by": str(requested_by),
            "format": fmt,
            "event_count": len(events),
            "export_hash": export_hash,
            "file_reference": f"export_{export_log.id}.{fmt.lower()}",
            "manifest": manifest,
            "created_at": export_log.created_at.isoformat()
        }

    @staticmethod
    def get_export_status(
        db: Session,
        tenant_id: uuid.UUID,
        export_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Retrieves an existing audit export log record by ID."""
        export_log = db.query(EventExportLog).filter(
            EventExportLog.id == export_id,
            EventExportLog.tenant_id == tenant_id
        ).first()

        if not export_log:
            raise HTTPException(status_code=404, detail=f"Export package '{export_id}' not found")

        return {
            "export_id": str(export_log.id),
            "tenant_id": str(export_log.tenant_id),
            "exported_by": str(export_log.exported_by),
            "filter_params_json": export_log.filter_params_json,
            "format": export_log.format,
            "record_count": export_log.record_count,
            "export_hash": export_log.file_hash,
            "status": "COMPLETED",
            "created_at": export_log.created_at.isoformat()
        }
