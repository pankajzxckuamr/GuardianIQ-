from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.modules.workflow_execution.models import WorkflowRunOutput
from app.modules.workflow_execution.output_parser import ParsedOutput
from app.shared.db_compat import db_flush

class RunOutputService:
    @staticmethod
    def check_high_risk(parsed_output: ParsedOutput) -> bool:
        if parsed_output.severity in ["HIGH", "CRITICAL"]:
            return True
        if parsed_output.risk_score is not None and parsed_output.risk_score >= 75.0:
            return True
        return False

    @staticmethod
    async def save_output(run_id: UUID, parsed_output: ParsedOutput, db: Session) -> WorkflowRunOutput:
        findings_dict = [
            {
                "finding_code": f.finding_code,
                "entity_type": f.entity_type,
                "entity_code": f.entity_code,
                "message": f.message
            }
            for f in parsed_output.findings
        ]
        
        recs_dict = [
            {
                "recommendation_type": r.recommendation_type,
                "priority": r.priority,
                "recommended_action": r.recommended_action
            }
            for r in parsed_output.recommendations
        ]
        
        output = WorkflowRunOutput(
            id=uuid4(),
            run_id=run_id,
            output_type="AGENT_EVALUATION",
            severity=parsed_output.severity,
            risk_score=parsed_output.risk_score,
            findings_json=findings_dict,
            recommendations_json=recs_dict,
            evidence_json=parsed_output.evidence,
            raw_output_json={"raw": parsed_output.raw_output} if parsed_output.raw_output else {},
            parse_status=parsed_output.parse_status,
            tenant_id=None # Defaulting, assuming the caller can patch or the DB populates it
        )
        db.add(output)
        await db_flush(db)
        return output
