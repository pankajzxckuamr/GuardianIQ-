import React, { useState } from 'react';
import { WorkflowRunOutputResponse } from '../../types/phase2';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  outputs: WorkflowRunOutputResponse[];
  canViewRaw: boolean;
}

export const RunOutputViewer: React.FC<Props> = ({ outputs, canViewRaw }) => {
  const [activeTab, setActiveTab] = useState<'FINDINGS' | 'RECOMMENDATIONS' | 'EVIDENCE' | 'RAW'>('FINDINGS');

  const tabs = ['FINDINGS', 'RECOMMENDATIONS', 'EVIDENCE'];
  if (canViewRaw) tabs.push('RAW');

  const activeOutput = outputs.find(o => o.output_type === activeTab) || outputs[0];

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
        {activeOutput ? (
          <pre className={styles.codeBlock}>{(activeOutput as any).output_content}</pre>
        ) : (
          <p className={styles.stateDesc}>No output available for {activeTab}</p>
        )}
      </div>
    </div>
  );
};
