import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { createClient } from "@/lib/supabase/server";
import { Chat } from "@/components/chat";

export default async function AgentPage({ params }: { params: { id: string } }) {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];
  const supabase = createClient();

  // Resolve the agent by slug-ish name "hr-policy-agent" -> title contains "HR Policy"
  const { data: agent } = await supabase
    .from("agents")
    .select("id, name, description")
    .eq("tenant_id", m.tenant_id)
    .ilike("name", "%HR Policy%")
    .limit(1)
    .single();

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold">{agent?.name ?? "HR Policy Agent"}</h1>
          {agent?.description && <p className="text-sm text-slate-600">{agent.description}</p>}
        </div>
        <a href="/dashboard" className="btn-ghost">← Dashboard</a>
      </header>
      <Chat agentId={agent?.id || ""} initialSessionId={null} />
      <p className="text-xs text-slate-500 mt-3">
        Retrieved policy text is wrapped as untrusted data. Tool calls go through a server-side gateway that
        checks tenant, role, and schema before executing. Every step is audited.
      </p>
    </main>
  );
}
