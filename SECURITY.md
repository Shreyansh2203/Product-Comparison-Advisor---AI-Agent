# Security Policy

## Reporting a vulnerability

If you believe you have found a vulnerability in the Product Comparison Advisor
agent configuration, report it privately rather than opening a public issue:

1. **Do not create a public GitHub issue or discussion.**
2. Contact the maintainer directly via the GitHub profile that owns this
   repository.
3. Include the scenario that reproduces it, what you expected, what happened,
   and the environment you tested in.
4. You will get an initial response within **48 hours** and updates until it is
   resolved.

Ordinary bug reports are welcome as plain issues — this policy is about
vulnerabilities, not about things that are simply broken.

## Threat model

The deliverable is a single declarative JSON document
(`PRODUCT_COMPARATOR_V13.json`) that imports into Oracle Fusion AI Agent
Studio. It describes a read-only agent: it calls three Oracle Fusion SCM REST
endpoints (`GET` only), renders an HTML comparison table, and writes nothing
back. Its attack surface is therefore:

**Prompt manipulation.** The agent's `Prompt` and `summarizationPrompt`
direct how it calls tools and renders output. A hostile prompt edit could
weaken a guardrail (for example, allowing HTML unescaped, permitting
injection, or fabricating values). The repository defends against this with
`scripts/validate_agent.py` and the `prompt_contract.py` harness, which prove
each guardrail is still written clause by clause and that CI fails on any
regression.

**Untrusted API data.** Values returned by Oracle Fusion APIs are treated as
literal strings to render, never as instructions. Every value is HTML-escaped
before placement in the table, so a value carrying `<script>` comes out as
text, never markup. The `validate_agent.py` gate enforces this mechanically.

**No secrets committed.** The configuration carries no credentials, tenancy
identifiers, hosts, or customer data. The validator fails the build if any
appear (`ocid1.*`, `-----BEGIN ... PRIVATE KEY-----`, `Bearer ...`,
`.oraclecloud.com`, `https://`, or the customer name `verdesian`).

**No cross-contamination between items.** Each column is sourced only from
that item's own tool responses, so one item's value can never leak into
another's column. Tool failures are rendered as `Data unavailable`, never as
a difference or an item-not-found verdict.

## Supported versions

This project has no released versions. Security fixes land on `main`.

| Branch  | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |

## Out of scope

- Denial of service through the agent's tool-calling budget
  (`MaximumInteractions`). That is an operator concern at import time.
- Behaviour of the model at runtime. This repository proves what the prompt
  requires, never what the model does. A tenant run is required for that.
- Changes an operator makes at import time (error-handler recipients, REST
  trigger endpoint). Those are tenant facts documented in the README.
