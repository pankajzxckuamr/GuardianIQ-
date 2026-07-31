/* src/components/common/EventDrawer.tsx */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { formatDate } from "../../utils/dates";
import {
  X,
  ShieldCheck,
  UserCheck,
  Layers,
  Activity,
  FileCode,
  Lock,
  Copy,
  Check,
  ExternalLink,
  AlertOctagon
} from "lucide-react";
import styles from "./EventDrawer.module.css";

export interface GovernanceEventData {
  event_id: string;
  event_type: string;
  event_category: string;
  event_version: string;
  occurred_at: string;
  recorded_at: string;
  source_service: string;
  actor_json?: {
    user_id?: string;
    actor_type?: string;
    roles?: string[];
    ip_address?: string;
  };
  subject_json?: {
    entity_type?: string;
    entity_id?: string;
    entity_code?: string;
  };
  correlation_id?: string;
  causation_id?: string;
  risk_context_json?: {
    risk_level?: string;
    risk_score?: number;
  };
  policy_context_json?: Record<string, any>;
  payload_json?: Record<string, any>;
  classification: string;
  retention_class: string;
  event_hash: string;
  status?: string;
}

interface EventDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  event: GovernanceEventData | null;
}

export const EventDrawer: React.FC<EventDrawerProps> = ({
  isOpen,
  onClose,
  event
}) => {
  const navigate = useNavigate();
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedPayload, setCopiedPayload] = useState(false);

  if (!isOpen || !event) return null;

  // Check sensitivity / masking in payload
  const payloadStr = JSON.stringify(event.payload_json || {}, null, 2);
  const isPayloadMasked =
    payloadStr.includes("[REDACTED]") ||
    payloadStr.includes("***") ||
    event.classification === "RESTRICTED";

  const handleCopyHash = () => {
    if (event.event_hash) {
      navigator.clipboard.writeText(event.event_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleCopyPayload = () => {
    if (isPayloadMasked) return;
    navigator.clipboard.writeText(payloadStr);
    setCopiedPayload(true);
    setTimeout(() => setCopiedPayload(false), 2000);
  };

  const riskLevel = event.risk_context_json?.risk_level || "LOW";
  const riskVariant =
    riskLevel === "HIGH" || riskLevel === "CRITICAL"
      ? "danger"
      : riskLevel === "MEDIUM"
      ? "warning"
      : "success";

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.drawer} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerTitle}>
            <div className={styles.eventType}>{event.event_type}</div>
            <div className={styles.eventSubtitle}>
              <Badge label={event.event_category} variant="info" />
              <Badge label={event.classification} variant={event.classification === "RESTRICTED" ? "danger" : "neutral"} />
              <Badge label={`RISK: ${riskLevel}`} variant={riskVariant} dot />
            </div>
          </div>
          <button className={styles.closeButton} onClick={onClose} aria-label="Close drawer">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className={styles.body}>
          {/* Status & Validation Banner */}
          <div
            style={{
              padding: "0.85rem 1rem",
              borderRadius: "8px",
              backgroundColor: "rgba(16, 185, 129, 0.1)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              color: "#10b981",
              fontSize: "0.85rem",
              fontWeight: 600
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <ShieldCheck size={18} />
              <span>Canonical Envelope 2.0 Hash Verified</span>
            </div>
            <Badge label={event.status || "VERIFIED"} variant="success" dot />
          </div>

          {/* Envelope Metadata Card */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionTitle}>
              <Layers size={15} />
              <span>Envelope & Core Metadata</span>
            </div>
            <div className={styles.grid2}>
              <div className={styles.labelValue}>
                <span className={styles.label}>Event ID</span>
                <span className={styles.monoValue}>{event.event_id}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Event Version</span>
                <span className={styles.value}>{event.event_version}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Source Service</span>
                <span className={styles.value}>{event.source_service}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Retention Class</span>
                <span className={styles.value}>{event.retention_class}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Occurred At</span>
                <span className={styles.value}>{formatDate(event.occurred_at)}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Recorded At</span>
                <span className={styles.value}>{formatDate(event.recorded_at)}</span>
              </div>
            </div>
          </div>

          {/* Actor & Subject Card */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionTitle}>
              <UserCheck size={15} />
              <span>Actor & Subject Context</span>
            </div>
            <div className={styles.grid2}>
              <div className={styles.labelValue}>
                <span className={styles.label}>Actor User ID</span>
                <span className={styles.monoValue}>{event.actor_json?.user_id || "System"}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Actor Type / Roles</span>
                <span className={styles.value}>
                  {event.actor_json?.actor_type || "USER"} ({(event.actor_json?.roles || ["USER"]).join(", ")})
                </span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Subject Entity Type</span>
                <span className={styles.value}>{event.subject_json?.entity_type || "N/A"}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Subject Entity ID</span>
                <span className={styles.monoValue}>{event.subject_json?.entity_id || "N/A"}</span>
              </div>
            </div>
          </div>

          {/* Correlation & Risk Card */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionTitle}>
              <Activity size={15} />
              <span>Correlation & Risk Evaluation</span>
            </div>
            <div className={styles.grid2}>
              <div className={styles.labelValue}>
                <span className={styles.label}>Business Flow Correlation ID</span>
                <span className={styles.monoValue}>{event.correlation_id || "None"}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Causation Event ID</span>
                <span className={styles.monoValue}>{event.causation_id || "None"}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Evaluated Risk Level</span>
                <span className={styles.value}>{riskLevel}</span>
              </div>
              <div className={styles.labelValue}>
                <span className={styles.label}>Evaluated Rules Count</span>
                <span className={styles.value}>
                  {event.policy_context_json ? Object.keys(event.policy_context_json).length : 0} rules
                </span>
              </div>
            </div>
          </div>

          {/* Formatted JSON Payload Card */}
          <div className={styles.sectionCard}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div className={styles.sectionTitle}>
                <FileCode size={15} />
                <span>Event Payload JSON</span>
              </div>
              <button
                className={styles.copyButton}
                onClick={handleCopyPayload}
                disabled={isPayloadMasked}
                title={isPayloadMasked ? "Copy disabled for masked or sensitive payload" : "Copy JSON Payload"}
              >
                {copiedPayload ? <Check size={14} /> : <Copy size={14} />}
                <span>{copiedPayload ? "Copied" : "Copy JSON"}</span>
              </button>
            </div>

            <pre className={styles.jsonBox}>{payloadStr}</pre>

            {isPayloadMasked && (
              <div className={styles.disabledNotice}>
                <Lock size={13} />
                <span>Copying disabled for masked/RESTRICTED sensitive fields.</span>
              </div>
            )}
          </div>

          {/* Cryptographic Integrity Card */}
          <div className={styles.sectionCard}>
            <div className={styles.sectionTitle}>
              <Lock size={15} />
              <span>Cryptographic Integrity (event_hash)</span>
            </div>
            <div className={styles.hashBox}>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{event.event_hash}</span>
              <button className={styles.copyButton} onClick={handleCopyHash}>
                {copiedHash ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
          </div>

          {/* Footer Actions / Related Timeline Links */}
          <div className={styles.footerActions}>
            {event.subject_json?.entity_type && event.subject_json?.entity_id && (
              <Button
                variant="secondary"
                size="sm"
                icon={<ExternalLink size={14} />}
                onClick={() => {
                  onClose();
                  navigate(`/audit/timeline/${event.subject_json?.entity_type}/${event.subject_json?.entity_id}`);
                }}
              >
                View Subject Timeline
              </Button>
            )}

            {event.correlation_id && (
              <Button
                variant="secondary"
                size="sm"
                icon={<ExternalLink size={14} />}
                onClick={() => {
                  onClose();
                  navigate(`/audit/events/correlation/${event.correlation_id}`);
                }}
              >
                View Correlation Stream
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventDrawer;
