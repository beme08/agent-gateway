import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { signOut } from "@/lib/demo-auth";

export default async function Dashboard() {
  const session = await getSession();
  if (!session) redirect("/");
  const m = session.memberships[0];
  const role = m?.role ?? "viewer";
  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <header className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">{m?.tenant_name}</h1>
          <p className="text-sm text-slate-600">
            Signed in as <code className="kbd">{session.user.email}</code> ({role})
          </p>
        </div>
        <form action={signOut}>
          <button className="btn-secondary">Sign out</button>
        </form>
      </header>

      <section className="grid sm:grid-cols-2 gap-4">
        <Card title="HR Policy Agent" href="/agents/hr-policy-agent" desc="Ask policy questions and create / view leave requests." />
        <Card title="My leave"         href="/leave"                  desc="Balance, request time off, view your requests." />
        {(role === "manager" || role === "admin") && (
          <Card title="Approvals"        href="/leave/approvals"        desc="Approve or reject your team's pending leave requests." />
        )}
        {role === "admin" && (
          <Card title="Audit dashboard" href="/audit"                  desc="Traces, tool calls, and security events." />
        )}
        <Card title="Architecture"     href="/architecture"           desc="Mermaid diagram of the system and the agent loop." />
      </section>
    </main>
  );
}

function Card({ title, href, desc }: { title: string; href: string; desc: string }) {
  return (
    <Link href={href} className="card p-5 hover:border-accent transition">
      <h2 className="font-semibold">{title}</h2>
      <p className="text-sm text-slate-600 mt-1">{desc}</p>
    </Link>
  );
}
