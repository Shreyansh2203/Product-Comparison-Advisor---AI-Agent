# Architecture

## Overview

Product-Comparison-Advisor is an Oracle AI Agent configuration package — not a deployable web application. It ships a validated Oracle AI Agent JSON definition plus validation tooling.

## Components

### Agent Configuration
- `PRODUCT_COMPARATOR_V13.json` — Oracle AI Agent V13 workflow specification
- `scripts/validate_agent.py` — Agent JSON validation
- `scripts/prompt_contract.py` — Prompt contract enforcement
- `scripts/prompt_fixtures.py` — Reusable prompt fixtures

### Validation
- `tests/test_agent_config.py` — Agent configuration assertions
- `tests/test_attribute_count.py` — Attribute count validation
- `tests/test_prompt_contract.py` — Prompt contract tests

### CI/CD
- `ci.yml` — General build & test
- `codeql.yml` — SAST security scanning
- `json-validate.yml` — Agent JSON schema validation