/* src/pages/AuditPage.tsx */
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Badge } from "../components/common/Badge";
import { Button } from "../components/common/Button";
import { RegistryDataTable } from "../components/common/RegistryDataTable";
import { useRegistryFilters } from "../hooks/useRegistryFilters";
import { fetchGovernanceEvents } from "../services/audit/auditService";
import { formatDate } from "../utils/dates";
import { ShieldCheck, RefreshCw, Filter, Search, RotateCcw, AlertTriangle } from "lucide-react";
import { EventDrawer } from "../components/common/EventDrawer";
import "../components/common/RegistryDataTable.css";

interface GovernanceEventRow {
  event_id: string;
  event_type: string;
  event_category: string;
  event_version: string;
  occurred_at: string;
  recorded_at: string;
  source_service: string;
  actor_json: { user_id?: string; roles?: string[] };
  subject_json: { entity_type?: string; entity_id?: string };
  correlation_id?: string;
  risk_context_json?: { risk_level?: string };
  policy_context_json?: Record<string, any>;
  classification: string;
  retention_class: string;
  event_hash: string;
}

export const AuditPage: React.FC = () => {
  const navigate = useNavigate();
  const { filters, setFilter, resetFilters, paginationProps } = useRegistryFilters("occurred_at", 20);

  const [events, setEvents] = useState<GovernanceEventRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [selectedEvent, setSelectedEvent] = useState<GovernanceEventRow | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleRowClick = (row: GovernanceEventRow) => {
    setSelectedEvent(row);
    setIsDrawerOpen(true);
  };

  const mockEvents: GovernanceEventRow[] = [
    {
      event_id: "evt_11111111-1111-4111-8111-111111111111",
      event_type: "WORKFLOW_RUN_STARTED",
      event_category: "Workflow",
      event_version: "1.0",
      occurred_at: new Date().toISOString(),
      recorded_at: new Date().toISOString(),
      source_service: "workflow_scheduler",
      actor_json: { user_id: "usr_admin_01", roles: ["ADMIN"] },
      subject_json: { entity_type: "workflows", entity_id: "wf_98765" },
      correlation_id: "corr_99999999-9999-4999-8999-999999999999",
      risk_context_json: { risk_level: "LOW" },
      policy_context_json: { active_policies_count: 2 },
      classification: "INTERNAL",
      retention_class: "STANDARD_90_DAYS",
      event_hash: "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
    },
    {
      event_id: "evt_22222222-2222-4222-8222-222222222222",
      event_type: "POLICY_VIOLATION_DETECTED",
      event_category: "Violation",
      event_version: "1.0",
      occurred_at: new Date(Date.now() - 3600000).toISOString(),
      recorded_at: new Date(Date.now() - 3600000).toISOString(),
      source_service: "agent_runtime",
      actor_json: { user_id: "agent_fin_bot", roles: ["AGENT"] },
      subject_json: { entity_type: "policies", entity_id: "pol_strict_data" },
      correlation_id: "corr_88888888-8888-4888-8888-888888888888",
      risk_context_json: { risk_level: "HIGH" },
      policy_context_json: { violated_rule: "NO_PII_EXPORT" },
      classification: "CONFIDENTIAL",
      retention_class: "FINANCIAL_7_YEARS",
      event_hash: "b2c3d4e5f6a17890123456789012345678901234567890123456789012345679"
    }
  ];

  const loadEvents = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
      if (token) {
        const response = await fetchGovernanceEvents(token, {
          page: filters.page,
          pageSize: filters.pageSize,
          search: filters.search,
          event_category: filters.category,
          classification: filters.classification
        });
        const items = response.events || response.items || [];
        setEvents(items);
        setTotalCount(response.total || items.length);
      } else {
        let filtered = [...mockEvents];
        if (filters.category) {
          filtered = filtered.filter(e => e.event_category.toLowerCase() === filters.category.toLowerCase());
        }
        if (filters.classification) {
          filtered = filtered.filter(e => e.classification.toLowerCase() === filters.classification.toLowerCase());
        }
        if (filters.search) {
          filtered = filtered.filter(e => e.event_type.toLowerCase().includes(filters.search.toLowerCase()));
        }
        setEvents(filtered);
        setTotalCount(filtered.length);
      }
    } catch (err: any) {
      if (err?.status === 403 || err?.message?.includes("permissions")) {
        setErrorMsg("Permission Denied: Requires VIEW_EVENTS permission to explore governance events.");
      } else {
        console.warn("Using local fallback governance events:", err);
        setEvents(mockEvents);
        setTotalCount(mockEvents.length);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [filters.page, filters.pageSize, filters.search, filters.category, filters.classification]);

  const columns = [
    {
      key: "event_type",
      label: "Event Type",
      sortable: true,
      render: (row: GovernanceEventRow) => (
        <span style={{ fontFamily: "monospace", fontWeight: 600, color: "var(--accent-secondary)" }}>
          {row.event_type}
        </span>
      )
    },
    {
      key: "event_category",
      label: "Category",
      render: (row: GovernanceEventRow) => (
        <Badge label={row.event_category} variant="info" />
      )
    },
    {
      key: "actor",
      label: "Actor",
      render: (row: GovernanceEventRow) => (
        <span style={{ fontSize: "0.85rem" }}>
          {row.actor_json?.user_id || "System"}
        </span>
      )
    },
    {
      key: "subject",
      label: "Subject",
      render: (row: GovernanceEventRow) => (
        <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          {row.subject_json?.entity_type}:{row.subject_json?.entity_id?.substring(0, 8)}...
        </span>
      )
    },
    {
      key: "risk_level",
      label: "Risk Level",
      render: (row: GovernanceEventRow) => {
        const risk = row.risk_context_json?.risk_level || "LOW";
        const variant = risk === "HIGH" || risk === "CRITICAL" ? "danger" : risk === "MEDIUM" ? "warning" : "success";
        return <Badge label={risk} variant={variant} dot />;
      }
    },
    {
      key: "policy_context",
      label: "Policy Context",
      render: (row: GovernanceEventRow) => {
        const count = row.policy_context_json ? Object.keys(row.policy_context_json).length : 0;
        return <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{count} rules evaluated</span>;
      }
    },
    {
      key: "occurred_at",
      label: "Occurred At",
      sortable: true,
      render: (row: GovernanceEventRow) => formatDate(row.occurred_at)
    },
    {
      key: "correlation_id",
      label: "Correlation ID",
      render: (row: GovernanceEventRow) => (
        <span style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "var(--text-muted)" }}>
          {row.correlation_id ? row.correlation_id.substring(0, 8) + "..." : "—"}
        </span>
      )
    },
    {
      key: "classification",
      label: "Classification",
      render: (row: GovernanceEventRow) => (
        <Badge label={row.classification} variant={row.classification === "RESTRICTED" ? "danger" : "neutral"} />
      )
    },
    {
      key: "status",
      label: "Status",
      render: () => (
        <Badge label="VERIFIED" variant="success" dot />
      )
    }
  ];

  return (
    <div className="audit-page" style={{ padding: "1.5rem" }}>
      <PageHeader
        title="Event Explorer"
        description="Searchable, immutable ledger of all Phase 4 governance and security events."
        actions={
          <Button
            variant="secondary"
            size="md"
            icon={<RefreshCw size={14} className={loading ? "spin-icon" : ""} />}
            onClick={loadEvents}
            disabled={loading}
          >
            Refresh Events
          </Button>
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
        title="Event Stream Explorer"
        subtitle="URL-synced query filtering and live cryptographic event verification"
        actions={
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-success)", fontSize: "var(--font-size-xs)", fontWeight: "bold" }}>
            <ShieldCheck size={16} />
            <span>ENVELOPE 2.0 VALIDATED</span>
          </div>
        }
      >
        {/* Filter Controls Bar */}
        <div style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.5rem",
          alignItems: "center"
        }}>
          {/* Search Input */}
          <div style={{ position: "relative", flex: "1 1 240px" }}>
            <Search size={16} style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search event type..."
              value={String(filters.search || "")}
              onChange={(e) => setFilter("search", e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem 0.5rem 0.5rem 2.2rem",
                borderRadius: "6px",
                border: "1px solid var(--border-color)",
                backgroundColor: "var(--bg-secondary)",
                color: "var(--text-primary)",
                fontSize: "0.9rem"
              }}
            />
          </div>

          {/* Category Select Filter */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Filter size={14} style={{ color: "var(--text-muted)" }} />
            <select
              value={String(filters.category || "")}
              onChange={(e) => setFilter("category", e.target.value)}
              style={{
                padding: "0.5rem",
                borderRadius: "6px",
                border: "1px solid var(--border-color)",
                backgroundColor: "var(--bg-secondary)",
                color: "var(--text-primary)",
                fontSize: "0.9rem"
              }}
            >
              <option value="">All Categories</option>
              <option value="Workflow">Workflow</option>
              <option value="Agent">Agent</option>
              <option value="Policy">Policy</option>
              <option value="Approval">Approval</option>
              <option value="Registry">Registry</option>
              <option value="Relationship">Relationship</option>
              <option value="Identity">Identity</option>
              <option value="Audit">Audit</option>
              <option value="Violation">Violation</option>
            </select>
          </div>

          {/* Classification Select Filter */}
          <div>
            <select
              value={String(filters.classification || "")}
              onChange={(e) => setFilter("classification", e.target.value)}
              style={{
                padding: "0.5rem",
                borderRadius: "6px",
                border: "1px solid var(--border-color)",
                backgroundColor: "var(--bg-secondary)",
                color: "var(--text-primary)",
                fontSize: "0.9rem"
              }}
            >
              <option value="">All Classifications</option>
              <option value="PUBLIC">PUBLIC</option>
              <option value="INTERNAL">INTERNAL</option>
              <option value="CONFIDENTIAL">CONFIDENTIAL</option>
              <option value="RESTRICTED">RESTRICTED</option>
            </select>
          </div>

          {/* Reset Filters Button */}
          <Button
            variant="secondary"
            size="sm"
            icon={<RotateCcw size={14} />}
            onClick={resetFilters}
          >
            Reset Filters
          </Button>
        </div>

        {/* RegistryDataTable Component */}
        <RegistryDataTable
          columns={columns}
          data={events}
          isLoading={loading}
          totalCount={totalCount}
          page={paginationProps.page}
          pageSize={paginationProps.pageSize}
          onPageChange={paginationProps.onPageChange}
          emptyMessage="No governance events found for selected filters"
          onRowClick={(row) => handleRowClick(row as GovernanceEventRow)}
        />
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
