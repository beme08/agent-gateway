"use client";

import { createClient } from "./supabase/browser";

export type SupportTicket = {
  id: string;
  ticket_ref: string;
  title: string;
  body: string;
  severity: string;
  category: string;
  status: string;
  reporter_email: string | null;
  affected_service: string | null;
  created_at: string;
};

export type TicketEvent = {
  id: string;
  event_type: string;
  actor: string;
  detail: Record<string, unknown>;
  trace_id: string | null;
  created_at: string;
};

export type ChatReply = {
  answer: string;
  trace_id: string | null;
  tool_calls: { tool: string; status: string; data?: any; reason?: string; approval_id?: string }[];
  blocked: boolean;
  block_reason: string | null;
};

async function api() {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("not signed in");
  const tenantId = sessionStorage.getItem("active_tenant_id") || "";
  const apiUrl = process.env.NEXT_PUBLIC_AGENT_API_URL || process.env.AGENT_API_URL || "http://localhost:8000";
  return { token: session.access_token, tenantId, apiUrl };
}

export async function runTicketPipeline(ticketId: string): Promise<ChatReply> {
  const c = await api();
  const res = await fetch(`${c.apiUrl}/v1/support/tickets/${ticketId}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${c.token}`,
      "X-Tenant-Id": c.tenantId,
    },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(`agent error: ${res.status} ${await res.text()}`);
  return res.json();
}
