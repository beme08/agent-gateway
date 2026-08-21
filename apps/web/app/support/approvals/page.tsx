import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";
import { approveSupportAction, rejectSupportAction } from "@/lib/support-actions";

export const dynamic = "force-dynamic";

export default async function SupportApprovalsPage() {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];
  if (m.role !== "manager" && m.role !== "admin") redirect("/support");

  const supabase = await createClient();
  const { data: pending } = await supabase
    .from("action_approvals")
    .select("*")
    .eq("tenant_id", m.tenant_id)
    .eq("status", "pending")
    .order("created_at", { ascending: true });

  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Agent action approvals</h1>
          <p className="text-sm text-slate-600">
            Approval-required actions proposed by the agent. Approving re-runs the full policy
            check with the original requester&apos;s context — approval never bypasses policy.
          </p>
        </div>
        <Link href="/support" className="btn-ghost">← Tickets</Link>
      </header>

      <div className="space-y-4">
        {(pending || []).map((a: any) => (
          <div key={a.id} className="card p-4">
            <div className="flex items-center gap-2 mb-2">
              <code className="kbd">{a.tool_name}</code>
              <span className="px-2 py-0.5 rounded text-xs bg-purple-100 text-purple-700">
                {a.risk_tier}
              </span>
              <span className="text-xs text-slate-500 font-mono">{a.id.slice(0, 8)}…</span>
            </div>
            <p className="text-sm text-slate-600 mb-2">{a.reason}</p>
            <pre className="text-xs bg-slate-50 rounded p-2 overflow-x-auto mb-3">
              {JSON.stringify(a.arguments, null, 2)}
            </pre>
            <div className="flex flex-wrap gap-2 items-end">
              <form action={async () => { "use server"; await approveSupportAction(a.id); }}>
                <button className="btn-primary text-xs">Approve &amp; execute</button>
              </form>
              <form
                action={async (fd: FormData) => {
                  "use server";
                  await rejectSupportAction(a.id, String(fd.get("note") || ""));
                }}
                className="flex gap-1 items-end"
              >
                <input name="note" placeholder="rejection note" className="input text-xs w-44" />
                <button className="btn-secondary text-xs">Reject</button>
              </form>
              {a.trace_id && (
                <span className="text-xs text-slate-400 ml-auto font-mono">trace {a.trace_id.slice(0, 8)}…</span>
              )}
            </div>
          </div>
        ))}
        {(!pending || pending.length === 0) && (
          <div className="card p-6 text-center text-slate-500 text-sm">
            No pending agent actions. 🎉
          </div>
        )}
      </div>
    </main>
  );
}
