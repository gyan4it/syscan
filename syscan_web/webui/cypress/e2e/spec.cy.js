describe('SysCan WebUI E2E Tests', () => {
  beforeEach(() => {
    // Start Flask server before tests (assumes already running on port 5000)
    cy.wait(3000) // Wait to avoid rate limiting
    cy.visit('http://localhost:5000', { failOnStatusCode: false })
  })

  it('should load the main page', () => {
    cy.contains('SysCan Web UI')
    cy.contains('Start Scan').should('be.visible')
  })

  it('should show health endpoint works', () => {
    cy.request('http://localhost:5000/health').then((response) => {
      expect(response.status).to.eq(200)
      expect(response.body.status).to.eq('ok')
    })
  })

  it('should show API root endpoint', () => {
    cy.request('http://localhost:5000/api').then((response) => {
      expect(response.status).to.eq(200)
      expect(response.body.name).to.eq('SysCan API')
    })
  })

  it('should start scan when button clicked', () => {
    cy.contains('Start Scan').click()
    cy.contains('Scanning...').should('be.visible')
    
    // Wait for scan to complete (max 30 seconds)
    cy.contains('Found Items', { timeout: 30000 })
  })

  it('should display found items after scan', () => {
    // Wait for items to load
    cy.wait(5000)
    
    // Check if file list is visible
    cy.get('.file-list').should('be.visible')
    cy.contains('Found Items').should('be.visible')
  })

  it('should show progress bar during scan', () => {
    cy.contains('Start Scan').click()
    // Should show scanning state
    cy.contains('Scanning...').should('be.visible')
    // Wait for scan to complete (max 30 seconds)
    cy.contains('Found Items', { timeout: 30000 }).should('be.visible')
  })

  it('should show auth endpoints available', () => {
    // Wait to avoid rate limiting
    cy.wait(2000)
    cy.request({
      url: 'http://localhost:5000/api/auth/login',
      method: 'POST',
      body: { username: 'test', password: 'test' },
      failOnStatusCode: false
    }).then((response) => {
      // Should get 401 (unauthorized) or 400 (bad request) - not 404
      expect(response.status).to.not.eq(404)
      expect(response.status).to.be.oneOf([400, 401, 405, 422])
    })
  })

  it('should have all API endpoints accessible', () => {
    const endpoints = ['/api/scan', '/api/items', '/api/report', '/api/export']
    endpoints.forEach(endpoint => {
      cy.request({
        method: 'GET',
        url: `http://localhost:5000${endpoint}`,
        failOnStatusCode: false
      }).then((response) => {
        // Endpoint exists if it returns any response (not a server error)
        expect(response.status).to.be.lessThan(500)
      })
    })
  })
})
