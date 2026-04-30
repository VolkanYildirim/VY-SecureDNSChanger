# 🛡️ VY-SecureDNSChanger

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg) ![Security](https://img.shields.io/badge/Security-Zero%20Leak-brightgreen.svg) ![Telemetry](https://img.shields.io/badge/Telemetry-None-red.svg)

A modern, privacy-first DNS switching utility designed for Windows environments. Built entirely in Python using `CustomTkinter` for a seamless, fatigue-free graphical interface.

## ⚙️ Security & Privacy Philosophy (Secure by Design)

As a core engineering standard, this project is strictly built on **Privacy-First** principles:

*   **Zero Telemetry:** The application does not collect, log, or transmit any user hardware data, IP addresses, or network configurations to third parties.
*   **Local Processing Only:** All DNS modification operations are executed strictly on the local machine using native Windows APIs. No external servers are pinged (Zero Call-Home).
*   **Low Attack Surface:** Relies on minimalistic and auditable libraries without unnecessary bloatware.

## 🚀 Current Development Status (V1.0 Skeleton)

*   [x] Modern GUI implementation with CustomTkinter (Dark/Light mode switch).
*   [ ] Windows Network Adapter discovery module (WMI/psutil integration).
*   [ ] UAC elevation and DNS modification logic (netsh/PowerShell integration).
*   [ ] Asynchronous ICMP Ping latency testing for fastest DNS resolution.

*Developed with a vision for secure network architectures and DevSecOps practices.*
