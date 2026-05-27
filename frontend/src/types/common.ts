/* src/types/common.ts */

export type StatusVariant = "success" | "warning" | "danger" | "info" | "neutral";

export interface NavItem {
  label: string;
  path: string;
  icon: string;
  requiredRoles?: string[];
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
}
