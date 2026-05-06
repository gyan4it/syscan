# Contributing to SysScan

Thank you for considering contributing to SysScan! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating, you agree to maintain a respectful and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

- Use the **feedback form** (feedback.html) or open an issue
- Describe the bug clearly with steps to reproduce
- Include system info (OS, Python version, RAM)
- Attach logs if available

### Suggesting Enhancements

- Use the **feedback form** with type "Feature Request"
- Explain why this enhancement would be useful
- Consider the roadmap in README.md before suggesting

### Pull Requests

1. **Fork the repository** (if on GitHub)
2. **Create a branch** for your feature/fix
3. **Write clear commit messages**
4. **Test your changes** - Run with `--dry-run` before submitting
5. **Update documentation** if needed

## Development Setup

```bash
# Clone/download the project
cd SysScan

# Install dependencies (for feedback server)
pip install -r requirements.txt

# Run tests (if available)
python -m pytest tests/

# Test the scanner
python system_cleaner.py --dry-run
```

## Coding Guidelines

### Python Style
- Follow **PEP 8** style guide
- Use **4 spaces** for indentation
- Write **clear variable names** (no single letters except loops)
- Add **docstrings** for functions

### Example:
```python
def calculate_directory_size(path):
    """
    Calculate total size of a directory recursively.
    
    Args:
        path: Path to the directory
        
    Returns:
        Total size in bytes
    """
    total = 0
    try:
        for entry in os.scandir(path):
            # ... implementation
    except (PermissionError, OSError):
        pass
    return total
```

### Performance Considerations
- **Use os.scandir()** instead of os.walk() for speed
- **Avoid blocking calls** in parallel workers
- **Test with large directories** (>10GB) to ensure performance

## Testing

### Manual Testing Checklist:
- [ ] Run with `--dry-run` - No deletions occur
- [ ] Run without `--dry-run` - Deletions work correctly
- [ ] Test with various exclusions - System files not touched
- [ ] Test registry scan - Orphaned entries detected
- [ ] Test feedback form - Submissions stored in CSV

### Performance Testing:
```bash
# Time the scan
time python system_cleaner.py --dry-run

# Should complete in ~17 seconds for 200GB
```

## Documentation

- Update **README.md** for user-facing changes
- Update **docs/ARCHITECTURE.md** for design changes
- Add **docstrings** to new functions
- Update **CHANGELOG.md** (if exists) with your changes

## Project Structure

```
SysScan/
├── system_cleaner.py      # Main scanner (keep under 500 lines)
├── feedback_server.py      # Flask server for feedback
├── feedback.html          # User feedback form
├── README.md             # User documentation
├── LICENSE               # MIT License
├── requirements.txt      # Python dependencies
├── docs/
│   ├── ARCHITECTURE.md  # System design
│   └── API.md           # Internal API docs
└── tests/
    ├── test_scanner.py   # Unit tests
    └── test_performance.py # Benchmarks
```

## Review Process

1. **Automated checks** (if configured)
   - Linting (flake8/pylint)
   - Tests (pytest)
   - Format check (black)

2. **Manual review**
   - Code quality
   - Performance impact
   - Security considerations
   - Documentation updates

## Questions?

- Use the **feedback form** (feedback.html)
- Email: admin@systemchecking.com
- Check existing issues/feedback first

---

**Thank you for helping make SysScan better! 🙏**
