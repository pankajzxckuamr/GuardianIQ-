import React from 'react';
import { AlertCircle } from 'lucide-react';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  approvalRequired: boolean;
  reasons: string[];
  approverGroupName?: string;
}

export const ApprovalRequirementBanner: React.FC<Props> = ({ approvalRequired, reasons, approverGroupName }) => {
  if (!approvalRequired) return null;

  return (
    <div className={styles.noticeBox}>
      <h3 className={styles.noticeTitle}>
        <AlertCircle size={15} /> Approval Required {approverGroupName && `from ${approverGroupName}`}
      </h3>
      <ul className={styles.bulletList} style={{ marginTop: 8 }}>
        {reasons.map((reason, idx) => (
          <li key={idx}>{reason}</li>
        ))}
      </ul>
    </div>
  );
};
