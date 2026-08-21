"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { runTicketPipeline, type ChatReply } from "@/lib/support-client";

const STATUS_STYLE: Record<string, string> = {
  allowed: "text-green-700",
  denied: "text-red-700",
  error: "text-red-600",
  pending_approval: "text-purple-700",
};

export default function RunTicketButton({ ticketId }: { ticketId: string }) {
  const [running, setRunning] = useState(false);
  const [reply, setReply] = useState<ChatReply | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function run() {
    setRunning(true);
    setError(null);
    setReply(null);
    try {
      const r = await runTicketPipeline(ticketId);
      setReply(r);
      router.refresh();
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="mt-4">
      <button onClick={run} disabled={running} className="btn-primary">
        {running ? "Agent working…" : "Run Support Ops agent"}
      </button>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {reply && (
        <div className="card mt-4 p-4 text-sm space-y-3">
          <div>
            <h3 className="font-semibold mb-1">Agent decision chain</h3>
            <ol className="list-decimal ml-5 space-y-1">
              {reply.tool_calls.length === 0 && <li className="text-slate-500">no tool calls</li>}
              {reply.tool_calls.map((tc, i) => (
                <li key={i}>
                  <code className="kbd">{tc.tool}</code>{" "}
                  <span className={STATUS_STYLE[tc.status] || ""}>{tc.status}</span>
                  {tc.reason && <span className="text-slate-500"> — {tc.reason}</span>}
                  {tc.approval_id && (
                    <span className="text-purple-700"> (approval {tc.approval_id.slice(0, 8)}…)</span>
                  )}
                </li>
              ))}
            </ol>
          </div>
          {reply.blocked && (
            <p className="text-red-700">
              Blocked by guardrail: <code className="kbd">{reply.block_reason}</code>
            </p>
          )}
          <div>
            <h3 className="font-semibold mb-1">Agent answer</h3>
            <p className="text-slate-700 whitespace-pre-wrap">{reply.answer}</p>
          </div>
          {reply.trace_id && (
            <p className="text-xs text-slate-500">
              trace: <code className="kbd">{reply.trace_id}</code>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
