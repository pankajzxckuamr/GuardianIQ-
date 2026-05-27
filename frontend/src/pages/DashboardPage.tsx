/* src/pages/DashboardPage.tsx */
import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Badge } from "../components/common/Badge";
import { Table } from "../components/common/Table";
import { useAuth } from "../hooks/useAuth";
import { 
  ShieldCheck, 
  Users, 
  Activity, 
  FileText,
  Lock,
  Globe
} from "lucide-react";
import "./DashboardPage.css";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description: string;
  glow?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, description, glow = false }) => {
  return (
    <Card className="metric-card" glow={glow}>
      <div className="metric-card-inner">
        <div className="metric-card-details">
          <span className="metric-card-title">{title}</span>
          <span className="metric-card-value">{value}</span>
          <span className="metric-card-desc">{description}</span>
        </div>
        <div className="metric-card-icon-wrap">
          {icon}
        </div>
      </div>
    </Card>
  );
};

export const DashboardPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading local UI elements
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  const recentSessions = [
    { id: "1", user: "administrator", ip: "192.168.1.50", device: "macOS - Chrome", status: "Active", time: "Just now" },
    { id: "2", user: currentUser?.name || currentUser?.username || currentUser?.email || "current_user", ip: "10.0.0.12", device: "Windows - Edge", status: "Active", time: "2 mins ago" },
    { id: "3", user: "security_auditor", ip: "172.16.25.4", device: "Linux - Firefox", status: "Terminated", time: "1 hour ago" },
  ];

  const columns = [
    { key: "user", header: "Identity" },
    { key: "ip", header: "IP Address" },
    { key: "device", header: "Device Signature" },
    { 
      key: "status", 
      header: "Status",
      render: (row: typeof recentSessions[0]) => (
        <Badge 
          label={row.status} 
          variant={row.status === "Active" ? "success" : "neutral"} 
          dot={row.status === "Active"}
        />
      )
    },
    { key: "time", header: "Last Active" },
  ];

  return (
    <div className="dashboard-page">
      <PageHeader 
        title="Security Cockpit" 
        description={`Welcome back, ${currentUser?.full_name || currentUser?.name || currentUser?.username || currentUser?.email}. Contextual RBAC is fully active.`} 
      />

      <div className="dashboard-grid">
        <MetricCard 
          title="Security Posture"
          value="COMPLIANT"
          icon={<ShieldCheck size={24} className="metric-icon success" />}
          description="Decryption & fingerprinting green"
          glow
        />

        <MetricCard 
          title="Active Tenants"
          value="1"
          icon={<Users size={24} className="metric-icon info" />}
          description="Default Platform Tenant active"
        />

        <MetricCard 
          title="System Health"
          value="99.9%"
          icon={<Activity size={24} className="metric-icon success" />}
          description="Database latency: 2.1 ms"
        />

        <MetricCard 
          title="Audit Trail"
          value="SECURE"
          icon={<FileText size={24} className="metric-icon warning" />}
          description="All event digests verified"
        />
      </div>

      <div className="dashboard-sections">
        <div className="dashboard-section-main">
          <Card title="Current Session Context" subtitle="Active identities and verified fingerprints on this domain">
            <Table 
              columns={columns} 
              data={recentSessions} 
              loading={loading} 
            />
          </Card>
        </div>

        <aside className="dashboard-section-sidebar">
          <Card title="Platform Controls" subtitle="Quick capabilities">
            <div className="controls-list">
              <div className="control-item">
                <Globe size={18} className="control-icon" />
                <div className="control-text">
                  <span className="control-title">Federated Domains</span>
                  <span className="control-desc">Configure active single sign-on</span>
                </div>
              </div>
              <div className="control-item">
                <Lock size={18} className="control-icon" />
                <div className="control-text">
                  <span className="control-title">Rotated Keys</span>
                  <span className="control-desc">AES-256 tokens update hourly</span>
                </div>
              </div>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
};
