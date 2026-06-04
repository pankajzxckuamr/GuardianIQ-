import React, { useEffect, useState } from 'react';
import { orchestrationService } from '../services/orchestration/orchestrationService';
import { WorkflowExecution } from '../services/orchestration/orchestrationTypes';
import styles from './ExecutionDashboardPage.module.css';
import { Loader2, PlayCircle, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

export const ExecutionDashboardPage: React.FC = () => {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchExecutions = async () => {
      try {
        const data = await orchestrationService.listExecutions();
        setExecutions(data || []);
      } catch (error) {
        console.error('Failed to fetch executions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExecutions();
    // Poll every 5 seconds for updates
    const interval = setInterval(fetchExecutions, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className={styles[`status-${status}`]} size={20} />;
      case 'RUNNING': return <Loader2 className={`animate-spin ${styles[`status-${status}`]}`} size={20} />;
      case 'FAILED': return <AlertTriangle className={styles[`status-${status}`]} size={20} />;
      case 'PENDING': return <Clock className={styles[`status-${status}`]} size={20} />;
      default: return <PlayCircle size={20} />;
    }
  };

  return (
    <div className={styles.pageContainer}>
      <header className={styles.header}>
        <h1>Execution Dashboard</h1>
        <p>Monitor live and past AI workflow executions and agent activities.</p>
      </header>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="animate-spin text-blue-500" size={32} />
        </div>
      ) : executions.length === 0 ? (
        <div className="text-center p-12 text-gray-500 border border-gray-700 rounded-lg">
          No workflow executions found. Trigger a workflow to see it here.
        </div>
      ) : (
        <div className={styles.executionList}>
          {executions.map((execution) => (
            <div key={execution.id} className={styles.executionCard}>
              <div className="flex items-center gap-4">
                {getStatusIcon(execution.status)}
                <div className={styles.cardInfo}>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-white">Execution</span>
                    {execution.is_dry_run && (
                      <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded">
                        DRY RUN
                      </span>
                    )}
                    <span className={`${styles.statusBadge} ${styles[`status-${execution.status}`]}`}>
                      {execution.status}
                    </span>
                  </div>
                  <div className={styles.workflowId}>
                    Workflow ID: {execution.workflow_id}
                  </div>
                  <div className="text-sm text-gray-400">
                    Started: {new Date(execution.started_at).toLocaleString()}
                  </div>
                </div>
              </div>
              
              <div className={styles.actions}>
                <button className={styles.viewButton} onClick={() => alert('Detailed execution view coming soon!')}>
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
