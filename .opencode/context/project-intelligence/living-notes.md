<!-- Context: project-intelligence/notes | Priority: high | Version: 1.1 | Updated: 2026-03-01 -->

# Living Notes

> Active issues, technical debt, open questions, and insights that don't fit elsewhere. Keep this alive.

## Quick Reference

- **Purpose**: Capture current state, problems, and open questions
- **Update**: Weekly or when status changes
- **Archive**: Move resolved items to bottom with status

## Technical Debt

| Item | Impact | Priority | Mitigation |
|------|--------|----------|------------|
| `pysnmp` 7.x Migration | Integration broken due to import changes | High | Refactor `AsustorNasApiClient` to use `v3arch.asyncio` |
| Blocking I/O in Event Loop | HA stability warnings | High | Ensure all SNMP calls and MIB loading are handled correctly |

### Technical Debt Details

**`pysnmp` 7.x Migration**  
*Priority*: High  
*Impact*: Integration fails to load or connect.  
*Root Cause*: `pysnmp` 7.x removed synchronous HLAPI and restructured namespaces.  
*Proposed Solution*: Use `pysnmp.hlapi.v3arch.asyncio` and `snake_case` methods.  
*Effort*: Medium  
*Status*: In Progress

## Open Questions

| Question | Stakeholders | Status | Next Action |
|----------|--------------|--------|-------------|
| Best way to handle MIB loading blocking? | Developer | Resolved | Hybrid Async Pattern implemented |

## Known Issues

| Issue | Severity | Workaround | Status |
|-------|----------|------------|--------|
| Raw CPU Entity ID | Low | None | Pending (Needs mapping) |
| Icon Refinement | Low | None | Pending |

### Issue Details

**Raw CPU Entity ID**  
*Severity*: Low  
*Impact*: One sensor shows a long alphanumeric ID instead of a friendly name.  
*Root Cause*: Dynamic sensor creation uses raw SNMP index/value for naming.  
*Fix Plan*: Implement a mapping or cleaner naming logic for CPU identifiers.  
*Status*: Pending

**Icon Refinement**  
*Severity*: Low  
*Impact*: Visual consistency.  
*Fix Plan*: Review and update `icon` attributes in `sensor.py`.  
*Status*: Pending

## Insights & Lessons Learned

### What Works Well
- **Vibecoding with OpenCode** - Rapid prototyping and architecture definition.
- **SNMP for Monitoring** - Reliable and lightweight for NAS hardware.

### What Could Be Better
- **Library Versioning** - `pysnmp` has a complex history and breaking changes in 7.x.

## Active Projects

| Project | Goal | Owner | Timeline |
|---------|------|-------|----------|
| ASUSTOR NAS Integration | V1 Monitoring | @NdR91 | Alpha (v0.1.0-alpha) |

## Archive (Resolved Items)

### Resolved: pysnmp 7.x Migration & Event Loop Blocking
- **Resolved**: 2026-03-02
- **Resolution**: Refactored `AsustorNasApiClient` to use `pysnmp.hlapi.v3arch.asyncio` inside `hass.async_add_executor_job` with `asyncio.run()`. This ensures MIB loading doesn't block the event loop while using the latest async-capable library.
- **Learnings**: `pysnmp` 7.x `next_cmd` returns a list of results when awaited, not an async iterator. Result keys must use `str(name)` for pure numeric OIDs to match constants reliably.

### Resolved: Initial Architecture
- **Resolved**: 2026-03-01
- **Resolution**: Defined SNMP v2c, `pysnmp` library, and Coordinator pattern.
- **Learnings**: Standard Linux MIBs are better for memory calculation than enterprise MIBs.

## Related Files

- `decisions-log.md` - Past decisions that inform current state
- `business-domain.md` - Business context for current priorities
- `technical-domain.md` - Technical context for current state
- `business-tech-bridge.md` - Context for current trade-offs
