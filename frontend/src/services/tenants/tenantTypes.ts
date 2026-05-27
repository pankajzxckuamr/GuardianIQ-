/* src/services/tenants/tenantTypes.ts */

export interface TenantRecord {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  owner_id?: string;
  plan?: string;
}

export interface CreateTenantPayload {
  name: string;
  slug: string;
}
