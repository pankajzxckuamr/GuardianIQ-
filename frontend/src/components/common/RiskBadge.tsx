/* src/components/common/RiskBadge.tsx */

import React from "react";
import styles from "./RiskBadge.module.css";

interface RiskBadgeProps {
  level: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level }) => {
  const normalizedLevel = level ? level.toLowerCase() : "";
  const modifierClass = styles[normalizedLevel] || "";

  return (
    <span className={`${styles.badge} ${modifierClass}`}>
      {level || "UNKNOWN"}
    </span>
  );
};
