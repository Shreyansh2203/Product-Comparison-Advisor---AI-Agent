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
*   Validate your JSON syntax before committing:

    ```bash
    python scripts/validate_agent.py
    python -m unittest discover -s tests
    ```

    Both commands use only the Python standard library. `validate_agent.py` is what CI runs, and it enforces the
    contract above: undefined tool references, a changed highlight colour, mixed REST API versions, missing
    anti-hallucination / prompt-injection / tool-failure guardrails, committed credentials or customer names, and
    README claims that no longer match the configuration will all fail the build.

*   Update `README.md` and `CHANGELOG.md` in the same pull request whenever you change agent behaviour.
*   Do not rename `PRODUCT_COMPARATOR_V13.json`. The file name is the agent's published code, and changing it is a
  breaking change for anyone who has already imported the agent. Record content changes under a new CHANGELOG
  version instead.
