export function BalanceCard({
  leaveType, allocated, used, pending, remaining,
}: { leaveType: string; allocated: number; used: number; pending: number; remaining: number }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{leaveType}</div>
      <div className="mt-2 grid grid-cols-4 gap-2 text-sm">
        <Stat label="Allocated" value={allocated} />
        <Stat label="Used"      value={used} />
        <Stat label="Pending"   value={pending} />
        <Stat label="Remaining" value={remaining} highlight={remaining < 2} />
      </div>
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div>
      <div className="text-[10px] text-slate-500">{label}</div>
      <div className={`text-lg font-semibold ${highlight ? "text-rose-600" : ""}`}>{value}</div>
    </div>
  );
}
