# Security Policy

## Supported Versions

Security updates are maintained for the current Community Edition branch.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately to the repository maintainer. Do not open a public issue containing secrets, exploit steps, or user data.

## Security Expectations

- Do not commit `.env` files, database URLs, API keys, or local SQLite databases.
- Use environment variables for provider keys and deployment-specific settings.
- Treat generated AI content as informational and non-advisory.
- Review CORS settings before public deployment.