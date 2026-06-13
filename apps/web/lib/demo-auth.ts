"use server";

import { redirect } from "next/navigation";
import { createClient } from "./supabase/server";

const DEMO_PASSWORD = "demo1234";

const ROLE_TO_EMAIL: Record<string, { tenant: "acme" | "globex"; email: string; route: string }> = {
  employee: { tenant: "acme", email: "employee@acme.test", route: "/leave" },
  manager:  { tenant: "acme", email: "manager@acme.test",  route: "/leave/approvals" },
  admin:    { tenant: "acme", email: "admin@acme.test",    route: "/audit" },
  viewer:   { tenant: "acme", email: "viewer@acme.test",   route: "/agents/hr-policy-agent" },
};

export async function signInAsDemoUser(role: keyof typeof ROLE_TO_EMAIL) {
  const spec = ROLE_TO_EMAIL[role];
  if (!spec) throw new Error("unknown role");
  const supabase = createClient();
  const { error } = await supabase.auth.signInWithPassword({
    email: spec.email,
    password: DEMO_PASSWORD,
  });
  if (error) throw new Error(error.message);
  // Pin the active tenant to acme for the demo buttons (the demo user is a
  // member of both tenants via create_demo_users.ts; we pick the Acme side).
  redirect(spec.route);
}

export async function signOut() {
  const supabase = createClient();
  await supabase.auth.signOut();
  redirect("/");
}
