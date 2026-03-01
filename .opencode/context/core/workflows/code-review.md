<!-- Context: workflows/review | Priority: high | Version: 2.0 | Updated: 2025-01-21 -->

# Code Review Guidelines (Home Assistant Custom Integration)

## Quick Reference

**Golden Rule**: Ensure code adheres to Home Assistant Core standards and async patterns.

**Checklist**: Async I/O, Type Hints, Setup Failures, Service Registration, Diagnostics.

**Report Format**: Summary, Assessment, Issues (🔴🟡🔵), Positive Observations, Recommendations.

---

## Review Checklist

### Home Assistant Core Patterns
- [ ] **Async I/O**: No blocking calls (`time.sleep`, `requests`, `open`) in the event loop. Are they wrapped in `hass.async_add_executor_job`?
- [ ] **Callbacks**: Are event listeners and state change functions decorated with `@callback`?
- [ ] **Setup Failures**: Are `ConfigEntryNotReady` and `ConfigEntryAuthFailed` used correctly? (No manual logging of these errors).
- [ ] **Service Actions**: Are services registered in `async_setup()` (not `async_setup_entry()`)?
- [ ] **Diagnostics**: Is `async_redact_data()` used to hide sensitive information?
- [ ] **Constants**: Are `homeassistant.const` values used instead of hardcoded strings (e.g., `PERCENTAGE`, `UnitOfTime.HOURS`)?
- [ ] **Time**: Is `dt_util.utcnow().isoformat()` used for timestamps?

### Architecture
- [ ] **Coordinator Pattern**: Do entities read data from the Coordinator? (They must NEVER call the API directly).
- [ ] **Entity Setup**: Do entities inherit from both the platform base and `HomeAssistantAsustorNASCustomEntity`?
- [ ] **Unique IDs**: Are `_attr_unique_id` values formatted correctly (`{entry_id}_{key}`)?

### Code Quality (Python)
- [ ] **Type Hints**: Are all function parameters, return values, and class attributes typed?
- [ ] **File Size**: Are files kept under 400 lines?
- [ ] **Linting**: Does the code pass `script/check` (Ruff, Pyright)?
- [ ] **Imports**: Are imports ordered correctly (future, stdlib, 3rd party, HA core, local)?

### Testing (If applicable)
- [ ] Are external API calls mocked?
- [ ] Are HA fixtures (`hass`, `config_entry`) used correctly?

## Review Report Format

```markdown
## Code Review: {Feature/PR Name}

**Summary:** {Brief overview}
**Assessment:** Approve / Needs Work / Requires Changes

---

### Issues Found

#### 🔴 Critical (Must Fix)
- **File:** `custom_components/ha_asustor_nas_custom_integration/sensor.py:42`
  **Issue:** Blocking I/O in event loop (`requests.get`).
  **Fix:** Use `aiohttp` or wrap in `hass.async_add_executor_job`.

#### 🟡 Warnings (Should Fix)
- **File:** `custom_components/ha_asustor_nas_custom_integration/api.py:15`
  **Issue:** Missing type hints for return value.
  **Fix:** Add `-> dict[str, Any]:`

#### 🔵 Suggestions (Nice to Have)
- **File:** `custom_components/ha_asustor_nas_custom_integration/const.py:28`
  **Issue:** Hardcoded unit string.
  **Fix:** Import `PERCENTAGE` from `homeassistant.const`.

---

### Positive Observations
- ✅ Correct use of DataUpdateCoordinator.
- ✅ Proper error handling and exception raising.

---

### Recommendations
{Next steps, improvements, follow-up items}
```

## Common Issues

### Critical (🔴)
- Blocking I/O in the event loop.
- Entities calling the API directly instead of using the Coordinator.
- Missing `async_redact_data()` in diagnostics.
- Manual logging of setup failures (`ConfigEntryNotReady`).

### Warnings (🟡)
- Missing type hints.
- Missing `@callback` decorators.
- Hardcoded units or relative time strings.
- Registering services in `async_setup_entry()`.