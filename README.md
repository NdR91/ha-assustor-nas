# Home Assistant ASUSTOR NAS Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/NdR91/ha-assustor-nas.svg)](https://github.com/NdR91/ha-assustor-nas/releases)
[![License](https://img.shields.io/github/license/NdR91/ha-assustor-nas.svg)](LICENSE)

## 👋 The Honest Story Behind This Project

I am a technology enthusiast working as a Sales Engineer in an Italian Tech company, where part of my role is specifically focused on Generative AI. I do not have a software development background (I only have a basic understanding of the fundamentals).

However, out of personal interest and continuous learning, I frequently experiment with next-generation AI coding agents like Google Antigravity and, more recently and stably, the open-source solution **OpenCode**.

When I noticed a lack of a solid, native Home Assistant integration for monitoring ASUSTOR NAS devices (without relying on complex YAML configurations or reverse-engineering undocumented web APIs), I decided to build one. But I immediately hit a wall: I didn't know how to code it.

Fortunately, we live in the age of AI. Through what is often called "vibecoding"—with a lot of patience, trial and error, and continuous iteration—I guided AI tools to build this component from scratch.

👉 **This integration is developed 100% with the help of AI.**

The decision to publish this repository is driven by two main reasons:
1. **Sharing the experience**: I've included the context files used by OpenCode (like the `.opencode/` directory and `AGENTS.md`) to help others understand how these agentic systems analyze, reason, and interpret a real codebase.
2. **It actually works**: I use it daily, and it has proven to be genuinely useful and reliable for monitoring my NAS.

Because this project was built entirely by AI, some parts of the code might look "unusual" or not perfectly idiomatic. For this reason, **everyone is invited to read and review the code**. Pull requests, suggestions, and improvements are more than welcome, and issues will be evaluated—often together with AI! 🙂

This is an open, honest, and evolving project.

---

## 🌟 Features

This integration connects to your ASUSTOR NAS via **SNMP v2c** to provide real-time monitoring data directly into Home Assistant.

- **UI Configuration**: No YAML required. Set up everything through the Home Assistant Config Flow.
- **Dynamic Discovery**: Automatically detects and creates sensors for:
  - Every CPU Core (Usage %)
  - Every Fan (RPM)
  - Every Temperature Sensor (CPU, System/Motherboard)
- **Accurate Memory Calculation**: Calculates real memory usage (Total - Free - Buffers - Cache) to match the ADM Activity Monitor UI, rather than relying on raw SNMP "Free" memory which is often misleading on Linux systems.
- **Centralized Polling**: Uses Home Assistant's `DataUpdateCoordinator` to fetch all data in a single, efficient asynchronous cycle, preventing network spam and timeouts.

## 🛠️ Prerequisites

Before installing this integration, you must enable SNMP on your ASUSTOR NAS:

1. Log in to your ASUSTOR ADM interface.
2. Go to **Settings** > **Services** > **SNMP**.
3. Enable the SNMP service.
4. Set the **SNMP Protocol** to `SNMP v1 / SNMP v2c`.
5. Note down the **Community** string (the default is usually `public`).

## 📦 Installation

### Method 1: HACS (Recommended)

1. Open Home Assistant and navigate to **HACS**.
2. Click on **Integrations**.
3. Click the three dots in the top right corner and select **Custom repositories**.
4. Add the URL of this repository (`https://github.com/NdR91/ha-assustor-nas`) and select **Integration** as the category.
5. Click **Add**.
6. Search for "ASUSTOR NAS" in HACS and click **Download**.
7. Restart Home Assistant.

### Method 2: Manual

1. Download the latest release from this repository.
2. Extract the `custom_components/ha_asustor_nas_custom_integration` folder.
3. Copy it into your Home Assistant `custom_components` directory.
4. Restart Home Assistant.

## ⚙️ Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **ASUSTOR NAS**.
4. Enter the required information:
   - **Host**: The IP address or hostname of your NAS.
   - **Port**: The SNMP port (default is `161`).
   - **Community**: The SNMP community string you set in ADM (e.g., `public`).
   - **Scan Interval**: How often to poll the NAS for data (default is `300` seconds).
5. Click **Submit**.

## 🏗️ Architecture & Technical Decisions

This integration was built following strict Home Assistant Core standards:

- **Why SNMP v2c?** It's native, lightweight, and doesn't require reverse-engineering undocumented ADM web APIs. It provides a stable and standardized way to monitor hardware.
- **Why `pysnmp-lextudio`?** Home Assistant strictly forbids blocking I/O in the main event loop. `pysnmp-lextudio` is a modern, pure-Python library that natively supports `asyncio`, making it perfect for our `DataUpdateCoordinator`.
- **Unique ID Strategy**: ASUSTOR NAS devices do not expose a Serial Number via the standard `ENTITY-MIB`. To ensure a stable `unique_id` (so Home Assistant recognizes the device even if its IP changes), the integration fetches the MAC address of the first network interface via `IF-MIB`.
- **Memory Calculation**: The ASUSTOR Enterprise MIB only exposes "Free" memory. On Linux, this value is almost zero because unused RAM is used for caching. To provide a "Memory Usage" percentage that matches the ADM web UI, we use the standard Linux `UCD-SNMP-MIB` to calculate: `Total - (Free + Buffers + Cache)`.

## 🤝 Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue. If you want to contribute code, feel free to open a pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
