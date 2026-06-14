import { readFile } from "node:fs/promises";
import { join } from "node:path";

async function readDoc(): Promise<string> {
  // Try a few candidate locations. Local dev: ../../docs/architecture.md
  // (cwd is apps/web, so ../../ reaches the repo root). Vercel build: cwd is
  // the apps/web root of the deployed slice, so ../../ is outside the build
  // and the file isn't there — fall back to a bundled copy under public/.
  const candidates = [
    join(process.cwd(), "..", "..", "docs", "architecture.md"),
    join(process.cwd(), "..", "docs", "architecture.md"),
    join(process.cwd(), "public", "architecture.md"),
  ];
  for (const c of candidates) {
    try {
      return await readFile(c, "utf-8");
    } catch {
      // try next
    }
  }
  return "# Architecture\n\nThe architecture doc is not available in this build.";
}

export default async function Architecture() {
  const md = await readDoc();
  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold mb-4">Architecture</h1>
      <pre className="card p-4 text-xs whitespace-pre-wrap">{md}</pre>
    </main>
  );
}
