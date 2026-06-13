// scripts/reset_demo.ts
// Calls reset_demo_tenant for the tenant the given admin user belongs to.
// Used by the nightly GitHub Actions cron.

import { createClient } from "@supabase/supabase-js";
import { config } from "dotenv";
import { resolve } from "node:path";

config({ path: resolve(process.cwd(), ".env") });

const email = process.argv.find((a) => a.startsWith("--email="))?.split("=")[1]
  || process.argv[process.argv.indexOf("--email") + 1];
if (!email) {
  console.error("usage: npx tsx reset_demo.ts --email <admin-email>");
  process.exit(1);
}

const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!, {
  auth: { persistSession: false },
});

async function main() {
  const { data: user } = await supabase.auth.admin.listUsers({ perPage: 200 });
  const target = user.users.find((u) => u.email === email);
  if (!target) throw new Error(`no auth user ${email}`);

  const { data: m } = await supabase
    .from("tenant_memberships")
    .select("tenant_id")
    .eq("user_id", target.id)
    .limit(1)
    .single();
  if (!m) throw new Error("no membership");
  const { error } = await supabase.rpc("reset_demo_tenant", { p_tenant_id: m.tenant_id });
  if (error) throw error;
  console.log(`reset demo tenant ${m.tenant_id} for ${email}`);
}
main().catch((e) => { console.error(e); process.exit(1); });
