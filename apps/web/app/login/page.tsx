import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export default function LoginPage({
  searchParams,
}: {
  searchParams: { error?: string; next?: string };
}) {
  async function login(formData: FormData) {
    "use server";
    const email = String(formData.get("email"));
    const password = String(formData.get("password"));
    const next = String(formData.get("next") || "/dashboard");
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) redirect(`/login?error=${encodeURIComponent(error.message)}`);
    redirect(next);
  }

  return (
    <main className="max-w-md mx-auto px-4 py-16">
      <h1 className="text-2xl font-semibold mb-2">Sign in</h1>
      <p className="text-sm text-slate-600 mb-6">
        For demo, use <code className="kbd">admin@acme.test</code> / <code className="kbd">demo1234</code>.
      </p>
      <form action={login} className="card p-5 space-y-3">
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" name="email" type="email" required className="input" />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" name="password" type="password" required className="input" />
        </div>
        {searchParams.error && (
          <p className="text-sm text-rose-600">{searchParams.error}</p>
        )}
        <button className="btn-primary w-full">Sign in</button>
      </form>
    </main>
  );
}
