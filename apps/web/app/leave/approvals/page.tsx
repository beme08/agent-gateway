import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";
import { approveLeaveRequest, rejectLeaveRequest } from "@/lib/leave-actions";

export default async function ApprovalsPage() {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];
  if (m.role !== "manager" && m.role !== "admin") redirect("/dashboard");

  const supabase = createClient();
  const { data: pending } = await supabase
    .from("leave_requests")
    .select("id, user_id, leave_type, start_date, end_date, total_days, reason, status, created_at, users:user_id (email, full_name)")
    .eq("tenant_id", m.tenant_id)
    .eq("status", "pending")
    .order("created_at", { ascending: true });

  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Approvals</h1>
        <a href="/dashboard" className="btn-ghost">← Dashboard</a>
      </header>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="text-left p-2">Employee</th>
              <th className="text-left p-2">Type</th>
              <th className="text-left p-2">Dates</th>
              <th className="text-left p-2">Days</th>
              <th className="text-left p-2">Reason</th>
              <th className="p-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(pending || []).map((r: any) => (
              <tr key={r.id} className="border-t border-slate-200 align-top">
                <td className="p-2">
                  <div className="font-medium">{r.users?.full_name || r.users?.email}</div>
                  <div className="text-xs text-slate-500">{r.users?.email}</div>
                </td>
                <td className="p-2">{r.leave_type}</td>
                <td className="p-2">{r.start_date} → {r.end_date}</td>
                <td className="p-2">{r.total_days}</td>
                <td className="p-2 text-slate-600">{r.reason || "—"}</td>
                <td className="p-2 text-right">
                  <div className="flex flex-col gap-2 items-end">
                    <form action={async () => { "use server"; await approveLeaveRequest(r.id); }}>
                      <button className="btn-primary text-xs">Approve</button>
                    </form>
                    <form
                      action={async (fd: FormData) => {
                        "use server";
                        await rejectLeaveRequest(r.id, String(fd.get("reason")));
                      }}
                      className="flex gap-1 items-end"
                    >
                      <input name="reason" placeholder="rejection reason" required className="input text-xs w-40" />
                      <button className="btn-secondary text-xs">Reject</button>
                    </form>
                  </div>
                </td>
              </tr>
            ))}
            {(!pending || pending.length === 0) && (
              <tr><td colSpan={6} className="p-4 text-center text-slate-500">No pending requests. 🎉</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
