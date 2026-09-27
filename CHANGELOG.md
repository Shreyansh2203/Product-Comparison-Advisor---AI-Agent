# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-27
Prompt hardening and verification tooling. `PRODUCT_COMPARATOR_V13.json` keeps its name and its agent code
(`PRODUCT_COMPARATOR_V13`); this is a content revision, not a re-versioning, so existing imports are unaffected.

### Added
- **HTML-escaping rule in both prompts, and a check for it.** The agent's entire output is a complete
  `<!DOCTYPE html>` document that the Oracle Visual Builder Compare Items component renders in an
  `<iframe srcdoc>`, while `summarizationPrompt` required every cell to be copied verbatim and
  `DATA INTEGRITY` rule 5 told the agent to display an HTML/JS payload as a literal string. Nobody
  had told it to escape that literal, so an `<img src=x onerror=...>` value written into any item
  `Description` by ordinary data entry reached the document as markup and executed in the Fusion
  origin. `DATA INTEGRITY` rule 6 and summarization rule 5 now require `&` → `&amp;`, `<` → `&lt;`,
  `>` → `&gt;` and `"` → `&quot;` in every value before it reaches a cell, and name the returned
  value as the thing being escaped rather than the thing being obeyed. `HTML_ESCAPE_SEQUENCES` is
  the single table both prompts and the offline renderer are checked against, so the two cannot
  drift, and the harness derives a `must_html_escape` obligation per cell when the rule is in force.
- **Input constraints for all three `resourcePath`s.** Each interpolates a token into a quoted
  `q=` filter literal (`ItemNumber='{ItemNumber}'`, `ItemNumber='{ItemNumber}' AND
  OrganizationCode='{OrgCode}'`, `InventoryItemId='{ItemId}'`) and `ItemNumber` is typed by the user,
  so one apostrophe broke out of the literal. The previous check only asked whether a named
  parameter *exists*. New `TOOL EXECUTION PROTOCOL` rule 6 states a `^...$` pattern for
  `ItemNumber`, `OrgCode` and `ItemId` and forbids the call when a value fails it; the same pattern
  and an explicit single-quote refusal now sit in each parameter's own `description`. A validator
  check requires both, requires the two to state the *same* pattern, and probes every breakout
  character against the pattern, so a character class that reads like a constraint and still accepts
  an apostrophe is reported.
- **No-unrequested-lookups rule.** The two-layer attribute whitelist constrains interpretation but
  not action, so nothing forbade a tool call for an item the user never named — including a call an
  injected value asked for. New `TOOL EXECUTION PROTOCOL` rule 7 forbids it, and the harness derives
  an `unrequested_calls` obligation from the call log when the rule is in force.
- **Inversion detection, so a guardrail cannot be neutralised by appending.** Clause presence is not
  enough: a prompt that keeps every required phrase and adds a clause permitting the opposite passes
  a presence check, and appending ", or when at least one cell is unknown" to `DIFFERENCES` was
  proven to give zero contract violations that way. Every `Rule` now carries `forbidden` patterns,
  matched against the rule's own body, and a test appends a sample inverting phrase to each one.
  `INVERSIONS` in the tests and the patterns in `prompt_contract` are cross-checked against each
  other, so neither half can be added alone.
- **Seven new guardrail rules**, taking the harness from eleven to eighteen: HTML escaping, tool-input
  patterns, no unrequested lookups, raw booleans never rendered, internal codes never rendered, the
  Item Number row never differenced, and the two fixed UNKNOWN renderings. `validate_agent`'s
  `check_guardrails` now delegates to these rule objects instead of searching the two prompts
  concatenated for keywords, so the gate is clause-scoped rather than keyword-anywhere.
- **Four new scenario fixtures**, and three tests that could not have failed before:
  - `raw-boolean-flags` supplies real JSON booleans. The prompt makes "NEVER output raw true/false"
    its first FATAL ERROR, and no fixture contained a `true`/`false` token, so the test asserting it
    inspected zero cells and could not fail.
  - `unexplained-lookup-code` sets `Lot Control` to `7`, a real tenant key the prompt gives no
    meaning for. The old lookup test only asserted codes the harness already knew, so rendering
    `'7'` — the FATAL ERROR the prompt names — passed.
  - `payload-contains-an-unknown-marker` puts the literal strings `N/A` and `Data unavailable` in a
    payload. The harness treated only `None`/`""`/`-` as unknown, so `Lot Control = "N/A"` against
    `No Control` produced a highlighted difference, contradicting `DATA INTEGRITY` rule 3. The
    marker set is now read out of the prompt's own `DIFFERENCES` rule rather than duplicated here.
  - `call-for-an-item-the-user-never-named` adds a third item's call to a two-item request.
- **Two new derived obligations and two new checks**: `must_html_escape` and `unrequested_calls` in
  the derivation, and `check_tool_parameter_values_are_constrained` plus `check_unknown_markers` in
  the contract. The UNKNOWN markers are parsed out of the prompt, and a prompt that stops
  enumerating them is a build failure rather than a silent empty set.
- **Validator: an `accepted/stale` finding is no longer reported when the run already failed.**
  `check_prompt_semantics` used to return as soon as the contract had any violation, so
  `tool/parameter-unbound` never fired and `classify` then reported the acknowledged entry as
  stale — failing `--strict` with a message pointing at `ACCEPTED_FINDINGS`, i.e. at a list that was
  perfectly fine, while the actual defect sat unremarked above it. Every check now runs on every
  call, and the stale-accepted report is suppressed when there are errors.
- **Tests: every accepted finding must appear in the README as its own table cell.**
  `code.split("/")[-1]` reduced `max-interactions/scope` to `scope`, a substring that occurred
  elsewhere in the README by accident, so the assertion passed while the README documented
  `max-interactions` and the validator emitted `max-interactions/scope`. An inverse test now fails
  on the prefix.
- **Validator: `guardrail/input-validation`, `guardrail/no-unrequested-lookups`,
  `guardrail/internal-code-translation` and `guardrail/html-escaping` as reported checks**, plus
  `tool/filter-constrained` as a confirmed check.
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
- **README: a Portfolio section** linking the author's other four repositories, and a data-flow mermaid diagram
  restored to the architecture section.
- **Tests: every relative link resolves and every table-of-contents anchor exists**, and every accepted finding is
  named in the README.
- **CI: the gate is now proved to be a gate.** A step injects a regression the validator must catch, on a
  throwaway copy, and fails the run if the validator accepts it.

### Changed
- **`Item Number` is now a whitelisted attribute and is exempt from the differencing rule.** The
  summarizer mandated an Item Number row while also saying "render ONLY the attributes listed in the
  system prompt" and "you MUST ONLY output the exact fields listed", and `STANDARD COMPARISON
  ATTRIBUTES` did not list it — so the row was simultaneously mandated and forbidden, and nothing
  exempted it from the differencing rule, making two different item numbers a highlighted
  "difference" on every single comparison. The whitelist is now 63 attributes (the operational
  group is 30, the extended group stays 33), the row is the first attribute under Overview, and a
  new `IDENTIFIER ROW` rule plus the summarizer's whitelist line both forbid highlighting it or
  listing it as a difference. The derivation builds it through the ordinary whitelist path, so the
  special case is gone. `tests/test_prompt_contract.py` deliberately **replaces**
  `test_the_item_number_row_highlights_because_the_rules_compare_it` (which pinned the broken
  behaviour) with `test_the_item_number_row_is_never_a_difference` and
  `test_the_identifier_exemption_is_a_gate_not_a_coincidence`; the second removes the rule's clause
  and asserts the row highlights again, so the exemption is shown to be read from the prompt rather
  than hard-coded. `test_the_item_number_row_is_a_summarizer_only_carve_out`, which asserted the row
  was *absent* from the whitelist, is replaced by
  `test_the_item_number_row_is_whitelisted_and_exempt_from_differencing`.
- **`'N/A'` is gone from the prompt.** `LOOKUP CODES` said to map a null code to `'N/A'` while the two
  `ABSOLUTELY CRITICAL` rules said an unknown value renders as `-`. A new `UNKNOWN MARKERS` bullet
  fixes the set at exactly two renderings — `-` for a value that is absent, `null`, empty, or a code
  whose display meaning the prompt does not state, and `Data unavailable` for a call that did not
  return usable data — and forbids a raw code and `N/A` outright. `LOOKUP CODES` now says a null or
  `-` `DefaultLotStatusId` renders as `-`, `DATA INTEGRITY` rule 2 covers the untranslatable code, and
  the FATAL ERROR bullet says such a code renders as `-` and the cell is UNKNOWN. The harness
  renders an unexplained code as `-` and does not highlight the row.
- **`derive()`'s claim is now true.** Its docstring said an obligation stops being claimed when its
  rule stops being written, but `_build_row` ran unconditionally, so with the differencing rule
  removed `in_force()` was `False` while `differences` stayed fully populated. `_build_row` now reads
  the differencing rule and the identifier-row rule from the contract, so with the differencing rule
  out of force no row is highlighted at all, and the rule is reported in `unspecified_rules`. Every
  obligation in the derivation is gated the same way, and a test asserts the gate is real.
- The harness derives its UNKNOWN marker set from the prompt's `DIFFERENCES` rule rather than holding
  a second copy, and keeps `N/A` only as a documented legacy compatibility marker.
- `Rule.forbidden` inversion patterns were added to every rule. The list is necessarily a list of
  known phrasings rather than a general test, and `Rule` and `CONTRIBUTING.md` both say so; extending
  it is a deliberate, reviewed edit.
- The attribute-count pins moved from 62 to 63 attributes and from 29 to 30 operational fields.
  `tests/test_attribute_count.py` no longer hard-codes the two rule-bullet names it excludes
  (`LOOKUP CODES`, `DIFFERENCE RENDERING`); it now tells a group bullet from a rule bullet by case,
  because a rule parsed as a group inflates the count, and the two new rule bullets would have done
  exactly that. A new test asserts the identifier row is inside the whitelist, which the count could
  not have seen.
- The README worked example is regenerated: the Item Number row is no longer highlighted, three rows
  differ instead of four, and `Key Differences` no longer lists Item Number. The HTML block is
  regenerated by the same test, so this is a consequence rather than an edit.
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
- `agents[0].MaximumInteractions` is still 20 and the top-level value is still null.
- **`PRODUCT_COMPARATOR_V13.json` kept its name, its agent code, and its 2-space / CRLF
  formatting.** The six lines that changed are six JSON string values, all of them prompt or tool
  description text; no key was added, removed, renamed, or reordered, and the file still round-trips
  byte-for-byte through `json.dumps(doc, indent=2, ensure_ascii=False)` with CRLF endings.
- **The two prompt issues the previous revision deferred to a human are now fixed in the prompt
  rather than documented for a tenant**: the Item Number row is whitelisted and exempt, and the
  `LOOKUP CODES` / `DATA INTEGRITY` contradiction is resolved in favour of `-`. Both are pinned by
  tests, and the tests that pinned the old behaviour were deliberately replaced rather than edited
  around.
- **A native `pattern` or `enum` binding was not added to the REST tool parameters.** Whether the
  AI Agent Studio export format accepts a machine-enforced validation key on a tool parameter could
  not be established from this repository, and adding a key Oracle may not recognise risks the import
  in the same way editing `modelConfiguration.code` does. The constraint is therefore written into
  the parameter's own `description` and into the prompt, both of which are certain to be read, and
  the README makes wiring a platform-side binding an explicit import-time step.
- **The `sandbox` attribute on the consuming `<iframe srcdoc>` is left for a human.** What is
  established and recorded in the README: the output is a complete HTML document, the Compare Items
  component renders it in an `srcdoc` frame, such a frame inherits the parent origin unless sandboxed,
  the document is agent-generated so a payload can close the context, and every attribute is writable
  through ordinary data entry. What is **not** established: whether the component sets `sandbox`, and
  with what value — no tenant, app bundle, or component source is reachable from this repository. The
  README gives the devtools check and lists it as an import step.

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
- The shipped configuration reports 0 errors, 0 warnings, 6 accepted, 28 confirmed.
- Test count went from 155 to 200. The baseline at the start of this pass was 158; four of the
  removed counts are the three vacuous assertions and the two tests that pinned the Item Number
  defect, replaced by tests that assert the fixed behaviour and a test that the fix is a gate.
- **Every new test was checked against `HEAD` before it was accepted.** Running HEAD's own
  `prompt_contract`/`prompt_fixtures` on HEAD's own JSON, in an isolated copy, reproduces each
  reported defect: no escaping instruction anywhere in either prompt, `'N/A'` emitted as a
  rendering, `Item Number` absent from the whitelist and highlighted as a difference on every
  comparison, an unexplained code `7` rendered as `'7'` and highlighted, a payload holding `N/A`
  highlighted against a known value, no fixture containing a `true`/`false` token, and appending
  ", or when at least one cell is unknown" to `DIFFERENCES` giving 0 contract violations with the
  rule still reported as in force. The same probe on the shipped tree gives the opposite for each.
- Runtime behaviour against an Oracle Fusion tenant is **not** verified by this revision, and neither is a CI run.
  Both remain open. In particular, whether the model obeys the escaping, input-validation, and
  no-unrequested-lookup rules is not established here; the harness only proves the rules are
  written and what they require.

## [1.0.0] - 2026-09-19
### Added
- Initial release of the Oracle Fusion Product Comparison Advisor configuration (`PRODUCT_COMPARATOR_V13.json`).
- Comprehensive README with architecture diagrams and Oracle deployment steps.
- Complete Community Health Profile (Contributing, Code of Conduct, Security Policy, Issue Templates, PR Template).
- Automated CI pipeline (GitHub Actions) for JSON syntax validation.
- CODEOWNERS file for PR review enforcement.
