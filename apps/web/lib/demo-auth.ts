"use server";

import { redirect } from "next/navigation";
import { createClient } from "./supabase/server";

const DEMO_PASSWORD = "demo1234";

const ROLE_TO_EMAIL: Record<string, { email: string }> = {
  employee: { email: "employee@acme.test" },
  manager:  { email: "manager@acme.test" },
  admin:    { email: "admin@acme.test" },
  viewer:   { email: "viewer@acme.test" },
};

export async function signInAsDemoUser(role: keyof typeof ROLE_TO_EMAIL) {
  const spec = ROLE_TO_EMAIL[role];
  if (!spec) throw new Error("unknown role");
  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({
    email: spec.email,
    password: DEMO_PASSWORD,
  });
  if (error) throw new Error(error.message);
  // Pin the active tenant to acme for the demo buttons (the demo user is a
  // member of both tenants via create_demo_users.ts; we pick the Acme side).
  // Land every persona on the dashboard so the agent chat, leave, approvals,
  // and audit are all one click away regardless of role.
  redirect("/dashboard");
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/");
}
