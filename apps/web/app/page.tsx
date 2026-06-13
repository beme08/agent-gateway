import { signInAsDemoUser } from "@/lib/demo-auth";

const ROLES = [
  { id: "employee", label: "Try as Employee", description: "Acme Corp employee. Ask about sick leave, PTO, and remote work; create a leave request.", accent: "bg-indigo-600" },
  { id: "manager",  label: "Try as Manager",  description: "Acme Corp manager. Approve or reject your team's pending leave requests.",          accent: "bg-emerald-600" },
  { id: "admin",    label: "Try as Admin",    description: "Acme Corp admin. View the full audit dashboard, traces, and security events.",     accent: "bg-rose-600" },
  { id: "viewer",   label: "Try as Viewer",   description: "Read-only access. Confirms ACL filtering &mdash; executive content is blocked.",    accent: "bg-slate-700" },
] as const;

export default function LandingPage() {
  return (
    <main className="max-w-5xl mx-auto px-4 py-12">
      <header className="mb-10">
        <h1 className="text-4xl font-bold tracking-tight">Secure Enterprise Agent Gateway</h1>
        <p className="mt-3 text-lg text-slate-600 max-w-2xl">
          A multi-tenant agentic AI platform where an HR Policy Agent answers policy questions with
          ACL-filtered RAG and performs sick-leave / PTO workflows through role-gated tools. Supabase
          RLS enforces tenant isolation. Every retrieval, tool call, and decision is traced.
        </p>
      </header>

      <section className="grid sm:grid-cols-2 gap-4 mb-12">
        {ROLES.map((r) => (
          <form
            key={r.id}
            action={async () => {
              "use server";
              await signInAsDemoUser(r.id);
            }}
            className="card p-5 flex flex-col gap-3"
          >
            <div className="flex items-center gap-3">
              <span className={`inline-block w-2 h-2 rounded-full ${r.accent}`} />
              <h2 className="font-semibold">{r.label}</h2>
            </div>
            <p className="text-sm text-slate-600" dangerouslySetInnerHTML={{ __html: r.description }} />
            <button type="submit" className="btn-primary self-start">{r.label} →</button>
          </form>
        ))}
      </section>

      <section className="card p-6 mb-10">
        <h2 className="font-semibold mb-2">Or sign in manually</h2>
        <p className="text-sm text-slate-600 mb-3">
          Demo credentials:&nbsp;
          <code className="kbd">admin@acme.test</code>&nbsp;/&nbsp;
          <code className="kbd">demo1234</code>
        </p>
        <a href="/login" className="btn-secondary">Go to login</a>
      </section>

      <section className="card p-6 mb-10">
        <h2 className="font-semibold mb-2">Architecture highlights</h2>
        <ul className="text-sm text-slate-700 list-disc list-inside space-y-1">
          <li>Multi-tenant Postgres with RLS keyed off <code className="kbd">tenant_memberships</code>.</li>
          <li>ACL-filtered pgvector retrieval — restricted tags never enter the prompt.</li>
          <li>Tool gateway with role gates, schema validation, and per-call policy decisions.</li>
          <li>Centralized leave transitions (Postgres functions) shared by UI and agent.</li>
          <li>Prompt-injection defense-in-depth: untrusted block, pattern detector, audit log.</li>
          <li>Full audit traces for retrievals, tool calls, blocked events, latencies.</li>
        </ul>
      </section>

      <WaitlistCTA />
    </main>
  );
}

function WaitlistCTA() {
  return (
    <section className="card p-6">
      <h2 className="font-semibold mb-2">Join the private beta</h2>
      <p className="text-sm text-slate-600 mb-3">
        We're not ready for self-serve yet, but you can join the waitlist and we'll reach out when a
        private beta opens.
      </p>
      <form action="/api/waitlist" method="post" className="flex flex-col sm:flex-row gap-2 sm:items-end">
        <div className="flex-1">
          <label className="label" htmlFor="email">Email</label>
          <input id="email" name="email" type="email" required className="input" placeholder="you@company.com" />
        </div>
        <div className="flex-1">
          <label className="label" htmlFor="company">Company</label>
          <input id="company" name="company" className="input" placeholder="Acme Corp" />
        </div>
        <div className="flex-1">
          <label className="label" htmlFor="role">Role</label>
          <input id="role" name="role" className="input" placeholder="CTO" />
        </div>
        <button className="btn-primary">Join waitlist</button>
      </form>
    </section>
  );
}
