# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| V13 | ✅ |
| < V13 | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability in Product-Comparison-Advisor, please report it responsibly.

**Do NOT** open a public GitHub issue for security vulnerabilities.

### How to Report

1. Email: [main.doga@gmail.com](mailto:main.doga@gmail.com) with subject "Product-Comparison-Advisor Security Vulnerability"
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix release**: Within 14 days (critical), 30 days (non-critical)

### Security Measures

- **No credentials in source**: Agent config contains no secrets, tokens, or customer data
- **Secret scanning**: GitHub secret scanning enabled
- **Push protection**: GitHub push protection enabled
- **SAST**: CodeQL on every push
- **Dependency audit**: Dependabot enabled
- **Disclosure**: No proprietary Oracle source code or sensitive client data

### Disclosure Policy

- Vulnerabilities are disclosed after a fix is released
- Credit is given to the reporter (unless they prefer anonymity)
- Public disclosure timeline: 90 days after fix release

## Security Contacts

- **Maintainer**: Shreyansh Srivastava ([@Shreyansh2203](https://github.com/Shreyansh2203))
- **Email**: main.doga@gmail.com