/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#f3f4f6",
          card: "#ffffff",
          border: "#e1e5ea",
          hover: "#f8f9fb",
          text: "#202938",
          muted: "#697383",
          subtle: "#858d99"
        },
        tier: {
          low: "#10b981",     // Emerald
          medium: "#d9ba0d",  // Amber
          high: "#e8660a",    // Orange
          critical: "#ee0b0b" // Red
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
