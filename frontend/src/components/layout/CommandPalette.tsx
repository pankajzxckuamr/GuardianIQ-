/* src/components/layout/CommandPalette.tsx */

import React, { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Search, PlusCircle, LayoutDashboard, Brain, Cpu, Plug, Database, GitBranch, Users, Link2, Building2
} from "lucide-react";
import * as registryService from "../../services/registry/registryService";
import styles from "./CommandPalette.module.css";

// Form Modals
import { ModelFormModal } from "../registry/ModelFormModal";
import { AgentFormModal } from "../registry/AgentFormModal";
import { ToolFormModal } from "../registry/ToolFormModal";
import { DataSourceFormModal } from "../registry/DataSourceFormModal";
import { WorkflowFormModal } from "../registry/WorkflowFormModal";

interface CommandItem {
  id: string;
  type: "ACTION" | "NAV" | "ENTITY";
  label: string;
  icon?: React.ReactNode;
  badge?: string;
  path?: string;
  onTrigger?: () => void;
}

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  // Modal states
  const [isModelModalOpen, setIsModelModalOpen] = useState(false);
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false);
  const [isToolModalOpen, setIsToolModalOpen] = useState(false);
  const [isDataSourceModalOpen, setIsDataSourceModalOpen] = useState(false);
  const [isWorkflowModalOpen, setIsWorkflowModalOpen] = useState(false);

  // Entities state
  const [entities, setEntities] = useState<CommandItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Global hotkey listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  // Reset when opened
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Handle entity search
  useEffect(() => {
    if (query.trim().length < 2) {
      setEntities([]);
      return;
    }

    setIsSearching(true);
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await registryService.globalSearch(query);
        if (res.data) {
          const newEntities: CommandItem[] = [];
          Object.keys(res.data).forEach((key) => {
            const items = (res.data as any)[key] || [];
            items.forEach((item: any) => {
              newEntities.push({
                id: `entity_${item.id}`,
                type: "ENTITY",
                label: item.name || item.code || "Unknown Entity",
                badge: item.entity_type,
                path: getEntityPath(item.entity_type, item.id),
                icon: getEntityIcon(item.entity_type)
              });
            });
          });
          setEntities(newEntities);
          setSelectedIndex(0);
        }
      } catch (err) {
        console.error("Global search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const getEntityPath = (type: string, id: string) => {
    const base = type.toLowerCase().replace("_", "-");
    if (type === "USER") return `/registry/users-roles?tab=users&search=${id}`;
    if (type === "ROLE") return `/registry/users-roles?tab=roles&search=${id}`;
    return `/registry/${base}s?search=${id}`;
  };

  const getEntityIcon = (type: string) => {
    const t = type.toUpperCase();
    if (t === "MODEL") return <Brain size={16} />;
    if (t === "AGENT") return <Cpu size={16} />;
    if (t === "TOOL") return <Plug size={16} />;
    if (t === "WORKFLOW") return <GitBranch size={16} />;
    if (t === "DATA_SOURCE") return <Database size={16} />;
    return <Search size={16} />;
  };

  const actions: CommandItem[] = useMemo(() => [
    { id: "action_model", type: "ACTION", label: "Register new AI Model", icon: <PlusCircle size={16} />, onTrigger: () => setIsModelModalOpen(true) },
    { id: "action_agent", type: "ACTION", label: "Register new AI Agent", icon: <PlusCircle size={16} />, onTrigger: () => setIsAgentModalOpen(true) },
    { id: "action_tool", type: "ACTION", label: "Register new Tool", icon: <PlusCircle size={16} />, onTrigger: () => setIsToolModalOpen(true) },
    { id: "action_ds", type: "ACTION", label: "Register new Data Source", icon: <PlusCircle size={16} />, onTrigger: () => setIsDataSourceModalOpen(true) },
    { id: "action_workflow", type: "ACTION", label: "Register new Workflow", icon: <PlusCircle size={16} />, onTrigger: () => setIsWorkflowModalOpen(true) },
  ], []);

  const navs: CommandItem[] = useMemo(() => [
    { id: "nav_dash", type: "NAV", label: "Go to Dashboard", icon: <LayoutDashboard size={16} />, path: "/dashboard" },
    { id: "nav_models", type: "NAV", label: "Go to AI Models", icon: <Brain size={16} />, path: "/registry/models" },
    { id: "nav_agents", type: "NAV", label: "Go to AI Agents", icon: <Cpu size={16} />, path: "/registry/agents" },
    { id: "nav_tools", type: "NAV", label: "Go to Tools", icon: <Plug size={16} />, path: "/registry/tools" },
    { id: "nav_workflows", type: "NAV", label: "Go to Workflows", icon: <GitBranch size={16} />, path: "/registry/workflows" },
    { id: "nav_ds", type: "NAV", label: "Go to Data Sources", icon: <Database size={16} />, path: "/registry/data-sources" },
    { id: "nav_users", type: "NAV", label: "Go to Users & Roles", icon: <Users size={16} />, path: "/registry/users-roles" },
    { id: "nav_depts", type: "NAV", label: "Go to Departments", icon: <Building2 size={16} />, path: "/registry/departments" },
    { id: "nav_rels", type: "NAV", label: "Go to Relationships", icon: <Link2 size={16} />, path: "/registry/relationships" },
  ], []);

  // Filter local items
  const filteredActions = actions.filter(a => a.label.toLowerCase().includes(query.toLowerCase()));
  const filteredNavs = navs.filter(n => n.label.toLowerCase().includes(query.toLowerCase()));

  const allResults = [...entities, ...filteredActions, ...filteredNavs];

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < allResults.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : allResults.length - 1));
    } else if (e.key === "Enter" && allResults[selectedIndex]) {
      e.preventDefault();
      executeCommand(allResults[selectedIndex]);
    }
  };

  // Scroll into view logic
  useEffect(() => {
    if (listRef.current) {
      const activeEl = listRef.current.querySelector(`.${styles.itemActive}`);
      if (activeEl) {
        activeEl.scrollIntoView({ block: "nearest" });
      }
    }
  }, [selectedIndex]);

  const executeCommand = (item: CommandItem) => {
    setIsOpen(false);
    if (item.onTrigger) {
      item.onTrigger();
    } else if (item.path) {
      navigate(item.path);
    }
  };

  const noResults = allResults.length === 0;

  return (
    <>
      {isOpen && (
        <div className={styles.overlay} onClick={() => setIsOpen(false)}>
          <div className={styles.palette} onClick={(e) => e.stopPropagation()}>
            <div className={styles.searchHeader}>
              <Search className={styles.searchIcon} size={20} />
              <input
                ref={inputRef}
                className={styles.searchInput}
                placeholder="Search commands, navigate, or find entities..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                onKeyDown={handleKeyDown}
              />
              <span className={styles.escHint}>ESC to close</span>
            </div>

            <div className={styles.resultsList} ref={listRef}>
              {noResults ? (
                <div className={styles.noResults}>
                  {isSearching ? "Searching..." : "No results found."}
                </div>
              ) : (
                <>
                  {entities.length > 0 && (
                    <div className={styles.group}>
                      <div className={styles.groupTitle}>Entities</div>
                      {entities.map((item, idx) => (
                        <div
                          key={item.id}
                          className={`${styles.item} ${idx === selectedIndex ? styles.itemActive : ""}`}
                          onClick={() => executeCommand(item)}
                          onMouseEnter={() => setSelectedIndex(idx)}
                        >
                          <div className={styles.itemIcon}>{item.icon}</div>
                          <div className={styles.itemLabel}>{item.label}</div>
                          {item.badge && <div className={styles.itemBadge}>{item.badge}</div>}
                        </div>
                      ))}
                    </div>
                  )}

                  {filteredActions.length > 0 && (
                    <div className={styles.group}>
                      <div className={styles.groupTitle}>Actions</div>
                      {filteredActions.map((item, idx) => {
                        const globalIdx = entities.length + idx;
                        return (
                          <div
                            key={item.id}
                            className={`${styles.item} ${globalIdx === selectedIndex ? styles.itemActive : ""}`}
                            onClick={() => executeCommand(item)}
                            onMouseEnter={() => setSelectedIndex(globalIdx)}
                          >
                            <div className={styles.itemIcon}>{item.icon}</div>
                            <div className={styles.itemLabel}>{item.label}</div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {filteredNavs.length > 0 && (
                    <div className={styles.group}>
                      <div className={styles.groupTitle}>Navigation</div>
                      {filteredNavs.map((item, idx) => {
                        const globalIdx = entities.length + filteredActions.length + idx;
                        return (
                          <div
                            key={item.id}
                            className={`${styles.item} ${globalIdx === selectedIndex ? styles.itemActive : ""}`}
                            onClick={() => executeCommand(item)}
                            onMouseEnter={() => setSelectedIndex(globalIdx)}
                          >
                            <div className={styles.itemIcon}>{item.icon}</div>
                            <div className={styles.itemLabel}>{item.label}</div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Render Modals silently so they can open when toggled */}
      <ModelFormModal isOpen={isModelModalOpen} onClose={() => setIsModelModalOpen(false)} onSuccess={() => {}} />
      <AgentFormModal isOpen={isAgentModalOpen} onClose={() => setIsAgentModalOpen(false)} onSuccess={() => {}} />
      <ToolFormModal isOpen={isToolModalOpen} onClose={() => setIsToolModalOpen(false)} onSuccess={() => {}} />
      <DataSourceFormModal isOpen={isDataSourceModalOpen} onClose={() => setIsDataSourceModalOpen(false)} onSuccess={() => {}} />
      <WorkflowFormModal isOpen={isWorkflowModalOpen} onClose={() => setIsWorkflowModalOpen(false)} onSuccess={() => {}} />
    </>
  );
};
