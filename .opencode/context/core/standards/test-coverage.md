<!-- Context: standards/tests | Priority: critical | Version: 2.0 | Updated: 2025-01-21 -->

# Test Coverage Standards (Home Assistant Custom Integration)

## Quick Reference

**Golden Rule**: Only write tests when explicitly requested by the developer.

**Test Structure**:
- `tests/` mirrors `custom_components/ha_asustor_nas_custom_integration/` structure.
- Use fixtures for common setup (Home Assistant mock, coordinator, etc.).
- Mock external API calls.

**Running Tests**:
```bash
script/test                           # All tests
script/test --cov-html                # With coverage report
script/test --snapshot-update         # Update Syrupy snapshots
```

---

## Principles

**Test Isolation**: Tests should not depend on external services or network calls.
**Mocking**: Mock the API client, not the Coordinator or Home Assistant Core.
**Fixtures**: Use `pytest` fixtures to set up the Home Assistant instance and configuration entries.

## Test Structure

```python
"""Test sensor platform."""

import pytest

from custom_components.ha_asustor_nas_custom_integration.sensor import async_setup_entry

@pytest.mark.unit
async def test_sensor_setup(hass, config_entry, coordinator):
    """Test sensor platform setup."""
    # Test implementation
```

## Mocking External APIs

- Use `aioresponses` or `pytest-httpx` to mock HTTP requests.
- Ensure all API endpoints used by the integration are mocked.
- Test both successful responses and error conditions (e.g., timeouts, 500 errors).

## Home Assistant Fixtures

- Use the `hass` fixture provided by `pytest-homeassistant-custom-component`.
- Create a `config_entry` fixture to simulate a configured integration.
- Use `async_fire_time_changed` to simulate time passing for coordinator updates.

## Testing Coordinator

- Test that the coordinator fetches data correctly.
- Test that the coordinator handles API errors gracefully (e.g., raises `UpdateFailed`).
- Test that the coordinator updates entities when data changes.

## Testing Entities

- Test that entities are created with the correct attributes (name, unique_id, state, etc.).
- Test that entities update their state when the coordinator data changes.
- Test that entities handle unavailability correctly.

## Testing Config Flow

- Test the user step (successful configuration, invalid credentials, etc.).
- Test discovery steps (e.g., zeroconf, ssdp) if applicable.
- Test reauth and reconfigure flows.

## Best Practices

✅ Mock external API calls.
✅ Use `pytest` fixtures for setup.
✅ Test both success and error paths.
✅ Verify entity attributes and state updates.
✅ Test config flow steps thoroughly.

**Golden Rule**: Only write tests when explicitly requested by the developer.