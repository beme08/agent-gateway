import "./globals.css";
import type { Metadata } from "next";
import { DisclaimerBanner } from "@/components/disclaimer-banner";

export const metadata: Metadata = {
  title: "Secure Enterprise Agent Gateway",
  description: "Multi-tenant agentic AI platform with RAG, role-gated tools, and audit tracing.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <DisclaimerBanner />
        {children}
      </body>
    </html>
  );
}
