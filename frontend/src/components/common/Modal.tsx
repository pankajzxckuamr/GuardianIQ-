import React, { useEffect } from 'react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="giq-modal-overlay" onClick={onClose}>
      <div className="giq-modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="giq-modal-header">
          <h2 className="giq-modal-title">{title}</h2>
          <button className="giq-modal-close" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>
        <div className="giq-modal-content">
          {children}
        </div>
        {footer && (
          <div className="giq-modal-footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
