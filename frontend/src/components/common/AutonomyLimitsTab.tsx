import React, { useState, useEffect } from "react";
import { Shield, Sliders, AlertCircle, CheckCircle2 } from "lucide-react";
import { KillSwitchControl } from "./KillSwitchControl";
import serverClient from "../../services/shared/apiClient";
import styles from "./AutonomyLimitsTab.module.css";

interface AutonomyLimitsTabProps {
  agentId: string;
}

export const AutonomyLimitsTab: React.FC<AutonomyLimitsTabProps> = ({ agentId }) => {
  const [maxAutonomy, setMaxAutonomy] = useState("SUPERVISED_AUTONOMOUS");
  const [rateLimit, setRateLimit] = useState(60);
  const [maxConcurrency, setMaxConcurrency] = useState(10);
  const [allowSubAgents, setAllowSubAgents] = useState(false);
  const [approvalThreshold, setApprovalThreshold] = useState(5000);
  const [isEngaged, setIsEngaged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    loadBoundary();
  }, [agentId]);

  const loadBoundary = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      const res = await serverClient.get<any>(`/api/v1/agent-boundaries/${agentId}`);
      const data = res?.data || res;
      if (data && (data.max_autonomy_level || data.id)) {
        setMaxAutonomy(data.max_autonomy_level || "SUPERVISED_AUTONOMOUS");
        setRateLimit(data.rate_limit_per_minute || 60);
        setMaxConcurrency(data.max_concurrency || 10);
        setAllowSubAgents(!!data.allow_sub_agent_spawn);
        setApprovalThreshold(data.require_approval_threshold || 5000);
        setIsEngaged(!data.is_active);
      }
    } catch {
      // Default to standard state if boundary not yet created
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFeedback(null);
    try {
      await serverClient.post("/api/v1/agent-boundaries", {
        agent_id: agentId,
        max_autonomy_level: maxAutonomy,
        allowed_access_modes_json: ["READ", "WRITE", "EXECUTE"],
        rate_limit_per_minute: Number(rateLimit),
        max_concurrency: Number(maxConcurrency),
        allow_sub_agent_spawn: allowSubAgents,
        require_approval_threshold: Number(approvalThreshold),
        is_active: !isEngaged,
      });
      setFeedback({ type: "success", message: "Agent autonomy boundary updated successfully!" });
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to save boundary." });
    } finally {
      setSaving(false);
    }
  };

  const handleKillSwitchToggle = async (newState: boolean) => {
    setIsEngaged(newState);
    try {
      await serverClient.post("/api/v1/agent-boundaries", {
        agent_id: agentId,
        max_autonomy_level: maxAutonomy,
        rate_limit_per_minute: Number(rateLimit),
        max_concurrency: Number(maxConcurrency),
        allow_sub_agent_spawn: allowSubAgents,
        require_approval_threshold: Number(approvalThreshold),
        is_active: !newState,
      });
      setFeedback({
        type: "success",
        message: newState ? "Emergency kill-switch engaged." : "Kill-switch deactivated. Agent operational.",
      });
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to toggle kill switch." });
    }
  };

  if (loading) {
    return <div className="py-8 text-center text-sm text-slate-400">Loading agent boundary limits...</div>;
  }

  return (
    <div className={styles.container}>
      {feedback && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
              : "bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-800"
          }`}
        >
          {feedback.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Kill Switch Header */}
      <KillSwitchControl
        agentId={agentId}
        isEngaged={isEngaged}
        onToggle={handleKillSwitchToggle}
      />

      <form onSubmit={handleSave} className="space-y-4">
        <div className={styles.grid}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Max Autonomy Level</label>
            <select
              value={maxAutonomy}
              onChange={(e) => setMaxAutonomy(e.target.value)}
              className={styles.select}
            >
              <option value="RECOMMEND_ONLY">RECOMMEND_ONLY (No execution permission)</option>
              <option value="HUMAN_IN_THE_LOOP">HUMAN_IN_THE_LOOP (Approval on every action)</option>
              <option value="SUPERVISED_AUTONOMOUS">SUPERVISED_AUTONOMOUS (Approval above threshold)</option>
              <option value="FULLY_AUTONOMOUS">FULLY_AUTONOMOUS (Full boundary execution)</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Rate Limit (requests / min)</label>
            <input
              type="number"
              min="1"
              max="10000"
              value={rateLimit}
              onChange={(e) => setRateLimit(parseInt(e.target.value) || 60)}
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Max Concurrency</label>
            <input
              type="number"
              min="1"
              max="100"
              value={maxConcurrency}
              onChange={(e) => setMaxConcurrency(parseInt(e.target.value) || 10)}
              className={styles.input}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Require Approval Threshold ($)</label>
            <input
              type="number"
              min="0"
              value={approvalThreshold}
              onChange={(e) => setApprovalThreshold(parseInt(e.target.value) || 0)}
              className={styles.input}
            />
          </div>
        </div>

        <div className={styles.checkboxRow}>
          <input
            type="checkbox"
            id="subAgentSpawn"
            checked={allowSubAgents}
            onChange={(e) => setAllowSubAgents(e.target.checked)}
            className="w-4 h-4 text-indigo-600 rounded"
          />
          <label htmlFor="subAgentSpawn" className="text-xs text-slate-700 dark:text-slate-300">
            <strong>Allow Dynamic Sub-Agent Spawning</strong> — Agent can delegate task executions to child agents within runtime boundaries.
          </label>
        </div>

        <div className={styles.saveRow}>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors disabled:opacity-50"
          >
            {saving ? "Saving Limits..." : "Save Autonomy Boundary"}
          </button>
        </div>
      </form>
    </div>
  );
};
