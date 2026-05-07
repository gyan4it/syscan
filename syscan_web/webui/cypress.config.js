// Cypress config (CommonJS format)
const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:5000',
    supportFile: false,
    viewportWidth: 1280,
    viewportHeight: 720,
  },
});
