# Track Specification: Canvas API Wrapper

## Goal
Replace the current manual `requests` calls in `clever.py` with a clean, reusable `CanvasClient` class that handles authentication, pagination, and unified error handling.

## Scope
- Centralized configuration for `BASE_URL` and `ACCESS_TOKEN`.
- Automated pagination for all list-based API endpoints.
- Unified error handling that maps technical API errors to friendly, actionable messages.
- District-agnostic design with pre-configured defaults for Broward Schools.

## Acceptance Criteria
- [ ] `CanvasClient` class implements methods for `get_user_self`, `get_courses`, `get_enrollments`, and `get_assignments`.
- [ ] All methods correctly handle and flatten paginated responses using the Canvas `Link` header.
- [ ] API errors (e.g., 401 Unauthorized, 404 Not Found) are caught and re-raised as custom, friendly exceptions.
- [ ] Unit tests (using `unittest.mock` or `responses`) achieve >80% coverage for the new client.
- [ ] Existing functionality in `clever.py` is refactored to use the new `CanvasClient`.

## Tech Stack (Specific to Track)
- **Language:** Python
- **Libraries:** `requests`
- **Testing:** `unittest`, `pytest-cov`
