"""
Unit tests for SysCan agent modules.
"""

import unittest
import os
import tempfile
import shutil

class TestScanner(unittest.TestCase):
    """Test GridScanner functionality."""

    def setUp(self):
        from syscan_web.agent import GridScanner
        self.scanner = GridScanner()

    def test_scanner_initialization(self):
        """Test scanner initializes with defaults."""
        self.assertIsNotNone(self.scanner)
        self.assertEqual(len(self.scanner.excludes), 13)
        self.assertGreater(len(self.scanner.specific_paths), 0)

    def test_size_format(self):
        """Test size formatting utility."""
        from syscan_web.agent.utils import format_size
        self.assertIn('GB', format_size(1024**3))  # 1 GB
        self.assertIn('MB', format_size(1024**2))  # 1 MB

    def test_exclusion_check(self):
        """Test path exclusion logic."""
        from syscan_web.agent.scanner import is_excluded
        self.assertTrue(is_excluded('C:/Users/Test/Documents', ['C:/Users/*/Documents']))
        self.assertFalse(is_excluded('C:/Users/Test/Projects', ['C:/Users/*/Documents']))

class TestAnalyzer(unittest.TestCase):
    """Test FileAnalyzer functionality."""

    def setUp(self):
        from syscan_web.agent import FileAnalyzer
        self.analyzer = FileAnalyzer()

    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer)

    def test_analyze_empty_items(self):
        """Test analysis with no items."""
        result = self.analyzer.analyze_items([])
        self.assertEqual(result['total_items'], 0)
        self.assertEqual(result['total_size_gb'], 0)

    def test_analyze_with_items(self):
        """Test analysis with sample items."""
        items = [('C:/test/path1', 2 * 1024**3), ('C:/test/path2', 1.5 * 1024**3)]
        result = self.analyzer.analyze_items(items)
        self.assertEqual(result['total_items'], 2)
        self.assertGreater(result['total_size_gb'], 3)

class TestDeleter(unittest.TestCase):
    """Test FileDeleter functionality."""

    def setUp(self):
        from syscan_web.agent import FileDeleter
        self.deleter = FileDeleter()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_deleter_initialization(self):
        """Test deleter initializes correctly."""
        self.assertIsNotNone(self.deleter)

    def test_delete_nonexistent_file(self):
        """Test deleting non-existent file returns error."""
        success, message = self.deleter.delete_item('C:/nonexistent/path')
        self.assertFalse(success)

    def test_send_to_recycle_bin(self):
        """Test recycle bin functionality (requires Windows)."""
        # Create a test file
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')

        # Try to send to recycle bin (Windows only)
        if os.name == 'nt':
            result = self.deleter.send_to_recycle_bin(test_file)
            self.assertTrue(result)
        else:
            print("Skipping recycle bin test (Windows only)")

if __name__ == '__main__':
    unittest.main()
