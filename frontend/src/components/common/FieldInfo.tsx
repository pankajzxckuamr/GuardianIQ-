import React from "react";
import { HelpCircle } from "lucide-react";
import styles from "./FieldInfo.module.css";

interface FieldInfoProps {
  tooltip: string;
}

export const FieldInfo: React.FC<FieldInfoProps> = ({ tooltip }) => {
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
          {tooltip}
        </div>
      </div>
    </span>
  );
};
