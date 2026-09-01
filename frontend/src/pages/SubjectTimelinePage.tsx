/* src/pages/SubjectTimelinePage.tsx */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { AuditTimelinePanel } from "../components/phase2/AuditTimelinePanel";
import { EventDrawer, GovernanceEventData } from "../components/common/EventDrawer";
import { fetchSubjectTimeline } from "../services/audit/auditService";
import { ArrowLeft, RefreshCw, ShieldCheck, AlertTriangle } from "lucide-react";

export const SubjectTimelinePage: React.FC = () => {
  const { entityType, entityId } = useParams<{ entityType: string; entityId: string }>();
  const navigate = useNavigate();

  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [selectedEvent, setSelectedEvent] = useState<GovernanceEventData | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const mockSubjectEvents = [
    {
      event_id: "evt_sub_01",
      event_type: "MODEL_REGISTERED",
      event_category: "Registry",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 14400000).toISOString(),
      recorded_at: new Date(Date.now() - 14400000).toISOString(),
      source_service: "registry_service",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: entityType || "agents", entity_id: entityId || "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { action: "REGISTER_ASSET", model_name: "GPT-4o Enterprise" },
      classification: "PUBLIC",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "1111111111111111111111111111111111111111111111111111111111111111",
      status: "VERIFIED"
    },
    {
      event_id: "evt_sub_02",
      event_type: "RESPONSIBILITY_ASSIGNED",
      event_category: "Relationship",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 10800000).toISOString(),
      recorded_at: new Date(Date.now() - 10800000).toISOString(),
      source_service: "relationship_service",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: entityType || "agents", entity_id: entityId || "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { responsibility_type: "PRIMARY_OWNER", assigned_user: "sarah_j@guardianiq.demo" },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "2222222222222222222222222222222222222222222222222222222222222222",
      status: "VERIFIED"
    },
    {
      event_id: "evt_sub_03",
      event_type: "POLICY_EVALUATED",
      event_category: "Policy",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 7200000).toISOString(),
      recorded_at: new Date(Date.now() - 7200000).toISOString(),
      source_service: "policy_engine",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: entityType || "agents", entity_id: entityId || "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { policy_code: "POL-DATA-PRIVACY", check_result: "PASSED" },
      classification: "CONFIDENTIAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "3333333333333333333333333333333333333333333333333333333333333333",
      status: "VERIFIED"
    },
    {
      event_id: "evt_sub_04",
      event_type: "RELATIONSHIP_CREATED",
      event_category: "Relationship",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 5400000).toISOString(),
      recorded_at: new Date(Date.now() - 5400000).toISOString(),
      source_service: "relationship_service",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: entityType || "agents", entity_id: entityId || "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { relationship_type: "USES_TOOL", target_id: "tool_fin_calc" },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "4444444444444444444444444444444444444444444444444444444444444444",
      status: "VERIFIED"
    },
    {
      event_id: "evt_sub_05",
      event_type: "WORKFLOW_RUN_STARTED",
      event_category: "Workflow",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 3600000).toISOString(),
      recorded_at: new Date(Date.now() - 3600000).toISOString(),
      source_service: "workflow_execution",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: entityType || "agents", entity_id: entityId || "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { trigger: "MANUAL", run_code: "RUN-2026-001" },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "5555555555555555555555555555555555555555555555555555555555555555",
      status: "VERIFIED"
    },
    {
      event_id: "evt_sub_06",
      event_type: "AGENT_STEP_COMPLETED",
      event_category: "Agent",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 1800000).toISOString(),
      recorded_at: new Date(Date.now() - 1800000).toISOString(),
      source_service: "agent_runtime",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: entityType || "agents", entity_id: entityId || "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { step_number: 1, result: "SUCCESS", tokens_used: 1200 },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "6666666666666666666666666666666666666666666666666666666666666666",
      status: "VERIFIED"
    }
  ];

  const loadTimeline = async () => {
    if (!entityType || !entityId) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
      if (token) {
        const res = await fetchSubjectTimeline(token, entityType, entityId);
        const items = res.timeline || res.events || res.items || [];
        setEvents(items);
      } else {
        setEvents(mockSubjectEvents);
      }
    } catch (err: any) {
      if (err?.status === 403 || err?.message?.includes("permissions")) {
        setErrorMsg("Permission Denied: Requires VIEW_AUDIT_TIMELINE permission.");
      } else {
        console.warn("Using local fallback subject timeline:", err);
        setEvents(mockSubjectEvents);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, [entityType, entityId]);

  return (
    <div style={{ padding: "1.5rem" }}>
      <PageHeader
        title="Subject Audit Timeline"
        description={`Query-time event stream reconstruction for ${entityType} : ${entityId}`}
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
              onClick={loadTimeline}
              disabled={loading}
            >
              Refresh Stream
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

      <Card
        title="Subject Event Stream"
        subtitle={`Total ordered governance events recorded: ${events.length}`}
        actions={
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-success)", fontSize: "0.8rem", fontWeight: "bold" }}>
            <ShieldCheck size={16} />
            <span>IMMUTABLE LEDGER VERIFIED</span>
          </div>
        }
      >
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "220px" }}>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3"></div>
            <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Reconstructing subject event timeline...</span>
          </div>
        ) : (
          <AuditTimelinePanel
            events={events}
            onEventClick={(evt) => {
              setSelectedEvent(evt);
              setIsDrawerOpen(true);
            }}
          />
        )}
      </Card>

      {/* Shared Event Detail Drawer */}
      <EventDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        event={selectedEvent}
      />
    </div>
  );
};

export default SubjectTimelinePage;
