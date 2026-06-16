import { signInAsDemoUser } from "@/lib/demo-auth";

// Role cards for the demo. We do NOT use fictional names, faces, or quotes
// anywhere in the public demo. The "photo" slots are clearly framed
// placeholders so a real customer can drop in a real team photo later.
const ROLES = [
  {
    id: "employee",
    label: "Employee",
    title: "Acme Corp · Employee role",
    description:
      "Ask the HR agent about vacation, sick, bereavement, and personal time. Submit a leave request in chat and watch it land on your manager's queue.",
    accent: "from-ink to-ink/90",
  },
  {
    id: "manager",
    label: "Manager",
    title: "Acme Corp · Manager role",
    description:
      "See your team's pending requests, approve or reject them. Every decision is audit-traced and tied to a verifiable tool call.",
    accent: "from-ink to-ink/90",
  },
  {
    id: "admin",
    label: "Admin",
    title: "Acme Corp · Admin role",
    description:
      "Open the audit dashboard: per-tenant usage, every chat trace, every blocked prompt-injection event. Reset the demo data with one click.",
    accent: "from-ink to-ink/90",
  },
  {
    id: "viewer",
    label: "Viewer",
    title: "Acme Corp · Read-only role",
    description:
      "Read-only access. Confirms the ACL filter blocks executive compensation content from the prompt, while still retrieving the public policy docs.",
    accent: "from-ink to-ink/90",
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

// HR-flavored use cases. Neutral copy, no quotes, no customer names, no logos.
const USE_CASES = [
  {
    title: "Onboarding Q&A",
    body: "New hires ask about benefits, payroll cycles, equipment, and travel policy in plain English and get citations from the actual handbook.",
  },
  {
    title: "Time-off filing",
    body: "Employees file vacation, sick, bereavement, parental, jury duty, and PTO carryover requests from chat or the web app. No email back-and-forth.",
  },
  {
    title: "Manager approvals",
    body: "Managers see their team's pending requests, approve or reject with one click, and every decision is recorded against the original chat trace.",
  },
  {
    title: "Audit & compliance",
    body: "Admins review per-tenant usage, every tool call, every blocked prompt-injection event, and export an immutable log for security review.",
  },
];

export default function LandingPage() {
  return (
    <main className="bg-canvas">
      <Hero />
      <TrustStrip />
      <Personas />
      <Features />
      <UseCases />
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
          <div className="inline-flex items-center gap-2 rounded-full border border-hairline bg-white px-3 py-1 text-xs text-ink-muted">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Public demo · live now
          </div>
          <h1 className="mt-5 text-4xl sm:text-5xl font-medium text-ink tracking-display">
            The HR-grade AI gateway
            <br className="hidden sm:block" />
            <span className="text-accent-orange"> your people actually trust.</span>
          </h1>
          <p className="mt-5 text-lg text-ink-muted max-w-2xl">
            A multi-tenant agentic AI platform where an HR Policy Agent answers policy questions with
            ACL-filtered retrieval, files time-off requests (vacation, PTO, sick, bereavement, parental,
            personal, jury duty, unpaid leave) through role-gated tools, and records every retrieval
            and decision to an immutable audit trail.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <a
              href="#personas"
              className="btn-primary px-5 py-3 text-sm"
            >
              Try the demo
              <span aria-hidden>→</span>
            </a>
            <a
              href="#architecture"
              className="btn-secondary px-5 py-3 text-sm"
            >
              See architecture
            </a>
          </div>
          <p className="mt-4 text-xs text-ink-muted">
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
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white to-surface-2" />
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
            <stop offset="0%" stopColor="#111111" />
            <stop offset="100%" stopColor="#111111" />
          </linearGradient>
        </defs>

        {/* desk */}
        <rect x="40" y="270" width="420" height="20" rx="6" fill="url(#desk)" stroke="#d3cec6" />
        <rect x="60" y="290" width="20" height="80" fill="#ebe7e1" />
        <rect x="420" y="290" width="20" height="80" fill="#ebe7e1" />

        {/* laptop */}
        <rect x="200" y="180" width="180" height="110" rx="10" fill="url(#laptop)" />
        <rect x="210" y="190" width="160" height="90" rx="4" fill="#111111" />
        <rect x="180" y="285" width="220" height="8" rx="3" fill="#111111" />
        {/* screen content: chat bubbles */}
        <rect x="220" y="200" width="120" height="14" rx="6" fill="#111111" opacity="0.85" />
        <rect x="220" y="222" width="90" height="10" rx="5" fill="#ebe7e1" />
        <rect x="220" y="238" width="140" height="10" rx="5" fill="#ebe7e1" />
        <rect x="220" y="254" width="100" height="10" rx="5" fill="#ff5600" opacity="0.9" />

        {/* left person */}
        <g transform="translate(70,120)">
          <circle cx="30" cy="30" r="28" fill="#ebe7e1" stroke="#d3cec6" />
          <circle cx="30" cy="26" r="10" fill="#111111" />
          <path d="M10 60 Q30 42 50 60 L50 78 L10 78 Z" fill="#111111" />
          <text x="30" y="98" textAnchor="middle" fontSize="11" fontFamily="ui-sans-serif" fill="#626260">Employee</text>
        </g>

        {/* right person */}
        <g transform="translate(380,120)">
          <circle cx="30" cy="30" r="28" fill="#ebe7e1" stroke="#d3cec6" />
          <circle cx="30" cy="26" r="10" fill="#ff5600" />
          <path d="M10 60 Q30 42 50 60 L50 78 L10 78 Z" fill="#ff5600" />
          <text x="30" y="98" textAnchor="middle" fontSize="11" fontFamily="ui-sans-serif" fill="#626260">Manager</text>
        </g>

        {/* floating UI chips */}
        <g>
          <rect x="80" y="60" width="120" height="22" rx="11" fill="#ffffff" stroke="#d3cec6" />
          <circle cx="93" cy="71" r="4" fill="#111111" />
          <text x="104" y="75" fontSize="10" fontFamily="ui-sans-serif" fill="#111111">Sick leave policy</text>
        </g>
        <g>
          <rect x="300" y="60" width="140" height="22" rx="11" fill="#ffffff" stroke="#d3cec6" />
          <circle cx="313" cy="71" r="4" fill="#ff5600" />
          <text x="324" y="75" fontSize="10" fontFamily="ui-sans-serif" fill="#111111">Approve request</text>
        </g>
        <g>
          <rect x="160" y="320" width="180" height="22" rx="11" fill="#ffffff" stroke="#d3cec6" />
          <circle cx="173" cy="331" r="4" fill="#ff5600" />
          <text x="184" y="335" fontSize="10" fontFamily="ui-sans-serif" fill="#111111">Audit trace recorded</text>
        </g>
      </svg>
    </div>
  );
}

function TrustStrip() {
  return (
    <section className="bg-white">
      <div className="max-w-6xl mx-auto px-6 py-5 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs">
        {TRUST_BADGES.map((b) => (
          <div key={b.label} className="flex items-center gap-2">
            <svg viewBox="0 0 20 20" className="w-4 h-4 text-ink-muted" fill="currentColor" aria-hidden>
              <path d="M10 1.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L10 14.9 4.8 17.6l1-5.8L1.5 7.7l5.9-.9L10 1.5z" />
            </svg>
            <div className="leading-tight">
              <div className="font-semibold text-ink text-[13px]">{b.label}</div>
              <div className="text-ink-muted">{b.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Personas() {
  return (
    <section id="personas" className="max-w-6xl mx-auto px-6 py-20">
      <div className="max-w-2xl">
        <div className="text-sm font-medium text-ink-muted">Try the demo</div>
        <h2 className="mt-2 text-3xl font-medium text-ink tracking-headline">Pick a role to sign in</h2>
        <p className="mt-3 text-ink-muted">
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
            className="group relative rounded-xl border border-hairline bg-white p-5 transition flex flex-col"
          >
            <PhotoPlaceholder role={r.id} />
            <div className="mt-4 text-xs font-medium text-ink-muted">{r.label}</div>
            <div className="mt-1 font-medium text-ink">{r.title}</div>
            <p className="mt-3 text-sm text-ink-muted leading-relaxed flex-1">{r.description}</p>
            <button
              type="submit"
              className="mt-5 btn-primary justify-between"
            >
              <span>Sign in as {r.label}</span>
              <span aria-hidden>→</span>
            </button>
          </form>
        ))}
      </div>

      <div className="mt-6 text-xs text-ink-muted">
        Manual sign-in also works at <a className="underline" href="/login">/login</a> using
        <code className="kbd mx-1">admin@acme.test</code>
        /
        <code className="kbd mx-1">demo1234</code>.
      </div>
    </section>
  );
}

// Role-first photo placeholder. The role name IS the visual — big, bold,
// with a thin accent stripe and a small monogram icon. No human likeness
// anywhere. The dashed border + tiny "photo placeholder" caption still
// make it obvious that a real team photo can be dropped in later.
function PhotoPlaceholder({ role }: { role: string }) {
  const meta: Record<string, { label: string; initial: string; accent: string; sub: string }> = {
    employee: {
      label: "Employee",
      initial: "E",
      accent: "from-ink to-ink/85",
      sub: "Asks about policy, files time off",
    },
    manager: {
      label: "Manager",
      initial: "M",
      accent: "from-ink to-ink/85",
      sub: "Approves and audits team requests",
    },
    admin: {
      label: "Admin",
      initial: "A",
      accent: "from-accent-orange to-accent-orange/85",
      sub: "Sees per-tenant traces & usage",
    },
    viewer: {
      label: "Viewer",
      initial: "V",
      accent: "from-ink-muted to-ink-muted/85",
      sub: "Read-only — confirms ACL filters",
    },
  };
  const m = meta[role] ?? { label: role, initial: role.charAt(0).toUpperCase(), accent: "from-ink-muted to-ink-muted/85", sub: "Demo role" };
  return (
    <div
      className="relative aspect-[16/9] w-full overflow-hidden rounded-lg border-2 border-dashed border-hairline bg-surface-2"
      role="img"
      aria-label={`Photo placeholder for the ${m.label} role — drop a real team photo here`}
    >
      {/* Left accent stripe, same gradient as the role card below */}
      <div className={`absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b ${m.accent}`} aria-hidden />

      {/* Center: big role label + monogram + sub-line */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-3">
        <div className={`flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br ${m.accent} text-white text-lg font-semibold `}>
          {m.initial}
        </div>
        <div className="mt-2 text-xl font-semibold tracking-tight text-ink">
          {m.label}
        </div>
        <div className="mt-0.5 text-[11px] text-ink-muted">
          {m.sub}
        </div>
      </div>

      {/* Bottom: tiny placeholder caption */}
      <span className="absolute bottom-1.5 left-3 right-3 text-[9px] text-ink-subtle text-center">
        Photo placeholder · drop a real team photo here
      </span>
    </div>
  );
}

function Features() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-20">
      <div className="text-sm font-medium text-ink-muted">What you get</div>
      <h2 className="mt-2 text-3xl font-medium text-ink tracking-headline">
        Built for the way HR, IT, and security actually work.
      </h2>

      <div className="mt-8 grid md:grid-cols-3 gap-5">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-xl border border-hairline bg-white p-6">
            <FeatureIcon name={f.icon} />
            <h3 className="mt-4 font-medium text-ink">{f.title}</h3>
            <p className="mt-2 text-sm text-ink-muted leading-relaxed">{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function FeatureIcon({ name }: { name: string }) {
  const common = "h-9 w-9 text-ink";
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



function UseCases() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-20">
      <div className="text-sm font-medium text-ink-muted">HR use cases</div>
      <h2 className="mt-2 text-3xl font-medium text-ink tracking-headline">
        What HR teams use it for on day one.
      </h2>
      <p className="mt-3 text-ink-muted max-w-2xl">
        Four workflows that replace the most common back-and-forth between employees, managers, and HR.
      </p>
      <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {USE_CASES.map((u) => (
          <div key={u.title} className="rounded-xl border border-hairline bg-white p-5">
            <h3 className="font-medium text-ink">{u.title}</h3>
            <p className="mt-2 text-sm text-ink-muted leading-relaxed">{u.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ArchitectureNotes() {
  return (
    <section id="architecture" className="max-w-6xl mx-auto px-6 py-20">
      <div className="rounded-xl border border-hairline bg-white p-8">
        <div className="text-sm font-medium text-ink-muted">Under the hood</div>
        <h2 className="mt-2 text-2xl font-medium text-ink tracking-headline">Architecture highlights</h2>
        <ul className="mt-5 grid md:grid-cols-2 gap-x-8 gap-y-2 text-sm text-ink-muted list-disc list-inside">
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
    <section className="max-w-6xl mx-auto px-6 py-20">
      <div className="rounded-xl border border-hairline bg-white p-8">
        <h2 className="text-2xl font-medium text-ink tracking-headline">Join the private beta</h2>
        <p className="mt-2 text-ink-muted">
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
          <button className="btn-orange px-5 py-2.5 text-sm">
            Join waitlist
          </button>
        </form>
      </div>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="border-t border-hairline bg-white">
      <div className="max-w-6xl mx-auto px-6 py-6 flex flex-wrap items-center justify-between gap-3 text-xs text-ink-muted">
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
