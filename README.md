# Suno-Hmnn-MCP 🎵

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP Standard](https://img.shields.io/badge/MCP-1.0.0-green.svg)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/FastMCP-Supported-000000.svg)](https://gofastmcp.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

> **Suno-Hmnn-MCP** is an enterprise-grade, local, self-healing Model Context Protocol (MCP) server that seamlessly bridges **Suno AI (v4/v3.5)** directly into **Hermes Agent App**, **Antigravity IDE**, **Cursor**, **Claude Desktop**, and custom web applications.

---

### 🌟 Community Initiative & Authorship
**Created & Maintained by:** **George AK Neihsial**  
*An open-source welfare initiative dedicated to providing developers, creators, and AI research communities with robust, zero-cost, user-friendly bridges between cutting-edge generative tools and local AI agents.*

---

## 🚀 Key Features

* **Zero Third-Party API Charges**: Operates using your existing native Suno Premier/Pro subscription with **zero middleman fees** or per-call charges.
* **Frictionless "Sign In" Wizard (`setup.py`)**: Uses native Chrome/Edge automation to capture authentic session cookies. **No manual copying of Developer Tools cookies required.**
* **Dual-Layer Token Rotation Engine**: Dynamically exchanges long-lived session cookies for short-lived, high-speed **Clerk Bearer JWTs**, delivering native API performance.
* **Self-Healing Request Middleware**: Intercepts `401 Unauthorized` responses mid-generation, silently refreshes JWT tokens on the fly, and replays requests without interrupting AI agent tasks.
* **Full Premier Studio Suite**:
  * **Custom Mode Generation**: `chirp-v4` and `chirp-v3-5` models with custom lyrics, style tags, and titles.
  * **Precision Timestamp Extensions**: Extend clips at exact millisecond timestamps (`continue_at`).
  * **Premier Stem Separation**: Isolate vocals and backing instrumentals into separate stems.
* **DAW Audio Exporter**: Automatically downloads uncompressed 24-bit `.wav` files and stems directly to your local project folder.
* **Local SQLite State Tracker (`studio_os.db`)**: Provides long-term memory for AI agents by logging clip IDs, prompts, tags, and local file locations.

---

## 🏗️ Architecture Overview

```
                        ┌────────────────────────────────────────────────────────┐
                        │   AI Clients / Editors                                 │
                        │   (Hermes Agent, Antigravity IDE, Cursor, Claude)     │
                        └───────────────────────────┬────────────────────────────┘
                                                    │ Standard MCP (stdio / HTTP)
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       SUNO-HMNN-MCP SERVER                                             │
│                                                                                                        │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐  ┌─────────────────────────────┐  │
│  │ Clerk Token Rotation Engine   │  │ Self-Healing HTTP Middleware  │  │ Local SQLite State Tracker  │  │
│  │  • Session Cookie Backup      │  │  • Catches 401 Unauthorized   │  │  • Clip History & Prompts   │  │
│  │  • Dynamic Bearer JWT Mint    │  │  • Transparent Request Replay │  │  • Local WAV File Paths     │  │
│  └───────────────────────────────┘  └───────────────────────────────┘  └─────────────────────────────┘  │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Authenticated HTTPS
                                                    ▼
                                       ┌─────────────────────────┐
                                       │   Suno.com / Clerk API  │
                                       └─────────────────────────┘
```

---

## 📦 Installation & Quick Start

### Prerequisites
* **Python 3.10+** installed on your system.
* **Google Chrome** or **Microsoft Edge** installed.
* An active **Suno AI** account.

### Step 1: Clone the Repository
```bash
git clone https://github.com/appeebaareecloudinfo-hash/Suno-Hmnn-MCP.git
cd Suno-Hmnn-MCP
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 3: Run the Automated Setup Wizard
Launch the interactive login portal:
```bash
python setup.py
```
1. A native browser window will launch to `https://app.suno.ai/`.
2. Click **"Sign In"** on the website and log into your account.
3. The wizard will automatically capture your session cookies, verify your account tier and remaining credits, and generate your `.env` configuration file securely.

---

## 🛠️ Integration Guide (Connecting to AI Clients)

### 1. Hermes Agent
Add the following to your `~/.hermes/config.yaml` or workspace `mcp.json`:

```yaml
mcp_servers:
  suno_premier:
    command: "python"
    args: ["/absolute/path/to/Suno-Hmnn-MCP/server.py"]
```

### 2. Antigravity IDE / Cursor / Windsurf
Add to `.cursor/mcp.json` or your global MCP settings:

```json
{
  "mcpServers": {
    "suno-hmnn": {
      "command": "python",
      "args": ["/absolute/path/to/Suno-Hmnn-MCP/server.py"]
    }
  }
}
```

### 3. Claude Desktop
Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "suno-hmnn": {
      "command": "python",
      "args": ["C:/Users/YourUsername/Suno-Hmnn-MCP/server.py"]
    }
  }
}
```

---

## 📖 MCP Tool Reference

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `suno_generate` | `prompt`, `tags`, `title`, `make_instrumental`, `model_version`, `custom_lyrics` | Generate new tracks using `chirp-v4` or `chirp-v3-5`. Supports Custom Mode. |
| `suno_extend` | `clip_id`, `continue_at`, `prompt`, `tags`, `title`, `model_version` | Extend an existing audio clip starting at timestamp `continue_at` (in seconds). |
| `suno_separate_stems` | `clip_id` | Trigger Premier stem separation to isolate Vocals and Instrumental tracks. |
| `suno_get_clip` | `clip_id` | Retrieve metadata, status, audio URLs, and stem states for a clip. |
| `suno_download_file` | `audio_url`, `filename`, `file_format` | Download uncompressed 24-bit `.wav`, `.mp3`, or stem files to local storage. |
| `suno_get_credits` | None | Fetch current account credit balance and plan details. |
| `suno_auth_status` | None | Diagnostic check on token rotation engine health and token expiration countdown. |

---

## ❓ Frequently Asked Questions (FAQ)

#### Q: Will using this flag or ban my Suno account?
**No.** `Suno-Hmnn-MCP` runs 100% locally on your home computer. It uses standard Chrome/Edge headers, human-paced polling intervals, and authentic Clerk Bearer JWT tokens. It behaves identically to you using the official web application in Chrome.

#### Q: Do my AI platform account and Suno account need to use the same email?
**No.** The architecture is completely decoupled. The MCP server acts as an air-gap on your local computer. Your AI agent (Claude, Hermes, Cursor) never sees your Suno password or email, and Suno never sees your AI platform accounts.

#### Q: How does the self-healing auth work?
Clerk JWT bearer tokens expire every few hours. When Suno returns an `HTTP 401 Unauthorized`, our internal middleware catches the error, uses the backup session cookie to silently request a fresh JWT from Clerk, updates its memory, and replays your generation task automatically.

#### Q: Can I run this as an HTTP server instead of stdio?
Yes! FastMCP supports HTTP transport out of the box. Run:
```bash
fastmcp run server.py:mcp --transport http --port 8000
```
Your local server is now accessible via REST API at `http://localhost:8000`.

---

## 📄 License & Community Welfare

This project is licensed under the **MIT License** — free for personal, educational, and commercial use.

**Initiative Leader:** **George AK Neihsial**  
*Building open, accessible, and user-centric software bridges for the global developer community.*
