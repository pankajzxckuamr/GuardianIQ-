/* src/components/common/Card.tsx */
import React from "react";
import "./Card.css";

interface CardProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({
  title, subtitle, actions, children, className = "", glow = false,
}) => {
  return (
    <div className={`card ${glow ? "card--glow" : ""} ${className}`}>
      {(title || actions) && (
        <div className="card-header">
          <div className="card-header-text">
            {title && <h3 className="card-title">{title}</h3>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
};
