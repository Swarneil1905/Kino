import type { Config } from "tailwindcss"

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        kino: {
          bg: "#0B0B0B",
          surface: "#181818",
          surface2: "#252525",
          accent: "#C41020",
          text: "#F0EEE8",
          text2: "#9E9C96",
          text3: "#565650",
          // legacy aliases so existing components do not break
          background: "#0B0B0B",
          elevated: "#252525",
          red: "#C41020",
          green: "#4ADE80",
          cyan: "#54B9C5",
          muted: "#9E9C96",
          "muted-dim": "#565650",
        },
        netflix: {
          red: "#C41020",
          black: "#0B0B0B",
          card: "#181818",
          surface: "#252525",
          "text-muted": "#9E9C96",
          muted: "#565650",
          "match-green": "#4ADE80",
          "explore-cyan": "#54B9C5",
        },
      },
      fontFamily: {
        sans: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
        serif: ["var(--font-playfair)", "Georgia", "serif"],
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
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out forwards",
        "slide-up": "slide-up 0.6s ease-out forwards",
        "fade-up": "fadeUp 0.5s ease forwards",
      },
    },
  },
  plugins: [],
}

export default config
