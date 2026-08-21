"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "./supabase/server";

async function requireApiCaller(minRole?: "manager" | "admin") {
  const supabase = await createClient();
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("not signed in");
  const { data: m } = await supabase
    .from("tenant_memberships")
    .select("tenant_id, role")
    .eq("user_id", session.user.id)
    .limit(1);
  const membership = (m || [])[0];
  if (!membership) throw new Error("no tenant membership");
  if (minRole && membership.role !== minRole && membership.role !== "admin" && !(minRole === "manager" && membership.role === "admin")) {
    throw new Error(`${minRole} role required`);
  }
  const apiUrl = process.env.NEXT_PUBLIC_AGENT_API_URL || process.env.AGENT_API_URL || "http://localhost:8000";
  return {
    token: session.access_token,
    tenantId: membership.tenant_id as string,
    apiUrl,
  };
}

export type ApprovalDecision = {
  approval_id: string;
  status: string;
  reason?: string;
  result?: unknown;
};

export async function approveSupportAction(approvalId: string, note?: string): Promise<ApprovalDecision> {
  const c = await requireApiCaller("manager");
  const res = await fetch(`${c.apiUrl}/v1/approvals/${approvalId}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${c.token}`,
      "X-Tenant-Id": c.tenantId,
    },
    body: JSON.stringify({ note: note ?? null }),
  });
  if (!res.ok) throw new Error(await res.text());
  revalidatePath("/support/approvals");
  return res.json();
}

export async function rejectSupportAction(approvalId: string, note?: string): Promise<ApprovalDecision> {
  const c = await requireApiCaller("manager");
  const res = await fetch(`${c.apiUrl}/v1/approvals/${approvalId}/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${c.token}`,
      "X-Tenant-Id": c.tenantId,
    },
    body: JSON.stringify({ note: note ?? null }),
  });
  if (!res.ok) throw new Error(await res.text());
  revalidatePath("/support/approvals");
  return res.json();
}
