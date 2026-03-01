# Functional Analysis: ASUSTOR NAS SNMP Integration

## 1. Overview
This document outlines the functional and technical requirements for the Home Assistant Custom Integration dedicated to monitoring ASUSTOR NAS devices via SNMP v2c.

**Integration Domain**: `ha_asustor_nas_custom_integration`
**Target**: ASUSTOR NAS (ADM OS)
**Protocol**: SNMP v2c (Read-only)

## 2. Architecture
The integration strictly follows Home Assistant Core patterns:
- **Config Flow**: UI-based configuration (No YAML).
- **DataUpdateCoordinator**: Centralized asynchronous polling to minimize network requests and ensure data consistency across all entities.
- **Dynamic Entities**: Entities are generated dynamically based on the SNMP tables discovered on the target device.

## 3. Configuration (Config Flow)
**User Inputs**:
- `host`: IP Address or Hostname
- `port`: SNMP Port (Default: 161)
- `community`: SNMP v2c Community String (Default: public)
- `scan_interval`: Polling frequency in seconds (Default: 300)

**Validation**:
During setup, the integration will perform an SNMP GET request to the NAS Model OID (`1.3.6.1.4.1.44738.2.1.0`). 
- Success: Proceeds to create the entry.
- Failure: Raises `ConfigEntryNotReady` or `InvalidAuth`.

**Unique ID**:
- Target: NAS MAC Address (via `IF-MIB::ifPhysAddress.2` or the first valid MAC address found).
- Fallback: Host IP (Not recommended, but fallback if SNMP doesn't expose unique hardware IDs).

## 4. Data Mapping (SNMP OIDs)
Base Enterprise OID: `1.3.6.1.4.1.44738.2`

### 4.1 Static Sensors (Scalars)
| Name | OID | Type | Processing |
| :--- | :--- | :--- | :--- |
| NAS Model | `...2.1.0` | String | Direct mapping |
| CPU Model | `...2.2.0` | Hex-String | Decode Hex to UTF-8 |

### 4.2 Dynamic Sensors (Tables)
The Coordinator will perform SNMP WALK/BULK operations on the following branches to discover available indices.

| Category | Base OID | HA Device Class | HA State Class | Unit |
| :--- | :--- | :--- | :--- | :--- |
| CPU Core Usage | `...2.3.1.2.*` | None | `measurement` | `%` |
| Fan RPM | `...2.4.1.2.*` | None | `measurement` | `RPM` |
| Temperatures | `...2.5.1.*` | `temperature` | `measurement` | `°C` |
| Memory (Standard) | `1.3.6.1.4.1.2021.4` | `data_size` | `measurement` | `MB` / `%` |

### 4.3 Detailed Table Mappings (Based on SNMP Walk)

**Memory Table (Standard Linux `UCD-SNMP-MIB` - `1.3.6.1.4.1.2021.4`)**:
- `...5.0` = `memTotalReal` (Total RAM in kB)
- `...6.0` = `memAvailReal` (Free RAM in kB)
- `...14.0` = `memBuffer` (Buffer RAM in kB)
- `...15.0` = `memCached` (Cached RAM in kB)
*Calculation for Used Memory % (to match ADM UI)*: 
`Used = Total - (Free + Buffers + Cached)`
`Usage % = (Used / Total) * 100`

**Temperatures Table (Enterprise `1.3.6.1.4.1.44738.2.5.1`)**:
- `...1.1` = Index (e.g., `1`)
- `...2.1` = CPU Temperature (e.g., `55` °C)
- `...3.1` = System/Motherboard Temperature (e.g., `42` °C)

## 5. Technical Stack & Dependencies
- **SNMP Library**: `pysnmp-lextudio` (Async-native, pure Python, fully compatible with Home Assistant and HACS).
- **I/O**: Strictly asynchronous (`asyncio`). No blocking calls in the HA event loop.

## 6. Error Handling & Resilience
- **Timeout/Unreachable**: Handled by the Coordinator. Entities will automatically become `unavailable` (`_attr_available = False`).
- **Data Parsing Errors**: Logged at `WARNING` or `ERROR` level without crashing the integration loop.
- **Dynamic Entities**: The Coordinator will perform an `snmpwalk` on tabular branches at each cycle. If a new index is detected (e.g., a new fan or temperature sensor), the integration will dynamically delegate the creation of the new entity to HA at runtime.

## 7. Future Scope (V2)
- SNMP v3 Support (AuthPriv).
- Disk/Volume monitoring (if exposed via standard HOST-RESOURCES-MIB or ASUSTOR enterprise MIB).
- Network interface monitoring.