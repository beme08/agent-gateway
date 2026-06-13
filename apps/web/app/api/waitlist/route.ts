import { NextResponse } from "next/server";
import { serviceClient } from "@/lib/supabase/server";

const buckets = new Map<string, number[]>();
function rateLimited(ip: string) {
  const now = Date.now();
  const arr = (buckets.get(ip) || []).filter((t) => now - t < 60 * 60 * 1000);
  arr.push(now);
  buckets.set(ip, arr);
  return arr.length > 5;
}

export async function POST(req: Request) {
  const ip = req.headers.get("x-forwarded-for") || "local";
  if (rateLimited(ip)) {
    return NextResponse.json({ error: "rate_limited" }, { status: 429 });
  }
  const body = await req.json().catch(() => ({}));
  const email = String(body.email || "").trim().toLowerCase();
  if (!email || !email.includes("@")) {
    return NextResponse.json({ error: "invalid_email" }, { status: 400 });
  }
  const supabase = serviceClient();
  const { error } = await supabase
    .from("waitlist_signups")
    .upsert({ email, company: body.company || null, role: body.role || null }, { onConflict: "email" });
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  return NextResponse.json({ ok: true });
}
