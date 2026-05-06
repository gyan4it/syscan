#!/usr/bin/env python
"""
Phase 1 Code Review Script
Checks all Python files for syntax errors, bugs, and issues.
"""

import py_compile
import os
import sys

def check_syntax(filepath):
    """Check a Python file for syntax errors."""
    try:
        py_compile.compile(filepath, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("Phase 1 Code Review - Syntax Check")
    print("=" * 60)
    
    base_path = r"C:\Users\Gyan4\Desktop\SystemChecking\Git_Repository"
    
    files_to_check = [
        r"syscan_web\agent\scanner.py",
        r"syscan_web\agent\analyzer.py",
        r"syscan_web\agent\deleter.py",
        r"syscan_web\agent\utils.py",
        r"syscan_web\common\config.py",
        r"syscan_web\common\constants.py",
        r"syscan_web\server\api.py",
        r"syscan_web\server\websocket.py",
        r"syscan_web\server\app.py",
        r"syscan_web\__init__.py",
        r"syscan_web\agent\__init__.py",
        r"syscan_web\common\__init__.py",
        r"syscan_web\server\__init__.py",
        r"syscan_web\tests\test_agent.py"
    ]
    
    results = []
    for f in files_to_check:
        full_path = os.path.join(base_path, f)
        if os.path.exists(full_path):
            success, error = check_syntax(full_path)
            results.append((f, success, error))
        else:
            results.append((f, False, "File not found"))
    
    # Print results
    print("\nSyntax Check Results:")
    print("-" * 60)
    for filepath, success, error in results:
        status = "PASS" if success else "FAIL"
        print(f"{status:10} {filepath}")
        if error:
            # Extract just the relevant part of the error
            lines = error.split('\n')
            for line in lines[:3]:  # Show first 3 lines
                if line.strip():
                    print(f"           {line.strip()}")
    
    # Summary
    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
