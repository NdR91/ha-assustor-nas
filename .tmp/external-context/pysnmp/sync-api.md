---
source: PySNMP 7.1 Official Documentation
library: PySNMP
package: pysnmp
topic: Synchronous API and 7.x Imports
fetched: 2026-03-01
official_docs: https://www.pysnmp.com/pysnmp/docs/api-reference.html
---

# PySNMP 7.x Synchronous API Status

In PySNMP 7.x (and since version 6.2), the **official synchronous high-level API has been removed**. It was briefly introduced in 6.0 but found to be unstable as a wrapper around the new asyncio core.

## Recommended Usage in 7.x
The standard for 7.x is the **asyncio-based High-Level API (hlapi)**. For synchronous-like behavior, you should use `asyncio.run()` to execute the async commands.

### Correct Import Statements (v3arch)
The `v3arch` (Version 3 Architecture) is the modern standard supporting SNMPv1, v2c, and v3.

```python
import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    get_cmd,   # Standard PEP 8 name in 7.x
    next_cmd   # Standard PEP 8 name in 7.x
)
```

*Note: The old camelCase names (`getCmd`, `nextCmd`) are deprecated in 7.x and may be removed in 8.0.*

### Synchronous Wrapper Example (7.x)
Since `UdpTransportTarget.create()` is now an async method in 7.1+, you must await it.

```python
import asyncio
from pysnmp.hlapi.v3arch.asyncio import *

async def run_get():
    snmp_engine = SnmpEngine()
    # In 7.1+, transport target creation is async
    transport = await UdpTransportTarget.create(('demo.pysnmp.com', 161))
    
    error_indication, error_status, error_index, var_binds = await get_cmd(
        snmp_engine,
        CommunityData('public'),
        transport,
        ContextData(),
        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
    )

    if error_indication:
        print(error_indication)
    elif error_status:
        print(f"{error_status.prettyPrint()} at {error_index and var_binds[int(error_index) - 1][0] or '?'}")
    else:
        for var_bind in var_binds:
            print(' = '.join([x.prettyPrint() for x in var_bind]))
            
    snmp_engine.close_dispatcher()

# Run synchronously
asyncio.run(run_get())
```

## v3arch vs v1arch
- **v3arch**: Full implementation of SNMPv3 architecture. Supports v1, v2c, and v3. This is the **standard** for most use cases.
- **v1arch**: Simplified architecture for SNMPv1 and v2c only. It is also `asyncio` based in 7.x.

## Key Changes in 7.x
1. **PEP 8 Renaming**: Most functions and classes now use `snake_case` (e.g., `get_cmd` instead of `getCmd`).
2. **Async Transport**: `UdpTransportTarget.create()` must be awaited.
3. **Module Path**: Imports are now under `pysnmp.hlapi.v3arch.asyncio` or `pysnmp.hlapi.v1arch.asyncio`.
