"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "./session";
import { serviceClient } from "./supabase/server";

async function requireCaller() {
  const s = await getSession();
  if (!s) throw new Error("not signed in");
  const m = s.memberships[0];
  if (!m) throw new Error("no tenant membership");
  return { userId: s.user.id, email: s.user.email, tenantId: m.tenant_id, role: m.role };
}

export async function createLeaveRequest(form: {
  leave_type: string;
  start_date: string;
  end_date: string;
  reason?: string;
}) {
  const c = await requireCaller();
  const supabase = serviceClient();
  const { data, error } = await supabase.rpc("create_leave_request", {
    p_tenant_id: c.tenantId,
    p_user_id: c.userId,
    p_leave_type: form.leave_type,
    p_start_date: form.start_date,
    p_end_date: form.end_date,
    p_reason: form.reason ?? null,
  });
  if (error) throw new Error(error.message);
  revalidatePath("/leave");
  revalidatePath("/leave/approvals");
  return data;
}

export async function cancelLeaveRequest(requestId: string) {
  const c = await requireCaller();
  const supabase = serviceClient();
  const { error } = await supabase.rpc("cancel_leave_request", {
    p_request_id: requestId,
    p_user_id: c.userId,
  });
  if (error) throw new Error(error.message);
  revalidatePath("/leave");
}

export async function approveLeaveRequest(requestId: string, note?: string) {
  const c = await requireCaller();
  if (c.role !== "manager" && c.role !== "admin") throw new Error("not authorized");
  const supabase = serviceClient();
  const { error } = await supabase.rpc("approve_leave_request", {
    p_request_id: requestId,
    p_manager_user_id: c.userId,
    p_note: note ?? null,
  });
  if (error) throw new Error(error.message);
  revalidatePath("/leave");
  revalidatePath("/leave/approvals");
}

export async function rejectLeaveRequest(requestId: string, reason: string) {
  const c = await requireCaller();
  if (c.role !== "manager" && c.role !== "admin") throw new Error("not authorized");
  if (!reason || !reason.trim()) throw new Error("rejection reason is required");
  const supabase = serviceClient();
  const { error } = await supabase.rpc("reject_leave_request", {
    p_request_id: requestId,
    p_manager_user_id: c.userId,
    p_reason: reason,
  });
  if (error) throw new Error(error.message);
  revalidatePath("/leave");
  revalidatePath("/leave/approvals");
}

export async function resetDemo() {
  const c = await requireCaller();
  if (c.role !== "admin") throw new Error("not authorized");
  const supabase = serviceClient();
  const { error } = await supabase.rpc("reset_demo_tenant", { p_tenant_id: c.tenantId });
  if (error) throw new Error(error.message);
  revalidatePath("/audit");
}
