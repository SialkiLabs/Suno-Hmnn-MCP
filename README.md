# Suno-Hmnn-MCP

A local Model Context Protocol server for connecting Suno music workflows with AI clients and developer tools.

Developed by **Sialki Labs**. Licensed under the [MIT License](LICENSE).

## Music tools for an MCP client

The server exposes tools for music generation, track extension, clip metadata, stem requests, audio downloads, account credits, and authentication diagnostics. It also includes audio/MIDI-based generation tools and a local library backed by SQLite.

Availability depends on Suno's current service behavior, your account permissions, and the implementation in this repository. Review tool definitions and test the workflow with your account before relying on it.

| Tool | Purpose |
| --- | --- |
| `suno_generate` | Request music generation, with an optional wait for audio. |
| `suno_extend` | Request an extension of an existing track. |
| `suno_generate_from_midi` | Submit MIDI-based generation input. |
| `suno_generate_from_audio` | Request generation from an uploaded audio prompt. |
| `suno_separate_stems` | Request stem separation for a clip. |
| `suno_get_clip` | Retrieve clip metadata and generation status. |
| `suno_download_file` | Download an available audio file. |
| `suno_list_local_library` | Read the local library. |
| `suno_get_credits` | Retrieve account credit information. |
| `suno_auth_status` | Inspect authentication state. |

## Local setup

Requirements: Python 3.10 or later, Chrome or Edge, and a Suno account with access to the features you intend to use. Suno subscription charges and service limits are separate from this project's software license.

```bash
git clone https://github.com/SialkiLabs/Suno-Hmnn-MCP.git
cd Suno-Hmnn-MCP
pip install -r requirements.txt
playwright install chromium
python wizard.py
```

The wizard opens a browser for Suno sign-in and saves authentication material in a local `.env` file. Treat that file as a credential store, not an encrypted vault. Do not commit it, share it, or include it in support logs.

## Connect an MCP client

Configure a client that supports local MCP processes to launch `server.py`. Use an absolute path and the Python executable from the environment where dependencies are installed.

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

Clients use different configuration formats. Consult the client's documentation for the configuration location and process permissions. The local process can access resources allowed by the account that runs it.

## How the server is organized

The implementation uses asynchronous HTTP requests, authentication handling, streamed file downloads, validated tool inputs, and local SQLite state. See `server.py` and `core/` for the implementation rather than treating this overview as a performance or security certification.

Audio files and the library database use an OS-specific Music directory, such as `~/Music/SunoStudio`. `SUNO_OUTPUT_DIR` controls the output directory; `SUNO_DATABASE_PATH` can separately select the database file.

Downloads accept HTTPS URLs on explicitly approved Suno CDN hosts and save new files only. They are limited to 250 MiB, check basic MP3/WAV signatures, and do not convert formats. Other CDN hosts require a reviewed code change. A signature check is not a full audio-decoding validation.

Polling distinguishes completed audio, failures, previews, and timeouts. A network failure during a generation request can leave acceptance unknown. Do not automatically repeat that request.

The existing consumer-session endpoints and model identifiers have not been verified against a live account. This repository does not implement Suno Platform API access. MIDI and audio-input tools are request implementations, not confirmation that the service accepts those operations.

## Account access and security

This is an independent integration developed by Sialki Labs, not a claim of endorsement by Suno. It connects to remote services and is not air-gapped.

- Use only accounts and material you are authorized to access.
- Review Suno's terms, plan restrictions, and rights associated with generated content.
- No guarantee can be made against account restrictions or changes to service access.
- Protect cookies, tokens, `.env`, and local library contents.
- Review the code and dependencies before running the process on a machine with sensitive data.

Report vulnerabilities privately using [SECURITY.md](SECURITY.md). Use [Issues](https://github.com/SialkiLabs/Suno-Hmnn-MCP/issues) for reproducible bugs that do not disclose secrets.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and review expectations and [ROADMAP.md](ROADMAP.md) for areas of potential work.

**Created by:** George AK Neihsial, Sialki Labs.  
**Project and business enquiries:** [george.ak@inmytongue.org](mailto:george.ak@inmytongue.org)

## Offline development checks

```bash
python -m pip install -e ".[test]"
python -m pytest
```

Tests use fake HTTP responses and temporary local storage. They do not require Suno credentials or submit generations. `test_gen.py` is a manual live script, not part of the automated suite; running it can spend credits.

Authentication cookies and tokens remain plaintext local credentials. The setup wizard verifies session access before saving them and does not prove that a generation operation is authorized or available. Live validation requires separate approval and an account with the appropriate permissions.
