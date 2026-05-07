# Phase 1: Foundation - TODO List

## Overview
**Duration:** 3 months  
**Goal:** Modularize existing code, create REST API, and establish WebSocket communication for real-time updates.

---

## Month 1: Modularization (Weeks 1-4)

### Week 1: Setup & Planning ✅ COMPLETED
- [x] **Task 1.1:** Set up GitHub repository with branches
  - Create branch: `git_manager.ps1 branch phase1-foundation` ✅
  - Set up Python virtual environment (`python -m venv venv`) ⏳
  - Install dependencies: `pip install flask flask-socketio pytest` ⏳
  - Create folder structure (see below) ✅

- [x] **Task 1.2:** Create folder structure ✅
  ```
  syscan_web/
  ├── agent/
  │   ├── __init__.py ✅
  │   ├── scanner.py ✅
  │   ├── analyzer.py ✅
  │   ├── deleter.py ✅
  │   └── utils.py ✅
  ├── server/
  │   ├── __init__.py ✅
  │   ├── app.py ✅
  │   ├── api.py ✅
  │   ├── websocket.py ✅
  │   └── main.py ✅
  ├── common/
  │   ├── __init__.py ✅
  │   ├── config.py ✅
  │   └── constants.py ✅
  └── tests/
      └── test_agent.py ✅
  ```

### Week 2: Extract Scanner Module ✅ COMPLETED
- [x] **Task 2.1:** Create `agent/scanner.py` ✅
  - Extract `scan_system()` from `system_cleaner.py` ✅
  - Create `GridScanner` class ✅
  - Move `get_size_fast()` function ✅
  - Move `collect_grid_cells()` function ✅
  - Move `scan_grid()` function ✅

- [x] **Task 2.2:** Update imports and dependencies ✅
  - Import `os`, `concurrent.futures`, `threading` ✅
  - Import from `utils.py`: `is_excluded()` ✅
  - Test: `python -m pytest tests/test_agent.py -v` (pending venv setup)

### Week 3: Extract Deleter & Analyzer Modules ✅ COMPLETED
- [x] **Task 3.1:** Create `agent/deleter.py` ✅
  - Extract `send_to_recycle_bin()` function ✅
  - Extract `permanent_delete()` function (from main) ✅
  - Create `FileDeleter` class ✅

- [x] **Task 3.2:** Create `agent/analyzer.py` ✅
  - Extract registry scan: `scan_registry_leftovers()` ✅
  - Create `FileAnalyzer` class ✅
  - Add `analyze_items()` function ✅

### Week 4: Extract Utilities ✅ COMPLETED
- [x] **Task 4.1:** Create `agent/utils.py` ✅
  - Move `is_excluded()` function ✅
  - Move `get_size_fast()` function ✅
  - Add helper functions ✅

- [x] **Task 4.2:** Create `common/config.py` ✅
  - Move `scan_paths` configuration ✅
  - Move `EXCLUDES` list ✅
  - Add `Config` class ✅

- [x] **Task 4.3:** Create `common/constants.py` ✅
  - Add constants for paths, patterns ✅
  - Add constants for timeouts, worker counts ✅

---

## Month 2: REST API (Weeks 5-8) 🔄 IN PROGRESS

### Week 5: Flask Application Factory ✅ COMPLETED
- [x] **Task 5.1:** Create `server/app.py` ✅
- [x] **Task 5.2:** Create `server/api.py` ✅ (basic endpoints)

### Week 6: API Endpoints Implementation 🔄 IN PROGRESS
- [x] **Task 6.1:** Implement `POST /api/scan/start` ✅
- [x] **Task 6.2:** Implement `POST /api/delete` ✅
- [ ] **Task 6.3:** Add pagination to `GET /api/items`
- [ ] **Task 6.4:** Add report generation endpoint

### Week 7: WebSocket Integration ✅ COMPLETED
- [x] **Task 7.1:** Create `server/websocket.py` ✅
- [x] **Task 7.2:** Emit progress updates ✅ (basic)

### Week 8: API Testing ⏳ PENDING
- [ ] **Task 8.1:** Write API tests (`tests/test_api.py`)
- [ ] **Task 8.2:** Load testing with locust

---

## Month 3: Integration & Testing (Weeks 9-12)

### Week 9: Module Integration
- [ ] **Task 9.1:** Update `system_cleaner.py` as CLI wrapper
  ```python
  from agent.scanner import GridScanner
  from agent.deleter import FileDeleter
  
  def main():
      scanner = GridScanner()
      # ... use new modules
  ```

- [ ] **Task 9.2:** Ensure backward compatibility
  - CLI still works: `python system_cleaner.py --dry-run`
  - All original features work (delete, tree view, etc.)

### Week 10: Comprehensive Testing
- [ ] **Task 10.1:** Unit tests for all modules
  - `tests/test_scanner.py` - 10+ test cases
  - `tests/test_analyzer.py` - 5+ test cases
  - `tests/test_deleter.py` - 5+ test cases
  - `tests/test_api.py` - 10+ test cases

- [ ] **Task 10.2:** Integration tests
  - Test scanner → API → WebSocket flow
  - Test delete functionality (recycle + permanent)
  - Test error handling

### Week 11: Documentation
- [ ] **Task 11.1:** Create `docs/API.md`
  - Document all REST endpoints
  - Document WebSocket events
  - Add request/response examples

- [ ] **Task 11.2:** Update `README.md`
  - Add new project structure
  - Add installation instructions
  - Add API usage examples

### Week 12: Demo & Review
- [ ] **Task 12.1:** Create demo script
  ```bash
  # demo.sh
  python system_cleaner.py --dry-run  # CLI still works
  python server/app.py  # Start API
  # Show progress via WebSocket
  ```

- [ ] **Task 12.2:** Code review & refactoring
  - Run `pylint` or `flake8`
  - Fix all warnings
  - Ensure PEP 8 compliance

- [ ] **Task 12.3:** Commit & push
  ```bash
  cd Git_Repository
  ./git_manager.ps1 commit "Phase 1: Modularization complete"
  ./git_manager.ps1 push
  ```

---

## Success Criteria (End of Phase 1)

### Code Metrics
- [ ] **Module count:** 4+ modules (scanner, analyzer, deleter, utils)
- [ ] **Code coverage:** >80% (measured by `pytest --cov`)
- [ ] **Test count:** 30+ tests passing
- [ ] **API endpoints:** 5+ REST endpoints working
- [ ] **WebSocket:** Real-time progress updates working

### Performance Metrics
- [ ] **API response time:** <100ms for all endpoints
- [ ] **Scan speed:** Same as original (~17s for 200GB)
- [ ] **WebSocket latency:** <50ms for progress updates

### Documentation
- [ ] **API.md:** All endpoints documented
- [ ] **README.md:** Updated with new structure
- [ ] **Code docstrings:** All functions documented

### Git & Collaboration
- [ ] **Branch:** `phase1-foundation` merged to `master`
- [ ] **Commits:** Descriptive commit messages
- [ ] **GitHub:** All code pushed to `https://github.com/gyan4it/syscan`

---

## Risks & Mitigation

### Risk 1: Breaking Changes
- **Problem:** Existing CLI may break during refactoring
- **Mitigation:** 
  - Keep `system_cleaner.py` as wrapper around new modules
  - Test CLI after each major change
  - Use feature flags if needed

### Risk 2: Time Investment
- **Problem:** 3 months for "invisible" changes
- **Mitigation:**
  - Show weekly demos of progress
  - Commit small changes frequently
  - Celebrate milestones (Module extracted, API working, etc.)

### Risk 3: Complexity Increase
- **Problem:** More files, more concepts
- **Mitigation:**
  - Clear folder structure
  - Good documentation
  - Simple examples

---

## Next Steps After Phase 1

1. **Your Approval:** Review this TODO list
2. **Start Week 1:** I'll run `./git_manager.ps1 branch phase1-foundation`
3. **Execute Tasks:** I'll inform you before each Git operation
4. **Weekly Updates:** I'll report progress every Friday

---

**Ready to start? Tell me "Start Phase 1" and I'll begin with Week 1 tasks! 🚀**
