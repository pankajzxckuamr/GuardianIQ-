import React, { createContext, useContext, useState } from 'react';

interface SessionContextType {
  activeTenantId: string | null;
  setActiveTenantId: (tenantId: string | null) => void;
  systemEnvironment: string;
  setSystemEnvironment: (env: string) => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);
  const [systemEnvironment, setSystemEnvironment] = useState<string>('production');

  return (
    <SessionContext.Provider value={{ activeTenantId, setActiveTenantId, systemEnvironment, setSystemEnvironment }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSessionStore = () => {
  const context = useContext(SessionContext);
  if (!context) throw new Error('useSessionStore must be used within SessionProvider');
  return context;
};
