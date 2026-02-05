# Contributing to iRacing Safety Car Generator

Thank you for your interest in contributing to the iRacing Safety Car Generator! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Project-Specific Guidelines](#project-specific-guidelines)
- [Resources](#resources)

## Getting Started

### Prerequisites

- Python 3.13 or higher
- Git for version control
- (Optional) Windows OS for full testing with iRacing integration
- (Optional) iRacing subscription for end-to-end testing

### Development Environment Setup

1. **Clone the repository:**
   ```bash
   git clone git@github.com:joshjaysalazar/iRacingSafetyCarGenerator.git
   cd iRacingSafetyCarGenerator
   ```

2. **Set up Python virtual environment:**
   ```bash
   python -m venv myenv

   # Activate virtual environment
   # On Windows:
   myenv\Scripts\activate
   # On macOS/Linux:
   source myenv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt      # Production dependencies
   pip install -r requirements-dev.txt  # Development dependencies (pytest, etc.)
   ```

4. **Run the application:**
   ```bash
   cd src
   python main.py                       # Normal mode
   python main.py -dev                  # Developer mode (extra GUI panel)
   python main.py -dev -dwi             # Cross-platform dev (no Windows automation)
   ```

5. **Run tests:**
   ```bash
   pytest                               # Run all tests
   pytest -v                            # Verbose output
   pytest -k test_name                  # Run specific test
   pytest --cov                         # With coverage report
   ```

### First Contribution Checklist

Before making your first contribution:

- [ ] Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand system design and patterns
- [ ] Read [.ai-context.md](.ai-context.md) to understand critical coding patterns
- [ ] Check [existing issues](https://github.com/joshjaysalazar/iRacingSafetyCarGenerator/issues) to avoid duplicates
- [ ] Set up your development environment and verify tests pass
- [ ] Familiarize yourself with the [Pull Request Process](#pull-request-process)

## Code Standards

### Python Style

Follow [PEP 8](https://pep8.org/) style guidelines with the following specifics:

**Naming Conventions:**
- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants and Enums: `UPPER_CASE`
- Private methods: `_leading_underscore`
- Factory functions: `function_name_factory` suffix

**Type Hints:**
- Always use type hints for function parameters and return values
- Use TypedDict for data models (see `Driver` in `src/core/drivers.py`)
- Use dataclasses for configuration objects (frozen=True for immutability)

Example:
```python
from typing import TypedDict
from dataclasses import dataclass

class Driver(TypedDict):
    driver_idx: int
    car_number: str
    lap_distance: float

@dataclass(frozen=True)
class Settings:
    max_events: int = 5
    threshold: float = 2.0

def calculate_distance(driver: Driver, multiplier: float) -> float:
    """Calculate total distance with multiplier.

    Args:
        driver: Driver data with lap information
        multiplier: Distance multiplier

    Returns:
        Calculated total distance
    """
    return driver["lap_distance"] * multiplier
```

**Docstrings:**
- Use Google-style docstrings for all public functions and classes
- Include Args and Returns sections
- Keep docstrings concise but informative

**Logging:**
- Use per-module loggers: `logger = logging.getLogger(__name__)`
- Choose appropriate log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages (state changes, events)
  - `WARNING`: Unexpected behavior that doesn't stop execution
  - `ERROR`: Errors that affect functionality
  - `EXCEPTION`: Exceptions with stack traces

Example:
```python
import logging
logger = logging.getLogger(__name__)

def process_driver(driver: Driver):
    logger.debug(f"Processing driver {driver['car_number']}")
    try:
        # ... processing logic
        logger.info(f"Successfully processed driver {driver['car_number']}")
    except Exception as e:
        logger.exception(f"Error processing driver {driver['car_number']}: {e}")
```

### Critical Design Patterns

The project uses several design patterns that must be followed:

**1. State Machine Pattern** (src/core/app.py, src/core/generator.py)
- Always use property setters for state transitions
- State changes trigger automatic GUI updates

**2. Double-Buffering Pattern** (src/core/drivers.py)
- Maintains current and previous driver data
- Enables delta detection (e.g., stopped cars)

**3. Protocol Pattern** (src/core/detection/)
- Use `SupportsDetect` protocol for new detectors
- Enables loose coupling and testability

**4. Factory Pattern** (src/core/interactions/, src/core/procedures/)
- Use factories for platform-specific implementations
- Enables cross-platform development

See [.ai-context.md](.ai-context.md) for detailed explanations and examples.

## Testing Requirements

### Test Coverage Expectations

- **New Features:** Aim for >80% code coverage
- **Bug Fixes:** Include regression test demonstrating the fix
- **Refactoring:** Ensure all existing tests still pass

### Test Organization

Tests are co-located with source code in `tests/` subdirectories:

```
src/core/
├── module.py
└── tests/
    ├── test_module.py
    └── test_module_integration.py
```

### Writing Tests

**Use common test utilities:**

```python
from core.tests.test_utils import make_driver, dict_to_config

def test_stopped_detector():
    # Create test driver with specific properties
    stopped_driver = make_driver(
        driver_idx=1,
        car_number="42",
        laps_completed=10,
        lap_distance=0.5
    )

    # Use in test
    assert stopped_driver["car_number"] == "42"
```

**Mock iRacing SDK calls:**

```python
def test_with_sdk(mocker):
    # Mock time for deterministic tests
    mocker.patch("time.time", return_value=1000.0)

    # Mock SDK instance
    mock_ir = mocker.Mock()
    mock_ir["CarIdxLap"] = [0, 10, 11, 9]
    mock_ir["CarIdxLapDistPct"] = [0.0, 0.5, 0.75, 0.25]

    # Use in test
    drivers = Drivers()
    drivers.update(mock_ir)
```

**Test naming convention:**
```python
def test_detector_detects_stopped_car():  # What it does
def test_threshold_met_with_proximity():   # Condition being tested
def test_random_detector_outside_window(): # Specific scenario
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest src/core/tests/test_generator.py

# Run specific test
pytest -k test_stopped_detector

# Run with coverage
pytest --cov

# Watch mode (requires pytest-watch)
ptw
```

All tests must pass before submitting a pull request.

## Commit Messages

### Format

Use conventional commit format:

```
<type>: <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no functional changes)
- `test`: Adding or modifying tests
- `docs`: Documentation changes
- `chore`: Maintenance tasks (dependencies, build scripts)
- `perf`: Performance improvements
- `style`: Code style changes (formatting, no functional changes)

### Examples

```
feat: Add proximity-based yellow flag clustering

Implements proximity clustering algorithm to group nearby incidents.
Only the largest cluster is evaluated against thresholds, preventing
scattered minor incidents from triggering false positives.

Closes #123
```

```
fix: Prevent double-counting drivers in threshold checker

Previously, the same driver could be counted multiple times if detected
in consecutive frames. Now tracks per-driver counts to ensure each
driver is only counted once per event type within the time window.

Fixes #456
```

```
docs: Update ARCHITECTURE.md with threshold checker algorithm
```

### Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Fix bug" not "Fixes bug")
- First line should be ≤72 characters
- Reference issues/PRs in footer (Closes #123, Fixes #456)
- Explain *what* and *why*, not *how* (code shows how)

## Pull Request Process

### Before Submitting

1. **Create an issue first** for non-trivial changes
   - Discuss the proposed change
   - Get feedback on approach
   - Avoid wasted effort on rejected changes

2. **Create a feature branch**
   ```bash
   git checkout -b feature/descriptive-name
   # or
   git checkout -b fix/issue-description
   ```

3. **Make your changes**
   - Follow code standards
   - Add tests
   - Update documentation

4. **Run tests locally**
   ```bash
   pytest
   ```

5. **Commit your changes**
   - Use conventional commit format
   - Make logical, atomic commits

### Submitting the PR

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub**
   - Use the PR template
   - Fill out all sections:
     - Description of changes
     - Type of change (feature, fix, etc.)
     - Testing performed
     - Related issues
   - Add appropriate labels

3. **PR Checklist** (from template):
   - [ ] Code follows project style guidelines
   - [ ] Self-review performed
   - [ ] Code commented where necessary
   - [ ] Documentation updated
   - [ ] No new warnings generated
   - [ ] Tests added/updated
   - [ ] All tests pass locally
   - [ ] Updated .ai-context.md if adding new patterns
   - [ ] Updated ARCHITECTURE.md if changing system design
   - [ ] Updated .ai-modules.md if adding new modules

### Review Process

1. **Automated checks** will run (tests, linting)
2. **Code review** by maintainers
   - Address all review comments
   - Push additional commits to the same branch
3. **Approval and merge** by maintainer

### After Merge

- Delete your feature branch (via GitHub UI or locally)
- Pull the updated main branch

## Project-Specific Guidelines

### Adding a New Detector

See [ARCHITECTURE.md - Extension Points](ARCHITECTURE.md#adding-a-new-detector) for detailed step-by-step guide.

**Key steps:**
1. Create detector file implementing `SupportsDetect` protocol
2. Add event type to `DetectorEventTypes` enum
3. Update `DetectorSettings` dataclass
4. Update `Detector.build_detector()`
5. Add threshold settings
6. Add GUI controls in `App`
7. Add settings properties in `Settings`
8. Create tests

**Remember:**
- Follow the protocol pattern
- Add comprehensive tests
- Update documentation

### Modifying Threshold Logic

**Before modifying threshold checker:**
- Understand the sliding time window algorithm
- Consider backward compatibility with existing settings
- Test with various scenarios (lag protection, proximity clustering)

**When modifying:**
- Update tests in `src/core/detection/tests/test_threshold_checker.py`
- Document algorithm changes in ARCHITECTURE.md
- Consider impact on existing safety car deployments

### GUI Changes

**Tkinter conventions:**
- Follow 3-column layout pattern
- Use grid layout manager consistently
- Update tooltips in `src/tooltips_text.json`
- Test UI responsiveness during generator operations

**State updates:**
- Always use `generator_state` property setter
- Never directly modify `_generator_state`
- Ensure GUI updates happen on main thread only

### Windows Automation

**Testing without Windows:**
- Use `-dwi` flag to enable mock implementations
- `MockSender` logs commands instead of sending
- `MockWindow` provides no-op window operations

**Testing with Windows:**
- Ensure iRacing is running and in focus
- Test timing delays (0.5s between commands)
- Verify chat commands actually work in-game

**Adding new commands:**
- Update `CommandSender.send_command()`
- Add appropriate timing delays
- Add mock equivalent in `MockSender`
- Test both real and mock implementations

## Resources

### Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design patterns
- [.ai-context.md](.ai-context.md) - Critical patterns and conventions
- [.ai-modules.md](.ai-modules.md) - Module quick reference
- [docs/RACING_CONCEPTS.md](docs/RACING_CONCEPTS.md) - Racing terminology

### External Resources

- [iRacing SDK Documentation](https://sajax.github.io/irsdkdocs/yaml) - Official SDK docs
- [pyirsdk Library](https://github.com/kutu/pyirsdk) - Python iRacing SDK wrapper
- [pyirsdk Tutorials](https://github.com/kutu/pyirsdk/tree/master/tutorials) - SDK usage examples
- [PEP 8](https://pep8.org/) - Python style guide
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message convention

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/joshjaysalazar/iRacingSafetyCarGenerator/issues)
- **Discussions:** Use GitHub Discussions for questions and ideas
- **Pull Requests:** Reference related issues in your PR description

### Project Maintainers

- [Joshua Abbott Salazar](https://github.com/joshjaysalazar) - Project Creator

---

## Thank You!

Your contributions help make this project better for the iRacing community. Whether you're fixing bugs, adding features, improving documentation, or helping with testing, your efforts are greatly appreciated!
