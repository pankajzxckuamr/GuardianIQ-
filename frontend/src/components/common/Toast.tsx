/* src/components/common/Toast.tsx */

import React from "react";
import styles from "./Toast.module.css";
import type { ToastItem } from "../../context/ToastContext";

interface ToastContainerProps {
  toasts: ToastItem[];
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts }) => {
  return (
    <div className={styles.container}>
      {toasts.map((toast) => (
        <div key={toast.id} className={`${styles.toast} ${styles[toast.type]}`}>
          <span className={styles.message}>{toast.message}</span>
        </div>
      ))}
    </div>
  );
};
