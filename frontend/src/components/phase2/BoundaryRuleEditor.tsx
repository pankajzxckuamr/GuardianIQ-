import React from 'react';
import { AlertTriangle } from 'lucide-react';
import styles from '../../pages/phase2Shared.module.css';

interface ToolOption {
  id: string;
  name: string;
  capability: string;
}

interface Props {
  allowedTools: string[];
  allowedDataSources: string[];
  blockedOperations: string[];
  onChange: (field: string, value: any) => void;
  toolOptions: ToolOption[];
}

export const BoundaryRuleEditor: React.FC<Props> = ({ allowedTools, blockedOperations, onChange, toolOptions }) => {
  return (
    <div className={styles.fieldStack}>
      <div>
        <h4 className={styles.subHeading}>Allowed Tools</h4>
        <div className={styles.checkboxList}>
          {toolOptions.map(tool => (
            <label key={tool.id} className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={allowedTools.includes(tool.id)}
                onChange={(e) => {
                  const newTools = e.target.checked
                    ? [...allowedTools, tool.id]
                    : allowedTools.filter(t => t !== tool.id);
                  onChange('allowedTools', newTools);
                }}
              />
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                {tool.name}
                {tool.capability === 'WRITE' && <AlertTriangle size={14} style={{ color: 'var(--color-warning)' }} />}
              </span>
            </label>
          ))}
          {toolOptions.length === 0 && <span className={styles.subText}>No tools available.</span>}
        </div>
      </div>
      <div>
        <label className={styles.fieldLabel}>Blocked Operations (comma separated)</label>
        <input
          type="text"
          className={styles.formControl}
          value={blockedOperations.join(', ')}
          onChange={(e) => onChange('blockedOperations', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
          placeholder="e.g. DROP TABLE, DELETE, EXECUTE"
        />
      </div>
    </div>
  );
};
