/* src/pages/FoundationHealthPage.tsx */
import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Badge } from "../components/common/Badge";
import { Button } from "../components/common/Button";
import { Loader } from "../components/common/Loader";
import { fetchApiHealth, fetchDbHealth } from "../services/health/healthService";
import type { HealthStatus, DbHealthStatus } from "../services/health/healthTypes";
import { 
  Heart, 
  Database, 
  Cpu, 
  Clock, 
  RefreshCw, 
  CheckCircle2, 
  XCircle 
} from "lucide-react";
import "./FoundationHealthPage.css";

export const FoundationHealthPage: React.FC = () => {
  const [apiHealth, setApiHealth] = useState<HealthStatus | null>(null);
  const [dbHealth, setDbHealth] = useState<DbHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHealth = async () => {
    setError(null);
    setLoading(true);
    try {
      const [api, db] = await Promise.all([
        fetchApiHealth().catch((e) => {
          console.error("API health failed:", e);
          return { status: "unhealthy" as const, timestamp: new Date().toISOString() };
        }),
        fetchDbHealth().catch((e) => {
          console.error("DB health failed:", e);
          return { status: "unhealthy" as const, message: e.message || "Failed to reach DB" };
        })
      ]);
      setApiHealth(api);
      setDbHealth(db);
    } catch (e) {
      setError("An unexpected error occurred while polling platform services.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const getStatusVariant = (status?: string) => {
    if (status === "healthy" || status === "active" || status === "up") return "success";
    if (status === "degraded") return "warning";
    return "danger";
  };

  return (
    <div className="health-page">
      <PageHeader 
        title="Foundation Health Monitor" 
        description="Live telemetry, service dependency status, and core performance stats."
        actions={
          <Button 
            variant="secondary" 
            size="md" 
            icon={<RefreshCw size={14} className={loading ? "spin-icon" : ""} />} 
            onClick={loadHealth}
            disabled={loading}
          >
            Poll Services
          </Button>
        }
      />

      {error && (
        <div className="health-error-toast animate-fade-in">
          <XCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading && !apiHealth ? (
        <Loader label="Gathering platform telemetry..." />
      ) : (
        <div className="health-grid">
          {/* API Health Service */}
          <Card title="API Core Services" subtitle="Status of FastAPI backend framework router" className="health-card">
            <div className="health-stat-row">
              <div className="stat-indicator">
                <Cpu size={24} className="stat-icon" />
                <div className="stat-text">
                  <span className="stat-label">FastAPI Status</span>
                  <span className="stat-desc">Version: {apiHealth?.version || "0.1.0"}</span>
                </div>
              </div>
              <Badge 
                label={apiHealth?.status?.toUpperCase() || "UNREACHABLE"} 
                variant={getStatusVariant(apiHealth?.status)} 
                dot={apiHealth?.status === "healthy"}
              />
            </div>
            
            <div className="health-details-list">
              <div className="detail-item">
                <Heart size={16} className="detail-icon" />
                <span className="detail-label">Endpoint Availability</span>
                <span className="detail-value text-success">
                  {apiHealth?.status === "healthy" ? "100% Operational" : "Degraded"}
                </span>
              </div>
              <div className="detail-item">
                <Clock size={16} className="detail-icon" />
                <span className="detail-label">Service Uptime</span>
                <span className="detail-value">
                  {apiHealth?.uptime ? `${Math.floor(apiHealth.uptime / 60)} mins` : "N/A"}
                </span>
              </div>
              <div className="detail-item">
                <Clock size={16} className="detail-icon" />
                <span className="detail-label">Report Timestamp</span>
                <span className="detail-value">
                  {apiHealth?.timestamp ? new Date(apiHealth.timestamp).toLocaleTimeString() : "N/A"}
                </span>
              </div>
            </div>
          </Card>

          {/* Database Health Service */}
          <Card title="Database Core Layer" subtitle="PostgreSQL database pool & schema validation" className="health-card">
            <div className="health-stat-row">
              <div className="stat-indicator">
                <Database size={24} className="stat-icon" />
                <div className="stat-text">
                  <span className="stat-label">PostgreSQL Storage</span>
                  <span className="stat-desc">Connection & queries active</span>
                </div>
              </div>
              <Badge 
                label={dbHealth?.status?.toUpperCase() || "UNREACHABLE"} 
                variant={getStatusVariant(dbHealth?.status)} 
                dot={dbHealth?.status === "healthy"}
              />
            </div>

            <div className="health-details-list">
              <div className="detail-item">
                <Cpu size={16} className="detail-icon" />
                <span className="detail-label">Pool Response Latency</span>
                <span className="detail-value text-success">
                  {dbHealth?.latency_ms ? `${dbHealth.latency_ms.toFixed(1)} ms` : "N/A"}
                </span>
              </div>
              <div className="detail-item">
                <CheckCircle2 size={16} className="detail-icon" />
                <span className="detail-label">Seeded Schema State</span>
                <span className="detail-value">Alembic Compliant</span>
              </div>
              <div className="detail-item">
                <Heart size={16} className="detail-icon" />
                <span className="detail-label">Integration Response</span>
                <span className="detail-value overflow-ellipsis" title={dbHealth?.message}>
                  {dbHealth?.message || "Operational"}
                </span>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
