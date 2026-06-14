/** @type {import('tailwindcss").Config} */
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1020",
        accent: "#4f46e5",
        "accent-soft": "#eef2ff",
        canvas: "#f6f7fb",
        "slate-line": "#e6e8ef",
        "muted": "#5b6478",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Inter", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06)",
        "card-hover": "0 1px 2px rgba(15, 23, 42, 0.06), 0 14px 36px rgba(15, 23, 42, 0.10)",
      },
      backgroundImage: {
        "hero-grid": "radial-gradient(circle at 1px 1px, rgba(15, 23, 42, 0.06) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};
