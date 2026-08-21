import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";
import RunTicketButton from "./RunTicketButton";

export const dynamic = "force-dynamic";

const ACTOR_STYLE: Record<string, string> = {
  agent: "bg-blue-100 text-blue-700",
  human: "bg-green-100 text-green-700",
  system: "bg-slate-100 text-slate-600",
};

export default async function TicketDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];

  const supabase = await createClient();
  const { data: ticket } = await supabase
    .from("support_tickets")
    .select("*")
    .eq("tenant_id", m.tenant_id)
    .eq("id", id)
    .single();
  if (!ticket) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-10">
        <p>Ticket not found.</p>
        <Link href="/support" className="btn-ghost mt-4 inline-block">← Back</Link>
      </main>
    );
  }

  const { data: events } = await supabase
    .from("ticket_events")
    .select("*")
    .eq("ticket_id", id)
    .order("created_at", { ascending: true });

  const { data: approvals } = await supabase
    .from("action_approvals")
    .select("*")
    .eq("tenant_id", m.tenant_id)
    .contains("context", { ticket_id: id })
    .order("created_at", { ascending: false });

  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-6">
        <div>
          <p className="text-xs font-mono text-slate-500">{ticket.ticket_ref}</p>
          <h1 className="text-2xl font-semibold">{ticket.title}</h1>
          <p className="text-sm text-slate-600 mt-1">
            <span className="px-2 py-0.5 rounded bg-slate-100 text-xs mr-2">{ticket.severity}</span>
            <span className="px-2 py-0.5 rounded bg-slate-100 text-xs mr-2">{ticket.status}</span>
            <span className="text-slate-500">{ticket.affected_service || "no service"}</span>
          </p>
        </div>
        <Link href="/support" className="btn-ghost">← Tickets</Link>
      </header>

      <section className="card p-4 mb-6">
        <h2 className="font-semibold mb-2">Ticket body</h2>
        <p className="text-sm text-slate-700 whitespace-pre-wrap">{ticket.body}</p>
      </section>

      <section className="mb-6">
        <h2 className="font-semibold mb-2">Agent run</h2>
        <p className="text-sm text-slate-600 mb-1">
          Runs triage → retrieval → diagnosis → policy/risk branch → remediation or approval → verification.
          Every step is authorized by the gateway and recorded on the trace.
        </p>
        <RunTicketButton ticketId={ticket.id} />
      </section>

      {(approvals || []).length > 0 && (
        <section className="card p-4 mb-6">
          <h2 className="font-semibold mb-2">Approval requests</h2>
          <ul className="text-sm space-y-2">
            {(approvals || []).map((a: any) => (
              <li key={a.id} className="flex items-center gap-2">
                <code className="kbd">{a.tool_name}</code>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  a.status === "pending" ? "bg-purple-100 text-purple-700" :
                  a.status === "executed" ? "bg-green-100 text-green-700" :
                  "bg-red-100 text-red-700"}`}>{a.status}</span>
                <span className="text-slate-500">{a.reason}</span>
                {a.status === "pending" && (m.role === "manager" || m.role === "admin") && (
                  <Link href="/support/approvals" className="text-accent text-xs hover:underline">review →</Link>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card p-4">
        <h2 className="font-semibold mb-2">Timeline</h2>
        <ul className="text-sm space-y-3">
          {(events || []).map((e: any) => (
            <li key={e.id} className="border-l-2 border-slate-200 pl-3">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-xs ${ACTOR_STYLE[e.actor] || "bg-slate-100"}`}>
                  {e.actor}
                </span>
                <span className="font-mono text-xs text-slate-500">{e.event_type}</span>
              </div>
              <pre className="text-xs text-slate-600 mt-1 whitespace-pre-wrap overflow-x-auto">
                {JSON.stringify(e.detail, null, 2)}
              </pre>
            </li>
          ))}
          {(!events || events.length === 0) && (
            <li className="text-slate-500">No events yet — run the agent to generate the decision chain.</li>
          )}
        </ul>
      </section>
    </main>
  );
}
