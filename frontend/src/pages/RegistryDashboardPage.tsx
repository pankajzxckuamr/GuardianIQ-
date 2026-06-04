/* src/pages/RegistryDashboardPage.tsx */

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../components/common/Card";
import { EmptyState } from "../components/common/EmptyState";
import { PageHeader } from "../components/common/PageHeader";
import * as registryService from "../services/registry/registryService";
import styles from "./RegistryDashboardPage.module.css";
import { Brain, Cpu, Plug, GitBranch, Users, Building2, Database, AlertTriangle, ArrowRight, Clock } from "lucide-react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from "recharts";

interface RecentItem {
  id: string;
  name: string;
  code: string;
  type: "MODEL" | "AGENT";
  updated_at: string;
}

export const RegistryDashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [recentUpdates, setRecentUpdates] = useState<RecentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingRecent, setLoadingRecent] = useState(true);

  // Set document title
  useEffect(() => {
    document.title = "Dashboard — GuardianIQ Registry";
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await registryService.getRegistrySummary();
      if (response && response.data) {
        setSummary(response.data);
      }
    } catch (error) {
      console.error("Failed to load registry summary:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentUpdates = async () => {
    try {
      const [modelsRes, agentsRes] = await Promise.all([
        registryService.listModels({ sort_by: "updated_at", sort_dir: "desc", per_page: 3 }),
        registryService.listAgents({ sort_by: "updated_at", sort_dir: "desc", per_page: 3 })
      ]);

      const modelsList = modelsRes.data?.items || [];
      const agentsList = agentsRes.data?.items || [];

      const combined: RecentItem[] = [
        ...modelsList.map((m: any) => ({
          id: m.id,
          name: m.model_name,
          code: m.model_code || "",
          type: "MODEL" as const,
          updated_at: m.updated_at
        })),
        ...agentsList.map((a: any) => ({
          id: a.id,
          name: a.agent_name,
          code: a.agent_code || "",
          type: "AGENT" as const,
          updated_at: a.updated_at
        }))
      ];

      // Sort client-side by updated_at descending
      combined.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      setRecentUpdates(combined.slice(0, 5));
    } catch (error) {
      console.error("Failed to load recently updated assets:", error);
    } finally {
      setLoadingRecent(false);
    }
  };

  // On mount and 60s auto-refresh
  useEffect(() => {
    loadDashboardData();
    loadRecentUpdates();

    const intervalId = setInterval(() => {
      loadDashboardData();
      loadRecentUpdates();
    }, 60000);

    return () => clearInterval(intervalId);
  }, []);

  const timeAgo = (dateStr: string) => {
    if (!dateStr) return "";
    const now = new Date();
    const past = new Date(dateStr);
    const ms = now.getTime() - past.getTime();
    if (ms < 0) return "just now";
    const secs = Math.floor(ms / 1000);
    const mins = Math.floor(secs / 60);
    const hours = Math.floor(mins / 60);
    const days = Math.floor(hours / 24);

    if (secs < 60) return "just now";
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  // Critical risk check
  const modelsCritical = summary?.models?.by_risk_level?.["CRITICAL"] ?? 0;
  const agentsCritical = summary?.agents?.by_risk_level?.["CRITICAL"] ?? 0;
  const criticalRiskCount = modelsCritical + agentsCritical;

  const cardsData = [
    {
      title: "AI Models",
      key: "models",
      count: summary?.models?.total ?? 0,
      path: "/registry/models",
      description: "Manage deployed LLMs, machine learning models, and forecasting scripts.",
      icon: <Brain size={20} />,
      hasBreakdown: true
    },
    {
      title: "AI Agents",
      key: "agents",
      count: summary?.agents?.total ?? 0,
      path: "/registry/agents",
      description: "Govern autonomous agents, operational modes, and execution boundaries.",
      icon: <Cpu size={20} />,
      hasBreakdown: true
    },
    {
      title: "Tools & Connectors",
      key: "tools",
      count: summary?.tools?.total ?? 0,
      path: "/registry/tools",
      description: "Audit connected CRM systems, databases, ticketing APIs, and webhooks.",
      icon: <Plug size={20} />,
      hasBreakdown: true
    },
    {
      title: "Workflows",
      key: "workflows",
      count: summary?.workflows?.total ?? 0,
      path: "/registry/workflows",
      description: "Review automated customer signals, approval steps, and risk reviews.",
      icon: <GitBranch size={20} />,
      hasBreakdown: true
    },
    {
      title: "Data Sources",
      key: "data_sources",
      count: summary?.data_sources?.total ?? 0,
      path: "/registry/data-sources",
      description: "Govern raw data classification, sensitivity levels, and datalake sources.",
      icon: <Database size={20} />,
      hasBreakdown: true
    },
    {
      title: "Users & Roles",
      key: "users",
      count: summary?.users?.total ?? 0,
      path: "/registry/users-roles",
      description: "Manage system personnel, access level roles, and security permissions.",
      icon: <Users size={20} />,
      hasBreakdown: false
    },
    {
      title: "Departments",
      key: "departments",
      count: summary?.departments?.total ?? 0,
      path: "/registry/departments",
      description: "Map company business units and organizational ownership structures.",
      icon: <Building2 size={20} />,
      hasBreakdown: false
    }
  ];

  // --- Chart Data Preparation ---
  const modelTypesData = summary?.models?.by_type
    ? Object.entries(summary.models.by_type).map(([key, value]) => ({ name: key, value }))
    : [];
  const PIE_COLORS = ['#7B8CF7', '#0ea5e9', '#3b82f6', '#06b6d4', '#00f0ff'];

  const agentRiskDataRaw = summary?.agents?.by_risk_level || {};
  const agentRiskData = [
    { name: 'Low', count: agentRiskDataRaw['LOW'] || 0, fill: '#10b981' },
    { name: 'Medium', count: agentRiskDataRaw['MEDIUM'] || 0, fill: '#f59e0b' },
    { name: 'High', count: agentRiskDataRaw['HIGH'] || 0, fill: '#f97316' },
    { name: 'Critical', count: agentRiskDataRaw['CRITICAL'] || 0, fill: '#ef4444' },
  ];

  const toolCategoryData = summary?.tools?.by_category
    ? Object.entries(summary.tools.by_category).map(([key, value]) => ({ name: key, count: value }))
    : [];

  return (
    <div className={styles.dashboard}>
      {/* Task D: Text Breadcrumb */}
      <div className={styles.breadcrumb}>Registry &gt; Dashboard</div>

      <PageHeader
        title="Governance Registry Dashboard"
        description="Real-time oversight and operational metrics of organizational assets."
      />

      {/* Task A: Critical Risk Banner */}
      {criticalRiskCount > 0 && (
        <div className={styles.criticalRiskBanner}>
          <AlertTriangle className={styles.bannerAlertIcon} size={20} />
          <div className={styles.bannerMessage}>
            <strong>CRITICAL GOVERNANCE ALERT</strong>: There are {criticalRiskCount} assets flagged with <strong>CRITICAL</strong> risk level inside the active registry. Ensure reviews are coordinated immediately.
          </div>
          <Link to="/registry/models?risk_level=CRITICAL" className={styles.bannerLink}>
            Audit Models &rarr;
          </Link>
        </div>
      )}

      {/* Registry Grid */}
      <div className={styles.grid}>
        {cardsData.map((card) => {
          const total = card.count;
          
          // Real status breakdowns
          const active = summary?.[card.key]?.by_status?.["ACTIVE"] ?? 0;
          const draft = summary?.[card.key]?.by_status?.["DRAFT"] ?? 0;
          const inactive = summary?.[card.key]?.by_status?.["INACTIVE"] ?? 0;
          const retired = (summary?.[card.key]?.by_status?.["RETIRED"] ?? 0) + 
            (summary?.[card.key]?.by_status?.["ARCHIVED"] ?? 0);

          const activePct = total > 0 ? (active / total) * 100 : 0;
          const draftPct = total > 0 ? (draft / total) * 100 : 0;
          const inactivePct = total > 0 ? (inactive / total) * 100 : 0;
          const retiredPct = total > 0 ? (retired / total) * 100 : 0;

          return (
            <Link to={card.path} key={card.key} className={styles.cardLink}>
              <Card glow className={styles.summaryCard}>
                <div className={styles.cardHeader}>
                  <div className={styles.iconWrapper}>{card.icon}</div>
                  <div className={styles.countBadge}>
                    {loading ? <span className={styles.pulseIndicator}>...</span> : total}
                  </div>
                </div>
                
                <div className={styles.cardContent}>
                  <h3 className={styles.entityTitle}>{card.title}</h3>
                  <p className={styles.entityDescription}>{card.description}</p>
                </div>

                {/* Proportional status segment bar */}
                {card.hasBreakdown && (
                  <div className={styles.segmentBarContainer}>
                    {total > 0 ? (
                      <div className={styles.segmentBar}>
                        <div 
                          className={`${styles.segmentSlice} ${styles.sliceActive}`} 
                          style={{ width: `${activePct}%` }}
                          title={`Active: ${active}`}
                        />
                        <div 
                          className={`${styles.segmentSlice} ${styles.sliceDraft}`} 
                          style={{ width: `${draftPct}%` }}
                          title={`Draft: ${draft}`}
                        />
                        <div 
                          className={`${styles.segmentSlice} ${styles.sliceInactive}`} 
                          style={{ width: `${inactivePct}%` }}
                          title={`Inactive: ${inactive}`}
                        />
                        <div 
                          className={`${styles.segmentSlice} ${styles.sliceRetired}`} 
                          style={{ width: `${retiredPct}%` }}
                          title={`Retired/Archived: ${retired}`}
                        />
                      </div>
                    ) : (
                      <div className={`${styles.segmentBar} ${styles.emptyBar}`} />
                    )}

                    <div className={styles.segmentLabels}>
                      <span className={styles.labelItem}><span className={`${styles.dot} ${styles.dotActive}`}>●</span> {active} A</span>
                      <span className={styles.labelItem}><span className={`${styles.dot} ${styles.dotDraft}`}>●</span> {draft} D</span>
                      <span className={styles.labelItem}><span className={`${styles.dot} ${styles.dotInactive}`}>●</span> {inactive} I</span>
                      <span className={styles.labelItem}><span className={`${styles.dot} ${styles.dotRetired}`}>●</span> {retired} R</span>
                    </div>
                  </div>
                )}

                <div className={styles.cardFooter}>
                  <span>Explore Registry</span>
                  <span className={styles.arrow}>→</span>
                </div>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Analytics Charts Grid */}
      <div className={styles.chartsGrid}>
        {/* Chart 1: AI Model Types */}
        <div className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Model Distribution</h3>
          <div className={styles.chartContainer}>
            {loading ? (
              <div className={styles.recentLoading}>Loading data...</div>
            ) : modelTypesData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Tooltip />
                  <Pie
                    data={modelTypesData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                    nameKey="name"
                    stroke="none"
                  >
                    {modelTypesData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="No models" description="No models registered yet." />
            )}
          </div>
        </div>

        {/* Chart 2: AI Agents by Risk */}
        <div className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Agents by Risk Level</h3>
          <div className={styles.chartContainer}>
            {loading ? (
              <div className={styles.recentLoading}>Loading data...</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agentRiskData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                  <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {agentRiskData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Chart 3: Tools by Category */}
        <div className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Tools by Category</h3>
          <div className={styles.chartContainer}>
            {loading ? (
              <div className={styles.recentLoading}>Loading data...</div>
            ) : toolCategoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={toolCategoryData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                  <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.5)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                  <Bar dataKey="count" fill="#7B8CF7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="No tools" description="No tools categorized yet." />
            )}
          </div>
        </div>
      </div>

      {/* Task A: Recently Updated section */}
      <div className={styles.recentSection}>
        <h2 className={styles.recentTitle}>Recently Modified Assets</h2>
        <Card className={styles.recentCardContainer}>
          {loadingRecent ? (
            <div className={styles.recentLoading}>Loading lifecycle logs...</div>
          ) : recentUpdates.length > 0 ? (
            <div className={styles.recentList}>
              {recentUpdates.map((item) => (
                <Link
                  key={item.id}
                  to={item.type === "MODEL" ? `/registry/models?search=${encodeURIComponent(item.code)}` : `/registry/agents?search=${encodeURIComponent(item.code)}`}
                  className={item.type === "MODEL" ? styles.recentRowModel : styles.recentRowAgent}
                >
                  <div className={styles.recentRowInfo}>
                    <span className={`${styles.recentBadge} ${item.type === "MODEL" ? styles.recentModel : styles.recentAgent}`}>
                      {item.type}
                    </span>
                    <span className={styles.recentName}>{item.name}</span>
                    <span className={styles.recentCode}>({item.code})</span>
                  </div>
                  <div className={styles.recentRowTime}>
                    <Clock size={12} className={styles.timeIcon} />
                    <span>{timeAgo(item.updated_at)}</span>
                    <ArrowRight size={14} className={styles.rowArrow} />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No recent updates found"
              description="Governance logs and life-cycle modifications will print here as registrations complete."
              icon="⚡"
            />
          )}
        </Card>
      </div>
    </div>
  );
};

export default RegistryDashboardPage;
