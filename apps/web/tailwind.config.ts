import type { Config } from "tailwindcss"

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        netflix: {
          red: "#E50914",
          black: "#141414",
          card: "#181818",
          surface: "#1a1a1a",
          "text-muted": "#B3B3B3",
          muted: "#808080",
          "match-green": "#46D369",
          "explore-cyan": "#54B9C5",
        },
        kino: {
          background: "#141414",
          surface: "#181818",
          elevated: "#1a1a1a",
          red: "#E50914",
          green: "#46D369",
          cyan: "#54B9C5",
          muted: "#B3B3B3",
          "muted-dim": "#808080",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Helvetica Neue", "Arial", "sans-serif"],
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out forwards",
        "slide-up": "slide-up 0.6s ease-out forwards",
      },
    },
  },
  plugins: [],
}

export default config
