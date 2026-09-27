# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-27
Prompt hardening and verification tooling. `PRODUCT_COMPARATOR_V13.json` keeps its name and its agent code
(`PRODUCT_COMPARATOR_V13`); this is a content revision, not a re-versioning, so existing imports are unaffected.

### Added
- **Offline behavioural test harness for the prompt contract.** `scripts/prompt_contract.py` parses the system
  prompt and the summarization prompt into named rules and asserts the *semantic* guardrails by structure. Each of
  the eleven rules must be written in its named block with each of its mandatory clauses present, so a rule whose
  heading survives but whose prohibition was edited away is reported rather than passing on substring presence. A
  test removes each clause in turn and asserts the rule it belongs to then fails.
- **Tool-signature cross-checks.** Every tool the prompt names is checked against the tools actually attached,
  parameters included. A parameter the prompt tells the agent to pass that a tool does not declare, a tool the
  prompt names that is not attached, and a parameter the prompt forbids that a tool does declare are all build
  failures. This is the class of bug the prompt once contained (`ItemId` / `OrganizationId`). The declared call
  sites, their order, and the sentences that state them are pinned, so a tool added without a call site, or a
  reordered protocol, also fails.
- **HTML output contract checks.** The highlight style as one literal, the `N+1` column rule, and the template's
  own column arithmetic: the header row, the body row, and the section row's `colspan` are read back out of the
  template and must agree for 2, 3, 4, and 7 items.
- **Oracle-shaped scenario fixtures.** `scripts/prompt_fixtures.py` supplies a failed tool call, an empty result
  set, a null attribute, an attribute absent from the payload, and an attribute value containing a prompt-injection
  attempt, all synthetic. `tests/test_prompt_contract.py` pins what the rules *as written* require of the agent for
  each, plus a lookup code, a boolean, a one-sided comparison, and the case where fewer than two items have usable
  data. This is rule verification, not model verification: nothing in this repository simulates a model response.
- **Validator: `reasoning_effort` and `k` are now validated.** `reasoning_effort` must be a value the provider
  documents, `k` must be a non-negative integer (`0` meaning top-k sampling off, so the model default applies),
  `max_completion_tokens` must be a positive integer, and all three must agree between the workflow-level and
  agent-level model configuration.
- **Validator: the two `MaximumInteractions` fields are now checked against each other.** A top-level budget below
  the agent's own budget would truncate the agent and is an error. The precedence question itself is reported as an
  accepted finding rather than guessed at, because Oracle documents a field of that name on both the agent and the
  agent team and does not say which one the export format honours.
- **Validator: declared-but-unbound tool parameters are reported.** `getProductCosts` declares four
  `ProductCosts.*` filter parameters that never appear in its `resourcePath`, so passing them cannot change the
  request. Reported rather than rewritten, because the tool binding is Oracle seeded.
- **README: a worked example.** A real request, the three Oracle API calls it triggers, a sample response, and the
  exact HTML output, using clearly synthetic item data. The HTML is regenerated from the prompt's own template and
  compared byte for byte, so the documentation cannot advertise an output shape the prompt does not specify.
- **README: "How to verify this before production".** A checklist for an Oracle engineer: what to run in a
  DEV/TEST instance, what to look for, and the five prompt points most likely to need tuning, ranked.
- **README: a data-flow mermaid diagram** restored to the architecture section.
- **Tests: every relative link resolves and every table-of-contents anchor exists**, and every accepted finding is
  named in the README.
- **CI: the gate is now proved to be a gate.** A step injects a regression the validator must catch, on a
  throwaway copy, and fails the run if the validator accepts it.

### Changed
- CI now pins `actions/checkout` and `actions/setup-python` to full 40-character commit SHAs with the release tag in
  a trailing comment. The SHAs were resolved from the upstream repositories with `git ls-remote --tags` and
  confirmed to be commit objects through the GitHub API.
- The accepted-findings list grew from four to six (`max-interactions/scope` and `tool/parameter-unbound` added),
  each with a written reason and a Known Limitations entry. The test that pins the list was strengthened, not
  relaxed: it now also requires the README to name every entry.
- `CONTRIBUTING.md` rewritten to cover editing the JSON safely, keeping it parseable and byte-formatting-stable, the
  validation and test commands, and the rule that the filename must never be renamed.

### Not changed, deliberately
- `modelConfiguration.code` still names `ORA_MODEL_CONFIG_PREMIUM_OPEN_AI_GPT_4_1_MINI` while the effective model is
  `OCI_GPT_5_MINI`. Oracle assigns the code; editing it risks breaking the import.
- `partnerMetadata.Name` is still `gvhb`, with no recorded provenance. It may be meaningful to Oracle.
- The `EMAIL` error handler is still empty. A placeholder recipient is worse than none.
- `Specification.triggers` is still an empty `REST` trigger, to be configured at import.
- **`PRODUCT_COMPARATOR_V13.json` was not modified at all in this revision.** Every change is to the tooling, the
  gate, the tests, and the documentation. Three prompt issues the harness surfaced are documented in the README for a
  human to resolve in a tenant rather than changed blind:
  1. the Item Number row is highlighted on every comparison, because the summarizer declares that row but nothing
     exempts it from the differencing rule;
  2. `COMPARISON RULES` says to map a null lookup code to `'N/A'`, while the two `ABSOLUTELY CRITICAL` rules say an
     unknown value renders as `-`. The harness follows the two critical rules and a test pins that choice;
  3. the `getProductCosts` invocation offers filters the tool cannot apply.

### Known issues (unchanged, needs a human in AI Agent Studio)
All six are reported by the validator as acknowledged `ACCEPT` findings with a written reason, recorded in
`ACCEPTED_FINDINGS`, and documented in the README's `Known Limitations` table.
- `modelConfiguration.code` is `ORA_MODEL_CONFIG_PREMIUM_OPEN_AI_GPT_4_1_MINI` while the effective model is
  `OCI_GPT_5_MINI`. The code is Oracle-assigned; the model is selected by `model`/`modelName`/`provider`. Left as
  shipped because changing an Oracle-assigned code can break an import.
- `partnerMetadata.Name` is the opaque value `gvhb`. Its origin is not recorded in this repository; a human must
  confirm it identifies no customer or person, and in particular that it is not someone's initials.
- `Specification.dataPipeline.errorHandlers` contains an `EMAIL` handler with empty recipients, subject, and body,
  so pipeline errors are silently dropped until an operator configures it.
- `Specification.triggers` is an empty `REST` trigger, so the calling endpoint contract is chosen at import.
- Top-level `MaximumInteractions` is null while `agents[0].MaximumInteractions` is 20. The agent's own budget is the
  one this configuration can govern, because `Architecture: single_agent` with `StartAgentId: null` and a single
  `WORKER` agent has no routing layer for a team-level budget to bound. That is a structural reading, not a
  documented one, so it is asserted and reported rather than enforced by editing a value nobody can test from here.
- `getProductCosts` declares four `ProductCosts.*` filter parameters that never appear in its `resourcePath`.

### Notes
- The shipped configuration reports 0 errors, 0 warnings, 6 accepted, 23 confirmed.
- Test count went from 60 to 155.
- Runtime behaviour against an Oracle Fusion tenant is **not** verified by this revision, and neither is a CI run.
  Both remain open.

## [1.0.0] - 2026-09-19
### Added
- Initial release of the Oracle Fusion Product Comparison Advisor configuration (`PRODUCT_COMPARATOR_V13.json`).
- Comprehensive README with architecture diagrams and Oracle deployment steps.
- Complete Community Health Profile (Contributing, Code of Conduct, Security Policy, Issue Templates, PR Template).
- Automated CI pipeline (GitHub Actions) for JSON syntax validation.
- CODEOWNERS file for PR review enforcement.
