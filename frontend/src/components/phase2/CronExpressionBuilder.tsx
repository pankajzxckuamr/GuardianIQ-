import React from 'react';
import styles from '../../pages/phase2Shared.module.css';

interface Props {
  value: string;
  onChange: (cron: string) => void;
  timezone: string;
}

export const CronExpressionBuilder: React.FC<Props> = ({ value, onChange, timezone }) => {
  return (
    <div className={styles.section}>
      <label className={styles.fieldLabel}>Schedule Expression (Cron)</label>
      <input
        type="text"
        className={styles.formControl}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="* * * * *"
      />
      <p className={styles.subText} style={{ marginTop: 8 }}>Timezone: {timezone}</p>
    </div>
  );
};
