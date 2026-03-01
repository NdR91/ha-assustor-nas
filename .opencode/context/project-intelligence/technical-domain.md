<!-- Context: project-intelligence/technical | Priority: high | Version: 1.1 | Updated: 2026-03-01 -->

# Technical Domain

> Document the technical foundation, architecture, and key decisions.

## Primary Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Language | Python | 3.13+ | Home Assistant standard |
| Framework | Home Assistant Core | Latest | Target platform |
| Protocol | SNMP | v2c | Native NAS monitoring |
| Key Libraries | `pysnmp` | >=7.1.4 | Maintained SNMP library |

## Architecture Pattern

```
Type: Home Assistant Custom Integration
Pattern: DataUpdateCoordinator
```

### Why This Architecture?
The `DataUpdateCoordinator` pattern is the Home Assistant best practice for polling-based integrations. It centralizes data fetching, reduces network overhead, and ensures all entities are updated simultaneously with consistent data.

## Project Structure

```
[Project Root]
├── custom_components/ha_asustor_nas_custom_integration/
│   ├── api/                # SNMP Client logic
│   ├── coordinator/        # DataUpdateCoordinator implementation
│   ├── config_flow_handler/# UI Setup logic
│   ├── sensor.py           # Sensor entity definitions
│   └── const.py            # Constants and OIDs
├── docs/                   # Documentation (Functional Analysis)
├── .opencode/              # AI Agent context and standards
└── script/                 # HA development scripts
```

## Key Technical Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| `pysnmp` 7.x | Maintained, async support | Breaking changes in imports |
| `UCD-SNMP-MIB` | Accurate memory usage | Matches ADM UI |
| MAC as Unique ID | Stable hardware ID | Reliable device tracking |

## Integration Points

| System | Purpose | Protocol | Direction |
|--------|---------|----------|-----------|
| ASUSTOR NAS | Monitoring data | SNMP v2c | Inbound |

## Related Files

- `business-domain.md` - Why this technical foundation exists
- `business-tech-bridge.md` - How business needs map to technical solutions
- `decisions-log.md` - Full decision history with context
