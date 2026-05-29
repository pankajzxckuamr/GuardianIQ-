import React, { useState, useEffect } from 'react';
import { Modal } from './Modal';
import styles from './ConfirmDeleteModal.module.css';

interface ConfirmDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  entityName: string;
  entityType: string;
  isDeleting?: boolean;
}

export const ConfirmDeleteModal: React.FC<ConfirmDeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  entityName,
  entityType,
  isDeleting = false
}) => {
  const [confirmText, setConfirmText] = useState('');
  
  useEffect(() => {
    if (!isOpen) {
      setConfirmText('');
    }
  }, [isOpen]);

  const handleConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    if (confirmText === entityName) {
      onConfirm();
    }
  };

  const isMatch = confirmText === entityName;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Delete ${entityType}`} size="md">
      <div className={styles.container}>
        <div className={styles.warningIcon}>
          ⚠️
        </div>
        <h3 className={styles.title}>Are you absolutely sure?</h3>
        <p className={styles.description}>
          This action <strong>cannot be undone</strong>. This will permanently delete the 
          {entityType.toLowerCase()} <strong>{entityName}</strong> and remove all of its associations.
        </p>
        
        <form onSubmit={handleConfirm} className={styles.form}>
          <label htmlFor="confirm-text" className={styles.label}>
            Please type <strong>{entityName}</strong> to confirm.
          </label>
          <input
            id="confirm-text"
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            disabled={isDeleting}
            className={styles.input}
            autoComplete="off"
            required
          />
          
          <div className={styles.actions}>
            <button
              type="button"
              onClick={onClose}
              disabled={isDeleting}
              className={styles.cancelBtn}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isMatch || isDeleting}
              className={`${styles.deleteBtn} ${isMatch ? styles.activeDelete : ''}`}
            >
              {isDeleting ? 'Deleting...' : 'I understand, delete this'}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
