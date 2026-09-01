import React, { useState } from 'react';
import { WorkflowRunOutputResponse } from '../../types/phase2';
import { AlertCircle, AlertTriangle } from 'lucide-react';
import { RegistryDataTable } from '../common/RegistryDataTable';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  outputs: WorkflowRunOutputResponse[];
  canViewRaw: boolean;
  error?: string | null;
}

export const RunOutputViewer: React.FC<Props> = ({ outputs, canViewRaw, error }) => {
  const [activeTab, setActiveTab] = useState<'FINDINGS' | 'RECOMMENDATIONS' | 'EVIDENCE' | 'RAW'>('FINDINGS');

  if (error) {
    return (
      <div className={styles.banner}>
        <AlertCircle size={16} /> {error}
      </div>
    );
  }

  if (!outputs || outputs.length === 0) {
    return <p className={styles.stateDesc}>No outputs generated for this run.</p>;
  }

  const tabs = ['FINDINGS', 'RECOMMENDATIONS', 'EVIDENCE'];
  if (canViewRaw) tabs.push('RAW');

  const activeOutput = outputs.find(o => o.output_type === activeTab) || outputs[0];
  let parsedContent: any = null;
  let parseError = false;

  if (activeOutput) {
    try {
      parsedContent = JSON.parse((activeOutput as any).output_content);
    } catch (e) {
      parseError = true;
    }
  }

  const renderContent = () => {
    if (!activeOutput) return <p className={styles.stateDesc}>No output available for {activeTab}</p>;

    if (parseError) {
      return (
        <div className={styles.fieldStack}>
          <div className={styles.dangerCard}>
            <AlertTriangle size={16} /> <strong>Warning:</strong> Failed to parse output JSON.
          </div>
          <details className={styles.detailsToggle} open>
            <summary>Raw Output Content</summary>
            <pre className={styles.codeBlock} style={{ marginTop: '8px' }}>{(activeOutput as any).output_content}</pre>
          </details>
        </div>
      );
    }

    if (activeOutput.output_type === 'FINDINGS') {
      const findings = Array.isArray(parsedContent) ? parsedContent : (parsedContent?.findings || []);
      const columns = [
        { key: 'finding_code', label: 'Finding Code', render: (r: any) => r.finding_code },
        { key: 'entity_type', label: 'Entity Type', render: (r: any) => r.entity_type },
        { key: 'entity_code', label: 'Entity Code', render: (r: any) => r.entity_code },
        { key: 'message', label: 'Message', render: (r: any) => r.message }
      ];
      return <RegistryDataTable columns={columns} data={findings} emptyMessage="No findings found in output." isLoading={false} totalCount={findings.length} page={1} pageSize={findings.length || 10} onPageChange={() => {}} />;
    }

    if (activeOutput.output_type === 'RECOMMENDATIONS') {
      const recommendations = Array.isArray(parsedContent) ? parsedContent : (parsedContent?.recommendations || []);
      const columns = [
        { key: 'type', label: 'Type', render: (r: any) => r.type },
        { key: 'priority', label: 'Priority', render: (r: any) => r.priority },
        { key: 'recommended_action', label: 'Action', render: (r: any) => r.recommended_action }
      ];
      return <RegistryDataTable columns={columns} data={recommendations} emptyMessage="No recommendations found in output." isLoading={false} totalCount={recommendations.length} page={1} pageSize={recommendations.length || 10} onPageChange={() => {}} />;
    }

    if (activeOutput.output_type === 'EVIDENCE' || activeTab === 'RAW') {
      return (
        <details className={styles.detailsToggle} open>
          <summary>{activeTab === 'RAW' ? 'Raw JSON' : 'Evidence JSON'}</summary>
          <pre className={styles.codeBlock} style={{ marginTop: '8px' }}>{JSON.stringify(parsedContent, null, 2)}</pre>
        </details>
      );
    }

    return <pre className={styles.codeBlock}>{JSON.stringify(parsedContent, null, 2)}</pre>;
  };

  return (
    <div className={styles.detailCard}>
      <div className={styles.detailTabsHeader}>
        <nav className={styles.detailTabsNav}>
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`${styles.tabLink} ${activeTab === tab ? styles.activeTab : ''}`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>
      <div className={styles.tabBody}>
        <div style={{ marginBottom: '16px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className={styles.tagChip}>{activeOutput?.output_type || activeTab}</span>
          {activeOutput?.severity && <span className={`${styles.pill} ${styles.pillWarning}`}>{activeOutput.severity}</span>}
          {activeOutput?.risk_score !== undefined && activeOutput.risk_score !== null && (
            <span className={styles.subText}>Risk Score: <strong>{activeOutput.risk_score}</strong></span>
          )}
        </div>
        {renderContent()}
      </div>
    </div>
  );
};
