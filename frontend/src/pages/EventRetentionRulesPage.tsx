/* src/pages/EventRetentionRulesPage.tsx */
import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import {
  Shield,
  ShieldAlert,
  PlusCircle,
  Search,
  Clock,
  Edit2,
  Trash2,
  Archive,
  EyeOff,
  Flame,
  Calendar,
  Layers,
  X,
  AlertCircle
} from "lucide-react";
import {
  fetchRetentionRules,
  createRetentionRule,
  updateRetentionRule,
  deleteRetentionRule,
  type EventRetentionRuleRecord,
} from "../services/events/eventRetentionService";
import styles from "./EventRetentionRulesPage.module.css";

const STANDARD_CATEGORIES = [
  "All",
  "Workflow",
  "Policy",
  "Boundary",
  "Violation",
  "Approval",
  "Identity",
  "Registry",
  "Audit"
];

const PRESETS = [
  { label: "30 Days", days: 30 },
  { label: "90 Days (Std)", days: 90 },
  { label: "1 Year", days: 365 },
  { label: "7 Years (Audit)", days: 2555 },
];

export const EventRetentionRulesPage: React.FC = () => {
  const [rules, setRules] = useState<EventRetentionRuleRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [actionFilter, setActionFilter] = useState<string>("ALL");
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingRule, setEditingRule] = useState<EventRetentionRuleRecord | null>(null);
  const [formCategory, setFormCategory] = useState<string>("Workflow");
  const [formDays, setFormDays] = useState<number>(90);
  const [formAction, setFormAction] = useState<string>("PURGE");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchRetentionRules();
      const loaded = res.data || [];
      loaded.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
      setRules(loaded);
    } catch (err: any) {
      setError(err.message || "Failed to fetch retention rules");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenCreateModal = () => {
    setEditingRule(null);
    setFormCategory("Workflow");
    setFormDays(90);
    setFormAction("PURGE");
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (rule: EventRetentionRuleRecord) => {
    setEditingRule(rule);
    setFormCategory(rule.event_category);
    setFormDays(rule.retention_days);
    setFormAction(rule.action);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formDays || formDays < 1) {
      alert("Retention period must be at least 1 day.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (editingRule) {
        await updateRetentionRule(editingRule.id, {
          retention_days: Number(formDays),
          action: formAction,
        });
      } else {
        await createRetentionRule({
          event_category: formCategory.trim(),
          retention_days: Number(formDays),
          action: formAction,
        });
      }
      setIsModalOpen(false);
      await loadRules();
    } catch (err: any) {
      setError(err.message || "Failed to save retention rule");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (ruleId: string, category: string) => {
    if (!window.confirm(`Are you sure you want to delete the retention rule for '${category}'?`)) return;
    try {
      await deleteRetentionRule(ruleId);
      await loadRules();
    } catch (err: any) {
      setError(err.message || "Failed to delete retention rule");
    }
  };

  const getActionBadge = (action: string) => {
    const act = (action || "PURGE").toUpperCase();
    if (act === "ARCHIVE") {
      return (
        <span className={`${styles.actionBadge} ${styles.archiveBadge}`}>
          <Archive size={12} /> ARCHIVE
        </span>
      );
    }
    if (act === "ANONYMIZE") {
      return (
        <span className={`${styles.actionBadge} ${styles.anonymizeBadge}`}>
          <EyeOff size={12} /> ANONYMIZE
        </span>
      );
    }
    return (
      <span className={`${styles.actionBadge} ${styles.purgeBadge}`}>
        <Flame size={12} /> PURGE
      </span>
    );
  };

  // Filter rules
  const filteredRules = rules.filter((r) => {
    const matchesSearch =
      r.event_category.toLowerCase().includes(search.toLowerCase()) ||
      r.action.toLowerCase().includes(search.toLowerCase());

    const matchesCategory =
      selectedCategory === "All" ||
      r.event_category.toLowerCase() === selectedCategory.toLowerCase();

    const matchesAction =
      actionFilter === "ALL" ||
      r.action.toUpperCase() === actionFilter.toUpperCase();

    return matchesSearch && matchesCategory && matchesAction;
  });

  const totalCount = filteredRules.length;
  const totalPages = Math.ceil(totalCount / pageSize) || 1;
  const startRecord = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRecord = Math.min(page * pageSize, totalCount);
  const paginatedRules = filteredRules.slice((page - 1) * pageSize, page * pageSize);

  const maxRetention = rules.length > 0 ? Math.max(...rules.map((r) => r.retention_days)) : 0;
  const purgeCount = rules.filter((r) => r.action.toUpperCase() === "PURGE").length;
  const archiveCount = rules.filter((r) => r.action.toUpperCase() === "ARCHIVE").length;

  return (
    <div className={styles.container}>
      <PageHeader
        title="Event Retention Rules"
        description="Configure automated data lifecycle policies, compliance archiving, and purge windows for governance event categories."
        actions={
          <button onClick={handleOpenCreateModal} className={styles.primaryBtn}>
            <PlusCircle size={16} /> New Retention Rule
          </button>
        }
      />

      {/* Summary Stats Cards */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Configured Rules</span>
            <Shield className="w-5 h-5 text-indigo-400" />
          </div>
          <div className={styles.statValue}>{rules.length}</div>
          <div className={styles.statSubtext}>Category lifecycle policies</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Max Retention Window</span>
            <Clock className="w-5 h-5 text-amber-400" />
          </div>
          <div className={styles.statValue}>
            {maxRetention > 0 ? `${maxRetention} Days` : "None"}
          </div>
          <div className={styles.statSubtext}>
            {maxRetention >= 2555 ? "7-Year Statutory Audit Compliance" : "Standard retention threshold"}
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Policy Breakdown</span>
            <Layers className="w-5 h-5 text-emerald-400" />
          </div>
          <div className={styles.statValue} style={{ fontSize: "1.2rem", color: "#34d399" }}>
            {archiveCount} Archive • {purgeCount} Purge
          </div>
          <div className={styles.statSubtext}>Cold storage vs permanent deletion</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Automated Enforcement</span>
            <ShieldAlert className="w-5 h-5 text-blue-400" />
          </div>
          <div className={styles.statValue} style={{ fontSize: "1.2rem", color: "#60a5fa" }}>
            Daily Sweeper
          </div>
          <div className={styles.statSubtext}>Background worker active</div>
        </div>
      </div>

      {/* Toolbar & Filters */}
      <div className={styles.toolbar}>
        <div className={styles.searchBox}>
          <Search size={16} className="text-slate-400" />
          <input
            type="text"
            placeholder="Search rules by category or action..."
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
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="ALL">All Actions</option>
            <option value="PURGE">Purge Only</option>
            <option value="ARCHIVE">Archive Only</option>
            <option value="ANONYMIZE">Anonymize Only</option>
          </select>
        </div>
      </div>

      {/* Category Pills */}
      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
        {STANDARD_CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => {
              setSelectedCategory(cat);
              setPage(1);
            }}
            style={{
              padding: "0.3rem 0.75rem",
              borderRadius: "20px",
              fontSize: "0.75rem",
              fontWeight: 600,
              background: selectedCategory === cat ? "rgba(99, 102, 241, 0.25)" : "rgba(255, 255, 255, 0.04)",
              borderColor: selectedCategory === cat ? "#818cf8" : "rgba(255, 255, 255, 0.08)",
              borderWidth: "1px",
              borderStyle: "solid",
              color: selectedCategory === cat ? "#818cf8" : "#94a3b8",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
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

      {/* Rules Grid */}
      {isLoading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
          <div className="animate-spin h-8 w-8 border-4 border-indigo-500 rounded-full border-t-transparent"></div>
        </div>
      ) : (
        <>
          <div className={styles.grid}>
            {paginatedRules.map((rule) => (
              <div key={rule.id} className={styles.ruleCard}>
                <div className={styles.cardTop}>
                  <div className={styles.cardHeaderLeft}>
                    <div className={styles.iconWrapper}>
                      <ShieldAlert size={20} />
                    </div>
                    <div>
                      <div className={styles.cardTitle}>{rule.event_category} Events</div>
                      <div className={styles.cardSubtitle}>
                        Created {new Date(rule.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  <div className={styles.cardActions}>
                    <button
                      onClick={() => handleOpenEditModal(rule)}
                      className={styles.actionIconBtn}
                      title="Edit Rule"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(rule.id, rule.event_category)}
                      className={`${styles.actionIconBtn} ${styles.deleteIconBtn}`}
                      title="Delete Rule"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className={styles.lifecycleSection}>
                  <div className={styles.lifecycleRow}>
                    <span className={styles.lifecycleLabel}>
                      <Clock size={14} /> Retention Window
                    </span>
                    <span className={styles.lifecycleValue}>
                      {rule.retention_days} Days ({Math.round(rule.retention_days / 30)} mos)
                    </span>
                  </div>

                  <div className={styles.lifecycleRow}>
                    <span className={styles.lifecycleLabel}>
                      <Calendar size={14} /> Lifecycle Action
                    </span>
                    {getActionBadge(rule.action)}
                  </div>

                  <div className={styles.timelineTrack}>
                    <div className={styles.timelineDot} />
                    <span>Recorded</span>
                    <div className={styles.timelineLine} />
                    <span>{rule.retention_days}d Retention</span>
                    <div className={styles.timelineLine} />
                    <span>{rule.action}</span>
                  </div>
                </div>
              </div>
            ))}

            {filteredRules.length === 0 && (
              <div className={styles.emptyState}>
                <ShieldAlert size={40} className="text-indigo-400 opacity-60" />
                <div className={styles.emptyTitle}>No Retention Rules Configured</div>
                <div className={styles.emptyDesc}>
                  {search || selectedCategory !== "All" || actionFilter !== "ALL"
                    ? "No retention rules match the active filter criteria. Try resetting your search filters."
                    : "No category retention policies have been defined yet. Events currently use default 90-day retention."}
                </div>
                <button onClick={handleOpenCreateModal} className={styles.primaryBtn} style={{ marginTop: "0.5rem" }}>
                  <PlusCircle size={16} /> Create Retention Rule
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
                Showing <strong style={{ color: "#fff" }}>{startRecord}-{endRecord}</strong> of <strong style={{ color: "#fff" }}>{totalCount}</strong> rules
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
                <ShieldAlert size={20} className="text-indigo-400" />
                {editingRule ? `Edit Retention Rule: ${editingRule.event_category}` : "Create Event Retention Rule"}
              </div>
              <button onClick={() => setIsModalOpen(false)} className={styles.modalCloseBtn}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className={styles.modalForm}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Target Event Category *</label>
                <select
                  disabled={!!editingRule}
                  className={styles.formSelect}
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                >
                  <option value="Workflow">Workflow</option>
                  <option value="Policy">Policy</option>
                  <option value="Boundary">Boundary</option>
                  <option value="Violation">Violation</option>
                  <option value="Approval">Approval</option>
                  <option value="Identity">Identity</option>
                  <option value="Registry">Registry</option>
                  <option value="Audit">Audit</option>
                  <option value="General">General</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Retention Duration (Days) *</label>
                <div className={styles.presetGrid} style={{ marginBottom: "0.5rem" }}>
                  {PRESETS.map((preset) => (
                    <button
                      key={preset.days}
                      type="button"
                      onClick={() => setFormDays(preset.days)}
                      className={`${styles.presetBtn} ${formDays === preset.days ? styles.activePresetBtn : ""}`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
                <input
                  type="number"
                  min="1"
                  max="7300"
                  required
                  className={styles.formInput}
                  value={formDays}
                  onChange={(e) => setFormDays(Number(e.target.value))}
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Expiration Lifecycle Action *</label>
                <select
                  className={styles.formSelect}
                  value={formAction}
                  onChange={(e) => setFormAction(e.target.value)}
                >
                  <option value="PURGE">PURGE — Permanently Delete from Database</option>
                  <option value="ARCHIVE">ARCHIVE — Move to Compressed Cold Storage / S3</option>
                  <option value="ANONYMIZE">ANONYMIZE — Strip PII & Retain Statistical Aggregates</option>
                </select>
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
                  {isSubmitting ? "Saving..." : editingRule ? "Update Rule" : "Create Rule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
