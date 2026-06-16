/** @type {import('tailwindcss").Config} */
// Intercom-inspired design system (https://getdesign.md/intercom/design-md)
// Cream canvas, charcoal ink, warm hairlines, single Fin Orange accent.
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Intercom palette
        ink: "#111111",
        "ink-muted": "#626260",
        "ink-subtle": "#7b7b78",
        "ink-tertiary": "#9c9fa5",
        canvas: "#f5f1ec",        // Intercom cream — anchor surface
        "surface-1": "#ffffff",   // white card surface (lifted from cream)
        "surface-2": "#ebe7e1",   // warm gray, used sparingly
        hairline: "#d3cec6",
        "hairline-soft": "#ebe7e1",
        "accent-orange": "#ff5600", // Fin Orange — reserved for waitlist CTA
      },
      fontFamily: {
        sans: ["Geist", "Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      },
      letterSpacing: {
        display: "-0.04em",
        headline: "-0.02em",
        body: "-0.01em",
      },
      backgroundImage: {
        "hero-grid": "radial-gradient(circle at 1px 1px, rgba(17, 17, 17, 0.05) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};
