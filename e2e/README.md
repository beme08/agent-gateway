# E2E walkthroughs (Playwright)

These scripts drive the live Vercel deployment in a real browser. They prove that the demo works end-to-end against the production Supabase project.

## Prerequisites

```bash
npm install --prefix e2e playwright
npx --prefix e2e playwright install chromium
```

## Usage

```bash
# Walk all four "Try as …" roles and capture screenshots
node e2e/landing-and-roles.mjs

# Walk the manager-approval flow: sign in as manager, approve the pending
# request, then sign in as admin and confirm the audit dashboard rendered.
node e2e/manager-approve.mjs
```

Screenshots land in `e2e/shots/`.

## What they verify

- `landing-and-roles.mjs` — public landing renders, each "Try as …" button signs in as the right seeded user and lands them on the right dashboard.
- `manager-approve.mjs` — manager sees the pending request, clicking Approve clears the queue, and the admin audit dashboard renders afterwards.

## CI

These can run in GitHub Actions with the `playwright` action; smoke before merge to `main`.
