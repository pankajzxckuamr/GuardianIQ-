import React, { createContext, useContext, useState } from 'react';

export interface BreadcrumbItem {
  label: string;
  url?: string;
}

interface NavigationContextType {
  breadcrumbs: BreadcrumbItem[];
  setBreadcrumbs: (crumbs: BreadcrumbItem[]) => void;
  activeModule: string;
  setActiveModule: (module: string) => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export const NavigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([]);
  const [activeModule, setActiveModule] = useState<string>('registry');

  return (
    <NavigationContext.Provider value={{ breadcrumbs, setBreadcrumbs, activeModule, setActiveModule }}>
      {children}
    </NavigationContext.Provider>
  );
};

export const useNavigationStore = () => {
  const context = useContext(NavigationContext);
  if (!context) throw new Error('useNavigationStore must be used within NavigationProvider');
  return context;
};
