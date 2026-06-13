import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";
import { BalanceCard } from "@/components/balance-card";
import { createLeaveRequest, cancelLeaveRequest } from "@/lib/leave-actions";

export default async function LeavePage() {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];
  const supabase = createClient();

  const year = new Date().getUTCFullYear();
  const [{ data: balances }, { data: requests }] = await Promise.all([
    supabase
      .from("leave_balances")
      .select("leave_type, allocated_days, used_days, pending_days, remaining_days")
      .eq("tenant_id", m.tenant_id)
      .eq("user_id", session.user.id)
      .eq("year", year),
    supabase
      .from("leave_requests")
      .select("id, leave_type, start_date, end_date, total_days, status, reason, manager_note, created_at")
      .eq("tenant_id", m.tenant_id)
      .eq("user_id", session.user.id)
      .order("created_at", { ascending: false }),
  ]);

  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">My leave</h1>
        <a href="/dashboard" className="btn-ghost">← Dashboard</a>
      </header>

      <section className="grid sm:grid-cols-3 gap-3 mb-8">
        {(balances || []).map((b: any) => (
          <BalanceCard
            key={b.leave_type}
            leaveType={b.leave_type}
            allocated={b.allocated_days}
            used={b.used_days}
            pending={b.pending_days}
            remaining={b.remaining_days}
          />
        ))}
        {(!balances || balances.length === 0) && (
          <p className="text-sm text-slate-500 col-span-3">
            No balance configured for this year. Ask your admin to seed one.
          </p>
        )}
      </section>

      <section className="card p-5 mb-8">
        <h2 className="font-semibold mb-3">Request time off</h2>
        <form action={async (fd: FormData) => {
          "use server";
          await createLeaveRequest({
            leave_type: String(fd.get("leave_type")),
            start_date: String(fd.get("start_date")),
            end_date: String(fd.get("end_date")),
            reason: String(fd.get("reason") || "") || undefined,
          });
        }} className="grid sm:grid-cols-4 gap-3">
          <div>
            <label className="label">Type</label>
            <select name="leave_type" className="input" defaultValue="vacation">
              <option value="vacation">Vacation</option>
              <option value="sick">Sick</option>
              <option value="personal">Personal</option>
            </select>
          </div>
          <div>
            <label className="label">Start</label>
            <input name="start_date" type="date" required className="input" />
          </div>
          <div>
            <label className="label">End</label>
            <input name="end_date" type="date" required className="input" />
          </div>
          <div>
            <label className="label">Reason</label>
            <input name="reason" className="input" placeholder="optional" />
          </div>
          <div className="sm:col-span-4">
            <button className="btn-primary">Submit request</button>
          </div>
        </form>
      </section>

      <section>
        <h2 className="font-semibold mb-3">My requests</h2>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="text-left p-2">Type</th>
                <th className="text-left p-2">Dates</th>
                <th className="text-left p-2">Days</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Note</th>
                <th className="p-2"></th>
              </tr>
            </thead>
            <tbody>
              {(requests || []).map((r: any) => (
                <tr key={r.id} className="border-t border-slate-200">
                  <td className="p-2">{r.leave_type}</td>
                  <td className="p-2">{r.start_date} → {r.end_date}</td>
                  <td className="p-2">{r.total_days}</td>
                  <td className="p-2"><StatusBadge status={r.status} /></td>
                  <td className="p-2 text-slate-600">{r.manager_note || r.reason || "—"}</td>
                  <td className="p-2 text-right">
                    {r.status === "pending" && (
                      <form action={async () => { "use server"; await cancelLeaveRequest(r.id); }}>
                        <button className="btn-ghost text-xs">Cancel</button>
                      </form>
                    )}
                  </td>
                </tr>
              ))}
              {(!requests || requests.length === 0) && (
                <tr><td colSpan={6} className="p-4 text-center text-slate-500">No requests yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-amber-100 text-amber-800",
    approved: "bg-emerald-100 text-emerald-800",
    rejected: "bg-rose-100 text-rose-800",
    cancelled: "bg-slate-100 text-slate-700",
  };
  return <span className={`inline-block rounded px-2 py-0.5 text-xs ${colors[status] || "bg-slate-100"}`}>{status}</span>;
}
