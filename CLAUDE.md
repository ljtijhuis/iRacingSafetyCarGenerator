# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run application
cd src && python main.py              # Normal mode
cd src && python main.py -dev         # Developer mode (extra GUI panel)
cd src && python main.py -dev -dwi    # Cross-platform dev (no Windows automation)

# Tests
pytest                                # Run all tests
pytest -v                             # Verbose
pytest -k test_name                   # Run specific test by name
pytest src/core/detection/tests/      # Run tests in a directory
pytest --cov                          # With coverage

# Build
python build.py                       # Create Windows executable via PyInstaller
```

## Context

Read these files for full project context:

- `.ai-context.md` — Patterns, conventions, testing requirements, extension points, gotchas, and post-implementation checklist
- `.ai-modules.md` — Module-by-module reference with responsibilities and dependencies
- `ARCHITECTURE.md` — Full system design documentation
- `docs/RACING_CONCEPTS.md` — Racing domain terminology
