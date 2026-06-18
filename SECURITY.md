# Security Policy

## Reporting a vulnerability

If you discover a security issue in this project, please report it privately:

- **Email**: open a GitHub issue with the `security` label, or contact the maintainer via the GitHub profile in the repo URL.
- **Response time**: 7 days
- **Disclosure policy**: We follow [coordinated disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure). Please do not file a public issue, open a public PR, or discuss the vulnerability on social media until we've had a chance to investigate and ship a fix.

## Scope

The following are in scope for security reports:

- The web tier (`apps/web/`) — Next.js 14 application
- The API tier (`apps/api/`) — FastAPI Python 3.11+ application
- The Supabase schema and RLS policies (`supabase/`)
- The build and deployment pipeline (`vercel.json`, `Dockerfile`, GitHub Actions)

The following are **out of scope**:

- The `docs/` folder (no executable code)
- The `DESIGN.md` file (documentation only)
- The demo seed data and demo credentials (`@acme.test`, `@globex.test`, password `demo1234`) — these are RFC 2606 reserved-TLD placeholders, never used for real authentication

## Supported versions

| Version | Supported |
|---|---|
| `main` branch | ✅ |
| Older branches | ❌ |

## Best practices for contributors

- Never commit a real secret. Use `.env.local` (gitignored) and reference values from `process.env`. See `.env.example` for the expected shape.
- Never paste API keys, Supabase service-role keys, JWT secrets, or Vercel tokens into issues, PRs, or commit messages.
- Use the pre-commit hook in `.githooks/` (opt-in: `git config core.hooksPath .githooks`) to catch secrets before they're committed.
- GitHub also runs secret scanning and push protection on this repo (see Settings → Code security and analysis). Defense in depth.
