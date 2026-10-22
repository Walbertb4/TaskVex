<div align="center">

# ⚡ TaskVex

### Autonomous, Lightweight & Privacy-First Native Windows AI Assistant
**Powered by Google Gemini 3.8 Live & Flash | Zero Electron | Pure Python & Vanilla JS**

[![Status](https://img.shields.io/badge/Status-Early%20Development-orange?style=for-the-badge)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Tests](https://img.shields.io/badge/Tests-804%20Passed-2ea44f?style=for-the-badge&logo=pytest&logoColor=white)](v1/tests)
[![Memory](https://img.shields.io/badge/RAM%20Footprint-~50--80%20MB%20(Target%20Idle)-blueviolet?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

*TaskVex is a deterministic, second-monitor companion and autonomous desktop assistant. It combines sub-second real-time voice streaming via Google Gemini Live API with a contract-driven, verified execution pipeline.*

</div>

---

## 🌟 Why TaskVex?

Most desktop AI assistants today are bloated Electron wrappers that consume 500+ MB of RAM, execute unconstrained shell commands, and store your API keys in plaintext `.env` files. 

**TaskVex takes a fundamentally different engineering approach:**

| Feature | TaskVex | Conventional AI Desktop Wrappers |
| :--- | :--- | :--- |
| **Memory Footprint** | **~50 – 80 MB RAM** *(Target baseline idle; Python + WebView2, excluding active local ML models)* | 350 – 600 MB RAM |
| **Engine** | **Native Edge WebView2 + Python** | Chromium + Node.js + Electron |
| **Frontend Dependencies**| **Zero npm packages** (Vanilla ES Modules + CSS) | 1,000+ `node_modules` dependencies |
| **Tool Execution** | **Deterministic Single-Worker FIFO + Policy Engine** | Blind shell / uncontrolled agent execution |
| **Credential Security** | **Windows Credential Manager** (`advapi32.dll`) | Plaintext `.env` / `config.json` |
| **Verification Standard** | **Read-back & OS evidence required** (`verified=True`) | Assumed success on tool call |
| **Voice Streaming** | **Sub-second Gemini 3.8 Live WebSockets** | Clunky REST STT ➔ LLM ➔ TTS cascades |

---

## 🔒 Voice & Data Privacy

* **Direct Gemini Live Streaming:** Voice conversation audio is streamed directly from your browser `AudioWorklet` to Google's Gemini Live API over encrypted WebSockets. Audio frames are never saved to disk, nor sent to third-party intermediary servers.
* **Offline Local Wake-Word:** Local keyword detection ("Vex" wake-word) runs **100% locally and offline on your CPU** using Sherpa-ONNX. When in sleep mode, no audio is transmitted across the network.
* **OS-Level Credential Protection:** API keys are never stored in plain text files or version control. They are encrypted into Windows Credential Manager using Win32 `advapi32.dll`.

---

## 🛡️ Security Principles & L0 ➔ L1–L4 Resolution Hierarchy

TaskVex evaluates and executes tasks according to strict safety invariants:

### Resolution Hierarchy
```text
[User Request / Goal] 
       │
       ▼
[Can be solved via L0 Direct Tool / API?] ──(YES)──► [L0: Direct Tool (Deterministic & Fast)]
       │                                             (Notes CRUD, App Launcher, OS Telemetry)
       ▼ (NO: GUI interaction required)
[L1: Memory / Verified Recipe exists?] ──(YES)──► [L1: Run verified recipe (Self-Healing)]
       │
       ▼ (NO / Interface changed)
[L2: DOM / Web tree available?] ──(YES)──► [L2: Chrome DevTools Protocol / DOM]
       │
       ▼ (NO: Pure Desktop App)
[L3: Windows UI Automation available?] ──(YES)──► [L3: Windows UIA (Accessibility tree)]
       │
       ▼ (NO: Canvas / Legacy / Game)
[L4: Vision budget available?] ──(YES: Last Resort)──► [L4: Local OCR / Screen bounding box]
```

### Safety Invariants:
1. **Policy Gate (Independent Authorization):** Every tool or GUI action must be evaluated by `PolicyEngine` (`ALLOW` / `CONFIRM` / `DENY`) before execution. The model cannot authorize its own actions.
2. **Mandatory Verification (`verified=True`):** A task is never assumed successful just because a command ran. Notes are verified by reading back disk state; launched apps are verified via `WS_VISIBLE` OS window handles.
3. **Never Repeat on Uncertain:** If an action returns `UNKNOWN` or `CANCELLED`, TaskVex immediately halts execution. Blind retries that could duplicate real-world side effects are forbidden.
4. **Data Tainting & Indirect Prompt Injection Defense:** All external data (web pages from L2, OCR text from L4, emails, clipboard or untrusted files) is tagged as untrusted data (`tainted = True`). When tainted context is active, side-effect tools (terminal, file deletion, email sending, note deletion) are automatically escalated to mandatory user confirmation (`CONFIRM`).

---

## 🚀 Status of Features

In accordance with [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`CORE_START_PLAN.md`](CORE_START_PLAN.md), capabilities are categorized as:
* **✅ Çalışıyor** (Implemented, verified with automated tests and active in core)
* **🧪 Test aşamasında** (Coded, undergoing unit / local manual verification)
* **🗓️ Planlı** (Architecturally mapped, scheduled for future stages)

### Core & Execution
* ✅ **Single-Worker FIFO TaskManager:** Deterministic serial task execution with zero race conditions.
* ✅ **Policy Engine:** Capability-based access control and validation gate.
* ✅ **Windows Credential Manager:** Secure storage for Gemini API keys via Win32 `advapi32.dll`.
* ✅ **Atomic JSON Storage:** Crash-safe read-back verified data storage with automatic recovery.

### Tools (L0)
* ✅ **Notes Engine (`notes.py`):** Create, list, update, delete notes with read-back verification and timestamp ordering.
* ✅ **Windows Apps (`windows_apps.py`):** System application cataloging and verified launch with `WS_VISIBLE` window detection.
* ✅ **System Telemetry (`telemetry.py`):** Read OS version, architecture, CPU count and platform info.
* 🗓️ **Terminal Execution (`terminal.py`):** Sandboxed local shell execution with strict allowlist and mandatory confirmation.
* 🗓️ **Google Workspace (`drive`, `calendar`, `gmail`):** Direct API integrations for calendar, files, and email.

### Model & Voice Session
* ✅ **Gemini 3.8 Live WebSocket Streaming:** Real-time bidirectional voice conversation with sub-second latency.
* ✅ **Server VAD & Audio Streaming:** 16 kHz mono PCM capture through browser `AudioWorklet`.
* ✅ **Bidirectional Barge-In (Interruption):** Speaking interrupts active voice playback with seamless sequential turn handoff.
* ✅ **Audio Device Selection:** Dynamic input (microphone) and output (speaker) device enumeration and routing.
* ✅ **Live Transcription:** Real-time streaming transcription of user speech and assistant replies.
* ✅ **Temporary Conversation Memory:** In-memory context retention (bounded to 12 turns / 16,000 characters).
* ✅ **Gemini REST ReAct Loop:** Multi-turn ReAct reasoning and tool calling via `gemini-3.8-flash` / `gemini-3.6-flash`.
* 🧪 **Local Wake-Word Detection:** Local "Vex" keyword spotting using `sherpa-onnx` ONNX models running on CPU.
* 🧪 **Single-Turn Sleep Mode:** Sleep intent detection ("uyku moduna geç", "sleep") with local socket shutdown and wake capability.
* 🧪 **REST TTS Playback:** Isolated text-to-speech voice playback for REST replies via `gemini-3.8-flash-lite-tts`.
* 🗓️ **Automatic Return-to-Sleep:** Auto-sleep timer in settings after interaction completion.
* 🗓️ **Persistent Long-Term Memory:** Personalized user facts, memory management, and editable memory entries.

---

## 🗺️ Roadmap (Aligned with CORE_START_PLAN.md)

- [x] **Stage 1 (Core Foundations):** Common Contracts, ToolRegistry, FIFO TaskManager, Atomic Storage ✅
- [x] **Stage 2 (Native Host & Bridge):** PyWebView Native Edge Host, Settings & Window State Bridge ✅
- [x] **Stage 3 (Notes Authority):** Backend Authority for Notes CRUD, Verified Read-Back, Backup & Restore ✅
- [x] **Stage 4 (Windows Apps):** Windows Application Catalog & Verified Launch with Window Discovery ✅
- [x] **Stage 5.1 – 5.5 (Gemini Live & Audio):** Real-time WebSockets, Server VAD, Barge-in, Device Routing, Conversation Memory ✅
- [ ] **Stage 5 Active Slice (Local Wake & Sleep):** Local Sherpa-ONNX Wake-Word ("Vex") & Sleep/Wake Mode 🧪
- [ ] **Stage 5 Finalization:** Integrated user acceptance, UI debloat, documentation lock.
- [ ] **Stage 6 (Personalization & External Integrations):** Long-term persistent memory, Google Workspace, Telegram & Discord bots 🗓️
- [ ] **Stage 7 (GUI Automation - Part 1):** L3 Windows UI Automation (UIA) & L1 Memory Verified Recipes 🗓️
- [ ] **Stage 8 (GUI Automation - Part 2):** L2 Web/DOM (CDP) & L4 Vision/OCR (with strict call budgets) 🗓️

---

## 📖 Documentation & Guides

* 🗣️ **[Commands Guide (commands.md)](commands.md):** User reference detailing all available spoken and typed conversational commands.
* 📐 **[Architecture Guide (ARCHITECTURE.md)](ARCHITECTURE.md):** Comprehensive technical specification, contracts, and lifecycle diagrams.
* 🤖 **[Agent Instructions (AGENTS.md)](AGENTS.md):** Development rules, Ponytail guidelines, and human-in-the-loop commit standards.
* 📜 **[Third-Party Notes (THIRD_PARTY_NOTES.md)](THIRD_PARTY_NOTES.md):** License boundaries, model origins, and upstream attributions.

---

## 📦 Getting Started

### Prerequisites
* **Windows 10** (Build 19041+) or **Windows 11**
* **Python 3.11+** (tested and verified with Python 3.14)
* **Microsoft Edge WebView2 Runtime** (installed by default on Windows 10/11)
* A **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```powershell
git clone https://github.com/Walbertb4/TaskVex.git
cd TaskVex/v1
```

### 2. Setup Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Install frozen dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt

# Verify package integrity
.\.venv\Scripts\python.exe -m pip check
```

### 3. Run the Test Suite
Ensure the deterministic core and bridge tests pass (804 tests):
```powershell
.\.venv\Scripts\python.exe -m pytest
```

### 4. Launch TaskVex
```powershell
.\.venv\Scripts\python.exe -m app.main
```
> **Tip:** Add `--debug` to enable Chromium Developer Tools within the native window.

### 5. Configure Your Gemini API Key
* **Via Desktop UI:** Open TaskVex, navigate to **Settings ➔ Connection**, paste your Gemini API key, and click **Save**. It is securely stored in Windows Credential Manager.
* **Via Environment Variable:**
  ```powershell
  $env:GEMINI_API_KEY = "your_api_key_here"
  ```

---

## 📄 License & Attribution

* **TaskVex Original Code:** Licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
* **Third-Party Dependencies & Pretrained Models:** 
  * `sherpa-onnx` is licensed under Apache-2.0.
  * Local keyword spotting ONNX model weights and pronunciation lexicons are sourced from upstream releases and downloaded to local cache; they are **not** relicensed under TaskVex's MIT license.
  * See [`THIRD_PARTY_NOTES.md`](THIRD_PARTY_NOTES.md) for full licensing boundaries and third-party notices.
