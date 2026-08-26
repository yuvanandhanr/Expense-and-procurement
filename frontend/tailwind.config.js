/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--bg)",
        foreground: "var(--text)",
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--text)",
        },
        popover: {
          DEFAULT: "var(--card-2)",
          foreground: "var(--text)",
        },
        primary: {
          DEFAULT: "var(--violet)",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "var(--card-2)",
          foreground: "var(--text)",
        },
        muted: {
          DEFAULT: "var(--line)",
          foreground: "var(--text-dim)",
        },
        accent: {
          DEFAULT: "var(--line-2)",
          foreground: "var(--text)",
        },
        destructive: {
          DEFAULT: "var(--pink)",
          foreground: "#FFFFFF",
        },
        border: "var(--line)",
        input: "var(--line)",
        ring: "var(--violet)",
        violet: "var(--violet)",
        pink: "var(--pink)",
        lime: "var(--lime)",
        cyan: "var(--cyan)",
      },
      borderRadius: {
        lg: "8px",
        md: "6px",
        sm: "4px",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
