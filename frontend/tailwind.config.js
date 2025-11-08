/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#fbbf24',
        dark: {
          100: '#1a1a2e',
          200: '#16213e',
          300: '#0f172a',
        }
      }
    },
  },
  plugins: [],
}
