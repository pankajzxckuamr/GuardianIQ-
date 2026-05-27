import React from 'react';
import { AppRouter } from '@/routes/AppRouter';
import { ToastProvider } from '@/components/feedback/Toast';
import { AuthProvider } from '@/context/AuthContext';

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </ToastProvider>
  );
};
