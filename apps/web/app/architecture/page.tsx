import { readFile } from "node:fs/promises";
import { join } from "node:path";

export default async function Architecture() {
  const md = await readFile(join(process.cwd(), "..", "..", "docs", "architecture.md"), "utf-8");
  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold mb-4">Architecture</h1>
      <pre className="card p-4 text-xs whitespace-pre-wrap">{md}</pre>
    </main>
  );
}
