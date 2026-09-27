# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-26
Prompt hardening and verification tooling. `PRODUCT_COMPARATOR_V13.json` keeps its name and its agent code
(`PRODUCT_COMPARATOR_V13`); this is a content revision, not a re-versioning, so existing imports are unaffected.

### Added
- `scripts/validate_agent.py`, a dependency-free validator covering structure, the prompt/tool contract, the
  guardrail set, the no-secrets disclosure claim, and the README cross-check. It replaces the previous bare
  `jq empty` parse as the real CI gate.
- `tests/test_agent_config.py`, 48 structural tests, including negative tests that prove the validator fails on
  each defect it claims to catch.
- Agent prompt section `DATA INTEGRITY (ABSOLUTELY CRITICAL)`: no fabrication, empty is not zero, unknown is not a
  difference, no cross-contamination between items, and an explicit prompt-injection guardrail stating that values
  returned by the SCM APIs are data to display and never instructions to follow.
- `4. TOOL FAILURES ARE NOT DIFFERENCES` in the summarization prompt, matching the new system-prompt rules.
- `README.md` sections documenting failure handling and the local validation commands.
- `check_deployment` in the validator: asserts that the import-time work an operator must still do is declared in
  the JSON and documented in the README. The empty `EMAIL` error handler and the empty `REST` trigger are reported
  as acknowledged findings, and dropping either import step from the README is now a hard error, so an accepted
  finding cannot quietly become an undocumented gap.
- `ACCEPTED_FINDINGS` in the validator: an explicit, reviewed list of the four findings that are real but
  deliberately not fixed, each with its reason. An entry that stops firing is reported as a warning, so the list
  cannot rot into a blanket suppression.
- `README.md` section `Known Limitations` recording all four acknowledged facts, including `partnerMetadata.Name`.
- `tests/test_agent_config.py`: 60 tests, up from 48. The new cases pin the four finding levels, prove a stale
  accepted entry is caught, prove `--strict` passes the shipped configuration and fails on a new warning, and prove
  that renaming the configuration file or dropping an import step fails the gate.

### Changed
- `LICENSE`: the copyright holder is now the full name `Shreyansh Srivastava`, matching the other repositories in
  this portfolio. No other licence text changed.
- `scripts/validate_agent.py` findings now carry one of four levels instead of two. A check that passes reports
  `OK` rather than `WARN`, an explicitly signed-off fact reports `ACCEPT` with its reason, and only an unsigned
  observation is a `WARN`. Previously all 21 outputs were `WARN`, so a real problem was indistinguishable from a
  passing check. The shipped configuration now reports 0 errors, 0 warnings, 4 accepted, 21 confirmed.
- `scripts/validate_agent.py` gained `--verbose` (list passing checks) and `--explain` (list the accepted findings
  and their reasons).
- The file-name check is now an error when the file name stops matching the declared agent code, rather than
  silently passing. The README has always stated that renaming the file breaks every existing import; the validator
  now enforces it.
- `MaximumInteractions` is reported as a confirmed check rather than being checked silently.
- CI: the validator step now runs with `--strict`, so an unsigned-off finding fails the build. Added
  `workflow_dispatch`, a concurrency group that cancels superseded runs, and a Python version banner.
- CI: the test step pipes through `tee` under `set -o pipefail` and asserts a non-zero test count, so a test
  failure still fails the build and a suite that silently collects nothing is caught.
- Tool execution protocol: `Get_Extended_Attribute_Values` is now called with `ItemId` only. It previously
  instructed the agent to also pass an `OrganizationId`, which that tool does not accept.
- Tool execution protocol: added an on-demand `getProductCosts` step. The tool was attached to the agent but no
  prompt text reached it, so it was unreachable in practice. It is keyed on `ItemNumber`, not `ItemId`, and its
  data is summary context only and never marks another attribute as differing.
- Tool failure handling: a transport, authentication, or server error is no longer reported as "item not found",
  and a failed or empty call now renders as `Data unavailable` instead of an empty value that could be read as a
  difference. Fewer than two usable items now stops the comparison instead of rendering a one-sided table.
- Summarization prompt: the `#ffe6e6` highlight is applied only when both cells hold a known value; unknown cells
  are never highlighted.
- Summarization prompt: `DO NOT COLLAPSE` is now scoped to the rows actually rendered, resolving its conflict with
  the documented show-only-differences behaviour. The anti-grouping intent is unchanged.
- `README.md`: corrected the data-flow diagram, which showed `getProductCosts` and
  `Get_Extended_Attribute_Values` being called "using IDs"; corrected `#ffe6e6`, which is the row background rather
  than the red text colour; added the model id, the REST API version, the empty-REST-trigger and no-op-EMAIL
  handler import steps, and the OCI home-region note.
- CI: `json-validate.yml` now runs the validator and the test suite on pushes and pull requests, with
  `actions/checkout@v4` and `actions/setup-python@v5`.

### Known issues (unchanged, needs a human in AI Agent Studio)
All four are unchanged from the shipped configuration. The validator now reports each one as an acknowledged
`ACCEPT` finding with its reason, not as an unacknowledged warning, and records them in `ACCEPTED_FINDINGS` and in
the README's `Known Limitations` section.
- `modelConfiguration.code` is `ORA_MODEL_CONFIG_PREMIUM_OPEN_AI_GPT_4_1_MINI` while the effective model is
  `OCI_GPT_5_MINI`. The code is Oracle-assigned; the model is selected by `model`/`modelName`/`provider`. Left as
  shipped because changing an Oracle-assigned code can break an import.
- `partnerMetadata.Name` is the opaque value `gvhb`. Its origin is not recorded in this repository; a human must
  confirm it identifies no customer or person, and in particular that it is not someone's initials.
- `Specification.dataPipeline.errorHandlers` contains an `EMAIL` handler with empty recipients, subject, and body,
  so pipeline errors are silently dropped until an operator configures it.
- `Specification.triggers` is an empty `REST` trigger, so the calling endpoint contract is chosen at import.

## [1.0.0] - 2026-09-19
### Added
- Initial release of the Oracle Fusion Product Comparison Advisor configuration (`PRODUCT_COMPARATOR_V13.json`).
- Comprehensive README with architecture diagrams and Oracle deployment steps.
- Complete Community Health Profile (Contributing, Code of Conduct, Security Policy, Issue Templates, PR Template).
- Automated CI pipeline (GitHub Actions) for JSON syntax validation.
- CODEOWNERS file for PR review enforcement.
