import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-slate-100 text-slate-600",
};

const STATUS_STYLES: Record<string, string> = {
  open: "bg-slate-100 text-slate-700",
  resolved: "bg-green-100 text-green-700",
  blocked: "bg-red-100 text-red-700",
  pending_approval: "bg-purple-100 text-purple-700",
};

export default async function SupportTicketsPage() {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];

  const supabase = await createClient();
  const { data: tickets } = await supabase
    .from("support_tickets")
    .select("*")
    .eq("tenant_id", m.tenant_id)
    .order("created_at", { ascending: false });

  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Support Operations</h1>
          <p className="text-sm text-slate-600">
            Tickets handled by the Support Ops agent — triage, diagnosis, remediation, verification.
          </p>
        </div>
        <Link href="/dashboard" className="btn-ghost">← Dashboard</Link>
      </header>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="text-left p-2">Ref</th>
              <th className="text-left p-2">Title</th>
              <th className="text-left p-2">Severity</th>
              <th className="text-left p-2">Status</th>
              <th className="text-left p-2">Service</th>
            </tr>
          </thead>
          <tbody>
            {(tickets || []).map((t: any) => (
              <tr key={t.id} className="border-t border-slate-200 hover:bg-slate-50">
                <td className="p-2 font-mono text-xs">{t.ticket_ref}</td>
                <td className="p-2">
                  <Link href={`/support/${t.id}`} className="font-medium hover:underline">
                    {t.title}
                  </Link>
                </td>
                <td className="p-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${SEVERITY_STYLES[t.severity] || "bg-slate-100"}`}>
                    {t.severity}
                  </span>
                </td>
                <td className="p-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${STATUS_STYLES[t.status] || "bg-slate-100 text-slate-700"}`}>
                    {t.status}
                  </span>
                </td>
                <td className="p-2 text-slate-600">{t.affected_service || "—"}</td>
              </tr>
            ))}
            {(!tickets || tickets.length === 0) && (
              <tr><td colSpan={5} className="p-4 text-center text-slate-500">No support tickets yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {(m.role === "manager" || m.role === "admin") && (
        <p className="mt-4 text-sm">
          <Link href="/support/approvals" className="text-accent hover:underline">
            Review pending agent actions →
          </Link>
        </p>
      )}
    </main>
  );
}
