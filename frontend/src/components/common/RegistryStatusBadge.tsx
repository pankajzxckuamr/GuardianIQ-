/* src/components/common/RegistryStatusBadge.tsx */

import React from "react";
import styles from "./RegistryStatusBadge.module.css";

interface RegistryStatusBadgeProps {
  status: string;
}

export const RegistryStatusBadge: React.FC<RegistryStatusBadgeProps> = ({ status }) => {
  const normalizedStatus = status ? status.toLowerCase() : "";
  const modifierClass = styles[normalizedStatus] || "";

  return (
    <span className={`${styles.badge} ${modifierClass}`}>
      {status || "UNKNOWN"}
    </span>
  );
};
