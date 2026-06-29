import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Finding:
    finding_code: str
    entity_type: str
    entity_code: str
    message: str

@dataclass
class Recommendation:
    recommendation_type: str
    priority: str
    recommended_action: str

@dataclass
class ParsedOutput:
    parse_status: str
    severity: str = "UNKNOWN"
    risk_score: Optional[float] = None
    findings: List[Finding] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    raw_output: str = ""

class OutputParser:
    @staticmethod
    def parse(raw_output: str) -> ParsedOutput:
        result = ParsedOutput(
            parse_status="PARSE_FAILED",
            raw_output=raw_output or ""
        )
        
        if not raw_output:
            return result
            
        try:
            data = json.loads(raw_output)
            if not isinstance(data, dict):
                return result
                
            result.severity = data.get("severity", "UNKNOWN")
            
            # Extract risk score safely
            risk_score_raw = data.get("risk_score")
            try:
                if risk_score_raw is not None:
                    result.risk_score = float(risk_score_raw)
            except (ValueError, TypeError):
                result.risk_score = None
                
            # Extract findings
            findings_raw = data.get("findings", [])
            if isinstance(findings_raw, list):
                for f in findings_raw:
                    if isinstance(f, dict):
                        result.findings.append(Finding(
                            finding_code=str(f.get("finding_code", "")),
                            entity_type=str(f.get("entity_type", "")),
                            entity_code=str(f.get("entity_code", "")),
                            message=str(f.get("message", ""))
                        ))
                        
            # Extract recommendations
            recs_raw = data.get("recommendations", [])
            if isinstance(recs_raw, list):
                for r in recs_raw:
                    if isinstance(r, dict):
                        result.recommendations.append(Recommendation(
                            recommendation_type=str(r.get("recommendation_type", "")),
                            priority=str(r.get("priority", "")),
                            recommended_action=str(r.get("recommended_action", ""))
                        ))
                        
            # Extract evidence
            evidence_raw = data.get("evidence", {})
            if isinstance(evidence_raw, dict):
                result.evidence = evidence_raw
                
            result.parse_status = "SUCCESS"
            return result
            
        except json.JSONDecodeError:
            return result
        except Exception:
            # Catch unexpected errors to ensure fallback
            return result
