# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clever Data Project — a Python utility that wraps the Canvas LMS API to automate retrieval and consolidation of student academic data (courses, enrollments, assignments, grades) for Broward Schools.

## Commands

**Run all tests:**
```bash
python -m pytest tests/
```

**Run a single test file:**
```bash
python -m unittest tests/test_canvas_client.py
```

**Run a single test case:**
```bash
python -m unittest tests.test_canvas_client.TestCanvasClient.test_get_success
```

**Lint:**
```bash
pylint canvas_client.py clever.py
```

**Run the main script:**
```bash
python clever.py
```

## Architecture

The project has two layers:

1. **`canvas_client.py` — reusable API client (`CanvasClient`)**
   - Handles authentication (Bearer token), retries (429/5xx via `urllib3.util.retry`), pagination (`_get_all` follows `Link: next` headers), and HTTP error mapping to typed exceptions (`CanvasAuthError`, `CanvasForbiddenError`, `CanvasNotFoundError`).
   - Public methods: `get_user_self()`, `get_courses()`, `get_enrollments(course_id)`, `get_assignments(course_id)`.
   - `_get()` — single-page fetch; `_get_all()` — auto-paginated fetch.

2. **`clever.py` — application script**
   - Instantiates `CanvasClient` with hardcoded `ACCESS_TOKEN` and `BASE_URL` for Broward Schools.
   - Orchestrates the data flow: authenticate → get courses → filter by term → get enrollments/assignments → write consolidated output to `combined_json` (a JSON file, gitignored).
   - Currently runs as a top-level script (no `main()` guard — a known deviation from the style guide).

Tests in `tests/test_canvas_client.py` use `unittest` with `unittest.mock.patch` on `requests.Session.get`.

## Code Style

Follows the Google Python Style Guide (`conductor/code_styleguides/python.md`):
- `snake_case` for functions/variables, `PascalCase` for classes, `ALL_CAPS` for constants.
- Max 80-char lines, 4-space indentation.
- Type annotations required on all public APIs.
- Docstrings with `Args:`, `Returns:`, `Raises:` sections on all public methods.
- Imports grouped: stdlib → third-party → local.
