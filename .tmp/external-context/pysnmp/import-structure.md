---
source: Context7 API / PySNMP Documentation
library: PySNMP
package: pysnmp
topic: Import Structure and Async Usage (v7.x)
fetched: 2026-03-01T12:00:00Z
official_docs: https://github.com/lextudio/pysnmp
---

# PySNMP 7.x Import Structure and Async Usage

## Correct Import Structure
In PySNMP 7.x (Lextudio fork), the high-level API (HLAPI) has been restructured. The error `cannot import name 'CommunityData' from 'pysnmp.hlapi'` occurs because these classes are no longer directly available in the `pysnmp.hlapi` namespace.

### Recommended Imports (Asyncio)
For Home Assistant and other async frameworks, use the `asyncio` sub-package:

```python
from pysnmp.hlapi.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    nextCmd
)
```

Alternatively, for the most modern "v3arch" implementation:
```python
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,  # PEP 8 name
    next_cmd  # PEP 8 name
)
```

## Breaking Changes (6.x to 7.x)
- **PEP 8 Renaming**: Method names have transitioned from camelCase to snake_case (e.g., `getCmd` -> `get_cmd`, `nextCmd` -> `next_cmd`).
- **Namespace Changes**: HLAPI components moved from `pysnmp.hlapi` to `pysnmp.hlapi.asyncio` or `pysnmp.hlapi.v3arch.asyncio`.
- **Transport Creation**: `UdpTransportTarget` may require `await UdpTransportTarget.create(('host', 161))` in some async contexts.

## Home Assistant Recommendations
- **Use Asyncio**: Always use `pysnmp.hlapi.asyncio` to avoid blocking the Home Assistant event loop.
- **Avoid Sync Calls**: Synchronous calls (`pysnmp.hlapi.v3arch.sync`) will trigger "blocking call in event loop" warnings and degrade performance.
- **Resource Cleanup**: Ensure `SnmpEngine` is closed when no longer needed to prevent resource leaks.

```python
# Example Async Usage
async def get_sys_descr():
    snmp_engine = SnmpEngine()
    try:
        error_indication, error_status, error_index, var_binds = await getCmd(
            snmp_engine,
            CommunityData('public'),
            UdpTransportTarget(('192.168.1.1', 161)),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
        )
        # Handle results...
    finally:
        snmp_engine.close()
```
