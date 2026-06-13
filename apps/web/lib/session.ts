import { createClient } from "./supabase/server";

export type SessionInfo = {
  user: { id: string; email: string | null };
  memberships: { tenant_id: string; tenant_name: string; tenant_slug: string; role: string; manager_user_id: string | null }[];
  activeTenantId: string | null;
};

export async function getSession(): Promise<SessionInfo | null> {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return null;

  const { data: rows } = await supabase
    .from("tenant_memberships")
    .select("tenant_id, role, manager_user_id, tenants:tenant_id (name, slug)")
    .eq("user_id", user.id);
  const memberships = (rows || []).map((r: any) => ({
    tenant_id: r.tenant_id,
    tenant_name: r.tenants?.name ?? "",
    tenant_slug: r.tenants?.slug ?? "",
    role: r.role,
    manager_user_id: r.manager_user_id,
  }));
  const activeTenantId = memberships[0]?.tenant_id ?? null;
  return {
    user: { id: user.id, email: user.email ?? null },
    memberships,
    activeTenantId,
  };
}

export async function getActiveMembership() {
  const session = await getSession();
  if (!session) return null;
  return session.memberships[0] ?? null;
}
