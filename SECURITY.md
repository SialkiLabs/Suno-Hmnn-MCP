# Security policy

Suno-Hmnn-MCP handles authentication material and makes requests to remote services. Local execution does not remove risks involving credentials, dependencies, file access, or service accounts.

## Report privately

Send potential vulnerabilities to **george.ak@inmytongue.org**. Do not publish exploit details, live credentials, or sensitive account information in an issue.

Include the affected file or tool, impact, safe reproduction steps, and the tested environment. Redact cookies and tokens. Provide the relevant commit identifier when possible so the implementation can be located precisely.

Reports will be reviewed by the maintainers. This policy does not promise a response or resolution deadline, an audit certification, or a paid bounty.

## Protect authentication material

- Keep `.env` and browser session material out of Git, screenshots, and logs.
- Restrict local file access. A plaintext environment file is not an encrypted credential vault.
- Run with only the operating-system permissions the task requires.
- Inspect dependencies and tool permissions before enabling automated actions.
- Revoke or rotate exposed credentials using the service's account controls.

Security-sensitive changes should include tests or clear reproduction and verification instructions. The software license does not guarantee account safety or service availability.
