/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'syscan-blue': '#3498db',
        'syscan-red': '#e74c3c',
        'syscan-green': '#2ecc71',
        'syscan-yellow': '#f1c40f',
        'syscan-gray': '#95a5a6',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
