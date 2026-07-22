import React from "react";
import { HelpCircle } from "lucide-react";
import styles from "./FieldInfo.module.css";

interface FieldInfoProps {
  tooltip: string;
  format?: string;
  example?: string;
}

export const FieldInfo: React.FC<FieldInfoProps> = ({ tooltip, format, example }) => {
  // Derive default format & generic example if not explicitly provided
  let displayFormat = format;
  let displayExample = example;

  if (!displayFormat || !displayExample) {
    const tLower = (tooltip || "").toLowerCase();
    
    if (tLower.includes("email")) {
      displayFormat = displayFormat || "Email address string";
      displayExample = displayExample || "john.doe@example.com";
    } else if (tLower.includes("code") || tLower.includes("identifier")) {
      displayFormat = displayFormat || "Alphanumeric uppercase code";
      displayExample = displayExample || "ASSET_001";
    } else if (tLower.includes("model")) {
      displayFormat = displayFormat || "AI Model reference";
      displayExample = displayExample || "Foundation Model 01";
    } else if (tLower.includes("tool") || tLower.includes("connector")) {
      displayFormat = displayFormat || "Tool connector reference";
      displayExample = displayExample || "REST API Connector";
    } else if (tLower.includes("workflow")) {
      displayFormat = displayFormat || "Workflow process reference";
      displayExample = displayExample || "Data Processing Workflow";
    } else if (tLower.includes("data source") || tLower.includes("dataset") || tLower.includes("training")) {
      displayFormat = displayFormat || "Data repository reference";
      displayExample = displayExample || "Customer Records Store";
    } else if (tLower.includes("department")) {
      displayFormat = displayFormat || "Enterprise department lookup";
      displayExample = displayExample || "Engineering";
    } else if (tLower.includes("user") || tLower.includes("owner") || tLower.includes("approver") || tLower.includes("leader")) {
      displayFormat = displayFormat || "User account lookup";
      displayExample = displayExample || "John Doe (john.doe@example.com)";
    } else if (tLower.includes("team") || tLower.includes("developed")) {
      displayFormat = displayFormat || "Organization team name";
      displayExample = displayExample || "AI Platform Team";
    } else if (tLower.includes("hosting")) {
      displayFormat = displayFormat || "Cloud / Hosting environment";
      displayExample = displayExample || "AWS Cloud";
    } else if (tLower.includes("status")) {
      displayFormat = displayFormat || "Lifecycle state enum";
      displayExample = displayExample || "ACTIVE";
    } else if (tLower.includes("json") || tLower.includes("payload") || tLower.includes("configuration")) {
      displayFormat = displayFormat || "Valid JSON object payload";
      displayExample = displayExample || '{"setting": "value"}';
    } else if (tLower.includes("description")) {
      displayFormat = displayFormat || "Free-form text";
      displayExample = displayExample || "Detailed description of operational purpose.";
    } else if (tLower.includes("url") || tLower.includes("endpoint") || tLower.includes("reference")) {
      displayFormat = displayFormat || "URL or system reference";
      displayExample = displayExample || "https://api.example.com/v1";
    } else if (tLower.includes("type") || tLower.includes("category") || tLower.includes("mode") || tLower.includes("level") || tLower.includes("role") || tLower.includes("policy") || tLower.includes("format") || tLower.includes("provider") || tLower.includes("region") || tLower.includes("action") || tLower.includes("permission") || tLower.includes("operation") || tLower.includes("class") || tLower.includes("clearance")) {
      displayFormat = displayFormat || "Dropdown selection enum";
      displayExample = displayExample || "STANDARD_OPTION";
    } else if (tLower.includes("version") || tLower.includes("tag")) {
      displayFormat = displayFormat || "Version string";
      displayExample = displayExample || "v1.0.0";
    } else if (tLower.includes("date") || tLower.includes("time")) {
      displayFormat = displayFormat || "Local ISO datetime";
      displayExample = displayExample || "2026-01-01 12:00";
    } else if (tLower.includes("threshold") || tLower.includes("score") || tLower.includes("limit") || tLower.includes("count")) {
      displayFormat = displayFormat || "Numeric value";
      displayExample = displayExample || "85";
    } else if (tLower.includes("name")) {
      displayFormat = displayFormat || "String (1-100 characters)";
      displayExample = displayExample || "Sample Asset Name";
    } else {
      displayFormat = displayFormat || "Form input field";
      displayExample = displayExample || "Generic Sample Value";
    }
  }

  return (
    <span className={styles.container}>
      <span className={styles.iconWrapper}>
        <HelpCircle size={14} className={styles.icon} />
      </span>
      <div className={styles.popover}>
        <div className={styles.popoverHeader}>
          <span className={styles.popoverTitle}>Field Guide</span>
        </div>
        <div className={styles.popoverContent}>
          <p style={{ margin: 0, lineHeight: 1.4 }}>{tooltip}</p>
          {(displayFormat || displayExample) && (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px", paddingTop: "8px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
              {displayFormat && (
                <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "0.725rem", alignItems: "baseline" }}>
                  <span style={{ color: "rgba(255,255,255,0.5)", fontWeight: 600 }}>Format:</span>
                  <span style={{ color: "#60a5fa", textAlign: "right" }}>{displayFormat}</span>
                </div>
              )}
              {displayExample && (
                <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "0.725rem", alignItems: "baseline" }}>
                  <span style={{ color: "rgba(255,255,255,0.5)", fontWeight: 600 }}>Example:</span>
                  <code style={{ background: "rgba(0,0,0,0.3)", padding: "1px 4px", borderRadius: "3px", color: "#fca5a5", fontFamily: "monospace" }}>{displayExample}</code>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </span>
  );
};
