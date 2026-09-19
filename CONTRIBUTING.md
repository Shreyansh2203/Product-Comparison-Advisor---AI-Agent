# Contributing to Oracle Fusion Product Comparison Advisor

First off, thank you for considering contributing to this project! It's people like you that make open-source tools great.

## How to Contribute

### 1. Reporting Bugs
If you find a bug (e.g., the agent hallucinates data or fails to map a specific SCM code), please open an issue in the GitHub repository. Include as much detail as possible, including the exact prompt used, the Oracle SCM version you are running, and the expected output.

### 2. Suggesting Enhancements
If you have ideas for how to improve the agent (e.g., adding new Oracle SCM endpoints like `itemsV3` or improving the HTML UI generation), please submit a feature request via GitHub Issues.

### 3. Submitting Pull Requests
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/amazing-feature`).
3. Make your modifications to the `PRODUCT_COMPARATOR_V13.json` configuration.
4. Commit your changes (`git commit -m 'feat: add new extended attribute mapping'`).
5. Push to the branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request.

## JSON Modification Guidelines
*   **Do not alter the core anti-hallucination guardrails** without rigorous testing in a DEV/TEST environment.
*   Ensure any new API endpoints added to the tool definitions follow the `11.13.18.05` (or newer) Oracle SCM REST API schema.
*   Validate your JSON syntax before committing.
