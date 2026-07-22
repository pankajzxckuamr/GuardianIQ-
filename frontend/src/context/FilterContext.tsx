import React, { createContext, useContext, useState, useCallback } from 'react';

interface FilterContextType {
  filters: Record<string, any>;
  setFilter: (key: string, value: any) => void;
  clearFilters: (moduleKey?: string) => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export const FilterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [filters, setFilters] = useState<Record<string, any>>({});

  const setFilter = useCallback((key: string, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const clearFilters = useCallback((moduleKey?: string) => {
    if (moduleKey) {
      setFilters((prev) => {
        const next = { ...prev };
        Object.keys(next).forEach((k) => {
          if (k.startsWith(`${moduleKey}:`)) {
            delete next[k];
          }
        });
        return next;
      });
    } else {
      setFilters({});
    }
  }, []);

  return (
    <FilterContext.Provider value={{ filters, setFilter, clearFilters }}>
      {children}
    </FilterContext.Provider>
  );
};

export const useFilterStore = () => {
  const context = useContext(FilterContext);
  if (!context) throw new Error('useFilterStore must be used within FilterProvider');
  return context;
};
