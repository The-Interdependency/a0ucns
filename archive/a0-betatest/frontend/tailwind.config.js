/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        bg: {
          base: "#030303",
          panel: "#0A0A0A",
          surface: "#121212",
          deep: "#050505",
        },
        accent: {
          cyan: "#22D3EE",
          amber: "#F59E0B",
          emerald: "#10B981",
          rose: "#F43F5E",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
        sans: ["'IBM Plex Sans'", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      letterSpacing: {
        ultra: "0.2em",
      },
    },
  },
  plugins: [],
};
