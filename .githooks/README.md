# Pre-commit secret scanner

A defensive hook that blocks common secret-leak patterns **before** a commit lands.

## What it catches (REJECTS the commit)

- API key shapes: `sk-...`, `sk_live_...`, `rk_...` (OpenAI/Stripe)
- AWS access key IDs: `AKIA[0-9A-Z]{16}`
- GitHub personal access tokens: `ghp_[A-Za-z0-9]{30,}`
- Slack tokens: `xox[abprs]-...`
- Supabase service-role JWT near the literal `service_role_key`
- Files named `.env`, `.env.*`, `apps/*/.env`, `apps/*/.env.*` (but not `.env.example`)
- Files named `auth.json` (Vercel token store)

## What it WARNS about (allows the commit)

- Real-looking email addresses in code files (`@acme.com`, etc.) — these are common in seed scripts; the warning is informational.
- US phone numbers: `NNN-NNN-NNNN`
- International phone numbers: `+NNNNNNNNNN`

## Always-skipped paths

- `package-lock.json`, `apps/*/package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`
- These would false-positive on hash strings.

## Whitelisted email patterns

- `*@acme.test`, `*@globex.test` (RFC 2606 reserved TLD, intentional placeholders)
- Anything inside `docs/`, `scripts/create_demo_users.ts`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`

## How to enable

```bash
git config core.hooksPath .githooks
```

That's it. The hook is **opt-in** so contributors who clone the repo aren't forced into using it.

## How to bypass (use sparingly)

```bash
git commit --no-verify
```

Document the reason in the commit message.

## Defense in depth

GitHub's native secret scanning + push protection (Settings → Code security and analysis) is the primary line of defense. This hook is the second layer.
