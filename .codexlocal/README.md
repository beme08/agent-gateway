# Project-local Codex configuration (placeholder)

Codex treats the literal `.codex/` folder inside any project as **read-only** —
it cannot be used for project-local config. This `.codexlocal/` folder is the
working substitute for the same purpose.

To activate the Supabase MCP for this project, do one of:

1. **Recommended — global config** (cleanest): append the snippet in
   `mcp-snippet.toml` to `~/.codex/config.toml`, then create
   `~/.codex/.env` (or set env vars in your shell) with `SUPABASE_PROJECT_REF`
   and `SUPABASE_ACCESS_TOKEN`.

2. **Project-local equivalent**: if you want only this project to see the
   Supabase MCP, copy `mcp-snippet.toml` into a Codex-supported location
   (the Codex docs confirm the project-local config is read from
   `<project>/.codex/config.toml`, which the Codex app protects as read-only
   in this environment, so option 1 is the practical path).
