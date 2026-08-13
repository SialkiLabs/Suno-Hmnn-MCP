# Suno-Hmnn-MCP 🎵

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP Standard](https://img.shields.io/badge/MCP-1.0.0-green.svg)](https://modelcontextprotocol.io/)
[![FastMCP Engine](https://img.shields.io/badge/FastMCP-Supported-000000.svg)](https://gofastmcp.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Architecture: Self--Healing](https://img.shields.io/badge/Auth-Self--Healing%20Clerk%20JWT-purple.svg)](#-architecture-overview)

> **Suno-Hmnn-MCP** is an enterprise-grade, local, self-healing Model Context Protocol (MCP) framework that bridges **Suno AI (v4/v3.5)** directly into **Hermes Agent App**, **Antigravity IDE**, **Cursor**, **Claude Desktop**, **VS Code**, and local REST API services.

---

### 🌟 Community Initiative & Developer Credit
**Lead Architect & Author:** **George AK Neihsial**  
*An open-source welfare initiative created to provide developers, creators, prompt engineers, and AI research communities with a robust, zero-cost, user-friendly bridge between cutting-edge generative audio platforms and local autonomous AI agents.*

---

## 📋 Table of Contents
1. [Why Suno-Hmnn-MCP? (Comparison Matrix)](#-why-suno-hmnn-mcp-comparison-matrix)
2. [Architecture Overview](#-architecture-overview)
3. [Exhaustive Function & Tool Reference](#-exhaustive-function--tool-reference)
4. [Step-by-Step Installation Tutorial](#-step-by-step-installation-tutorial)
5. [Client Integration Guide (Hermes, Antigravity, Claude, Cursor)](#-client-integration-guide)
6. [Complete Music Production Workflow Guide](#-complete-music-production-workflow-guide)
7. [DAW Import & Stem Isolation (Ableton, FL Studio, Reaper)](#-daw-import--stem-isolation)
8. [Comprehensive FAQ & Security Deep-Dive](#-comprehensive-faq--security-deep-dive)
9. [Troubleshooting Guide](#-troubleshooting-guide)
10. [License & Authorship](#-license--authorship)

---

## ⚡ Why Suno-Hmnn-MCP? (Comparison Matrix)

| Feature | Standard Open-Source Script | Paid API Wrappers (e.g. AceData) | **Suno-Hmnn-MCP** |
| :--- | :---: | :---: | :---: |
| **Cost** | Free (Fragile) | $0.02 - $0.05 / song | **100% FREE (Uses your plan)** |
| **Authentication** | Manual DevTools Cookie Paste | Paid API Key | **Automated Playwright Portal** |
| **Token Expiry Handling** | Crashes on 401 | N/A | **Self-Healing Clerk JWT Refresh** |
| **Model Support** | Basic v3 | v3 / v4 | **Native v4 & v3.5 Support** |
| **Audio Quality** | Low-res MP3 | MP3 / WAV | **Uncompressed 24-bit WAV & MP3** |
| **Stem Isolation** | ❌ No | Extra Fee | **Native Premier Vocal/Backing Stems** |
| **Precision Extension** | ❌ No | Limited | **Millisecond Timestamp Extensions** |
| **State Tracking** | Memory Only | Cloud Database | **Local SQLite Engine (`studio_os.db`)** |
| **Local Privacy** | Partial | No (Third-party servers) | **100% Local Desktop Air-Gap** |

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
│                                       SUNO-HMNN-MCP FRAMEWORK                                          │
│                                                                                                        │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐  ┌─────────────────────────────┐  │
│  │ Clerk Token Rotation Engine   │  │ Self-Healing HTTP Middleware  │  │ Local SQLite State Tracker  │  │
│  │  • Full Cookie Bundle Vault   │  │  • Intercepts 401 Unauthorized│  │  • Track History & Prompts  │  │
│  │  • Dynamic Bearer JWT Mint    │  │  • Silent Request Replay      │  │  • Local File Indexing      │  │
│  └───────────────────────────────┘  └───────────────────────────────┘  └─────────────────────────────┘  │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │ Authenticated HTTPS / REST
                                                    ▼
                                       ┌─────────────────────────┐
                                       │   Suno.com / Clerk API  │
                                       └─────────────────────────┘
```

---

## 🧰 Exhaustive Function & Tool Reference

`Suno-Hmnn-MCP` exposes 7 production-grade tools directly to your AI Agents:

### 1. `suno_generate`
Generates original music tracks using custom lyrics or prompt descriptions.
* **Parameters:**
  * `prompt` (*string*): Descriptive prompt for song style or theme.
  * `tags` (*string*): Music genres, instruments, or vocal styles (e.g. `"synthwave, energetic, female vocal"`).
  * `title` (*string*): Song title.
  * `make_instrumental` (*boolean*): If `true`, removes all vocals.
  * `model_version` (*string*): `"chirp-v4"` (Default) or `"chirp-v3-5"`.
  * `custom_lyrics` (*string*): Custom structured lyrics (with `[Verse]`, `[Chorus]` tags).

### 2. `suno_extend`
Extends an existing track starting from an exact timestamp.
* **Parameters:**
  * `clip_id` (*string*): The unique ID of the parent clip to extend.
  * `continue_at` (*number*): Timestamp in seconds where extension begins (e.g. `120.5`).
  * `prompt` (*string*): Additional lyrics or style guidance for the extended section.
  * `tags` (*string*): Updated music tags for the new section.
  * `title` (*string*): Title for the extended version.

### 3. `suno_separate_stems`
Triggers Premier stem isolation on an existing clip.
* **Parameters:**
  * `clip_id` (*string*): The clip ID to separate.
* **Returns:** Clip metadata containing individual audio URLs for isolated **Vocals** and **Instrumental** tracks.

### 4. `suno_get_clip`
Retrieves live clip metadata, generation status, lyrics alignment, and audio download links.
* **Parameters:**
  * `clip_id` (*string*): Target clip ID.

### 5. `suno_download_file`
Downloads uncompressed WAV, MP3, or stem files safely to local storage.
* **Parameters:**
  * `audio_url` (*string*): Direct CDN audio URL.
  * `filename` (*string*): Output filename (e.g. `"cyberpunk_master"`).
  * `file_format` (*string*): `"wav"` (Default) or `"mp3"`.

### 6. `suno_get_credits`
Returns account information, plan type (`Free`, `Pro`, `Premier`), and remaining credit allowance.

### 7. `suno_auth_status`
Diagnostic tool that reports the health of the Clerk Token Rotation Engine and remaining JWT lifespan.

---

## 🛠️ Step-by-Step Installation Tutorial

### Prerequisites
1. **Python 3.10 or higher** installed.
2. **Google Chrome** or **Microsoft Edge** browser installed.
3. An active **Suno AI** account.

### 1. Clone & Set Up Directory
```bash
git clone https://github.com/SialkiLabs/Suno-Hmnn-MCP.git
cd Suno-Hmnn-MCP
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Run the Automated Auth Portal
Launch the frictionless login wizard:
```bash
python wizard.py
```

* **What happens:**
  1. The setup wizard boots Google Chrome natively.
  2. Log into your Suno account on the Chrome window.
  3. As soon as you log in, the wizard captures your secure cookie bundle, verifies your account tier, fetches your remaining credit balance, and writes your `.env` configuration file automatically.

---

## 🔌 Client Integration Guide

### Hermes Agent
Add to `~/.hermes/config.yaml` or workspace `mcp.json`:
```yaml
mcp_servers:
  suno_premier:
    command: "python"
    args: ["/absolute/path/to/Suno-Hmnn-MCP/server.py"]
```

### Antigravity IDE & Cursor
Add to `.cursor/mcp.json`:
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

### Claude Desktop
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

### Standalone REST API Mode
To run as a local HTTP server for custom web apps or webhooks:
```bash
fastmcp run server.py:mcp --transport http --port 8000
```

---

## 🎼 Complete Music Production Workflow Guide

### Prompting Strategy for v4 Models
For best results with Suno `chirp-v4`, structure your prompts with explicit musical style tags:

```markdown
[Genre: Cyberpunk Synthwave]
[Tempo: 120 BPM]
[Instruments: Analog Synths, Heavy Bass, Electronic Drums]
[Vocals: Distorted Female Vocal, Reverb]

[Verse 1]
Midnight glowing neon lights,
Wires humming through the night...

[Chorus]
Digital dreams in an analog soul,
System override in full control!
```

---

## 🎧 DAW Import & Stem Isolation

Once `suno_separate_stems` completes, use `suno_download_file` to save your stems locally.

**File Organization:**
```
C:\Users\YourName\hermy-hq\music-outputs\
├── cyberpunk_master.wav       # Full Mix (24-bit WAV)
├── cyberpunk_vocals.wav       # Isolated Vocals
└── cyberpunk_instrumental.wav # Backing Track
```

**Importing into DAWs:**
1. **Ableton Live / FL Studio / Reaper / Logic Pro**: Drag `cyberpunk_vocals.wav` and `cyberpunk_instrumental.wav` into separate audio tracks.
2. Apply local EQ, compression, or sidechaining to mix Suno vocals with your custom instrument tracks.

---

## 🛡️ Security & Code Auditability Guarantee

`Suno-Hmnn-MCP` is engineered with an uncompromising commitment to privacy and open-source transparency:
* **100% Local Air-Gap**: Zero data, tokens, or cookies are ever transmitted to any third-party telemetry, analytics, or external server.
* **Direct Official Endpoints**: All network communications occur exclusively between your local PC (`127.0.0.1`) and Suno's official domain (`suno.com` / `clerk.suno.com`).
* **Non-Invasive Setup**: The interactive `wizard.py` script runs strictly in user-space and requires **no administrator/root privileges**.
* **Auditable Codebase**: Every single line of network and state management code is open-source, readable, and under 500 lines of standard Python (`core/auth.py`, `core/client.py`).

---

## ❓ Comprehensive FAQ & Security Deep-Dive

#### Q: Will this get my Suno account flagged or banned?
**No.** `Suno-Hmnn-MCP` runs locally on your PC. It uses native Chrome/Edge headers, human-paced polling intervals, and authentic Clerk Bearer JWT tokens. It is indistinguishable from standard web browser traffic.

#### Q: How does the Self-Healing Token Engine work?
Clerk JWT bearer tokens expire periodically. When Suno returns an `HTTP 401 Unauthorized`, our internal middleware catches the response, uses the stored session cookie to silently request a new JWT from Clerk, updates its memory, and replays your generation request transparently.

#### Q: Do my AI Agent and Suno accounts need the same email?
**No.** The architecture is completely decoupled. The MCP server acts as an air-gap on your local machine.

#### Q: Where are generated files stored?
By default, all audio files are saved to `C:\Users\YourUsername\hermy-hq\music-outputs\`. You can customize this by setting `SUNO_OUTPUT_DIR` in `.env`.

---

## 🚨 Troubleshooting Guide

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'mcp'` | Packages installed in virtual environment | Run `python` using the full path to your virtual environment (e.g. `venv\Scripts\python.exe setup.py`). |
| `Error fetching credits: HTTP 307` | Suno API endpoint redirect | Fixed in latest version by enabling `follow_redirects=True` in `httpx`. Run `git pull`. |
| `Login timed out` | Chrome window closed before login | Re-run `python setup.py` and ensure you complete login in Chrome. |

---

## 📄 License & Authorship

Licensed under the **MIT License** — free for personal, educational, and commercial use.

**Lead Developer:** **George AK Neihsial**  
*An initiative for the welfare of the open-source community.*

---

## 🔍 Search Engine Index & Long-Tail Query Mapping

*This section optimizes discovery for search engine crawlers (Google, Bing, Perplexity, ChatGPT, Claude) and GitHub's internal code search.*

* **Primary Keywords**: Suno AI MCP, Suno MCP Server, Suno API Python, Suno v4 MCP, Suno Premier API, Suno Stem Separation API, Suno WAV Exporter, Suno Claude MCP, Suno Cursor MCP, Suno Hermes Agent.
* **Supported Integrations**: Hermes Agent App, Antigravity IDE, Cursor IDE, Windsurf, Claude Desktop, VS Code, Roo Code, Cline, LibreChat.
* **Supported Features**: Suno chirp-v4, Suno chirp-v3-5, Custom Lyrics Generator, Timestamp Audio Extensions, Stem Isolator (Vocals/Instrumental), Uncompressed 24-bit WAV Downloader, Clerk Token Rotation Engine.

