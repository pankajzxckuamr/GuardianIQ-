import React, { useState } from 'react';
import { AlertCircle, HelpCircle, X } from 'lucide-react';

interface Props {
  open?: boolean;
  title: string;
  message: string;
  onConfirm: (reason?: string) => void;
  onCancel: () => void;
  requireReason?: boolean;
  confirmLabel?: string;
  confirmVariant?: 'primary' | 'danger' | 'secondary';
  isLoading?: boolean;
}

export const ConfirmActionModal: React.FC<Props> = ({ 
  open = true, 
  title, 
  message, 
  onConfirm, 
  onCancel, 
  requireReason,
  confirmLabel = 'Confirm',
  confirmVariant = 'primary',
  isLoading = false
}) => {
  const [reason, setReason] = useState('');

  if (!open) return null;

  const isDanger = confirmVariant === 'danger';

  return (
    <div 
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1050,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        backgroundColor: 'rgba(5, 9, 20, 0.82)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)'
      }}
      onClick={onCancel}
    >
      <div 
        style={{
          width: '100%',
          maxWidth: '480px',
          background: 'linear-gradient(180deg, #131b2e 0%, #0d1322 100%)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '16px',
          padding: '24px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 35px rgba(99, 102, 241, 0.12)',
          color: '#f8fafc',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button 
          onClick={onCancel}
          style={{
            position: 'absolute',
            top: '18px',
            right: '18px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '8px',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)';
            e.currentTarget.style.color = '#f8fafc';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
            e.currentTarget.style.color = '#94a3b8';
          }}
        >
          <X size={16} />
        </button>

        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '16px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: isDanger ? 'rgba(239, 68, 68, 0.15)' : 'rgba(99, 102, 241, 0.15)',
            border: `1px solid ${isDanger ? 'rgba(239, 68, 68, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            color: isDanger ? '#ef4444' : '#818cf8'
          }}>
            {isDanger ? <AlertCircle size={22} /> : <HelpCircle size={22} />}
          </div>
          <div style={{ flex: 1, paddingRight: '24px' }}>
            <h3 style={{ margin: '0 0 6px 0', fontSize: '1.15rem', fontWeight: 600, color: '#f8fafc' }}>
              {title}
            </h3>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#94a3b8', lineHeight: 1.5 }}>
              {message}
            </p>
          </div>
        </div>

        {requireReason && (
          <div style={{ marginTop: '16px', marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, color: '#cbd5e1', marginBottom: '6px' }}>
              Reason <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <textarea
              rows={3}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: 'rgba(10, 15, 29, 0.7)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '8px',
                padding: '10px 12px',
                color: '#f8fafc',
                fontSize: '0.875rem',
                outline: 'none',
                resize: 'vertical',
                fontFamily: 'inherit'
              }}
              placeholder="Please provide a reason..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              onFocus={(e) => e.currentTarget.style.borderColor = '#6366f1'}
              onBlur={(e) => e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.12)'}
            />
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
          <button
            type="button"
            disabled={isLoading}
            onClick={onCancel}
            style={{
              padding: '9px 18px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#cbd5e1',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              if (!isLoading) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
            }}
            onMouseLeave={(e) => {
              if (!isLoading) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
            }}
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isLoading || (requireReason && !reason.trim())}
            onClick={() => onConfirm(reason)}
            style={{
              padding: '9px 22px',
              borderRadius: '8px',
              border: 'none',
              background: isDanger 
                ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' 
                : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: '#ffffff',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: (isLoading || (requireReason && !reason.trim())) ? 'not-allowed' : 'pointer',
              opacity: (isLoading || (requireReason && !reason.trim())) ? 0.6 : 1,
              boxShadow: isDanger 
                ? '0 4px 14px rgba(239, 68, 68, 0.35)' 
                : '0 4px 14px rgba(99, 102, 241, 0.35)',
              transition: 'all 0.15s ease'
            }}
          >
            {isLoading ? 'Processing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
