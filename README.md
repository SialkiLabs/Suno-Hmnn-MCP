# Suno Premier Studio OS

A local, zero-cost FastMCP server granting Hermes Agent, Antigravity IDE, and Claude full programmatic access to Suno Premier features (v4 models, stems, exact-timestamp extensions, and uncompressed WAV downloads).

## Features
- **Zero Third-Party APIs**: Uses your native Suno Premier account safely from your local IP.
- **Dual-Layer Auth**: Seamless failover between Clerk Bearer JWTs and session cookies.
- **Full Premier Toolset**:
  - `suno_generate` (Custom lyrics, v4/v3.5)
  - `suno_extend` (Extend clips at precise `continue_at` timestamps)
  - `suno_separate_stems` (Isolate vocals and instrumentals)
  - `suno_get_clip` (Fetch audio and status)

## Quickstart for Hermes Agent
1. Install dependencies: `pip install "mcp[cli]" httpx`
2. Add to your config (`mcp.json` or `.hermes/config.yaml`):
```json
{
  "mcpServers": {
    "suno-premier": {
      "command": "python",
      "args": ["/absolute/path/to/suno-premier-studio-os/server.py"],
      "env": {
        "SUNO_SESSION_TOKEN": "YOUR_JWT",
        "SUNO_COOKIE": "YOUR_COOKIE"
      }
    }
  }
}
```
