"use client";

import { useState, FormEvent } from "react";

type Status = "idle" | "submitting" | "success" | "error";

const EMAIL_RE = /.+@.+\..+/;

function friendlyError(code: string, fallback: string): string {
  switch (code) {
    case "invalid_email":
      return "That email doesn't look right — please double-check it.";
    case "rate_limited":
      return "Too many attempts from your network. Try again in an hour.";
    default:
      return fallback;
  }
}

export function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (status === "submitting") return;
    setError(null);

    if (!EMAIL_RE.test(email.trim())) {
      setError("That email doesn't look right — please double-check it.");
      setStatus("error");
      return;
    }

    setStatus("submitting");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          company: company.trim() || undefined,
          role: role.trim() || undefined,
        }),
      });
      const body = await res.json().catch(() => ({} as { error?: string; ok?: boolean }));
      if (!res.ok) {
        setError(friendlyError(body.error ?? "", `Submission failed (HTTP ${res.status}).`));
        setStatus("error");
        return;
      }
      setStatus("success");
    } catch (err) {
      setError(
        err instanceof Error
          ? `Network error: ${err.message}`
          : "Network error — please try again."
      );
      setStatus("error");
    }
  }

  function reset() {
    setEmail("");
    setCompany("");
    setRole("");
    setError(null);
    setStatus("idle");
  }

  if (status === "success") {
    return (
      <div className="mt-5 rounded-md border border-hairline bg-surface-2 p-5" role="status" aria-live="polite">
        <div className="text-base font-medium text-ink">You're on the list.</div>
        <p className="mt-1 text-sm text-ink-muted">
          We'll reach out at <span className="font-medium text-ink">{email}</span> when the next cohort opens.
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-3 text-sm font-medium text-ink-muted hover:text-ink underline underline-offset-4"
        >
          Add another email
        </button>
      </div>
    );
  }

  const submitting = status === "submitting";

  return (
    <form
      onSubmit={onSubmit}
      className="mt-5 grid sm:grid-cols-4 gap-3 sm:items-end"
      noValidate
    >
      <div className="sm:col-span-1">
        <label className="label" htmlFor="waitlist-email">Email</label>
        <input
          id="waitlist-email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="input"
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-invalid={status === "error" ? "true" : undefined}
          disabled={submitting}
        />
      </div>
      <div className="sm:col-span-1">
        <label className="label" htmlFor="waitlist-company">Company</label>
        <input
          id="waitlist-company"
          name="company"
          className="input"
          placeholder="Acme Corp"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          disabled={submitting}
        />
      </div>
      <div className="sm:col-span-1">
        <label className="label" htmlFor="waitlist-role">Role</label>
        <input
          id="waitlist-role"
          name="role"
          className="input"
          placeholder="Head of People"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          disabled={submitting}
        />
      </div>
      <div className="sm:col-span-4 flex flex-wrap items-center gap-3">
        <button
          type="submit"
          className="btn-orange px-5 py-2.5 text-sm"
          disabled={submitting}
        >
          {submitting ? "Joining…" : "Join waitlist"}
        </button>
        {status === "error" && error && (
          <p
            role="alert"
            className="text-sm text-red-700"
            aria-live="assertive"
          >
            {error}
          </p>
        )}
      </div>
    </form>
  );
}
