/* src/components/common/Loader.tsx */
import React from "react";
import "./Loader.css";

interface LoaderProps {
  fullScreen?: boolean;
  label?: string;
}

export const Loader: React.FC<LoaderProps> = ({ fullScreen = false, label = "Loading..." }) => {
  return (
    <div className={`loader-wrap ${fullScreen ? "loader-wrap--full" : ""}`}>
      <div className="loader-ring">
        <div /><div /><div /><div />
      </div>
      {label && <p className="loader-label">{label}</p>}
    </div>
  );
};
