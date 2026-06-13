"use client";

import { createClient } from "./supabase/browser";

export type ChatReply = {
  answer: string;
  trace_id: string | null;
  tool_calls: { tool: string; status: string; data?: any; latency_ms?: number; reason?: string }[];
  blocked: boolean;
  block_reason: string | null;
};

export async function sendChat(message: string, sessionId: string | null, agentId: string | null): Promise<ChatReply> {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("not signed in");
  const tenantId = sessionStorage.getItem("active_tenant_id") || "";

  const apiUrl = process.env.NEXT_PUBLIC_AGENT_API_URL || process.env.AGENT_API_URL || "http://localhost:8000";
  const res = await fetch(`${apiUrl}/v1/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.access_token}`,
      "X-Tenant-Id": tenantId,
    },
    body: JSON.stringify({ message, session_id: sessionId, agent_id: agentId }),
  });
  if (!res.ok) {
    throw new Error(`agent error: ${res.status} ${await res.text()}`);
  }
  return res.json();
}
