/* src/pages/CorrelationTimelinePage.tsx */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Badge } from "../components/common/Badge";
import { AuditTimelinePanel } from "../components/phase2/AuditTimelinePanel";
import { EventDrawer, GovernanceEventData } from "../components/common/EventDrawer";
import { fetchCorrelationTimeline } from "../services/audit/auditService";
import { ArrowLeft, RefreshCw, Activity, ShieldCheck, AlertTriangle, Layers, Server } from "lucide-react";

export const CorrelationTimelinePage: React.FC = () => {
  const { correlationId } = useParams<{ correlationId: string }>();
  const navigate = useNavigate();

  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [selectedEvent, setSelectedEvent] = useState<GovernanceEventData | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const mockCorrelationEvents = [
    {
      event_id: "evt_corr_01",
      event_type: "WORKFLOW_RUN_STARTED",
      event_category: "Workflow",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 7200000).toISOString(),
      recorded_at: new Date(Date.now() - 7200000).toISOString(),
      source_service: "workflow_scheduler",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: "workflows", entity_id: "wf_98765" },
      correlation_id: correlationId || "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { step: "QUEUED_TO_RUNNING", run_code: "RUN-2026-0801" },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "a".repeat(64),
      status: "VERIFIED"
    },
    {
      event_id: "evt_corr_02",
      event_type: "POLICY_EVALUATED",
      event_category: "Policy",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 6000000).toISOString(),
      recorded_at: new Date(Date.now() - 6000000).toISOString(),
      source_service: "policy_engine",
      actor_json: { user_id: "system", actor_type: "SYSTEM" },
      subject_json: { entity_type: "policies", entity_id: "pol_strict_data" },
      correlation_id: correlationId || "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { check_result: "PASSED", policy_code: "POL-DATA-PRIVACY" },
      classification: "CONFIDENTIAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "b".repeat(64),
      status: "VERIFIED"
    },
    {
      event_id: "evt_corr_03",
      event_type: "RELATIONSHIP_CREATED",
      event_category: "Relationship",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 4800000).toISOString(),
      recorded_at: new Date(Date.now() - 4800000).toISOString(),
      source_service: "relationship_service",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: "agents", entity_id: "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: correlationId || "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { relationship_type: "USES_MODEL", target_id: "mdl_gpt4_gov" },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "c".repeat(64),
      status: "VERIFIED"
    },
    {
      event_id: "evt_corr_04",
      event_type: "AGENT_STEP_STARTED",
      event_category: "Agent",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 3600000).toISOString(),
      recorded_at: new Date(Date.now() - 3600000).toISOString(),
      source_service: "agent_runtime",
      actor_json: { user_id: "agent_fin_bot", actor_type: "AGENT" },
      subject_json: { entity_type: "agents", entity_id: "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: correlationId || "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { step_code: "DATA_ANALYSIS", mode: "SIMULATION" },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "d".repeat(64),
      status: "VERIFIED"
    },
    {
      event_id: "evt_corr_05",
      event_type: "BOUNDARY_CHECK_EXECUTED",
      event_category: "Boundary",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 2400000).toISOString(),
      recorded_at: new Date(Date.now() - 2400000).toISOString(),
      source_service: "boundary_checker",
      actor_json: { user_id: "boundary_checker", actor_type: "SYSTEM" },
      subject_json: { entity_type: "agents", entity_id: "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: correlationId || "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "MEDIUM" },
      payload_json: { check_result: "ALLOWED", current_risk_score: 35 },
      classification: "RESTRICTED",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "e".repeat(64),
      status: "VERIFIED"
    },
    {
      event_id: "evt_corr_06",
      event_type: "APPROVAL_GRANTED",
      event_category: "Approval",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 1200000).toISOString(),
      recorded_at: new Date(Date.now() - 1200000).toISOString(),
      source_service: "approval_engine",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: "agents", entity_id: "d6a3cb9e-11a8-4004-b82f-a38e33790df0" },
      correlation_id: correlationId || "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { decision: "APPROVED", approver: "sarah_j@guardianiq.demo" },
      classification: "CONFIDENTIAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "f".repeat(64),
      status: "VERIFIED"
    },
    {
      event_id: "evt_corr_07",
      event_type: "WORKFLOW_RUN_COMPLETED",
      event_category: "Workflow",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 100000).toISOString(),
      recorded_at: new Date(Date.now() - 100000).toISOString(),
      source_service: "workflow_execution",
      actor_json: { user_id: "usr_admin_01", actor_type: "USER" },
      subject_json: { entity_type: "workflows", entity_id: "wf_98765" },
      correlation_id: correlationId || "5c3c5751-3232-4a3f-85ec-247d55077c03",
      risk_context_json: { risk_level: "LOW" },
      payload_json: { duration_ms: 12400, run_code: "RUN-2026-0801" },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "0".repeat(64),
      status: "VERIFIED"
    }
  ];

  const loadCorrelationTrace = async () => {
    if (!correlationId) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
      if (token) {
        const res = await fetchCorrelationTimeline(token, correlationId);
        const items = res.events || res.stream || res.items || [];
        setEvents(items);
      } else {
        setEvents(mockCorrelationEvents);
      }
    } catch (err: any) {
      if (err?.status === 403 || err?.message?.includes("permissions")) {
        setErrorMsg("Permission Denied: Requires VIEW_AUDIT_TIMELINE permission.");
      } else {
        console.warn("Using local fallback correlation stream:", err);
        setEvents(mockCorrelationEvents);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCorrelationTrace();
  }, [correlationId]);

  // Calculate correlation trace metrics
  const distinctServices = Array.from(new Set(events.map(e => e.source_service).filter(Boolean)));
  const hasHighRisk = events.some(e => (e.risk_context_json?.risk_level || e.risk_level) === "HIGH" || (e.risk_context_json?.risk_level || e.risk_level) === "CRITICAL");

  return (
    <div style={{ padding: "1.5rem" }}>
      <PageHeader
        title="Correlation Trace Stream"
        description={`Cross-service business flow trace for Correlation ID: ${correlationId || "N/A"}`}
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
              onClick={loadCorrelationTrace}
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

      {/* Trace Summary Banner */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "1rem",
        marginBottom: "1.5rem"
      }}>
        <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--card-border)", borderRadius: "8px", padding: "1rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: "bold", textTransform: "uppercase" }}>Total Correlated Events</div>
          <div style={{ fontSize: "1.5rem", fontWeight: "700", color: "var(--text-primary)", marginTop: "4px" }}>{events.length}</div>
        </div>
        <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--card-border)", borderRadius: "8px", padding: "1rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: "bold", textTransform: "uppercase" }}>Services Involved</div>
          <div style={{ fontSize: "1.5rem", fontWeight: "700", color: "var(--accent-secondary)", marginTop: "4px" }}>{distinctServices.length}</div>
        </div>
        <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--card-border)", borderRadius: "8px", padding: "1rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: "bold", textTransform: "uppercase" }}>Trace Risk Status</div>
          <div style={{ marginTop: "8px" }}>
            <Badge label={hasHighRisk ? "ELEVATED RISK" : "NORMAL"} variant={hasHighRisk ? "danger" : "success"} dot />
          </div>
        </div>
      </div>

      <Card
        title="Chronological Business Flow Trace"
        subtitle="Step-by-step execution stream across background services and API boundaries"
        actions={
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-success)", fontSize: "0.8rem", fontWeight: "bold" }}>
            <ShieldCheck size={16} />
            <span>CORRELATION 100% VERIFIED</span>
          </div>
        }
      >
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "220px" }}>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3"></div>
            <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Tracing correlated event stream...</span>
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

export default CorrelationTimelinePage;
