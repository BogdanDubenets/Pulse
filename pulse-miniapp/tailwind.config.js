/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Pulse Brand — Dark Theme
        background: "#1A1D2E",
        surface: "#252A3F",
        primary: "#FF6B6B",
        secondary: "#4ECDC4",
        accent: "#FDCB6E",
        text: {
          primary: "#FFFFFF",
          secondary: "#B2B9C4",
          muted: "#636E72",
        },
        border: "#3A4059",
        // Status Colors
        success: "#00B894",
        warning: "#FDCB6E",
        error: "#D63031",
        trending: "#FF6B6B",
        verified: "#4ECDC4",
        pending: "#95A5A6",
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
