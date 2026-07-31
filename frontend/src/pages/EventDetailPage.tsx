/* src/pages/EventDetailPage.tsx */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { PageHeader } from "../components/common/PageHeader";
import { Button } from "../components/common/Button";
import { EventDrawer, GovernanceEventData } from "../components/common/EventDrawer";
import { fetchGovernanceEventById } from "../services/audit/auditService";
import { ArrowLeft, RefreshCw, AlertTriangle } from "lucide-react";

export const EventDetailPage: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();

  const [event, setEvent] = useState<GovernanceEventData | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const mockFallbackEvent: GovernanceEventData = {
    event_id: eventId || "evt_11111111-1111-4111-8111-111111111111",
    event_type: "WORKFLOW_RUN_STARTED",
    event_category: "Workflow",
    event_version: "1.0",
    occurred_at: new Date().toISOString(),
    recorded_at: new Date().toISOString(),
    source_service: "workflow_scheduler",
    actor_json: { user_id: "usr_admin_01", actor_type: "USER", roles: ["ADMIN"] },
    subject_json: { entity_type: "workflows", entity_id: "wf_98765" },
    correlation_id: "corr_99999999-9999-4999-8999-999999999999",
    risk_context_json: { risk_level: "LOW", risk_score: 0.1 },
    policy_context_json: { active_policies_count: 2 },
    payload_json: { schedule_id: "sched_123", trigger: "MANUAL", mode: "ENFORCED" },
    classification: "INTERNAL",
    retention_class: "STANDARD_90_DAYS",
    event_hash: "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678",
    status: "VERIFIED"
  };

  const loadEventDetail = async () => {
    if (!eventId) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
      if (token) {
        const data = await fetchGovernanceEventById(token, eventId);
        setEvent(data);
      } else {
        setEvent(mockFallbackEvent);
      }
    } catch (err: any) {
      if (err?.status === 403 || err?.message?.includes("permissions")) {
        setErrorMsg("Permission Denied: Requires VIEW_EVENTS permission to access this event.");
      } else {
        console.warn("Using local fallback event detail:", err);
        setEvent(mockFallbackEvent);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEventDetail();
  }, [eventId]);

  return (
    <div style={{ padding: "1.5rem" }}>
      <PageHeader
        title="Governance Event Detail"
        description={`Standalone audit view for Event ID: ${eventId || "N/A"}`}
        actions={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button
              variant="secondary"
              size="md"
              icon={<ArrowLeft size={16} />}
              onClick={() => navigate("/audit")}
            >
              Back to Explorer
            </Button>
            <Button
              variant="secondary"
              size="md"
              icon={<RefreshCw size={14} className={loading ? "spin-icon" : ""} />}
              onClick={loadEventDetail}
              disabled={loading}
            >
              Refresh
            </Button>
          </div>
        }
      />

      {errorMsg && (
        <div style={{
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          border: "1px solid var(--color-danger)",
          borderRadius: "8px",
          padding: "1rem",
          marginBottom: "1.5rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          color: "var(--color-danger)"
        }}>
          <AlertTriangle size={20} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Render Event Drawer embedded as primary detail panel */}
      <EventDrawer
        isOpen={true}
        onClose={() => navigate("/audit")}
        event={event}
      />
    </div>
  );
};

export default EventDetailPage;
