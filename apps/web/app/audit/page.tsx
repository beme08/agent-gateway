import { redirect } from "next/navigation";
import Link from "next/link";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";
import { resetDemo } from "@/lib/leave-actions";

export default async function AuditPage() {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];
  if (m.role !== "admin") redirect("/dashboard");
  const supabase = createClient();

  const [{ data: traces }, { data: toolCalls }, { data: events }, { data: tenant }] = await Promise.all([
    supabase
      .from("agent_traces")
      .select("id, user_id, user_message, final_status, latency_ms, retrieval_safety_status, input_safety_status, created_at, tool_loop_count")
      .eq("tenant_id", m.tenant_id)
      .order("created_at", { ascending: false })
      .limit(50),
    supabase
      .from("tool_calls")
      .select("id, tool_name, status, policy_decision, policy_reason, created_at, trace_id")
      .eq("tenant_id", m.tenant_id)
      .order("created_at", { ascending: false })
      .limit(50),
    supabase
      .from("security_events")
      .select("id, event_type, severity, details, created_at, user_id")
      .eq("tenant_id", m.tenant_id)
      .order("created_at", { ascending: false })
      .limit(50),
    supabase
      .from("tenants")
      .select("monthly_message_count, monthly_tool_call_count, document_count, storage_used_mb, max_messages_per_month, max_documents, max_storage_mb, plan, usage_period_start")
      .eq("id", m.tenant_id)
      .single(),
  ]);

  const counts = {
    chats: traces?.length ?? 0,
    tool_calls: toolCalls?.length ?? 0,
    denied: toolCalls?.filter((t: any) => t.status === "denied").length ?? 0,
    suspicious: events?.filter((e: any) => e.event_type === "suspicious_prompt" || e.event_type === "suspicious_chunk").length ?? 0,
  };

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Audit dashboard</h1>
        <div className="flex gap-2">
          <a href="/dashboard" className="btn-ghost">← Dashboard</a>
          <form action={async () => { "use server"; await resetDemo(); }}>
            <button className="btn-secondary text-xs">Reset demo data</button>
          </form>
        </div>
      </header>

      <section className="grid sm:grid-cols-4 gap-3 mb-8">
        <Stat label="Recent chats"   value={counts.chats} />
        <Stat label="Tool calls"     value={counts.tool_calls} />
        <Stat label="Denied calls"   value={counts.denied} danger={counts.denied > 0} />
        <Stat label="Suspicious events" value={counts.suspicious} danger={counts.suspicious > 0} />
      </section>

      {tenant && (
        <section className="card p-4 mb-8">
          <h2 className="font-semibold mb-2">Tenant usage</h2>
          <div className="grid sm:grid-cols-3 gap-3 text-sm">
            <Meter label="Messages / month" used={tenant.monthly_message_count} max={tenant.max_messages_per_month} />
            <Meter label="Tool calls / month" used={tenant.monthly_tool_call_count} max={tenant.max_messages_per_month} />
            <Meter label="Documents" used={tenant.document_count} max={tenant.max_documents} />
          </div>
          <p className="text-xs text-slate-500 mt-2">Plan: <code className="kbd">{tenant.plan}</code> · period start: {new Date(tenant.usage_period_start).toISOString().slice(0,10)}</p>
        </section>
      )}

      <section className="mb-8">
        <h2 className="font-semibold mb-2">Recent traces</h2>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="text-left p-2">When</th>
                <th className="text-left p-2">User message</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Loops</th>
                <th className="text-left p-2">Latency</th>
                <th className="p-2"></th>
              </tr>
            </thead>
            <tbody>
              {(traces || []).map((t: any) => (
                <tr key={t.id} className="border-t border-slate-200">
                  <td className="p-2 whitespace-nowrap text-slate-500">{new Date(t.created_at).toLocaleString()}</td>
                  <td className="p-2 max-w-md truncate">{t.user_message}</td>
                  <td className="p-2">
                    {t.input_safety_status !== "clean" && <span className="text-xs text-rose-600 mr-1">in:{t.input_safety_status}</span>}
                    {t.retrieval_safety_status !== "clean" && <span className="text-xs text-amber-600 mr-1">ret:{t.retrieval_safety_status}</span>}
                    {t.final_status}
                  </td>
                  <td className="p-2">{t.tool_loop_count}</td>
                  <td className="p-2">{t.latency_ms ?? "—"} ms</td>
                  <td className="p-2 text-right">
                    <Link href={`/audit/traces/${t.id}`} className="text-xs text-accent">view →</Link>
                  </td>
                </tr>
              ))}
              {(!traces || traces.length === 0) && (
                <tr><td colSpan={6} className="p-4 text-center text-slate-500">No traces yet — go chat with the agent.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <div>
          <h2 className="font-semibold mb-2">Tool calls</h2>
          <ul className="space-y-1 text-sm">
            {(toolCalls || []).map((t: any) => (
              <li key={t.id} className="card p-2">
                <div className="flex justify-between">
                  <span><code className="kbd">{t.tool_name}</code> · {t.status}</span>
                  <span className="text-xs text-slate-500">{new Date(t.created_at).toLocaleString()}</span>
                </div>
                {t.policy_reason && <div className="text-xs text-slate-500 mt-1">{t.policy_reason}</div>}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="font-semibold mb-2">Security events</h2>
          <ul className="space-y-1 text-sm">
            {(events || []).map((e: any) => (
              <li key={e.id} className="card p-2">
                <div className="flex justify-between">
                  <span><code className="kbd">{e.event_type}</code> · <span className="text-xs text-slate-500">{e.severity}</span></span>
                  <span className="text-xs text-slate-500">{new Date(e.created_at).toLocaleString()}</span>
                </div>
                {e.details && <pre className="text-xs text-slate-500 mt-1 whitespace-pre-wrap">{JSON.stringify(e.details, null, 2).slice(0, 240)}</pre>}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </main>
  );
}

function Stat({ label, value, danger }: { label: string; value: number; danger?: boolean }) {
  return (
    <div className="card p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-2xl font-semibold ${danger ? "text-rose-600" : ""}`}>{value}</div>
    </div>
  );
}

function Meter({ label, used, max }: { label: string; used: number; max: number }) {
  const pct = Math.min(100, Math.round((used / Math.max(1, max)) * 100));
  return (
    <div>
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className="h-2 bg-slate-100 rounded">
        <div className={`h-2 rounded ${pct > 80 ? "bg-rose-500" : "bg-accent"}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="text-xs text-slate-500 mt-1">{used} / {max}</div>
    </div>
  );
}
