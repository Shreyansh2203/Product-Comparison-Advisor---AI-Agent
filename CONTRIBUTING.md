# Contributing to Oracle Fusion Product Comparison Advisor

Thanks for considering a contribution. This project is small on purpose: it is one
agent configuration, its validation gate, and its tests. The rules below are short
because the failure modes they prevent are expensive.

## The one rule that is absolute

**Never rename `PRODUCT_COMPARATOR_V13.json`.** Not to fix a typo, not to bump a
version, not to match a local folder name. The file name is the agent's published
code: anyone who has already imported this agent, or who follows a link to it, is
referring to that exact path. Renaming it is a breaking change, and the version in
the name is bumped by Oracle on export rather than by us. Record content changes
in [`CHANGELOG.md`](./CHANGELOG.md) under the existing `1.1.0` heading instead.

## Editing the configuration safely

[`PRODUCT_COMPARATOR_V13.json`](./PRODUCT_COMPARATOR_V13.json) is the deliverable.
Because it is imported into a running Oracle environment, treat every edit as a
deployment.

1. **Keep it parseable.** Validate after *every single change*, not once at the end
   of a batch:

   ```bash
   python -c "import json; json.load(open('PRODUCT_COMPARATOR_V13.json', encoding='utf-8'))"
   ```

2. **Keep the formatting stable.** The file uses four-space indentation and is
   already re-serialised by Oracle on export. Do not reflow it, do not re-indent it,
   and do not add comments. A whole-file reformat makes the next diff unreadable and
   buries the behavioural change you actually made. If you edit the JSON
   programmatically, write it back with `json.dump(..., indent=4, ensure_ascii=False)`
   and confirm the diff shows only your lines.

3. **No secrets, ever.** No tenant URLs, no credentials, no tokens, no customer
   names, no real item data. The gate enforces this, but the point is that a
   reviewer should never have to trust the gate.

4. **No third-party dependencies and no `.env`.** Standard library only, and there
   is no build step. Adding a dependency changes the project's deployment model for
   everyone who clones it.

5. **Do not weaken the guardrails without testing in a DEV or TEST instance.** The
   prompts in `DATA INTEGRITY`, `TOOL EXECUTION PROTOCOL`, and the summarization
   prompt's `STRICT FORMATTING RULES` are the agent's correctness. The gate checks
   that each rule and each of its mandatory clauses is still written; it cannot check
   that the model still obeys them. That is the part only a tenant can tell you.

6. **Do not change** the tool names, the output format, the raw-HTML requirement, or
   the `#ffe6e6` / `#cc0000` highlight contract. Those are published interfaces
   between the agent and the frontend that renders its output.

7. **New endpoints** must follow the `11.13.18.05` Oracle SCM REST API schema, and
   every REST operation must use the same version as the existing ones.

8. **A new tool means a new call site.** `scripts/prompt_contract.py` holds a
   `CALL_SITES` table that the validator enforces: every tool attached to the agent
   must have a declared call site with its real parameters, and the prompt must state
   that call contract verbatim. This is the check that catches a prompt telling the
   agent to pass an argument a tool does not declare.

9. **A whitelist change means a fixture change.** `scripts/prompt_fixtures.py` keys
   its synthetic responses on the attribute names the prompt lists, and a test
   asserts the two match exactly. If you add or rename a whitelisted attribute,
   update the fixture in the same commit.

## Run the gate before you push

These are the same three commands CI runs, and all three must pass:

```bash
python -c "import json; json.load(open('PRODUCT_COMPARATOR_V13.json', encoding='utf-8'))"
python scripts/validate_agent.py --strict
python -m unittest discover -s tests
```

`validate_agent.py` is stdlib-only and enforces the contract above: undefined tool
references, a parameter a tool does not declare, a changed highlight colour, mixed
REST API versions, missing anti-hallucination / prompt-injection / tool-failure
guardrails, unvalidated model properties, committed credentials or customer names,
and README claims that no longer match the configuration all fail the build.

`--strict` is what makes it a gate rather than a report. It fails on any finding not
already signed off in `ACCEPTED_FINDINGS`, so:

- an acknowledged limitation cannot quietly become a regression, because
  `ACCEPTED_FINDINGS` goes stale and the stale entry itself becomes a warning;
- a new problem cannot hide by being added to `ACCEPTED_FINDINGS`. If you add an
  entry, you are signing off on a fact you can justify, and you must give it a
  written reason **and** document it in the README's Known Limitations table, which
  a test enforces.

## The two suites, and what each one can tell you

`tests/test_agent_config.py` checks the configuration: shape, tool structure,
disclosure, secrets, the model, and the validator's own behaviour.

`tests/test_prompt_contract.py` checks the prompt contract. It parses the prompt into
named rules and asserts that each rule is actually written with each of its mandatory
clauses, cross-checks every tool and parameter the prompt names against the declared
signatures, checks the HTML output template's column arithmetic against the stated
`N+1` rule, and feeds representative Oracle-shaped tool responses to the rules as
written to pin what those rules require of the agent.

That second suite is **rule verification, not model verification**. It proves the
prompt says what it must say and that those statements imply the pinned behaviour.
It cannot prove the model obeys them; only a run in a tenant can. Please do not
describe it as a behavioural test of the agent.

## Submitting a pull request

1. Fork the repository and branch from `main`.
2. Make the change, keeping the JSON's formatting stable.
3. Update [`README.md`](./README.md) and [`CHANGELOG.md`](./CHANGELOG.md) in the same
   pull request whenever you change agent behaviour or the contract. The README's
   worked example is generated from the prompt's own template and compared byte for
   byte, so a prompt change that alters the output shape will fail the tests until
   the example is regenerated.
4. Run the three commands above.
5. Open the pull request, describing what changed in the prompt and why, and flagging
   anything that needs a tenant to confirm.

## Reporting a bug

Open an issue and include the exact prompt used, the Oracle SCM version, the
organisation context, the request, and the full output. If the agent hallucinated a
value or failed to map a specific SCM code, the tool response is the most useful
thing you can attach.

## Hardening a prompt rule

The `RULES` table in `scripts/prompt_contract.py` is the list of guardrails the
harness enforces. Adding a rule means adding its mandatory clauses there, and a test
will immediately check that removing any one of those clauses fails. If you strengthen
an existing rule, add the new clause and let the test tell you the rule is enforced
rather than merely present.

Clause presence is only half of it. A rule can also be *inverted* — every required
phrase kept, with a clause added that permits the opposite — and a presence check
reports that as healthy. Every rule therefore carries a set of `forbidden` patterns
that, if they match the rule body, mean the rule is not in force. When you add a rule,
add patterns to it and a matching sample phrase to `INVERSIONS` in
`tests/test_prompt_contract.py`; a test fails if a pattern has no sample or a sample
has no pattern, so neither half can be added alone. The sample phrases are necessarily
a list of known phrasings rather than a general test: extending it is a deliberate,
reviewed edit, which is the point.
