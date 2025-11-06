# Contributing

Thank you for your interest in contributing to `filetype-detector`! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python >= 3.8
- rye (recommended) or pip/venv
- Git

### Setting Up Development Environment

1. **Clone the repository**:
```bash
git clone <repository-url>
cd filetype-detector
```

2. **Install dependencies**:
```bash
rye sync
```

Or with pip:
```bash
pip install -e ".[dev]"
```

3. **Install system dependencies** (for MagicInferencer and CascadingInferencer):

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install libmagic1
```

**Fedora/RHEL/CentOS:**
```bash
sudo dnf install file-libs
# or: sudo yum install file-libs
```

**Arch Linux:**
```bash
sudo pacman -S file
```

**macOS:**
```bash
brew install libmagic
# or: sudo port install file
```

**Windows:**
```bash
pip install python-magic-bin
```

**Alpine Linux (Docker):**
```bash
apk add --no-cache file
```

**Verify installation:**
```bash
file --version
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with logging
pytest tests/ -v -s

# Run specific test file
pytest tests/test_magic_inferencer.py -v

# Run with coverage
pytest tests/ --cov=src/filetype_detector --cov-report=html
```

### Code Quality

**Linting**:
```bash
# Check lint errors (if configured)
ruff check src/ tests/
```

**Type Checking**:
```bash
mypy src/
```

### Building Documentation

```bash
mkdocs serve  # Local development server
mkdocs build  # Build static site
```

## Coding Standards

### Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Docstrings in numpy-style format
- Line length: 88 characters (Black default)

### Docstring Format

Use numpy-style docstrings:

```python
def infer(self, file_path: Union[Path, str]) -> str:
    """Infer the file format from a path.

    Parameters
    ----------
    file_path : Union[Path, str]
        Path to the file to analyze.

    Returns
    -------
    str
        File extension with leading dot.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
```

### Naming Conventions

- Classes: `PascalCase` (e.g., `MagicInferencer`)
- Functions/Methods: `snake_case` (e.g., `infer`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `FILE_FORMAT_INFERENCER_MAP`)

## Adding New Features

### Adding a New Inferencer

1. **Create inferencer class**:
```python
from filetype_detector.base_inferencer import BaseInferencer

class MyInferencer(BaseInferencer):
    def infer(self, file_path: Union[Path, str]) -> str:
        # Implementation
        return ".ext"
```

2. **Add to inferencer map** (optional):
```python
# In inferencer.py
from .my_inferencer import MyInferencer

FILE_FORMAT_INFERENCER_MAP["my_inferencer"] = lambda path: MyInferencer().infer(path)
```

3. **Update type definitions**:
```python
InferencerType = Union[Literal["magika", "magic", "my_inferencer"], None]
```

4. **Write tests**:
```python
# tests/test_my_inferencer.py
class TestMyInferencer:
    def test_basic_functionality(self):
        # Test implementation
        pass
```

5. **Update documentation**:
   - Add to README.md
   - Create API documentation in `docs/api/`
   - Add examples to `docs/examples.md`

### Adding Tests

Follow existing test patterns:

1. **Use fixtures** from `conftest.py`
2. **Mock external dependencies** when appropriate
3. **Test error cases** (FileNotFoundError, ValueError, RuntimeError)
4. **Use loguru** for test logging
5. **Include docstrings** explaining what each test does

Example:
```python
def test_infer_with_string_path(self, sample_text_file):
    """Test inferring extension from string path."""
    logger.debug(f"Testing with file: {sample_text_file}")
    inferencer = MagicInferencer()
    extension = inferencer.infer(str(sample_text_file))
    logger.success(f"Result: {extension}")
    assert extension == ".txt"
```

## Commit Guidelines

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Build/tooling changes

**Example:**
```
feat(inferencer): add CustomInferencer class

Implements a new inferencer that uses custom detection logic.
Includes tests and documentation updates.

Closes #123
```

## Pull Request Process

1. **Create a branch**:
```bash
git checkout -b feature/my-feature
```

2. **Make changes**:
   - Write code
   - Add tests
   - Update documentation
   - Ensure all tests pass

3. **Commit changes**:
```bash
git add .
git commit -m "feat: add new feature"
```

4. **Push and create PR**:
```bash
git push origin feature/my-feature
```

5. **PR Checklist**:
   - [ ] All tests pass
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] No lint errors
   - [ ] Commit messages follow conventions

## Documentation

### Updating Documentation

1. **Markdown files** in `docs/` directory
2. **API docs** auto-generated from docstrings
3. **Examples** in `docs/examples.md`
4. **README.md** for GitHub overview

### Adding API Documentation

When adding new classes/methods:
1. Add numpy-style docstrings
2. Include examples in docstrings
3. Update relevant markdown files in `docs/api/`

## Testing Strategy

### Unit Tests
- Mock external dependencies
- Test individual methods
- Fast execution

### Integration Tests
- Use real files (via fixtures)
- Test end-to-end flows
- Verify actual detection accuracy

### Test Coverage

Aim for high test coverage:
- All public methods tested
- Error cases covered
- Edge cases handled

## Questions?

If you have questions:
1. Check existing documentation
2. Review existing code for patterns
3. Open an issue for discussion

Thank you for contributing! 🎉

