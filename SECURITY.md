# Security Policy & Vulnerability Disclosure

## 🛡️ Our Security Commitment
**Sialki Labs** takes software security, data privacy, and user protection seriously. 

Because **Suno-Hmnn-MCP** operates locally on your machine (`localhost`) and interacts directly with authentication tokens, we maintain an uncompromising standard of code transparency and security hygiene.

---

## 🔒 Security Architecture Highlights
* **Zero Outbound Telemetry**: No user data, prompt history, session tokens, or system analytics are ever transmitted to external tracking servers.
* **User-Space Execution**: All setup scripts (`wizard.py`) and FastMCP server entrypoints (`server.py`) run strictly within standard user permissions and **never request root/administrator privileges**.
* **Credential Vaulting**: Local credentials are stored exclusively in `.env` (which is excluded from Git tracking via `.gitignore`).

---

## 🐛 Reporting a Vulnerability

If you discover a potential security vulnerability within **Suno-Hmnn-MCP**, please do **NOT** open a public GitHub issue.

Instead, please report the vulnerability directly to the Lead Architect:

* **Email**: `daplewjioneihsial@gmail.com`
* **Lead Architect**: George AK Neihsial
* **Organization**: Sialki Labs (`github.com/SialkiLabs`)

### What to Include in Your Report:
1. Description of the vulnerability and its potential impact.
2. Step-by-step reproduction steps or proof-of-concept script.
3. Suggested fix or mitigation, if available.

We pledge to acknowledge your report within **24 hours** and provide an estimated resolution timeline within **48 hours**.
