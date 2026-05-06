describe('SysCan WebUI E2E Tests', () => {
  beforeEach(() => {
    // Start Flask server before tests (assumes already running on port 5000)
    cy.visit('http://localhost:5000')
  })

  it('should load the main page', () => {
    cy.contains('SysCan Web UI')
    cy.contains('Start Scan').should('be.visible')
  })

  it('should start scan when button clicked', () => {
    cy.contains('Start Scan').click()
    cy.contains('Scanning...').should('be.visible')
    
    // Wait for scan to complete (max 30 seconds)
    cy.contains('Scan Complete!', { timeout: 30000 })
    cy.contains('Found Items').should('be.visible')
  })

  it('should display file tree with checkboxes', () => {
    // Wait for items to load
    cy.wait(5000)
    
    // Check if file tree is visible
    cy.get('.file-tree').should('be.visible')
    cy.get('input[type="checkbox"]').should('have.length.gt', 0)
  })

  it('should select all items when button clicked', () => {
    cy.contains('Select All').click()
    cy.get('input[type="checkbox"]:checked').should('have.length.gt', 0)
  })

  it('should show star ratings', () => {
    cy.get('.star-rating').should('be.visible')
    cy.get('.star-rating').should('contain', '★')
  })

  it('should open delete dialog when delete button clicked', () => {
    cy.contains('Delete Selected').click()
    cy.get('.delete-dialog').should('be.visible')
    cy.contains('Delete').should('be.visible')
  })

  it('should cancel delete dialog', () => {
    cy.contains('Cancel').click()
    cy.get('.delete-dialog').should('not.exist')
  })

  it('should show progress bar during scan', () => {
    cy.contains('Start Scan').click()
    cy.get('.progress-bar').should('be.visible')
    cy.contains('Progress:', { timeout: 30000 })
  })
})
