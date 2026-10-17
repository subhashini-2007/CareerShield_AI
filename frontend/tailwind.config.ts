import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#060A14",
          900: "#0B132B",
          850: "#111B38",
          800: "#1C2541",
          700: "#27355B",
          600: "#3A4D80",
        },
        shield: {
          blue: "#2563EB",
          lightBlue: "#3B82F6",
          cyan: "#06B6D4",
          brightCyan: "#22D3EE",
        },
        risk: {
          low: "#10B981",       // Low Risk - Emerald
          lowBg: "#064E3B",
          caution: "#F59E0B",   // Needs Caution - Amber
          cautionBg: "#78350F",
          high: "#EF4444",      // High Risk Indicators - Red
          highBg: "#7F1D1D",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
