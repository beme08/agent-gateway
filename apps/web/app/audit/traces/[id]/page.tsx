import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";

export default async function TraceDetail({ params }: { params: { id: string } }) {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];
  if (m.role !== "admin") redirect("/dashboard");
  const supabase = createClient();

  const { data: trace } = await supabase
    .from("agent_traces")
    .select("*")
    .eq("id", params.id)
    .eq("tenant_id", m.tenant_id)
    .single();
  if (!trace) return <main className="max-w-4xl mx-auto p-10"><p>Not found.</p></main>;

  const { data: calls } = await supabase
    .from("tool_calls")
    .select("*")
    .eq("trace_id", params.id)
    .order("created_at", { ascending: true });

  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Trace detail</h1>
        <a href="/audit" className="btn-ghost">← Audit</a>
      </header>

      <section className="card p-4 mb-6 text-sm">
        <div className="grid grid-cols-2 gap-2">
          <div><strong>When:</strong> {new Date(trace.created_at).toLocaleString()}</div>
          <div><strong>Latency:</strong> {trace.latency_ms ?? "—"} ms</div>
          <div><strong>Status:</strong> {trace.final_status}</div>
          <div><strong>Loops:</strong> {trace.tool_loop_count}</div>
          <div><strong>Input safety:</strong> {trace.input_safety_status}</div>
          <div><strong>Retrieval safety:</strong> {trace.retrieval_safety_status}</div>
          <div><strong>Model:</strong> {trace.model_name}</div>
          <div><strong>Embedding model:</strong> {trace.embedding_model}</div>
        </div>
        <div className="mt-3">
          <strong>User message:</strong>
          <div className="bg-slate-50 rounded p-2 mt-1">{trace.user_message}</div>
        </div>
        {trace.retrieval_query && (
          <div className="mt-3">
            <strong>Retrieval query:</strong>
            <div className="bg-slate-50 rounded p-2 mt-1 text-xs">{trace.retrieval_query}</div>
          </div>
        )}
      </section>

      <section>
        <h2 className="font-semibold mb-2">Timeline</h2>
        <ol className="space-y-3">
          <Step label="User message" body={trace.user_message} />
          <Step
            label="Retrieval"
            body={`Retrieved ${trace.retrieved_chunk_ids?.length ?? 0} chunk(s).${trace.retrieval_safety_status !== "clean" ? " ⚠ " + trace.retrieval_safety_status : ""}`}
          />
          {(calls || []).map((c: any) => (
            <Step
              key={c.id}
              label={`Tool call: ${c.tool_name}`}
              body={
                <div>
                  <div className="flex gap-2 text-xs">
                    <span className="kbd">{c.status}</span>
                    {c.policy_reason && <span className="kbd">{c.policy_reason}</span>}
                    {c.latency_ms != null && <span className="kbd">{c.latency_ms} ms</span>}
                  </div>
                  <details className="mt-2">
                    <summary className="text-xs cursor-pointer">arguments</summary>
                    <pre className="text-xs bg-slate-50 p-2 rounded mt-1 overflow-auto">{JSON.stringify(c.arguments, null, 2)}</pre>
                  </details>
                  {c.result && (
                    <details className="mt-1">
                      <summary className="text-xs cursor-pointer">result</summary>
                      <pre className="text-xs bg-slate-50 p-2 rounded mt-1 overflow-auto">{JSON.stringify(c.result, null, 2)}</pre>
                    </details>
                  )}
                </div>
              }
            />
          ))}
          <Step label="Final answer" body={trace.final_status === "refused" ? "(refused by safety check)" : "see agent_messages table for the full text"} />
        </ol>
      </section>
    </main>
  );
}

function Step({ label, body }: { label: string; body: React.ReactNode }) {
  return (
    <li className="card p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-sm mt-1">{body}</div>
    </li>
  );
}
