import React, { useState, useEffect, useRef } from "react";
import { Lightbulb, X } from "lucide-react";
import styles from "./ScreenGuide.module.css";

interface ScreenGuideProps {
  id?: string;
  title?: string;
  description?: string;
  content?: React.ReactNode;
  children?: React.ReactNode;
}

export const ScreenGuide: React.FC<ScreenGuideProps> = ({ id, title, description, content, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const renderContent = () => {
    if (content) return content;
    if (children) return children;
    
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "8px", paddingRight: "4px" }}>
        {title && <h4 style={{ color: "#fbbf24", margin: "0 0 4px 0", fontSize: "0.9rem", fontWeight: 600 }}>{title}</h4>}
        {description && <p style={{ margin: 0, fontSize: "0.8rem", color: "rgba(255, 255, 255, 0.8)", lineHeight: 1.5 }}>{description}</p>}
      </div>
    );
  };

  return (
    <div className={styles.container} ref={containerRef} id={id}>
      <button 
        className={styles.iconBtn} 
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        title="Screen Guide"
      >
        <Lightbulb size={20} className={styles.icon} />
      </button>
      {isOpen && (
        <div className={styles.popover} onClick={(e) => e.stopPropagation()}>
          <div className={styles.popoverHeader}>
            <div className={styles.titleWrap}>
              <Lightbulb size={16} className={styles.headerIcon} />
              <span className={styles.popoverTitle}>Screen Guide</span>
            </div>
            <button 
              className={styles.closeBtn} 
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsOpen(false);
              }}
            >
              <X size={14} />
            </button>
          </div>
          <div className={styles.popoverContent}>
            {renderContent()}
          </div>
        </div>
      )}
    </div>
  );
};
