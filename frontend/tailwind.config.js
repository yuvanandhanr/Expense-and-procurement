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
          DEFAULT: "var(--primary)",
          hover: "var(--primary-hover)",
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
        ring: "var(--primary)",
        apple: {
          blue: "var(--primary)",
          green: "var(--lime)",
          amber: "var(--amber)",
          red: "var(--pink)",
          teal: "var(--cyan)",
        },
        violet: "var(--primary)",
        pink: "var(--pink)",
        lime: "var(--lime)",
        cyan: "var(--cyan)",
      },
      borderRadius: {
        "3xl": "24px",
        "2xl": "18px",
        xl: "14px",
        lg: "10px",
        md: "8px",
        sm: "6px",
      },
      boxShadow: {
        'apple-sm': '0 2px 8px rgba(0, 0, 0, 0.04)',
        'apple-md': '0 6px 20px rgba(0, 0, 0, 0.06)',
        'apple-lg': '0 12px 36px rgba(0, 0, 0, 0.08)',
        'apple-glow': '0 0 24px rgba(10, 132, 255, 0.25)',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'SF Pro Display', 'sans-serif'],
        display: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
