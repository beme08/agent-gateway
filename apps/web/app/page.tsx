import { signInAsDemoUser } from "@/lib/demo-auth";

const ROLES = [
  {
    id: "employee",
    label: "Employee",
    fullName: "Sam Patel",
    title: "Software Engineer · Acme Corp",
    description:
      "Ask the HR agent about sick leave, vacation balance, and remote work policy. Submit a leave request in chat.",
    accent: "from-indigo-500 to-indigo-600",
    initialsBg: "bg-indigo-100 text-indigo-700",
    initials: "SP",
  },
  {
    id: "manager",
    label: "Manager",
    fullName: "Riya Chen",
    title: "Engineering Manager · Acme Corp",
    description:
      "See your team's pending requests, approve or reject sick leave and PTO. Every decision is audit-traced.",
    accent: "from-emerald-500 to-emerald-600",
    initialsBg: "bg-emerald-100 text-emerald-700",
    initials: "RC",
  },
  {
    id: "admin",
    label: "Admin",
    fullName: "Alex Morgan",
    title: "Workplace Operations Lead · Acme Corp",
    description:
      "Open the audit dashboard: per-tenant usage, every chat trace, every blocked prompt-injection event.",
    accent: "from-rose-500 to-rose-600",
    initialsBg: "bg-rose-100 text-rose-700",
    initials: "AM",
  },
  {
    id: "viewer",
    label: "Viewer",
    fullName: "Jordan Lee",
    title: "New Hire · Acme Corp",
    description:
      "Read-only access. Confirms the ACL filter blocks executive compensation content from the prompt.",
    accent: "from-slate-500 to-slate-600",
    initialsBg: "bg-slate-100 text-slate-700",
    initials: "JL",
  },
] as const;

const TRUST_BADGES = [
  { label: "Multi-tenant RLS", sub: "Postgres row-level security" },
  { label: "Audit-traced", sub: "Retrievals · tools · decisions" },
  { label: "Role-gated tools", sub: "Server-side authorization" },
  { label: "ACL-filtered RAG", sub: "Restricted tags never enter prompt" },
  { label: "Prompt-injection defense", sub: "Pattern detector + audit log" },
];

const FEATURES = [
  {
    title: "Ask & answer with citations",
    body: "The HR agent retrieves your company handbooks with role-aware ACL filtering and cites the exact page and section for every answer.",
    icon: "search",
  },
  {
    title: "Act on behalf, safely",
    body: "The agent can create leave requests, check balances, and route approvals through a server-authorized tool gateway — never directly to the database.",
    icon: "wand",
  },
  {
    title: "See every decision",
    body: "Per-tenant usage counters, full chat traces, blocked-event log, and a one-click 'show me why' timeline for any tool call.",
    icon: "shield",
  },
];

export default function LandingPage() {
  return (
    <main className="bg-canvas">
      <Hero />
      <TrustStrip />
      <Personas />
      <Features />
      <Testimonial />
      <ArchitectureNotes />
      <WaitlistCTA />
      <SiteFooter />
    </main>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 bg-hero-grid [background-size:22px_22px] opacity-60" aria-hidden />
      <div className="relative max-w-6xl mx-auto px-6 pt-16 pb-14 grid lg:grid-cols-12 gap-10 items-center">
        <div className="lg:col-span-7">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-line bg-white px-3 py-1 text-xs text-muted shadow-card">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Public demo · live now
          </div>
          <h1 className="mt-5 text-4xl sm:text-5xl font-semibold tracking-tight text-ink">
            The HR-grade AI gateway
            <br className="hidden sm:block" />
            <span className="text-accent"> your people actually trust.</span>
          </h1>
          <p className="mt-5 text-lg text-muted max-w-2xl">
            A multi-tenant agentic AI platform where an HR Policy Agent answers policy questions with
            ACL-filtered retrieval, performs sick leave and PTO through role-gated tools, and records
            every retrieval and decision to an immutable audit trail.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <a
              href="#personas"
              className="inline-flex items-center gap-2 rounded-md bg-accent px-5 py-3 text-sm font-semibold text-white shadow-card hover:opacity-95"
            >
              Try the demo
              <span aria-hidden>→</span>
            </a>
            <a
              href="#architecture"
              className="inline-flex items-center gap-2 rounded-md border border-slate-line bg-white px-5 py-3 text-sm font-semibold text-ink hover:bg-slate-50"
            >
              See architecture
            </a>
          </div>
          <p className="mt-4 text-xs text-muted">
            No signup. Click any role to sign in as a seeded demo user.
          </p>
        </div>
        <div className="lg:col-span-5">
          <HeroIllustration />
        </div>
      </div>
    </section>
  );
}

function HeroIllustration() {
  // Inline SVG: a small "office team" composition — desk + laptop + 3 people avatars
  return (
    <div className="relative aspect-[5/4] w-full">
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white to-accent-soft shadow-card" />
      <svg
        viewBox="0 0 500 400"
        className="absolute inset-0 h-full w-full"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-label="Illustration of a small HR team working with the agent"
      >
        <defs>
          <linearGradient id="desk" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#e6e8ef" />
          </linearGradient>
          <linearGradient id="laptop" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#1f243a" />
            <stop offset="100%" stopColor="#0b1020" />
          </linearGradient>
        </defs>

        {/* desk */}
        <rect x="40" y="270" width="420" height="20" rx="6" fill="url(#desk)" stroke="#dfe2ec" />
        <rect x="60" y="290" width="20" height="80" fill="#dfe2ec" />
        <rect x="420" y="290" width="20" height="80" fill="#dfe2ec" />

        {/* laptop */}
        <rect x="200" y="180" width="180" height="110" rx="10" fill="url(#laptop)" />
        <rect x="210" y="190" width="160" height="90" rx="4" fill="#0b1020" />
        <rect x="180" y="285" width="220" height="8" rx="3" fill="#1f243a" />
        {/* screen content: chat bubbles */}
        <rect x="220" y="200" width="120" height="14" rx="6" fill="#4f46e5" opacity="0.85" />
        <rect x="220" y="222" width="90" height="10" rx="5" fill="#3a3f5c" />
        <rect x="220" y="238" width="140" height="10" rx="5" fill="#3a3f5c" />
        <rect x="220" y="254" width="100" height="10" rx="5" fill="#10b981" opacity="0.85" />

        {/* left person */}
        <g transform="translate(70,120)">
          <circle cx="30" cy="30" r="28" fill="#eef2ff" stroke="#c7d2fe" />
          <circle cx="30" cy="26" r="10" fill="#4f46e5" />
          <path d="M10 60 Q30 42 50 60 L50 78 L10 78 Z" fill="#4f46e5" />
          <text x="30" y="98" textAnchor="middle" fontSize="11" fontFamily="ui-sans-serif" fill="#5b6478">Employee</text>
        </g>

        {/* right person */}
        <g transform="translate(380,120)">
          <circle cx="30" cy="30" r="28" fill="#ecfdf5" stroke="#a7f3d0" />
          <circle cx="30" cy="26" r="10" fill="#10b981" />
          <path d="M10 60 Q30 42 50 60 L50 78 L10 78 Z" fill="#10b981" />
          <text x="30" y="98" textAnchor="middle" fontSize="11" fontFamily="ui-sans-serif" fill="#5b6478">Manager</text>
        </g>

        {/* floating UI chips */}
        <g>
          <rect x="80" y="60" width="120" height="22" rx="11" fill="#ffffff" stroke="#e6e8ef" />
          <circle cx="93" cy="71" r="4" fill="#4f46e5" />
          <text x="104" y="75" fontSize="10" fontFamily="ui-sans-serif" fill="#0b1020">Sick leave policy</text>
        </g>
        <g>
          <rect x="300" y="60" width="140" height="22" rx="11" fill="#ffffff" stroke="#e6e8ef" />
          <circle cx="313" cy="71" r="4" fill="#10b981" />
          <text x="324" y="75" fontSize="10" fontFamily="ui-sans-serif" fill="#0b1020">Approve request</text>
        </g>
        <g>
          <rect x="160" y="320" width="180" height="22" rx="11" fill="#ffffff" stroke="#e6e8ef" />
          <circle cx="173" cy="331" r="4" fill="#f43f5e" />
          <text x="184" y="335" fontSize="10" fontFamily="ui-sans-serif" fill="#0b1020">Audit trace recorded</text>
        </g>
      </svg>
    </div>
  );
}

function TrustStrip() {
  return (
    <section className="border-y border-slate-line bg-white">
      <div className="max-w-6xl mx-auto px-6 py-5 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs">
        {TRUST_BADGES.map((b) => (
          <div key={b.label} className="flex items-center gap-2">
            <svg viewBox="0 0 20 20" className="w-4 h-4 text-emerald-600" fill="currentColor" aria-hidden>
              <path d="M10 1.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L10 14.9 4.8 17.6l1-5.8L1.5 7.7l5.9-.9L10 1.5z" />
            </svg>
            <div className="leading-tight">
              <div className="font-semibold text-ink">{b.label}</div>
              <div className="text-muted">{b.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Personas() {
  return (
    <section id="personas" className="max-w-6xl mx-auto px-6 py-14">
      <div className="max-w-2xl">
        <div className="text-xs font-semibold uppercase tracking-wider text-accent">Try the demo</div>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-ink">Pick a role to sign in</h2>
        <p className="mt-3 text-muted">
          Each button signs you in as a real seeded user inside Acme Corp, with a real leave balance,
          a real manager, and a real audit log. Every action you take is end-to-end traceable.
        </p>
      </div>

      <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {ROLES.map((r) => (
          <form
            key={r.id}
            action={async () => {
              "use server";
              await signInAsDemoUser(r.id);
            }}
            className="group relative rounded-xl border border-slate-line bg-white p-5 shadow-card hover:shadow-card-hover transition flex flex-col"
          >
            <div className="flex items-center gap-3">
              <PersonAvatar initials={r.initials} bg={r.initialsBg} />
              <div className="min-w-0">
                <div className="text-xs uppercase tracking-wider text-muted">{r.label}</div>
                <div className="font-semibold text-ink truncate">{r.fullName}</div>
              </div>
            </div>
            <div className="mt-2 text-xs text-muted truncate">{r.title}</div>
            <p className="mt-4 text-sm text-ink/80 leading-relaxed flex-1">{r.description}</p>
            <button
              type="submit"
              className={`mt-5 inline-flex items-center justify-between gap-2 rounded-md bg-gradient-to-r ${r.accent} px-4 py-2 text-sm font-semibold text-white shadow-card hover:opacity-95`}
            >
              <span>Sign in as {r.label}</span>
              <span aria-hidden>→</span>
            </button>
          </form>
        ))}
      </div>

      <div className="mt-6 text-xs text-muted">
        Manual sign-in also works at <a className="underline" href="/login">/login</a> using
        <code className="kbd mx-1">admin@acme.test</code>
        /
        <code className="kbd mx-1">demo1234</code>.
      </div>
    </section>
  );
}

function PersonAvatar({ initials, bg }: { initials: string; bg: string }) {
  return (
    <div
      className={`h-11 w-11 shrink-0 rounded-full ${bg} flex items-center justify-center font-semibold text-sm ring-4 ring-white shadow-card`}
      aria-hidden
    >
      {initials}
    </div>
  );
}

function Features() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-12">
      <div className="text-xs font-semibold uppercase tracking-wider text-accent">What you get</div>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-ink">
        Built for the way HR, IT, and security actually work.
      </h2>

      <div className="mt-8 grid md:grid-cols-3 gap-5">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-xl border border-slate-line bg-white p-6 shadow-card">
            <FeatureIcon name={f.icon} />
            <h3 className="mt-4 font-semibold text-ink">{f.title}</h3>
            <p className="mt-2 text-sm text-muted leading-relaxed">{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function FeatureIcon({ name }: { name: string }) {
  const common = "h-9 w-9 text-accent";
  if (name === "search") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={common} aria-hidden>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" strokeLinecap="round" />
        <path d="M11 8v6M8 11h6" strokeLinecap="round" />
      </svg>
    );
  }
  if (name === "wand") {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={common} aria-hidden>
        <path d="M5 19 19 5" strokeLinecap="round" />
        <path d="M14 4l2 2M18 8l2 2M4 14l2 2" strokeLinecap="round" />
        <circle cx="7" cy="7" r="1.4" fill="currentColor" />
        <circle cx="17" cy="17" r="1.4" fill="currentColor" />
      </svg>
    );
  }
  // shield
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={common} aria-hidden>
      <path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z" />
      <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Testimonial() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-10">
      <figure className="rounded-2xl border border-slate-line bg-white p-8 shadow-card grid md:grid-cols-12 gap-6 items-center">
        <div className="md:col-span-9">
          <svg viewBox="0 0 24 24" className="h-7 w-7 text-accent" fill="currentColor" aria-hidden>
            <path d="M9 4c-3 1-5 4-5 8v8h8v-8H7c0-3 1-5 3-6L9 4Zm10 0c-3 1-5 4-5 8v8h8v-8h-5c0-3 1-5 3-6L19 4Z" />
          </svg>
          <blockquote className="mt-3 text-xl text-ink leading-relaxed">
            “We piloted the agent with 80 employees in their first week. People got answers
            to leave questions in under five seconds, and our HRBP team finally trusted the
            audit log enough to sign off on rolling it out company-wide.”
          </blockquote>
          <figcaption className="mt-4 text-sm text-muted">
            <span className="font-semibold text-ink">Maya Ortiz</span> · Director, People Operations · Acme Corp
          </figcaption>
        </div>
        <div className="md:col-span-3 flex md:justify-end">
          <div
            className="h-24 w-24 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center font-semibold text-2xl ring-4 ring-white shadow-card"
            aria-hidden
          >
            MO
          </div>
        </div>
      </figure>
    </section>
  );
}

function ArchitectureNotes() {
  return (
    <section id="architecture" className="max-w-6xl mx-auto px-6 py-10">
      <div className="rounded-2xl border border-slate-line bg-white p-8 shadow-card">
        <div className="text-xs font-semibold uppercase tracking-wider text-accent">Under the hood</div>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Architecture highlights</h2>
        <ul className="mt-5 grid md:grid-cols-2 gap-x-8 gap-y-2 text-sm text-ink/80 list-disc list-inside">
          <li>Multi-tenant Postgres with RLS keyed off <code className="kbd">tenant_memberships</code>.</li>
          <li>ACL-filtered pgvector retrieval — restricted tags never enter the prompt.</li>
          <li>Tool gateway with role gates, schema validation, and per-call policy decisions.</li>
          <li>Centralized leave transitions (Postgres functions) shared by UI and agent.</li>
          <li>Prompt-injection defense-in-depth: untrusted block, pattern detector, audit log.</li>
          <li>Full audit traces for retrievals, tool calls, blocked events, latencies.</li>
        </ul>
      </div>
    </section>
  );
}

function WaitlistCTA() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-10">
      <div className="rounded-2xl border border-slate-line bg-white p-8 shadow-card">
        <h2 className="text-2xl font-semibold tracking-tight text-ink">Join the private beta</h2>
        <p className="mt-2 text-muted">
          Not ready for self-serve yet. Drop your email and we'll reach out when the next
          cohort opens.
        </p>
        <form
          action="/api/waitlist"
          method="post"
          className="mt-5 grid sm:grid-cols-4 gap-3 sm:items-end"
        >
          <div className="sm:col-span-1">
            <label className="label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" required className="input" placeholder="you@company.com" />
          </div>
          <div className="sm:col-span-1">
            <label className="label" htmlFor="company">Company</label>
            <input id="company" name="company" className="input" placeholder="Acme Corp" />
          </div>
          <div className="sm:col-span-1">
            <label className="label" htmlFor="role">Role</label>
            <input id="role" name="role" className="input" placeholder="Head of People" />
          </div>
          <button className="rounded-md bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-card hover:opacity-95">
            Join waitlist
          </button>
        </form>
      </div>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="border-t border-slate-line bg-white">
      <div className="max-w-6xl mx-auto px-6 py-6 flex flex-wrap items-center justify-between gap-3 text-xs text-muted">
        <div>
          Secure Enterprise Agent Gateway · public demo
        </div>
        <div className="flex items-center gap-4">
          <a className="hover:text-ink" href="/login">Sign in</a>
          <a className="hover:text-ink" href="#architecture">Architecture</a>
          <a className="hover:text-ink" href="https://github.com/beme08/agent-gateway">GitHub</a>
        </div>
      </div>
    </footer>
  );
}
