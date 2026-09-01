import React, { useState } from "react";
import { AlertOctagon, Power, ShieldAlert, CheckCircle2 } from "lucide-react";
import styles from "./KillSwitchControl.module.css";

interface KillSwitchControlProps {
  agentId: string;
  isEngaged: boolean;
  onToggle: (newState: boolean) => Promise<void>;
  disabled?: boolean;
}

export const KillSwitchControl: React.FC<KillSwitchControlProps> = ({
  isEngaged,
  onToggle,
  disabled = false,
}) => {
  const [loading, setLoading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleClick = () => {
    setConfirmOpen(true);
  };

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onToggle(!isEngaged);
      setConfirmOpen(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className={`${styles.killSwitchContainer} ${isEngaged ? styles.activeKillSwitch : ""}`}>
        <div className={styles.infoSection}>
          <div className={styles.titleRow}>
            {isEngaged ? (
              <ShieldAlert className="w-5 h-5 text-rose-600" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            )}
            <span>Emergency Kill Switch</span>
            {isEngaged && (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                ENGAGED (BLOCKED)
              </span>
            )}
          </div>
          <p className={styles.desc}>
            {isEngaged
              ? "All actions, tool executions, and model invocations for this agent are immediately blocked at the runtime gateway."
              : "Agent runtime operations are operating normally under active policy boundaries."}
          </p>
        </div>

        <button
          type="button"
          disabled={disabled || loading}
          onClick={handleClick}
          className={`${styles.toggleBtn} ${isEngaged ? styles.disengageBtn : styles.engageBtn}`}
        >
          <Power className="w-4 h-4" />
          {loading ? "Processing..." : isEngaged ? "Deactivate Kill Switch" : "Engage Kill Switch"}
        </button>
      </div>

      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-rose-600">
              <AlertOctagon className="w-8 h-8" />
              <h4 className="text-lg font-bold text-slate-900 dark:text-white">
                {isEngaged ? "Resume Agent Operations?" : "Activate Emergency Kill Switch?"}
              </h4>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {isEngaged
                ? "This will remove the runtime lock and allow the agent to execute permitted operations according to its active policies."
                : "Activating the kill switch will immediately reject all inbound requests for this agent across the runtime gateway."}
            </p>
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setConfirmOpen(false)}
                className="flex-1 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={handleConfirm}
                className={`flex-1 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors ${
                  isEngaged ? "bg-emerald-600 hover:bg-emerald-700" : "bg-rose-600 hover:bg-rose-700"
                }`}
              >
                {loading ? "Updating..." : isEngaged ? "Resume Operations" : "Engage Now"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
