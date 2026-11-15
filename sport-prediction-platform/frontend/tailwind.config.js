/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0B0F19",
        cardBg: "#161F30",
        cardHover: "#1E293B",
        accentGreen: "#10B981",
        accentAmber: "#F59E0B",
        accentBlue: "#3B82F6"
      }
    },
  },
  plugins: [],
}
