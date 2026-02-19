/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        skywash: "#E9F1FF",
        midnight: "#0B1D3A",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.1)",
      },
    },
  },
  plugins: [],
};