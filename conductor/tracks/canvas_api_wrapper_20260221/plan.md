# Implementation Plan: Canvas API Wrapper

## Phase 1: Foundation & Base Client Implementation [checkpoint: 73e35c4]
- [x] **Task: Setup initial CanvasClient class and base GET method.** 223d8bc
    - [x] Write tests for `CanvasClient` initialization (handling missing credentials).
    - [x] Implement `CanvasClient` class with `BASE_URL` and `ACCESS_TOKEN` configuration.
    - [x] Write tests for the base `_get` method (handling successful and failing HTTP requests).
    - [x] Implement the base `_get` method using `requests.Session` for efficient connections.
- [x] **Task: Implement Automated Pagination Logic.** 88d0dbb
    - [x] Write tests for `_get_all` method (simulating multiple pages via `Link` headers).
    - [x] Implement the `_get_all` helper method to consolidate paginated results.
- [x] **Task: Conductor - User Manual Verification 'Phase 1: Foundation' (Protocol in workflow.md)** 73e35c4

## Phase 2: Core API Methods & Data Retrieval
- [x] **Task: Implement user and course retrieval methods.** 90ca69e
    - [ ] Write tests for `get_user_self` and `get_courses`.
    - [ ] Implement `get_user_self` and `get_courses` methods.
- [x] **Task: Implement enrollment and assignment retrieval methods.** 05cf8c4
    - [ ] Write tests for `get_enrollments` and `get_assignments`.
    - [ ] Implement `get_enrollments` and `get_assignments` methods.
- [ ] **Task: Conductor - User Manual Verification 'Phase 2: Core Methods' (Protocol in workflow.md)**

## Phase 3: Error Handling & Resilience
- [ ] **Task: Implement custom exception mapping.**
    - [ ] Write tests for error handling (handling 401, 403, 404, and 500 status codes).
    - [ ] Implement custom exception classes (e.g., `CanvasAuthError`, `CanvasNotFoundError`) and mapping logic.
- [ ] **Task: Implement timeout and basic retry logic.**
    - [ ] Write tests for network timeouts and retries.
    - [ ] Implement configurable timeouts and a simple retry mechanism for 5xx errors.
- [ ] **Task: Conductor - User Manual Verification 'Phase 3: Error Handling' (Protocol in workflow.md)**

## Phase 4: Refactoring and Integration
- [ ] **Task: Refactor existing clever.py to use CanvasClient.**
    - [ ] Replace hardcoded API calls in `clever.py` with `CanvasClient` method calls.
    - [ ] Verify that current student info and course data are still correctly printed/processed.
- [ ] **Task: Conductor - User Manual Verification 'Phase 4: Integration' (Protocol in workflow.md)**

## Phase 5: Documentation and Cleanup
- [ ] **Task: Complete Docstrings and Final Cleanup.**
    - [ ] Ensure all public methods have clear, informative docstrings following Google or NumPy style.
    - [ ] Run final linting and type checks (if tools are available).
- [ ] **Task: Conductor - User Manual Verification 'Phase 5: Cleanup' (Protocol in workflow.md)**
