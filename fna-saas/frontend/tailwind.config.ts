import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
          800: "#5b21b6",
          900: "#4c1d95",
        },
        navy: {
          700: "#1e2d5a",
          800: "#162147",
          900: "#0f1630",
        },
        advora: {
          purple: "#8B5CF6",
          orange: "#F97316",
          teal:   "#06B6D4",
          pink:   "#EC4899",
          sky:    "#38BDF8",
        },
      },
      backgroundImage: {
        "advora-gradient": "linear-gradient(135deg, #7c3aed 0%, #06b6d4 50%, #f97316 100%)",
        "advora-hero":     "linear-gradient(135deg, #0f1630 0%, #1e2d5a 60%, #2d1b69 100%)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px 0 rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px 0 rgba(0,0,0,0.10), 0 2px 4px 0 rgba(0,0,0,0.06)",
        "brand-glow": "0 0 20px rgba(124,58,237,0.25)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-in": "slideIn 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          from: { transform: "translateX(-100%)" },
          to:   { transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
