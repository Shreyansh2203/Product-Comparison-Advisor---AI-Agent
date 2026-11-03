# Product-Comparison-Advisor

[![JSON Validation](https://github.com/Shreyansh2203/Product-Comparison-Advisor---AI-Agent/actions/workflows/json-validate.yml/badge.svg)](https://github.com/Shreyansh2203/Product-Comparison-Advisor---AI-Agent/actions/workflows/json-validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Single agent](https://img.shields.io/badge/AI%20Agent-single%20agent%20%C2%B7%20SCM-blue)](PRODUCT_COMPARATOR_V13.json)

An Oracle Fusion Cloud AI Agent that compares two or more Items from the product
catalogue across **63 product and manufacturing attributes** and returns a self-contained
HTML comparison table. It is a single declarative JSON document
([PRODUCT_COMPARATOR_V13.json](PRODUCT_COMPARATOR_V13.json)) that imports into Oracle
Fusion AI Agent Studio. This repository also carries the pure-stdlib Python harness that
keeps that document internally consistent, and the test suite that pins its behaviour —
including this README, which is part of the contract rather than a brochure.

## 📖 Table of Contents

- [Overview](#overview)
- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Repository contents](#repository-contents)
- [The three tools](#the-three-tools)
- [Output contract](#output-contract)
- [Model and catalogue scope](#model-and-catalogue-scope)
- [Guardrails](#guardrails)
- [🎯 Worked Example](#-worked-example)
- [Installation and import](#installation-and-import)
- [Validation](#validation)
- [Development and tests](#development-and-tests)
- [Known limitations](#known-limitations)
- [Security and data handling](#security-and-data-handling)
- [License](#license)

---

## Overview

Comparing two Items by hand means opening the same record twice and eyeballing dozens of
fields — an error-prone exercise precisely where mistakes are expensive (pay-to-produce,
pay-to-design, supplier quality). The Product Comparison Advisor automates the read-only
part of that job: given two or more item numbers it pulls the authoritative values from
Oracle Fusion, aligns them side by side, flags the rows that genuinely differ, and tells
you which ones it could not tell.

The deliverable is not a service or an app. It is the agent definition itself, kept honest
by tooling: structure checks, a prompt-contract harness that proves each behavioural rule
is actually written, and cross-document tests that fail when this file stops matching the
configuration next to it. It does not contain proprietary Oracle source code or sensitive
client data, and the worked example below uses synthetic demonstration items only.

## What it does

Given two or more item numbers and an organisation code, the agent:

1. Calls `Get_Operational_Attribute_Values` with the item number and organization, reads
   the 15-digit `ItemId` out of the response, and then calls `Get_Extended_Attribute_Values`
   with only that `ItemId` — the two calls are sequential, never parallel.
2. Builds a side-by-side HTML comparison table over the standard attribute set, renders
   rows that differ on values known on both sides with the `#ffe6e6` highlight, and leaves
   unknowns as `-` rather than guessing.
3. Offers an explicit "Show only the differences" toggle to collapse the shared rows.
4. Answers cost questions on demand via `getProductCosts` — and never calls it otherwise.

Nothing is written back to Oracle. The agent is read-only.

## Architecture

Single-agent design (`Architecture: single_agent`). The agent reasons over three seeded
REST tools; there is no multi-agent handoff and no human-approval step.

```mermaid
flowchart TD
    U([User: compare two items]) --> A[PRODUCT_COMPARATOR_V13 agent · Gpt-5 Mini]
    A -->|Get_Operational_Attribute_Values · ItemNumber, OrgCode| B[/fscmRestApi/resources/11.13.18.05/itemOperationalAttributes]
    B -->|response carries 15-digit ItemId| A
    A -->|Get_Extended_Attribute_Values · ItemId| C[/fscmRestApi/resources/11.13.18.05/itemExtendedAttributes]
    A -->|getProductCosts · ItemNumber<br/>only when the question is about cost| D[/fscmRestApi/resources/11.13.18.05/itemsV2]
    A --> T[Self-contained HTML comparison table<br/>differing rows in #ffe6e6]
```

Key properties of the flow:

- **Inventory item ids, not names.** `Get_Extended_Attribute_Values` is keyed on the
  15-digit `ItemId` and rejects an `OrganizationId`; the 15-digit id is only available
  after the operational call returns, which is why the two calls are strictly ordered.
- **Costs are opt-in.** `getProductCosts` is called only when the user asks about cost,
  price, or margin. It is never used to mark another attribute as differing.
- **Both tools reject filter metacharacters.** Before every call, `ItemNumber` must match
  `^[A-Za-z0-9._-]{1,40}$`, `OrgCode` must match `^[A-Za-z0-9._-]{1,10}$`, and `ItemId`
  must match `^[0-9]{15}$`. A value outside its pattern is not trimmed, escaped, or
  guessed — the call is refused and the user is told why.

## Repository contents

| Path | What it is |
|---|---|
| [PRODUCT_COMPARATOR_V13.json](PRODUCT_COMPARATOR_V13.json) | The agent definition as exported from AI Agent Studio; the deliverable |
| [scripts/validate_agent.py](scripts/validate_agent.py) | Structural, contract, guardrail, disclosure and deployment validator |
| [scripts/prompt_contract.py](scripts/prompt_contract.py) | Offline harness that parses the prompt into named rules and proves each is written |
| [scripts/prompt_fixtures.py](scripts/prompt_fixtures.py) | Synthetic scenarios and the HTML renderer used to produce the worked example |
| [tests/](tests/) | Structural, prompt-contract and cross-document tests |
| [.github/workflows/json-validate.yml](.github/workflows/json-validate.yml) | CI: parse check, `--strict` validator, full suite |
| [.github/workflows/codeql.yml](.github/workflows/codeql.yml) | CodeQL for the harness code |

## The three tools

The agent calls exactly three seeded REST tools. Tool codes are Oracle seeded and are not
editable from this repository, which is part of why the configuration is documentary rather
than generative.

| Tool | Purpose | REST call (all `GET`, version `11.13.18.05`) |
|---|---|---|
| `Get_Operational_Attribute_Values` | Operational attributes for an item in an organisation; response carries the 15-digit inventory item id | `/fscmRestApi/resources/11.13.18.05/itemOperationalAttributes` |
| `Get_Extended_Attribute_Values` | Extended attributes for an inventory item id, e.g. packaging, handling, compliance | `/fscmRestApi/resources/11.13.18.05/itemExtendedAttributes` |
| `getProductCosts` | Item cost information | `/fscmRestApi/resources/11.13.18.05/itemsV2` |

The operational endpoint is queried by `ItemNumber` and `OrgCode`; the extended endpoint by
`InventoryItemId`; the costs endpoint by `ItemNumber`, with optional `ProductCosts.*` filter
parameters (see [Known limitations](#known-limitations): those filters are bound to nothing).

## Output contract

- **One table, two-plus items.** A single self-contained HTML table with one column per
  item; grouped sections (Overview, Product Details (ITEM_EXTENDED_ATTRIBUTES),
  Manufacturing, Inventory, Physical Attributes, Sales & Order Management, Planning,
  Purchasing), in that order.
- **Only real differences are red.** A row that differs on values known on both sides is
  highlighted with `#ffe6e6` and bolded. A row that is unknown on at least one side renders
  `-` and is not highlighted. `Data unavailable` renders when the call failed, and is also
  not a difference. A raw code, a `N/A`, or an error string is never rendered as a value.
- **Yes/No booleans stay Yes/No.** Raw Oracle booleans are translated through the documented
  contract; raw `Y`/`N`, `True`/`False`, `1`/`0` are never shown in the table.
- **HTML injection is impossible by construction.** Every value taken from the API response
  is HTML-escaped before it is placed into the table; `<script>` from a description field
  comes out as text, never as markup.
- **Show only the differences** — the answer carries an explicit toggle that hides rows on
  which all stated values agree.
- **Nothing is written.** No POST/PUT/PATCH anywhere; the agent has no mutation path.

## Model and catalogue scope

- Model: **Gpt-5 Mini** (`modelConfiguration`, provider `CERT_PREMIUM`), reasoning effort
  `medium`, max completion tokens 8000.
- Single agent, `MaximumInteractions: 20` on the agent. The top-level beside
  `Architecture` also carries `MaximumInteractions: null` — see [Known
  limitations](#known-limitations).
- The whitelist holds **63 product and manufacturing attributes**, drawn from two sources:
  the 33-field `ITEM_EXTENDED_ATTRIBUTES` group seeded from the extended-attributes tool,
  and the remaining 30 operational-attribute fields — and `tests/test_attribute_count.py`
  fails if either number or the wording ever drifts.
- Family `SCM`, product `PRODUCT_MANAGEMENT`, use case `NA` as exported.

## Guardrails

The prompt is a list of named rules, and each rule is proven in force by the offline
harness rather than asserted in prose. The ones that matter most:

- **No fabrication.** Values are never invented or inferred. A missing value is rendered
  unknown, never interpolated from a similar item, a name match, or an earlier answer.
- **Unknown is not a difference.** A null/absent/`-`/`Data unavailable` cell renders as
  unknown and can never be reported as a difference.
- **Tool failure is unknown data, not a difference.** A failed call is surfaced as
  `Data unavailable`; it never produces a "differs" verdict or a crash.
- **Insufficient items abort.** Fewer than two items with data ends the comparison rather
  than producing a partial table.
- **Prompt injection is data, never instructions.** Values returned by the API are treated
  as literal strings to render, never as instructions to follow.
- **Escape everything.** All dynamic values are HTML-escaped on the way into the table.
- **Guess-free tool calls.** No call is issued with a value that fails its pattern; no
  parameter is invented; `getProductCosts` is cost-questions only.

## 🎯 Worked Example

Two synthetic demonstration items (`SYNTH-1001` in organisation `DEMO1`, `SYNTH-1002`)
compared on the standard attribute set. 3 rows differ on values known on both sides and are
highlighted; 3 rows are unknown on at least one side and are shown as a dash rather than
highlighted.

```html
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<style>
  .agy-table { width:100%; border-collapse:collapse; margin:15px 0; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; font-size:14px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }
  .agy-table th { background-color:#f4f5f7; color:#172b4d; padding:12px; text-align:left; border-bottom:2px solid #dfe1e6; }
  .agy-table td { padding:10px 12px; border-bottom:1px solid #dfe1e6; color:#091e42; }
  .agy-section { background-color:#e9ecef !important; color:#495057; text-transform:uppercase; font-size:12px; letter-spacing:0.5px; }
  .agy-summary { font-family:-apple-system,sans-serif; color:#333; line-height:1.6; font-size:14px; }
</style>
</head>
<body>
<p class="agy-summary"><b>Total Items Compared: 2</b></p>
<table class="agy-table">
<thead>
<tr><th style="width:25%;">Attribute</th><th>SYNTH-1001</th><th>SYNTH-1002</th></tr>
<tr class="agy-section"><th colspan="3"><b>Overview</b></th></tr>
<tr><td>Item Number</td><td>SYNTH-1001</td><td>SYNTH-1002</td></tr>
<tr><td>Description</td><td>Synthetic demonstration item</td><td>Synthetic demonstration item</td></tr>
<tr style="background-color: #ffe6e6; font-weight: bold; color: #cc0000;"><td>Item Status</td><td>Active</td><td>Hold</td></tr>
<tr><td>Lifecycle Phase</td><td>Implementation</td><td>Implementation</td></tr>
<tr><td>User Item Type</td><td>Finished Good</td><td>Finished Good</td></tr>
<tr><td>Long Description</td><td>Synthetic item published as the README worked example</td><td>Synthetic item published as the README worked example</td></tr>
<tr><td>Primary Unit of Measure</td><td>Each</td><td>Each</td></tr>
<tr><td>Secondary Unit of Measure</td><td>-</td><td>-</td></tr>
<tr class="agy-section"><th colspan="3"><b>Product Details (ITEM_EXTENDED_ATTRIBUTES)</b></th></tr>
<tr style="background-color: #ffe6e6; font-weight: bold; color: #cc0000;"><td>Packaging Size</td><td>SYNTH-PKG-A</td><td>SYNTH-PKG-B</td></tr>
<tr><td>Packable Size</td><td>12</td><td>12</td></tr>
<tr><td>Sample Reporting</td><td>No</td><td>No</td></tr>
<tr><td>Control Organism</td><td>None</td><td>None</td></tr>
<tr><td>Transportation Method</td><td>Ambient</td><td>Ambient</td></tr>
<tr><td>Internal Description</td><td>Synthetic demo item</td><td>Synthetic demo item</td></tr>
<tr><td>Net Weight Unit</td><td>g</td><td>g</td></tr>
<tr><td>Net Weight Value</td><td>500</td><td>500</td></tr>
<tr><td>Brand Type</td><td>None</td><td>None</td></tr>
<tr><td>Product Line</td><td>Synthetic</td><td>Synthetic</td></tr>
<tr><td>Factory Formula (FFN)</td><td>None</td><td>None</td></tr>
<tr><td>FFN Description</td><td>None</td><td>None</td></tr>
<tr><td>GTS Flag</td><td>No</td><td>No</td></tr>
<tr><td>Process Flow Rate</td><td>None</td><td>None</td></tr>
<tr><td>Packaging Type</td><td>Bottle</td><td>Bottle</td></tr>
<tr><td>Equipment Type</td><td>None</td><td>None</td></tr>
<tr><td>Shipping Status</td><td>Active</td><td>Active</td></tr>
<tr><td>Package Format</td><td>Bottle</td><td>Bottle</td></tr>
<tr><td>ePIF ID</td><td>None</td><td>None</td></tr>
<tr><td>Company Brand</td><td>None</td><td>None</td></tr>
<tr><td>Attribute</td><td>None</td><td>None</td></tr>
<tr><td>Minimum Order Qty</td><td>1</td><td>1</td></tr>
<tr><td>ABC Class</td><td>C</td><td>C</td></tr>
<tr><td>Container Fill Ratio</td><td>-</td><td>100</td></tr>
<tr><td>Cases Per Pallet</td><td>24</td><td>24</td></tr>
<tr><td>Country of Origin</td><td>XX</td><td>XX</td></tr>
<tr><td>ECCN Number</td><td>None</td><td>None</td></tr>
<tr><td>DOT Shipping Description</td><td>None</td><td>None</td></tr>
<tr><td>DOT Exception</td><td>No</td><td>No</td></tr>
<tr><td>International Shipping Description</td><td>None</td><td>None</td></tr>
<tr><td>Manufactured Description</td><td>Synthetic</td><td>Synthetic</td></tr>
<tr><td>3rd Party Testing Required</td><td>No</td><td>No</td></tr>
<tr><td>Nutrient Class</td><td>None</td><td>None</td></tr>
<tr class="agy-section"><th colspan="3"><b>Manufacturing</b></th></tr>
<tr><td>Contract Manufacturing</td><td>Yes</td><td>Yes</td></tr>
<tr class="agy-section"><th colspan="3"><b>Inventory</b></th></tr>
<tr><td>Material Control</td><td>No</td><td>No</td></tr>
<tr><td>Inventory Item</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Stocked</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Transaction Enabled</td><td>Yes</td><td>Yes</td></tr>
<tr style="background-color: #ffe6e6; font-weight: bold; color: #cc0000;"><td>Lot Control</td><td>Full Control</td><td>No Control</td></tr>
<tr><td>Lot Expiration</td><td>No</td><td>No</td></tr>
<tr><td>Lot Expiration Control</td><td>No</td><td>No</td></tr>
<tr><td>Status</td><td>Active</td><td>Active</td></tr>
<tr><td>Lot Status Enabled</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Default Lot Status</td><td>Active</td><td>-</td></tr>
<tr class="agy-section"><th colspan="3"><b>Physical Attributes</b></th></tr>
<tr><td>Weight</td><td>1000</td><td>1000</td></tr>
<tr><td>Unit Weight</td><td>1 kg</td><td>1 kg</td></tr>
<tr class="agy-section"><th colspan="3"><b>Sales &amp; Order Management</b></th></tr>
<tr><td>Sales Account</td><td>No</td><td>No</td></tr>
<tr class="agy-section"><th colspan="3"><b>Planning</b></th></tr>
<tr><td>General Planning</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Planning Method</td><td>Planning</td><td>Planning</td></tr>
<tr><td>Make or Buy</td><td>Buy</td><td>Buy</td></tr>
<tr><td>Planner</td><td>DEMO Planner</td><td>DEMO Planner</td></tr>
<tr><td>MPS/MRP Planning</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Costing</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Cumulative Total</td><td>No</td><td>No</td></tr>
<tr class="agy-section"><th colspan="3"><b>Purchasing</b></th></tr>
<tr><td>Purchasable</td><td>Yes</td><td>Yes</td></tr>
</tbody>
</table>

<div class="agy-summary">
<h3>Business Summary</h3>
<p>Two synthetic demonstration items compared on the standard attribute set. 3 rows differ on values known on both sides and are highlighted; 3 rows are unknown on at least one side and are shown as a dash rather than highlighted.</p>
<h3>Cross-Module Insights</h3>
<ul>
<li><b>Inventory:</b> Both items are stocked, with lot control on one item and off on the other.</li>
<li><b>Procurement:</b> Both items are purchasable, so no purchasing difference is reported.</li>
<li><b>Planning:</b> Both items use the same planning method and planner.</li>
</ul>
<h3>Key Differences</h3>
<ul><li>Item Status</li><li>Packaging Size</li><li>Lot Control</li></ul>
</div>
</body></html>
```

The highlighted rows are Item Status, Packaging Size and Lot Control — the three rows that
differ on values known on both sides. Container Fill Ratio (`-` on SYNTH-1001) and Default
Lot Status (`-` on SYNTH-1002) are unknown on one side and render as a dash, not as
differences.

## Installation and import

The document imports into AI Agent Studio as an agent. Two parts of the configuration are
tenant facts and ship intentionally blank; finish both at import time, not before:

1. **The `errorHandlers` entry for the pipeline.** The `EMAIL` error handler ships with
   empty `toList`, `ccList`, `subject` and `body`. Pipeline errors are discarded until you
   set real values; the import-time step is to fill in the recipients for a mailbox your
   organisation actually monitors.
2. **The `triggers` entry (REST).** The REST trigger declares no inputs. The endpoint
   contract belongs to whichever system calls the agent, so you choose it at import —
   leave it blank and the agent has no invocation path.

Both are asserted by the validator (see [Validation](#validation)) and neither can be known
from this repository, so neither value is invented.

After import, sanity-check the three tools land enabled and scoped as
read-only, and run one comparison against two synthetic items in a test organisation before
pointing the agent at real catalogue questions.

## Validation

Two gates run in CI on every push and pull request
([.github/workflows/json-validate.yml](.github/workflows/json-validate.yml)):

```bash
python -m json.tool PRODUCT_COMPARATOR_V13.json > /dev/null   # syntax
python scripts/validate_agent.py --strict --no-readme          # contract gate
python -m unittest discover -s tests -v                        # full suite
```

`validate_agent.py` is a pure-stdlib, zero-dependency validator. Its findings carry one of
four levels — `OK`, `ACCEPT`, `WARN`, `ERROR` — and `--strict` fails on anything that is
not either clean or explicitly signed off in `ACCEPTED_FINDINGS`. What it checks, briefly:

- **structure** — the document has the keys AI Agent Studio expects and is self-consistent
- **contract** — every tool the prompt names is attached, parameters match the
  documentation, the seeded tool codes are untouched, the model and the three REST
  endpoints are present and consistent
- **guardrails** — each named rule is written in its own prompt block, clause by clause
- **disclosure** — no credentials, tenancy identifiers, or customer data anywhere in the
  document, and this README still describes it accurately
- **deployment** — the two import-time steps above are still declared, and documented

The accepted findings are listed in [Known limitations](#known-limitations). An accepted
entry that stops firing is itself reported as stale, so the list cannot decay into a blanket
suppression.

## Development and tests

```bash
python -m unittest discover -s tests     # everything, no third-party dependencies
```

The suite is stdlib-only by design; there is nothing to install. Coverage of the harness is
near-total, and the cross-document tests are the point, not a courtesy:

- `tests/test_attribute_count.py` parses the whitelist out of the prompt and requires the
  **63 product and manufacturing attributes** figure in this file, plus the 33-field
  extended group and the 30 operational-attribute fields; the pins are exact on purpose.
- The prompt-contract tests prove each guardrail rule is written, that no prompt line
  permits what a rule forbids, and that the renderer output in this README is byte-identical
  to what the harness produces for the worked-example scenario.
- The README links, the table of contents, the constraints on tool names and endpoints, and
  the accepted-findings table are all asserted, so this file cannot drift.

## Known limitations

These are the findings the validator reports as `ACCEPT` rather than `WARN`, each with the
reason it stands. They are acknowledged, not hidden; each row names the exact code:

| `model-code` | `modelConfiguration.code` (`ORA_MODEL_CONFIG_PREMIUM_OPEN_AI_GPT_4_1_MINI`) is assigned by Oracle when the agent is exported, and the model is actually selected by `model`/`modelName`/`provider`. Rewriting an Oracle-assigned code risks breaking the AI Agent Studio import; the mismatch is recorded instead. |
| `partner-metadata` | `partnerMetadata.Name` is an opaque four-character value whose provenance is recorded nowhere in this repository. It may be meaningful to Oracle, so it is left exactly as shipped. A human must confirm it identifies no customer or person before production use. |
| `pipeline/error-handler` | The `EMAIL` error handler's `toList`, `ccList`, `subject` and `body` are tenant facts that cannot be known here. Inventing a placeholder address would be worse than an empty one, so the README makes it an explicit operator task at import time. |
| `trigger/rest-empty` | The REST trigger declares no inputs, because the endpoint contract belongs to whichever system calls the agent. It must be chosen at import; it cannot be derived from this repository. |
| `max-interactions/scope` | The document declares two fields named `MaximumInteractions`: the agent's 20, and the top-level one beside `Architecture`, which is `null`. Oracle documents the same field name in two places with the same meaning (the Agents tab and the Agent Team record) but does not document which the export format honours when both are present. The agent's 20 stands, the top level stays null, and a human must confirm precedence in AI Agent Studio. |
| `tool/parameter-unbound` | `getProductCosts` declares four `ProductCosts.*` filter parameters that never appear in its resourcePath, so passing them cannot change the HTTP request. The tool binding is Oracle seeded (`ORA_SCM_PRODUCTMAN_ITEMCOSTS`) and not editable here, so the prompt's "plus optional cost filters" cannot be exercised. Reported rather than rewritten. |

## Security and data handling

It does not contain proprietary Oracle source code or sensitive client data. Every example
in this repository and in the prompt is synthetic: `SYNTH-1001`, `SYNTH-1002`, `DEMO1`,
`SYNTH-PKG-A`. No real item numbers, customer names, 10-digit organisation ids, tenancy
ocids, hosts, credentials, or connection strings appear anywhere in this repository; the
validator enforces this mechanically and fails the build if one ever appears.

The prompt itself is written so that hostile input is boring: values returned by the API
are data, never instructions; values rendered into the table are HTML-escaped; and no tool
is reachable with a filter metacharacter that could break out of a query literal.

To report a security problem, do not open a public issue; contact the author directly via
the GitHub profile that owns this repository.

## License

[MIT](LICENSE)
