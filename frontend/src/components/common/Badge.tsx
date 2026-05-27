/* src/components/common/Badge.tsx */
import React from "react";
import "./Badge.css";
import type { StatusVariant } from "../../types/common";

interface BadgeProps {
  label: string;
  variant?: StatusVariant;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ label, variant = "neutral", dot = false }) => {
  return (
    <span className={`badge badge--${variant}`}>
      {dot && <span className="badge-dot" />}
      {label}
    </span>
  );
};
