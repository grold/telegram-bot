# Enhanced Error Reporting Middleware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture and log all handler exceptions with full context (traceback, exception type) into the existing SQLite database and enhance the `/log` command to view them.

**Architecture:** Update `InteractionLoggingMiddleware` to wrap handler execution in a `try/except` block, storing the results in an expanded `logs` table.

**Tech Stack:** Python 3.13, aiogram 3, sqlite3

---

### Task 1: Update Database Schema

**Files:**
- Modify: `database.py`

- [ ] **Step 1: Add new columns to `init_db`**
Update `init_db()` in `database.py` to include `status`, `exception`, and `traceback` columns.
```python
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            ...
            status TEXT DEFAULT 'SUCCESS',
            exception TEXT,
            traceback TEXT
        )
    ''')
    # Migrations
    try:
        cursor.execute("ALTER TABLE logs ADD COLUMN status TEXT DEFAULT 'SUCCESS'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE logs ADD COLUMN exception TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE logs ADD COLUMN traceback TEXT")
    except sqlite3.OperationalError:
        pass
```

- [ ] **Step 2: Update `add_interaction_log` signature and implementation**
Update `add_interaction_log` to accept the new fields and insert them into the database.
```python
def add_interaction_log(..., status='SUCCESS', exception=None, traceback=None):
    # ... update INSERT statement ...
```

- [ ] **Step 3: Run migration/init**
Run `uv run python -c "from database import init_db; init_db()"` to verify the schema update.

- [ ] **Step 4: Commit**
```bash
git add database.py
git commit -m "feat(db): add status, exception, and traceback columns to logs table"
```

### Task 2: Enhance InteractionLoggingMiddleware

**Files:**
- Modify: `middlewares/command_logging.py`

- [ ] **Step 1: Add imports**
Ensure `traceback` and `sys` (if needed) are imported.

- [ ] **Step 2: Implement try/except block**
Wrap `result = await handler(event, data)` and capture details.
```python
        status = "SUCCESS"
        exception_name = None
        tb_text = None
        
        try:
            result = await handler(event, data)
        except Exception as e:
            status = "ERROR"
            exception_name = type(e).__name__
            tb_text = traceback.format_exc()
            raise e
        finally:
            # ... call add_interaction_log with status, exception_name, tb_text ...
```

- [ ] **Step 3: Commit**
```bash
git add middlewares/command_logging.py
git commit -m "feat(middleware): capture and log exceptions in InteractionLoggingMiddleware"
```

### Task 3: Update Log Viewer (/log)

**Files:**
- Modify: `handlers/log.py`
- Modify: `database.py` (update `get_recent_logs`)

- [ ] **Step 1: Update `get_recent_logs` for filtering**
Update `get_recent_logs` to support a `status` filter.
```python
def get_recent_logs(limit=10, query=None, status_filter=None):
    # ... update SQL to handle status_filter='ERROR' ...
```

- [ ] **Step 2: Update `cmd_log` handler**
Update parsing logic to detect "errors" keyword and use the new status filter.
```python
        if "errors" in args:
            status_filter = "ERROR"
            args.remove("errors")
        # ... fetch with status_filter ...
```

- [ ] **Step 3: Update log entry formatting**
Add emojis (✅/❌) and exception name to the output.
```python
            status_icon = "✅" if log['status'] == 'SUCCESS' else "❌"
            exc_display = f" | ⚠️ <b>{log['exception']}</b>" if log['exception'] else ""
            entry = (
                f"<b>{status_icon} {time_str} | 👤 {user_display}{role_display}{chat_display}{exc_display}</b>\n"
                f"📝 <i>{log['content']}</i> ({log['duration_ms']:.1f}ms){bot_ver}"
            )
```

- [ ] **Step 4: Commit**
```bash
git add handlers/log.py database.py
git commit -m "feat(log): add error status indicator and 'errors' filter to /log command"
```

### Task 4: Verification Tests

**Files:**
- Create: `tests/test_error_logging.py`

- [ ] **Step 1: Write integration test**
Create a test that uses a mock handler that raises an exception and verify the log entry.
```python
@pytest.mark.asyncio
async def test_middleware_logs_exception():
    # 1. Setup mock middleware and failing handler
    # 2. Call middleware
    # 3. Assert add_interaction_log was called with status='ERROR'
    # 4. Check DB for the entry
```

- [ ] **Step 2: Run tests**
Run `uv run pytest tests/test_error_logging.py`
Expected: PASS

- [ ] **Step 3: Commit**
```bash
git add tests/test_error_logging.py
git commit -m "test: add integration test for error capturing in middleware"
```
