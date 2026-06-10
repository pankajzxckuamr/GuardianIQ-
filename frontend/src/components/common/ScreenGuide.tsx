import React, { useState, useEffect, useRef } from "react";
import { Lightbulb, X } from "lucide-react";
import styles from "./ScreenGuide.module.css";

interface ScreenGuideProps {
  content: React.ReactNode;
}

export const ScreenGuide: React.FC<ScreenGuideProps> = ({ content }) => {
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

  return (
    <div className={styles.container} ref={containerRef}>
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
            {content}
          </div>
        </div>
      )}
    </div>
  );
};
