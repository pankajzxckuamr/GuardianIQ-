/* src/pages/TenantsPage.tsx */
import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Badge } from "../components/common/Badge";
import { Table } from "../components/common/Table";
import { Button } from "../components/common/Button";
import { FormField } from "../components/common/FormField";
import { fetchTenants, createTenant } from "../services/tenants/tenantService";
import type { TenantRecord } from "../services/tenants/tenantTypes";
import { formatDate } from "../utils/dates";
import { Plus, Users, RefreshCw } from "lucide-react";

export const TenantsPage: React.FC = () => {
  const [tenants, setTenants] = useState<TenantRecord[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Create Modal state
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mockTenants: TenantRecord[] = [
    {
      id: "ten_default",
      name: "Default Platform Tenant",
      slug: "default",
      is_active: true,
      created_at: new Date().toISOString(),
    }
  ];

  const loadTenants = async () => {
    setLoading(true);
    try {
      const token = JSON.parse(localStorage.getItem("guardianiq_access_token") || "null");
      if (token) {
        const response = await fetchTenants(token, 1, 20);
        setTenants(response.items || []);
      } else {
        setTenants(mockTenants);
      }
    } catch (e) {
      console.warn("Using local fallback tenants data:", e);
      setTenants(mockTenants);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTenants();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !slug) {
      setError("Please fill in all fields.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const token = JSON.parse(localStorage.getItem("guardianiq_access_token") || "null");
      if (token) {
        const newRecord = await createTenant(token, { name, slug });
        setTenants((prev) => [...prev, newRecord]);
        setName("");
        setSlug("");
        setShowForm(false);
      } else {
        // Fallback simulate create
        const newRecord: TenantRecord = {
          id: `ten_${Date.now()}`,
          name,
          slug,
          is_active: true,
          created_at: new Date().toISOString()
        };
        setTenants((prev) => [...prev, newRecord]);
        setName("");
        setSlug("");
        setShowForm(false);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to register tenant.");
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    { key: "name", header: "Tenant Identity", render: (row: TenantRecord) => (
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: "bold" }}>
        <Users size={16} style={{ color: "var(--accent-primary)" }} />
        <span>{row.name}</span>
      </div>
    )},
    { 
      key: "slug", 
      header: "Domain Slug", 
      render: (row: TenantRecord) => (
        <span style={{ fontFamily: "monospace", color: "var(--accent-secondary)" }}>{row.slug}</span>
      ) 
    },
    { key: "created_at", header: "Provisioned On", render: (row: TenantRecord) => formatDate(row.created_at) },
    { 
      key: "is_active", 
      header: "Status",
      render: (row: TenantRecord) => (
        <Badge 
          label={row.is_active ? "ACTIVE" : "SUSPENDED"} 
          variant={row.is_active ? "success" : "neutral"} 
          dot={row.is_active}
        />
      )
    },
  ];

  return (
    <div className="tenants-page">
      <PageHeader 
        title="Federated Tenants" 
        description="Configure isolated tenant spaces, domain routes, and enterprise isolation boundaries."
        actions={
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button 
              variant="secondary" 
              size="md" 
              icon={<RefreshCw size={14} className={loading ? "spin-icon" : ""} />} 
              onClick={loadTenants}
              disabled={loading}
            >
              Sync
            </Button>
            <Button 
              variant="primary" 
              size="md" 
              icon={<Plus size={14} />} 
              onClick={() => setShowForm(!showForm)}
            >
              Register Tenant
            </Button>
          </div>
        }
      />

      {showForm && (
        <div style={{ marginBottom: "var(--spacing-lg)" }} className="animate-fade-in">
          <Card title="Register New Federated Tenant" subtitle="Boundaries will automatically establish isolation rules.">
            <form onSubmit={handleCreate} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {error && (
                <div style={{ padding: "var(--spacing-sm) var(--spacing-md)", border: "1px solid rgba(239, 68, 68, 0.25)", background: "rgba(239, 68, 68, 0.1)", color: "var(--color-danger)", borderRadius: "var(--radius-sm)", fontSize: "var(--font-size-sm)" }}>
                  {error}
                </div>
              )}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <FormField 
                  label="Tenant Name" 
                  placeholder="e.g. Acme Corp" 
                  value={name} 
                  onChange={(e) => setName(e.target.value)}
                  disabled={submitting}
                  required
                />
                <FormField 
                  label="Domain Slug" 
                  placeholder="e.g. acme" 
                  value={slug} 
                  onChange={(e) => setSlug(e.target.value)}
                  disabled={submitting}
                  required
                />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
                <Button type="button" variant="ghost" onClick={() => setShowForm(false)} disabled={submitting}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" loading={submitting}>
                  Provision Space
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      <Card title="Registered Spaces" subtitle="Logical isolation namespaces mapping physical databases.">
        <Table 
          columns={columns} 
          data={tenants} 
          loading={loading} 
        />
      </Card>
    </div>
  );
};
