<!-- Context: standards/code | Priority: critical | Version: 2.0 | Updated: 2025-01-21 -->
# Code Standards (Home Assistant Custom Integration)

## Quick Reference

**Core Philosophy**: Modular, Asynchronous, Type-Hinted, Home Assistant Core Patterns
**Golden Rule**: Entities read from Coordinator, NEVER call API directly.

**Critical Patterns** (use these):
- ✅ **Async Everything**: All I/O operations must be async (`aiohttp`, `asyncio`).
- ✅ **Type Annotations**: Required for all function parameters, return values, and class attributes.
- ✅ **Small Files**: 200-400 lines per file. One class per file when practical.
- ✅ **Coordinator Pattern**: Entities -> Coordinator -> API Client.
- ✅ **Setup Failures**: Raise `ConfigEntryNotReady` (offline) or `ConfigEntryAuthFailed` (expired auth). Do NOT log manually.

**Anti-Patterns** (avoid these):
- ❌ **Blocking I/O in Event Loop**: Never use `time.sleep()`, `requests`, or synchronous file operations without `hass.async_add_executor_job`.
- ❌ **Missing `@callback`**: Event listeners and state change callbacks must use `@callback` from `homeassistant.core`.
- ❌ **Hardcoded Units**: Always use constants from `homeassistant.const` (e.g., `PERCENTAGE`, `UnitOfTime.HOURS`).
- ❌ **Relative Time**: Always use UTC timestamps (`dt_util.utcnow().isoformat()`).

---

## Core Philosophy

**Modular**: Separate API client, Coordinator, Config Flow, and Entity Platforms.
**Asynchronous**: Non-blocking event loop is critical for Home Assistant performance.
**Maintainable**: Strict typing, linting (Ruff), and formatting.

## Principles

### File Structure
- `__init__.py` - Platform setup with `async_setup_entry()`
- Individual files - One class per file (e.g., `sensor/air_quality.py`)
- `const.py` - Module constants only (no logic)

**Naming:**
- Files: `snake_case.py`
- Classes: `PascalCase` prefixed with `HomeAssistantAsustorNASCustom`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Async Patterns
- `async def` for coroutines, `await` for async calls
- `asyncio.gather()` for concurrent operations
- `asyncio.timeout()` for timeouts (not `async_timeout`)
- **Blocking operations (NEVER in event loop):** `open()`, `os.listdir()`, `urllib`, `time.sleep()`.
  - **Must run in executor:** `await hass.async_add_executor_job(blocking_func)`

### Home Assistant Requirements
- **Service Actions**: Register in `async_setup()` (NOT `async_setup_entry()`). Format: `<integration_domain>.<action_name>`.
- **Event Names**: Prefix with integration domain: `<domain>_<event_name>`.
- **Diagnostics**: CRITICAL: Use `async_redact_data()` from `homeassistant.helpers.redact` to remove sensitive data (passwords, tokens).

### Entity Classes
- Inherit from both platform entity and `HomeAssistantAsustorNASCustomEntity` (order matters).
- Set `_attr_unique_id` in `__init__` (format: `{entry_id}_{key}`).
- Handle unavailability via `_attr_available`.

## Error Handling
- Use specific exceptions from the integration's exception module.
- **Logging levels:**
  - `_LOGGER.exception()` - Errors with full traceback (in exception handlers)
  - `_LOGGER.error()` - Errors affecting functionality
  - `_LOGGER.warning()` - Recoverable issues
  - `_LOGGER.debug()` - Detailed troubleshooting
- **Log message style:** No periods at end, never log credentials, use `%` formatting (Ruff G004).

## Validation
Run before submitting: `script/type-check`, `script/lint`, `script/test`
- Fix root cause - Don't bypass checks.
- **Suppressing checks (use sparingly):** Specific suppression only (`# noqa: F401 - Reason`). Never use blanket `# noqa`.