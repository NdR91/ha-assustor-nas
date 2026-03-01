<!-- Context: project-intelligence/decisions | Priority: high | Version: 1.1 | Updated: 2026-03-01 -->

# Decisions Log

> Record major architectural and business decisions with full context. This prevents "why was this done?" debates.

## Decision: Use `pysnmp` 7.x (Lextudio)

**Date**: 2026-03-01
**Status**: Decided
**Owner**: @NdR91 / OpenCode

### Context
The original `pysnmp` library was unmaintained. The `pysnmp-lextudio` fork was the standard for a while but has now been merged back into the main `pysnmp` package (v7.x). Home Assistant requires non-blocking I/O.

### Decision
Use `pysnmp>=7.1.4` and its `asyncio`-based high-level API (`v3arch.asyncio`).

### Rationale
- Version 7.x is the officially maintained version.
- It supports `asyncio` natively.
- It is compatible with Python 3.13.

### Alternatives Considered
| Alternative | Pros | Cons | Why Rejected? |
|-------------|------|------|---------------|
| `pysnmp-lextudio` | Familiar | Deprecated | Merged into main `pysnmp`. |
| `snmpit` | Simple | Less feature-rich | `pysnmp` is the industry standard. |

### Impact
- **Positive**: Long-term maintainability, native async support.
- **Negative**: Breaking changes in imports and method names compared to 6.x.
- **Risk**: MIB loading might still block the event loop if not handled carefully.

---

## Decision: Memory Calculation via `UCD-SNMP-MIB`

**Date**: 2026-03-01
**Status**: Decided
**Owner**: @NdR91 / OpenCode

### Context
The ASUSTOR Enterprise MIB only exposes "Free" memory, which is misleading on Linux as it doesn't account for Buffers/Cache. The ADM UI shows "Utilization" which excludes these.

### Decision
Use standard Linux `UCD-SNMP-MIB` (`1.3.6.1.4.1.2021.4`) to fetch Total, Free, Buffers, and Cached memory.
Formula: `Used = Total - (Free + Buffers + Cached)`.

### Rationale
Matches the user experience in the ADM Activity Monitor.

---

## Decision: Unique ID via MAC Address

**Date**: 2026-03-01
**Status**: Decided
**Owner**: @NdR91 / OpenCode

### Context
ASUSTOR NAS devices do not reliably expose a Serial Number via SNMP. Home Assistant needs a stable `unique_id`.

### Decision
Use the MAC address of the first valid network interface found via `IF-MIB` (`1.3.6.1.2.1.2.2.1.6`).

### Rationale
MAC addresses are stable hardware identifiers.

---

## Related Files
- `technical-domain.md` - Technical implementation affected by these decisions
- `living-notes.md` - Current open questions that may become decisions
