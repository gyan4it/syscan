#!/usr/bin/env python
"""
Phase 1 Runtime Bug Test
Tests all modules for runtime errors and logical bugs.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_scanner():
    """Test GridScanner for bugs."""
    print("Testing GridScanner...")
    try:
        from syscan_web.agent.scanner import GridScanner, is_excluded
        
        # Test 1: Initialization
        scanner = GridScanner()
        print("  [OK] GridScanner initialized")
        
        # Test 2: is_excluded function
        assert is_excluded('C:/Users/Test/Documents', ['C:/Users/*/Documents']) == True
        assert is_excluded('C:/Users/Test/Projects', ['C:/Users/*/Documents']) == False
        print("  [OK] is_excluded works")
        
        # Test 3: get_optimal_workers
        workers = scanner.get_optimal_workers()
        assert workers > 0 and workers <= 256
        print(f"  [OK] get_optimal_workers: {workers}")
        
        return True
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analyzer():
    """Test FileAnalyzer for bugs."""
    print("\nTesting FileAnalyzer...")
    try:
        from syscan_web.agent.analyzer import FileAnalyzer
        
        analyzer = FileAnalyzer()
        print("  [OK] FileAnalyzer initialized")
        
        # Test analyze_items with empty list
        result = analyzer.analyze_items([])
        assert result['total_items'] == 0
        assert result['total_size_gb'] == 0
        print("  [OK] analyze_items with empty list")
        
        # Test analyze_items with data
        items = [('C:/test/path1', 2 * 1024**3), ('C:/test/path2', 1.5 * 1024**3)]
        result = analyzer.analyze_items(items)
        assert result['total_items'] == 2
        assert result['total_size_gb'] > 3
        print("  [OK] analyze_items with data")
        
        return True
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deleter():
    """Test FileDeleter for bugs."""
    print("\nTesting FileDeleter...")
    try:
        from syscan_web.agent.deleter import FileDeleter
        
        deleter = FileDeleter()
        print("  [OK] FileDeleter initialized")
        
        # Test delete_item with non-existent path
        success, msg = deleter.delete_item('C:/nonexistent/path')
        assert success == False
        print("  [OK] delete_item with non-existent path")
        
        return True
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test Config for bugs."""
    print("\nTesting Config...")
    try:
        from syscan_web.common.config import Config
        
        config = Config()
        print("  [OK] Config initialized")
        
        # Test get method
        val = config.get('scan', 'min_size_gb')
        assert val == 1
        print("  [OK] Config.get works")
        
        return True
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api():
    """Test API for bugs."""
    print("\nTesting API imports...")
    try:
        from syscan_web.server.app import create_app
        
        app = create_app()
        print("  [OK] Flask app created")
        
        # Test client
        with app.test_client() as client:
            # Test health endpoint
            resp = client.get('/health')
            assert resp.status_code == 200
            print("  [OK] /health endpoint works")
            
            # Test root endpoint
            resp = client.get('/')
            assert resp.status_code == 200
            print("  [OK] / endpoint works")
        
        return True
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Phase 1 Runtime Bug Test")
    print("=" * 60)
    
    results = []
    results.append(("Scanner", test_scanner()))
    results.append(("Analyzer", test_analyzer()))
    results.append(("Deleter", test_deleter()))
    results.append(("Config", test_config()))
    results.append(("API", test_api()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status:10} {name}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
