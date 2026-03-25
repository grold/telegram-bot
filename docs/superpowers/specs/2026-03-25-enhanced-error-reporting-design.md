# Design Specification: Enhanced Error Reporting Middleware

**Date:** 2026-03-25  
**Topic:** Infrastructure & Reliability  
**Status:** Approved

## 1. Overview
This project enhances the bot's reliability by integrating error capturing directly into the interaction logging middleware. This ensures that every failure is recorded with full user and chat context, enabling faster debugging and better visibility through the existing `/log` command.

## 2. Technical Design

### 2.1 Database Schema Changes (`database.py`)
Update the `logs` table to include the following columns:
- `status`: `TEXT` (Default: 'SUCCESS', Options: 'SUCCESS', 'ERROR')
- `exception`: `TEXT` (Store the exception class name)
- `traceback`: `TEXT` (Full Python traceback)

**Migration Plan:**
Add `ALTER TABLE` statements to `init_db()` to ensure these columns exist in existing installations.

### 2.2 Middleware Enhancement (`middlewares/command_logging.py`)
Modify `InteractionLoggingMiddleware` to capture errors:
- Wrap `await handler(event, data)` in a `try/except` block.
- Capture `type(e).__name__` and `traceback.format_exc()` on failure.
- Ensure `add_interaction_log` is called in a `finally` block or on both paths to guarantee duration and status are always recorded.
- Re-raise the exception to maintain original bot behavior (e.g., showing a fallback message if configured).

### 2.3 Log Viewer Update (`handlers/log.py`)
Enhance the `/log` command to leverage the new data:
- Add a visual indicator (e.g., ❌ for ERROR, ✅ for SUCCESS) in the log output.
- Add support for a `errors` filter (e.g., `/log errors` or `/log 20 errors`).
- (Future-proofing) Allow viewing the traceback for a specific log ID via a separate command or interactive button.

### 2.4 User Interface Enhancement
The log output will be updated to:
`📅 2026-03-25 10:00 | 👤 @user | ❌ ERROR: ValueError`
`📝 /weather non_existent_city (120.5ms) [🤖 0.6.1]`

## 3. Implementation Tasks
1. Update `database.py` with new schema and migration logic.
2. Refactor `middlewares/command_logging.py` to capture and re-raise exceptions.
3. Update `handlers/log.py` to display status and support the `errors` filter.
4. Add unit tests to verify error capturing in middleware.

## 4. Success Criteria
- Every exception raised within a handler is recorded in the `logs` table.
- `/log errors` successfully filters and displays only failed interactions.
- No regression in bot performance or duration tracking accuracy.
