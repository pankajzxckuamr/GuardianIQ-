import React, { useMemo } from 'react';
import { AlertTriangle } from 'lucide-react';
import styles from '../../pages/phase2Shared.module.css';

interface ToolOption {
  id: string;
  tool_code?: string;
  tool_name?: string;
  name?: string;
  access_mode?: string;
  capability?: string;
}

interface Props {
  allowedTools: string[];
  allowedDataSources: string[];
  blockedOperations: string[];
  onChange: (field: string, value: any) => void;
  toolOptions: ToolOption[];
}

const WRITE_MODES = new Set(['WRITE', 'EXECUTE', 'ADMIN']);

function normalizeTool(tool: ToolOption) {
  const code = tool.tool_code || tool.id;
  const accessMode = tool.access_mode || tool.capability || 'READ';
  return {
    id: tool.id,
    code,
    label: tool.tool_name || tool.name || code,
    accessMode,
    isWriteCapable: WRITE_MODES.has(accessMode),
  };
}

function matchesAllowedTool(allowedTools: string[], tool: ReturnType<typeof normalizeTool>) {
  return allowedTools.includes(tool.code) || allowedTools.includes(tool.id);
}

export const BoundaryRuleEditor: React.FC<Props> = ({ allowedTools, blockedOperations, onChange, toolOptions }) => {
  const tools = useMemo(() => toolOptions.map(normalizeTool), [toolOptions]);

  const selectedCodes = useMemo(
    () => tools.filter(tool => matchesAllowedTool(allowedTools, tool)).map(tool => tool.code),
    [allowedTools, tools],
  );

  const selectedTools = useMemo(
    () => tools.filter(tool => matchesAllowedTool(allowedTools, tool)),
    [allowedTools, tools],
  );

  return (
    <div className={styles.fieldStack}>
      <div>
        <label className={styles.fieldLabel} htmlFor="allowed-tools-select">Allowed Tools</label>
        {tools.length > 0 ? (
          <>
            <select
              id="allowed-tools-select"
              multiple
              className={`${styles.formControl} ${styles.multiSelect}`}
              value={selectedCodes}
              onChange={(e) => {
                const next = Array.from(e.target.selectedOptions, option => option.value);
                onChange('allowed_tools_json', next);
              }}
            >
              {tools.map(tool => (
                <option key={tool.id} value={tool.code}>
                  {tool.label} ({tool.accessMode})
                </option>
              ))}
            </select>
            <p className={styles.subText}>Hold Cmd/Ctrl (or Shift) to select multiple tools.</p>
            {selectedTools.length > 0 && (
              <div className={styles.selectedChips}>
                {selectedTools.map(tool => (
                  <span key={tool.code} className={styles.tagChip}>
                    {tool.label}
                    {tool.isWriteCapable && (
                      <AlertTriangle size={12} style={{ marginLeft: 4, color: 'var(--color-warning, #f59e0b)' }} />
                    )}
                  </span>
                ))}
              </div>
            )}
          </>
        ) : (
          <p className={styles.subText}>No tools available. Register tools in the Registry first.</p>
        )}
      </div>
      <div>
        <label className={styles.fieldLabel} htmlFor="blocked-operations-input">Blocked Operations (comma separated)</label>
        <input
          id="blocked-operations-input"
          type="text"
          className={styles.formControl}
          value={blockedOperations.join(', ')}
          onChange={(e) => onChange('blocked_operations_json', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
          placeholder="e.g. DROP TABLE, DELETE, EXECUTE"
        />
      </div>
    </div>
  );
};
