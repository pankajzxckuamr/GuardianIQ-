/* src/pages/EventSchemaRegistryPage.tsx */
import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import {
  Database,
  PlusCircle,
  Search,
  Edit2,
  Trash2,
  Copy,
  Check,
  CheckCircle2,
  XCircle,
  Layers,
  Code2,
  Sparkles,
  X,
  AlertCircle
} from "lucide-react";
import {
  fetchEventSchemas,
  createEventSchema,
  updateEventSchema,
  deleteEventSchema,
  type EventSchemaRecord,
} from "../services/events/eventSchemaService";
import styles from "./EventSchemaRegistryPage.module.css";

const STANDARD_CATEGORIES = [
  "All",
  "Identity",
  "Workflow",
  "Policy",
  "Boundary",
  "Violation",
  "Approval",
  "Registry",
  "Audit"
];

const DEFAULT_SCHEMA_TEMPLATE = (eventType: string, category: string) => ({
  $schema: "http://json-schema.org/draft-07/schema#",
  title: `${eventType || "EVENT_NAME"} Schema`,
  type: "object",
  properties: {
    event_id: { type: "string", format: "uuid" },
    tenant_id: { type: "string", format: "uuid" },
    event_type: { type: "string", const: eventType || "EVENT_NAME" },
    event_category: { type: "string", const: category || "General" },
    payload_json: {
      type: "object",
      properties: {
        action_name: { type: "string" },
        status: { type: "string" }
      }
    }
  },
  required: ["event_id", "tenant_id", "event_type", "event_category", "payload_json"]
});

export const EventSchemaRegistryPage: React.FC = () => {
  const [schemas, setSchemas] = useState<EventSchemaRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingSchema, setEditingSchema] = useState<EventSchemaRecord | null>(null);
  const [formEventType, setFormEventType] = useState<string>("");
  const [formCategory, setFormCategory] = useState<string>("Workflow");
  const [formVersion, setFormVersion] = useState<string>("1.0");
  const [formIsActive, setFormIsActive] = useState<boolean>(true);
  const [formJsonString, setFormJsonString] = useState<string>("");
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    loadSchemas();
  }, []);

  const loadSchemas = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchEventSchemas();
      const loaded = res.data || [];
      loaded.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
      setSchemas(loaded);
    } catch (err: any) {
      setError(err.message || "Failed to fetch event schemas");
    } finally {
      setIsLoading(false);
    }
  };

  const getCategoryFromSchema = (schema: EventSchemaRecord): string => {
    if (schema.json_schema?.properties?.event_category?.const) {
      return schema.json_schema.properties.event_category.const;
    }
    if (schema.json_schema?.event_category) {
      return schema.json_schema.event_category;
    }
    return "General";
  };

  const handleOpenCreateModal = () => {
    setEditingSchema(null);
    setFormEventType("");
    setFormCategory("Workflow");
    setFormVersion("1.0");
    setFormIsActive(true);
    setFormJsonString(JSON.stringify(DEFAULT_SCHEMA_TEMPLATE("NEW_EVENT", "Workflow"), null, 2));
    setJsonError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (schema: EventSchemaRecord) => {
    setEditingSchema(schema);
    setFormEventType(schema.event_type);
    const cat = getCategoryFromSchema(schema);
    setFormCategory(cat);
    setFormVersion(schema.version || "1.0");
    setFormIsActive(schema.is_active);
    setFormJsonString(JSON.stringify(schema.json_schema || {}, null, 2));
    setJsonError(null);
    setIsModalOpen(true);
  };

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(formJsonString);
      setFormJsonString(JSON.stringify(parsed, null, 2));
      setJsonError(null);
    } catch (err: any) {
      setJsonError("Invalid JSON: " + err.message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setJsonError(null);

    let parsedSchema: any;
    try {
      parsedSchema = JSON.parse(formJsonString);
    } catch (err: any) {
      setJsonError("Invalid JSON Schema format: " + err.message);
      return;
    }

    setIsSubmitting(true);
    try {
      if (editingSchema) {
        await updateEventSchema(editingSchema.id, {
          json_schema: parsedSchema,
          is_active: formIsActive,
        });
      } else {
        await createEventSchema({
          event_type: formEventType.trim().toUpperCase(),
          version: formVersion.trim() || "1.0",
          json_schema: parsedSchema,
          is_active: formIsActive,
        });
      }
      setIsModalOpen(false);
      await loadSchemas();
    } catch (err: any) {
      setJsonError(err.message || "Failed to save schema");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleActive = async (schema: EventSchemaRecord) => {
    try {
      await updateEventSchema(schema.id, {
        is_active: !schema.is_active,
      });
      await loadSchemas();
    } catch (err: any) {
      setError(err.message || "Failed to update status");
    }
  };

  const handleDelete = async (schemaId: string, eventType: string) => {
    if (!window.confirm(`Are you sure you want to delete schema for '${eventType}'?`)) return;
    try {
      await deleteEventSchema(schemaId);
      await loadSchemas();
    } catch (err: any) {
      setError(err.message || "Failed to delete schema");
    }
  };

  const handleCopyJson = (schema: EventSchemaRecord) => {
    navigator.clipboard.writeText(JSON.stringify(schema.json_schema || {}, null, 2));
    setCopiedId(schema.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Filter schemas
  const filteredSchemas = schemas.filter((s) => {
    const category = getCategoryFromSchema(s);
    const matchesSearch =
      s.event_type.toLowerCase().includes(search.toLowerCase()) ||
      category.toLowerCase().includes(search.toLowerCase());

    const matchesCategory =
      selectedCategory === "All" ||
      category.toLowerCase() === selectedCategory.toLowerCase();

    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "ACTIVE" && s.is_active) ||
      (statusFilter === "INACTIVE" && !s.is_active);

    return matchesSearch && matchesCategory && matchesStatus;
  });

  const totalCount = filteredSchemas.length;
  const totalPages = Math.ceil(totalCount / pageSize) || 1;
  const startRecord = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRecord = Math.min(page * pageSize, totalCount);
  const paginatedSchemas = filteredSchemas.slice((page - 1) * pageSize, page * pageSize);

  const activeCount = schemas.filter((s) => s.is_active).length;
  const categoriesCount = new Set(schemas.map((s) => getCategoryFromSchema(s))).size;

  return (
    <div className={styles.container}>
      <PageHeader
        title="Event Schema Registry"
        description="Manage, validate, and version JSON schemas for enterprise governance events and immutable audit logs."
        actions={
          <button onClick={handleOpenCreateModal} className={styles.primaryBtn}>
            <PlusCircle size={16} /> New Schema
          </button>
        }
      />

      {/* Summary Stats Cards */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Total Event Schemas</span>
            <Database className="w-5 h-5 text-indigo-400" />
          </div>
          <div className={styles.statValue}>{schemas.length}</div>
          <div className={styles.statSubtext}>Registered in governance store</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Active Schemas</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className={styles.statValue}>{activeCount}</div>
          <div className={styles.statSubtext}>Enforcing payload validation</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Domain Categories</span>
            <Layers className="w-5 h-5 text-purple-400" />
          </div>
          <div className={styles.statValue}>{categoriesCount}</div>
          <div className={styles.statSubtext}>Workflow, Policy, Identity, Boundary</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Schema Protocol</span>
            <Sparkles className="w-5 h-5 text-blue-400" />
          </div>
          <div className={styles.statValue} style={{ fontSize: "1.2rem", color: "#60a5fa" }}>
            JSON Schema v7
          </div>
          <div className={styles.statSubtext}>Fail-closed outbox validation</div>
        </div>
      </div>

      {/* Toolbar & Filters */}
      <div className={styles.toolbar}>
        <div className={styles.searchBox}>
          <Search size={16} className="text-slate-400" />
          <input
            type="text"
            placeholder="Search schemas by event type or category..."
            className={styles.searchInput}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
          {search && (
            <button onClick={() => { setSearch(""); setPage(1); }} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}>
              <X size={14} />
            </button>
          )}
        </div>

        <div className={styles.filtersRow}>
          <select
            className={styles.filterSelect}
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active Only</option>
            <option value="INACTIVE">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Category Pills */}
      <div className={styles.categoryPills}>
        {STANDARD_CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => {
              setSelectedCategory(cat);
              setPage(1);
            }}
            className={`${styles.categoryPill} ${selectedCategory === cat ? styles.activeCategoryPill : ""}`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.85rem 1rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "8px", color: "#f87171", fontSize: "0.85rem" }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Schemas Grid */}
      {isLoading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
          <div className="animate-spin h-8 w-8 border-4 border-indigo-500 rounded-full border-t-transparent"></div>
        </div>
      ) : (
        <>
          <div className={styles.grid}>
            {paginatedSchemas.map((schema) => {
              const category = getCategoryFromSchema(schema);
              return (
                <div key={schema.id} className={styles.schemaCard}>
                  <div className={styles.cardTop}>
                    <div className={styles.cardHeaderLeft}>
                      <div className={styles.iconWrapper}>
                        <Database size={20} />
                      </div>
                      <div>
                        <div className={styles.cardTitle}>{schema.event_type}</div>
                        <div className={styles.cardSubtitle}>
                          Version {schema.version || "1.0"} • Created {new Date(schema.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    <div className={styles.cardActions}>
                      <button
                        onClick={() => handleCopyJson(schema)}
                        className={styles.actionIconBtn}
                        title="Copy JSON Schema"
                      >
                        {copiedId === schema.id ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} />}
                      </button>
                      <button
                        onClick={() => handleOpenEditModal(schema)}
                        className={styles.actionIconBtn}
                        title="Edit Schema"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(schema.id, schema.event_type)}
                        className={`${styles.actionIconBtn} ${styles.deleteIconBtn}`}
                        title="Delete Schema"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  <div className={styles.metaRow}>
                    <span className={`${styles.metaBadge} ${styles.categoryBadge}`}>
                      {category}
                    </span>
                    <button
                      onClick={() => handleToggleActive(schema)}
                      style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
                    >
                      <span className={`${styles.metaBadge} ${schema.is_active ? styles.activeBadge : styles.inactiveBadge}`}>
                        {schema.is_active ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                        {schema.is_active ? "Active" : "Inactive"}
                      </span>
                    </button>
                  </div>

                  <div>
                    <div className={styles.jsonHeader}>
                      <span>Payload Validation Schema</span>
                      <span style={{ fontSize: "0.7rem", color: "#64748b" }}>JSON Schema v7</span>
                    </div>
                    <div className={styles.jsonBox}>
                      <pre>{JSON.stringify(schema.json_schema || {}, null, 2)}</pre>
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredSchemas.length === 0 && (
              <div className={styles.emptyState}>
                <Database size={40} className="text-indigo-400 opacity-60" />
                <div className={styles.emptyTitle}>No Event Schemas Found</div>
                <div className={styles.emptyDesc}>
                  {search || selectedCategory !== "All"
                    ? "No schemas match the active filter criteria. Try clearing your search or category."
                    : "No governance event schemas are registered in the system."}
                </div>
                <button onClick={handleOpenCreateModal} className={styles.primaryBtn} style={{ marginTop: "0.5rem" }}>
                  <PlusCircle size={16} /> Create Event Schema
                </button>
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalCount > 0 && (
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 16px",
              background: "rgba(15, 23, 42, 0.6)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "8px",
              fontSize: "0.85rem",
              color: "#94a3b8",
              marginTop: "16px"
            }}>
              <div>
                Showing <strong style={{ color: "#fff" }}>{startRecord}-{endRecord}</strong> of <strong style={{ color: "#fff" }}>{totalCount}</strong> schemas
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span>Page <strong style={{ color: "#fff" }}>{page}</strong> of <strong style={{ color: "#fff" }}>{totalPages}</strong></span>
                <div style={{ display: "flex", gap: "6px" }}>
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                    style={{
                      padding: "4px 12px",
                      borderRadius: "6px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      background: page <= 1 ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                      color: page <= 1 ? "#475569" : "#fff",
                      cursor: page <= 1 ? "not-allowed" : "pointer",
                      fontSize: "0.8rem",
                      fontWeight: 600
                    }}
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                    style={{
                      padding: "4px 12px",
                      borderRadius: "6px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      background: page >= totalPages ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                      color: page >= totalPages ? "#475569" : "#fff",
                      cursor: page >= totalPages ? "not-allowed" : "pointer",
                      fontSize: "0.8rem",
                      fontWeight: 600
                    }}
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className={styles.modalBackdrop} onClick={() => setIsModalOpen(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div className={styles.modalTitle}>
                <Database size={20} className="text-indigo-400" />
                {editingSchema ? `Edit Schema: ${editingSchema.event_type}` : "Register New Event Schema"}
              </div>
              <button onClick={() => setIsModalOpen(false)} className={styles.modalCloseBtn}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className={styles.modalForm}>
              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Event Type *</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingSchema}
                    placeholder="Enter event type code (e.g. EVENT_NAME)..."
                    className={styles.formInput}
                    value={formEventType}
                    onChange={(e) => {
                      const val = e.target.value;
                      setFormEventType(val);
                      if (!editingSchema) {
                        try {
                          const current = JSON.parse(formJsonString);
                          current.title = `${val || "EVENT_NAME"} Schema`;
                          if (current.properties?.event_type) current.properties.event_type.const = val;
                          setFormJsonString(JSON.stringify(current, null, 2));
                        } catch {}
                      }
                    }}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Category</label>
                  <select
                    className={styles.formSelect}
                    value={formCategory}
                    onChange={(e) => {
                      const val = e.target.value;
                      setFormCategory(val);
                      try {
                        const current = JSON.parse(formJsonString);
                        if (current.properties?.event_category) current.properties.event_category.const = val;
                        setFormJsonString(JSON.stringify(current, null, 2));
                      } catch {}
                    }}
                  >
                    <option value="Workflow">Workflow</option>
                    <option value="Policy">Policy</option>
                    <option value="Identity">Identity</option>
                    <option value="Boundary">Boundary</option>
                    <option value="Violation">Violation</option>
                    <option value="Approval">Approval</option>
                    <option value="Registry">Registry</option>
                    <option value="Audit">Audit</option>
                    <option value="General">General</option>
                  </select>
                </div>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Schema Version</label>
                  <input
                    type="text"
                    disabled={!!editingSchema}
                    placeholder="Enter schema version (e.g. 1.0.0)..."
                    className={styles.formInput}
                    value={formVersion}
                    onChange={(e) => setFormVersion(e.target.value)}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.formLabel}>Status</label>
                  <select
                    className={styles.formSelect}
                    value={formIsActive ? "ACTIVE" : "INACTIVE"}
                    onChange={(e) => setFormIsActive(e.target.value === "ACTIVE")}
                  >
                    <option value="ACTIVE">Active (Enforced)</option>
                    <option value="INACTIVE">Inactive (Disabled)</option>
                  </select>
                </div>
              </div>

              <div className={styles.formGroup}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.2rem" }}>
                  <label className={styles.formLabel}>JSON Schema Definition (Draft-07) *</label>
                  <button
                    type="button"
                    onClick={handleFormatJson}
                    className={styles.secondaryBtn}
                    style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
                  >
                    <Code2 size={13} /> Format JSON
                  </button>
                </div>
                <textarea
                  required
                  className={styles.formTextarea}
                  value={formJsonString}
                  onChange={(e) => {
                    setFormJsonString(e.target.value);
                    setJsonError(null);
                  }}
                />
                {jsonError && <div className={styles.jsonError}>{jsonError}</div>}
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className={styles.secondaryBtn}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={styles.primaryBtn}
                >
                  {isSubmitting ? "Saving..." : editingSchema ? "Update Schema" : "Register Schema"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
