import { signInAsDemoUser } from "@/lib/demo-auth";

// Role cards for the demo. We do NOT use fictional names or quotes
// anywhere in the public demo. Each role card uses a real faceless Pexels
// stock photo (hands, desk, back of head) as the backdrop — no human
// likeness, no invented avatar.
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
      <RiskTiers />
      <Personas />
      <SupportOps />
      <Features />
      <UseCases />
      <UnderTheHood />
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
            LLM proposes. Gateway decides.
            <br className="hidden sm:block" />
            <span className="text-accent-orange"> Every action audited.</span>
          </h1>
          <p className="mt-5 text-lg text-ink-muted max-w-2xl">
            A multi-tenant agentic AI platform where agents operate on company systems — but only
            through a server-side tool gateway that decides what&apos;s{" "}
            <strong className="text-ink">allowed</strong>, what needs{" "}
            <strong className="text-ink">human approval</strong>, and what&apos;s{" "}
            <strong className="text-ink">structurally blocked</strong>. Two operational
            environments, one gateway: HR policy with ACL-filtered RAG, and production incident
            response with risk-tiered remediation.
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
          <p className="mt-1.5 text-xs text-ink-muted">
            <span className="text-emerald-600 font-semibold">✓ Demo suite passing</span>
            {" · "}last verified 2026-08-22 ·{" "}
            <a className="underline" href="#architecture">
              sanitized run summary
            </a>
          </p>
          <p className="mt-2 text-xs text-ink-muted/80">
            Reference prototype for portfolio purposes — not a live customer deployment. Runs on a
            free-tier stack, so first responses after idle can take up to a minute while the API
            wakes (subsequent turns are prompt). On faster frontier-based routing the same agent
            answers in seconds; the gateway, guardrails, and audit chain are identical either way.
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

const RISK_TIERS = [
  {
    tier: "Auto",
    style: "bg-emerald-100 text-emerald-700",
    what: "Executes immediately",
    examples: "restart service · health check · notify Slack · update ticket",
  },
  {
    tier: "Approval",
    style: "bg-purple-100 text-purple-700",
    what: (
      <>
        Pauses as <code className="kbd">pending_approval</code> → human approves → gateway{" "}
        <strong>re-checks policy</strong> → executes
      </>
    ),
    examples: "rollback deployment · scale service",
  },
  {
    tier: "Blocked",
    style: "bg-red-100 text-red-700",
    what: "Denied before authorization even runs — for all roles, including admin",
    examples: "delete production data",
  },
] as const;

function RiskTiers() {
  return (
    <section className="bg-white border-t border-hairline">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <h2 className="text-sm font-medium text-ink-muted">
          Every tool call passes the policy engine:
        </h2>
        <div className="mt-4 grid md:grid-cols-3 gap-4">
          {RISK_TIERS.map((t) => (
            <div key={t.tier} className="rounded-xl border border-hairline bg-canvas p-5">
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${t.style}`}>
                {t.tier}
              </span>
              <p className="mt-3 text-sm text-ink leading-relaxed">{t.what}</p>
              <p className="mt-2 text-xs text-ink-muted">{t.examples}</p>
            </div>
          ))}
        </div>
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
              data-testid={`role-${r.id}`}
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

// Role-first visual. The role name IS the visual — big, bold,
// with a thin accent stripe and a small monogram icon. The background is
// a real faceless Pexels stock photo (hands, desk, back of head) so the
// demo feels human without inventing a person. The bottom caption credits
// Pexels per the free-license convention.
const ROLE_PHOTO: Record<
  string,
  { src: string; credit: string; tint: string }
> = {
  employee: {
    src: "/photos/employee.jpg",
    credit: "Photo: Pexels",
    tint: "from-ink/55 via-ink/20 to-transparent",
  },
  manager: {
    src: "/photos/manager.jpg",
    credit: "Photo: Pexels",
    tint: "from-ink/45 via-ink/15 to-transparent",
  },
  admin: {
    src: "/photos/admin.jpg",
    credit: "Photo: Pexels",
    tint: "from-ink/50 via-ink/20 to-transparent",
  },
  viewer: {
    src: "/photos/viewer.jpg",
    credit: "Photo: Pexels",
    tint: "from-ink/55 via-ink/25 to-transparent",
  },
};

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
  const photo = ROLE_PHOTO[role];
  return (
    <div
      className="relative aspect-[16/9] w-full overflow-hidden rounded-lg border border-hairline bg-surface-2"
      role="img"
      aria-label={`${m.label} role — faceless stock photo backdrop`}
    >
      {photo ? (
        <img
          src={photo.src}
          alt=""
          loading="lazy"
          className="absolute inset-0 h-full w-full object-cover"
        />
      ) : null}

      {/* Soft top-to-bottom darken so the centered label reads on any photo */}
      {photo ? (
        <div
          className={`absolute inset-0 bg-gradient-to-b ${photo.tint}`}
          aria-hidden
        />
      ) : null}

      {/* Left accent stripe, same gradient as the role card below */}
      <div className={`absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b ${m.accent}`} aria-hidden />

      {/* Center: big role label + monogram + sub-line */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-3">
        <div className={`flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br ${m.accent} text-white text-lg font-semibold `}>
          {m.initial}
        </div>
        <div className="mt-2 text-xl font-semibold tracking-tight text-white drop-shadow-sm">
          {m.label}
        </div>
        <div className="mt-0.5 text-[11px] text-white/85 drop-shadow-sm">
          {m.sub}
        </div>
      </div>

      {/* Bottom: tiny photo credit (Pexels free license) */}
      <span className="absolute bottom-1.5 left-3 right-3 text-[9px] text-white/70 text-center drop-shadow-sm">
        {photo?.credit ?? "Photo placeholder"}
      </span>
    </div>
  );
}

// The 12 Support Ops tools, mirrored from apps/api/app/agent/tools/support_tools.py.
// Tier counts: 9 auto · 2 approval_required · 1 prohibited.
const SUPPORT_TOOLS: { name: string; tier: "auto" | "approval" | "blocked"; desc: string }[] = [
  { name: "get_ticket", tier: "auto", desc: "Retrieve ticket details" },
  { name: "update_ticket", tier: "auto", desc: "Update ticket status and fields" },
  { name: "search_knowledge", tier: "auto", desc: "Query the support knowledge base" },
  { name: "query_service_health", tier: "auto", desc: "Check current service health" },
  { name: "get_recent_deployments", tier: "auto", desc: "List recent deployment history" },
  { name: "restart_service", tier: "auto", desc: "Restart a failing service" },
  { name: "verify_service_health", tier: "auto", desc: "Confirm service health post-remediation" },
  { name: "create_github_issue", tier: "auto", desc: "Open a tracking issue" },
  { name: "notify_slack", tier: "auto", desc: "Post an alert to the on-call channel" },
  { name: "rollback_deployment", tier: "approval", desc: "Roll back to a previous deployment — held pending human approval, then re-checked against policy before executing" },
  { name: "scale_service", tier: "approval", desc: "Scale a service up or down — held pending human approval, then re-checked against policy before executing" },
  { name: "delete_production_data", tier: "blocked", desc: "Structurally denied for all roles — even admin. Gate runs before authorization." },
];

const TIER_BADGE: Record<string, string> = {
  auto: "bg-emerald-100 text-emerald-700",
  approval: "bg-purple-100 text-purple-700",
  blocked: "bg-red-100 text-red-700",
};

function SupportOps() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-20">
      <div className="max-w-2xl">
        <div className="text-sm font-medium text-ink-muted">Support Operations</div>
        <h2 className="mt-2 text-3xl font-medium text-ink tracking-headline">
          Same gateway, different risk surface.
        </h2>
        <p className="mt-3 text-ink-muted">
          The same tool gateway serves a second operational environment: production incident
          response. An agent triages tickets, diagnoses issues, and proposes remediation across
          12 tools — each one risk-tiered and enforced server-side. Sign in and open{" "}
          <strong className="text-ink">Support Operations</strong> from the dashboard to run a
          ticket and watch the decision chain build live.
        </p>
      </div>

      <div className="mt-8 overflow-x-auto rounded-xl border border-hairline bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-xs text-ink-muted">
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">Tool</th>
              <th className="px-4 py-3 font-medium">Risk tier</th>
              <th className="px-4 py-3 font-medium">What it does</th>
            </tr>
          </thead>
          <tbody>
            {SUPPORT_TOOLS.map((t, i) => (
              <tr key={t.name} className="border-b border-hairline last:border-0">
                <td className="px-4 py-2.5 text-ink-muted">{i + 1}</td>
                <td className="px-4 py-2.5">
                  <code className="kbd">{t.name}</code>
                </td>
                <td className="px-4 py-2.5">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${TIER_BADGE[t.tier]}`}>
                    {t.tier}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-ink-muted">{t.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 text-xs text-ink-muted">
        9 auto · 2 approval · 1 blocked — enforced in{" "}
        <code className="kbd">apps/api/app/agent/tools/policy.py</code>, not in the prompt.
      </div>

      <div className="mt-10 grid md:grid-cols-2 gap-5">
        <div className="rounded-xl border border-hairline bg-white p-5">
          <h3 className="font-medium text-ink">Denied call — real trace, sanitized</h3>
          <pre className="mt-3 text-xs text-ink-muted whitespace-pre-wrap font-mono leading-relaxed">{`tool:       delete_production_data
risk_tier:  PROHIBITED
caller:     Support Ops agent (admin session)

decision:   DENIED — prohibited gate (pre-authorization)
reason:     structurally denied for all roles;
            gate runs before authorization —
            even admin cannot override

audit:      tool_calls row written (status: denied)
            security_event logged (prohibited_attempt)`}</pre>
        </div>
        <div className="rounded-xl border border-hairline bg-white p-5">
          <h3 className="font-medium text-ink">Approved call — real trace, sanitized</h3>
          <pre className="mt-3 text-xs text-ink-muted whitespace-pre-wrap font-mono leading-relaxed">{`agent:      rollback_deployment (payments-api)
gateway:    risk_tier=approval_required
            → status=pending_approval

human:      approved (manager session)
gateway:    RE-CHECKED policy
            role=manager · tool=rollback_deployment
            tier=approval_required → ALLOWED

execution:  rollback payments-api v1.9.1 → v1.9.0
post-check: verify_service_health → healthy

audit:      tool_calls row written (status: executed)
            approval row: 06c3c87e… (executed)`}</pre>
        </div>
      </div>
    </section>
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

function UnderTheHood() {
  return (
    <section id="architecture" className="max-w-6xl mx-auto px-6 py-20">
      <div className="rounded-xl border border-hairline bg-white p-8">
        <div className="text-sm font-medium text-ink-muted">Under the hood</div>
        <h2 className="mt-2 text-2xl font-medium text-ink tracking-headline">Architecture highlights</h2>
        <ul className="mt-5 grid md:grid-cols-2 gap-x-8 gap-y-2 text-sm text-ink-muted list-disc list-inside">
          <li>Multi-tenant Postgres with RLS keyed off <code className="kbd">tenant_memberships</code>.</li>
          <li>ACL-filtered pgvector retrieval — restricted tags never enter the prompt.</li>
          <li>Tool gateway with role gates, schema validation, and per-call policy decisions.</li>
          <li>Risk tiers: 9 auto · 2 approval · 1 blocked — enforced server-side, not in the prompt.</li>
          <li>Prompt-injection defense-in-depth: untrusted block, pattern detector, audit log.</li>
          <li>Full audit traces for retrievals, tool calls, blocked events, latencies.</li>
        </ul>
        <div className="mt-6 flex flex-wrap gap-4 text-sm">
          <a className="underline hover:text-ink" href="https://github.com/beme08/agent-gateway">
            View source on GitHub →
          </a>
          <a className="underline hover:text-ink" href="#architecture">
            See architecture →
          </a>
        </div>
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
