#!/usr/bin/env python3
"""Structural and contract validation for the Product Comparison Advisor agent configuration.

The deliverable of this repository is a single declarative JSON document that is
imported into Oracle Fusion AI Agent Studio. A plain `jq empty` only proves the
file parses; it says nothing about whether the document is internally consistent
or whether the README still describes it accurately.

This script closes that gap. It is a pure-stdlib validator with no runtime
dependencies, runnable as:

    python scripts/validate_agent.py

It performs five families of checks:

  * structure    - the document has the keys AI Agent Studio expects and is self-consistent
  * contract     - the prompt only calls tools that are actually defined, the model
                   and REST endpoints are present, and the documented output
                   contract (HTML table, #ffe6e6 highlight) is intact
  * guardrails   - the anti-hallucination, prompt-injection, and tool-failure
                   guardrails are present in the agent prompt text
  * disclosure   - no credentials, tenancy identifiers, or customer data are
                   committed, and the README still matches the configuration
  * deployment   - the work an operator must finish at import time is still
                   declared, and the README still tells them to do it

Findings carry one of four levels, and the distinction between them is the
point of the script. A check that passes is reported as `OK`, not as a
warning; a check that reports something real but unfixable in this repository
is reported as `ACCEPT` and carries the reason recorded in `ACCEPTED_FINDINGS`
below; only something that nobody has signed off on is a `WARN` or an `ERROR`.
A gate whose output is one undifferentiated wall of lines teaches readers to
ignore it, so `--strict` fails on `WARN` alone and the shipped configuration
passes it.

Exit codes: 0 = no errors, 1 = at least one error (or a warning under
`--strict`), 2 = the validator could not run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(REPO_ROOT, "PRODUCT_COMPARATOR_V13.json")
DEFAULT_README = os.path.join(REPO_ROOT, "README.md")

ERROR = "ERROR"
WARNING = "WARN"
ACCEPTED = "ACCEPT"
OK = "OK"

# Findings that are genuine observations but that this repository has
# deliberately decided not to fix. Each is downgraded from WARN to ACCEPT when
# it fires, so the default output separates "nobody has signed this off" from
# "this is signed off, here is why". A finding is only listed here when fixing
# it is either impossible without tenant information or would risk breaking an
# existing Oracle AI Agent Studio import.
#
# Adding an entry is a decision, not a silencing mechanism: the reason is
# printed with the finding, documented in README.md under "Known Limitations",
# and the entry itself goes stale (a real WARN) if the underlying finding stops
# firing, so the list cannot quietly rot into a blanket suppression.
ACCEPTED_FINDINGS = {
    "model-code": (
        "Oracle assigns modelConfiguration.code when the agent is exported, and the "
        "model is selected by model/modelName/provider rather than by this code. Editing "
        "an Oracle-assigned code risks breaking the AI Agent Studio import, so the "
        "mismatch is recorded here instead of rewritten."
    ),
    "partner-metadata": (
        "partnerMetadata.Name is an opaque four-character value whose provenance is not "
        "recorded anywhere in this repository. It may be meaningful to Oracle, so it is "
        "left exactly as shipped. A human must confirm it identifies no customer or "
        "person; see README 'Known Limitations'."
    ),
    "pipeline/error-handler": (
        "The EMAIL error handler's recipient, subject, and body are tenant facts that "
        "cannot be known from this repository, and a placeholder address would be worse "
        "than an empty one. The README makes it an explicit operator task at import time."
    ),
    "trigger/rest-empty": (
        "The REST trigger's endpoint contract belongs to whichever system calls the "
        "agent, which is not known at authoring time. The README makes it an explicit "
        "operator task at import time."
    ),
}

TOP_LEVEL_KEYS = {
    "Specification",
    "WorkflowCode",
    "Name",
    "Description",
    "Family",
    "Product",
    "agents",
    "agentMappings",
    "partnerMetadata",
}

AGENT_KEYS = {
    "Specification",
    "AgentCode",
    "Name",
    "Prompt",
    "tools",
    "AgentType",
    "MaximumInteractions",
}

AGENT_ROLE_KEYS = {"modelConfiguration", "agentRole", "summarizationPrompt"}

# The tool naming convention used by this agent family: `Get_X_Y` / `getXxx`.
TOOL_REF_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")
TOOL_REF_SHAPE_RE = re.compile(r"^(?:Get_|get)[A-Za-z0-9_]+$")
ENDPOINT_RE = re.compile(r"/fscmRestApi/resources/([0-9.]+)/([A-Za-z0-9_]+)")
README_ENDPOINT_RE = re.compile(r"/fscmRestApi/resources/([0-9.]+)/([A-Za-z0-9_]+)")

HIGHLIGHT_COLOR = "#ffe6e6"

# Guardrail categories. Each entry is (code, label, any-of keyword groups).
# A group is satisfied when every alternative in it appears (case-insensitively).
GUARDRAIL_CATEGORIES = [
    (
        "no-fabrication",
        "explicitly forbids inventing or inferring values",
        [["no fabrication"], ["must be copied"], ["does not exist for you"]],
    ),
    (
        "unknown-is-not-a-difference",
        "states that missing/null data is not a difference",
        [["unknown is not a difference"]],
    ),
    (
        "tool-failure-handling",
        "states that a failed tool call is unknown data, not a difference",
        [["tool failure"], ["not a difference"]],
    ),
    (
        "insufficient-data",
        "refuses to compare when fewer than two items have data",
        [["too few valid items"], ["fewer than two"]],
    ),
    (
        "prompt-injection",
        "treats API-returned values as data, never as instructions",
        [["prompt injection"], ["untrusted"], ["not instructions"]],
    ),
    (
        "boolean-translation",
        "keeps the documented Yes/No boolean translation contract",
        [["boolean values"], ["yes", "no"]],
    ),
]

SECRET_VALUE_PATTERNS = [
    ("tenancy OCID", re.compile(r"ocid1\.[a-z0-9]+\.[a-z0-9-]*ocid1")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{8,}")),
    ("OCI host", re.compile(r"\.oraclecloud\.com")),
    ("absolute URL", re.compile(r"https?://")),
]

SECRET_KEY_PATTERN = re.compile(
    r'"(password|passwd|secret|client_secret|api_key|apikey|auth_token|'
    r'access_token|refresh_token|private_key|connection_string)"\s*:',
    re.IGNORECASE,
)

CUSTOMER_NAME_PATTERN = re.compile(r"verdesian", re.IGNORECASE)


class Finding:
    __slots__ = ("level", "code", "message", "reason")

    def __init__(self, level, code, message, reason=None):
        self.level = level
        self.code = code
        self.message = message
        self.reason = reason

    def __str__(self):
        head = "%-6s [%s] %s" % (self.level, self.code, self.message)
        if self.reason:
            return head + "\n         reason: " + self.reason
        return head


def finding(level, code, message):
    return Finding(level, code, message)


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()

def reject_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError("duplicate JSON key: %s" % key)
        seen[key] = value
    return seen


def load_config(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    doc = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    return doc, raw


def get_agent(doc):
    agents = doc.get("agents") or []
    if not agents:
        return None
    return agents[0]


def collect_tool_names(agent):
    names = []
    for tool in agent.get("tools") or []:
        rest = tool.get("RestTool") or {}
        props = rest.get("ObjectProperties") or {}
        for entry in props.get("tools") or []:
            name = entry.get("name")
            if name:
                names.append(name)
    return names


def collect_endpoints(agent):
    endpoints = []
    for tool in agent.get("tools") or []:
        rest = tool.get("RestTool") or {}
        props = rest.get("ObjectProperties") or {}
        for entry in props.get("tools") or []:
            endpoints.append(
                {
                    "tool": entry.get("name"),
                    "resourcePath": entry.get("resourcePath", ""),
                    "base": rest.get("RestResourcePath", ""),
                    "operationType": entry.get("operationType"),
                    "params": [
                        p.get("name")
                        for p in entry.get("parameterDefinitions") or []
                    ],
                }
            )
    return endpoints


def prompt_texts(agent):
    spec = agent.get("Specification") or {}
    return " ".join(
        [
            agent.get("Prompt") or "",
            spec.get("agentRole") or "",
            spec.get("summarizationPrompt") or "",
        ]
    )


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------


def check_structure(doc, raw, ctx):
    out = []
    missing = sorted(TOP_LEVEL_KEYS - set(doc))
    if missing:
        out.append(finding(ERROR, "top-level-keys", "missing top-level keys: %s" % ", ".join(missing)))
    else:
        out.append(finding(OK, "top-level-keys", "all expected top-level keys present"))

    spec = doc.get("Specification") or {}
    if spec.get("jsonSchemaName") != "Workflow.spec":
        out.append(
            finding(
                WARNING,
                "schema-name",
                "Specification.jsonSchemaName is %r, expected 'Workflow.spec'" % spec.get("jsonSchemaName"),
            )
        )
    if doc.get("Architecture") != "single_agent":
        out.append(
            finding(
                WARNING,
                "architecture",
                "top-level Architecture is %r, expected 'single_agent'" % doc.get("Architecture"),
            )
        )

    agents = doc.get("agents") or []
    if len(agents) != 1:
        out.append(finding(ERROR, "agent-count", "expected exactly 1 agent, found %d" % len(agents)))
        return out

    agent = agents[0]
    missing_agent = sorted(AGENT_KEYS - set(agent))
    if missing_agent:
        out.append(
            finding(ERROR, "agent-keys", "missing agent keys: %s" % ", ".join(missing_agent))
        )
    missing_role = sorted(AGENT_ROLE_KEYS - set(agent.get("Specification") or {}))
    if missing_role:
        out.append(
            finding(
                ERROR,
                "agent-spec-keys",
                "missing agent Specification keys: %s" % ", ".join(missing_role),
            )
        )

    # Identity must agree everywhere it is declared, otherwise an import binds
    # the workflow to a different agent than the one that was reviewed.
    codes = {
        "WorkflowCode": doc.get("WorkflowCode"),
        "Name": doc.get("Name"),
        "agentMappings[0].AgentCode": (doc.get("agentMappings") or [{}])[0].get("AgentCode"),
        "agentMappings[0].AgentTargetCode": (doc.get("agentMappings") or [{}])[0].get("AgentTargetCode"),
        "Specification.agentsValueMappings[0].agentCode": (
            (spec.get("agentsValueMappings") or [{}])[0].get("agentCode")
        ),
        "agents[0].AgentCode": agent.get("AgentCode"),
        "agents[0].Name": agent.get("Name"),
    }
    distinct = {v for v in codes.values() if v is not None}
    if len(distinct) > 1:
        out.append(
            finding(
                ERROR,
                "identity-mismatch",
                "agent identity is inconsistent: %s" % ", ".join("%s=%s" % (k, v) for k, v in codes.items()),
            )
        )
    else:
        out.append(finding(OK, "identity", "agent identity consistent: %s" % next(iter(distinct))))

    if not isinstance(agent.get("MaximumInteractions"), int) or agent.get("MaximumInteractions", 0) < 1:
        out.append(
            finding(
                ERROR,
                "max-interactions",
                "agents[0].MaximumInteractions must be a positive integer, got %r"
                % agent.get("MaximumInteractions"),
            )
        )
    else:
        out.append(
            finding(OK, "max-interactions", "agent turn limit: %d" % agent["MaximumInteractions"])
        )

    # The file name is the agent's published code and existing imports bind to
    # it, so a rename is a breaking change rather than a cosmetic one.
    declared_file = os.path.basename(ctx["config_path"])
    if codes["WorkflowCode"] and not declared_file.startswith(str(codes["WorkflowCode"])):
        out.append(
            finding(
                ERROR,
                "file-name",
                "file name %r does not match the declared agent code %r; renaming this file "
                "breaks every existing import" % (declared_file, codes["WorkflowCode"]),
            )
        )
    else:
        out.append(
            finding(OK, "file-name", "file name %r matches the declared agent code" % declared_file)
        )

    partner = doc.get("partnerMetadata") or {}
    opaque = {k: v for k, v in partner.items() if v and len(str(v).strip()) <= 4}
    if opaque:
        out.append(
            finding(
                WARNING,
                "partner-metadata",
                "partnerMetadata contains an opaque short value %s; confirm it identifies no customer or person"
                % opaque,
            )
        )
    return out


def check_contract(doc, raw, ctx):
    out = []
    agent = get_agent(doc)
    if agent is None:
        return out

    tool_names = collect_tool_names(agent)
    if not tool_names:
        out.append(finding(ERROR, "tools", "no REST tools are defined on the agent"))
        return out
    out.append(
        finding(OK, "tools", "tools defined: %s" % ", ".join(tool_names))
    )

    # Every tool the prompt tells the agent to call must actually be defined.
    text = prompt_texts(agent)
    referenced = []
    for match in TOOL_REF_RE.finditer(text):
        token = match.group(1)
        if token in tool_names:
            referenced.append(token)
        elif TOOL_REF_SHAPE_RE.match(token):
            out.append(
                finding(
                    ERROR,
                    "undefined-tool",
                    "prompt references tool %r which is not defined (defined: %s)"
                    % (token, ", ".join(tool_names)),
                )
            )
    missing_refs = [n for n in tool_names if n not in referenced]
    if missing_refs:
        out.append(
            finding(
                WARNING,
                "unreferenced-tool",
                "tool(s) attached but never mentioned in the prompt text: %s"
                % ", ".join(missing_refs),
            )
        )
    else:
        out.append(
            finding(OK, "tool-references", "every defined tool is referenced in the prompt text")
        )

    # Model configuration must be present at both levels and self-consistent.
    for label, mc in (
        ("Specification.modelConfiguration", (doc.get("Specification") or {}).get("modelConfiguration")),
        ("agents[0].Specification.modelConfiguration", (agent.get("Specification") or {}).get("modelConfiguration")),
    ):
        if not mc:
            out.append(finding(ERROR, "model", "%s is missing" % label))
            continue
        if not mc.get("model") or not mc.get("modelName"):
            out.append(finding(ERROR, "model", "%s is missing model/modelName" % label))
    top = (doc.get("Specification") or {}).get("modelConfiguration") or {}
    inner = (agent.get("Specification") or {}).get("modelConfiguration") or {}
    if top and inner:
        for key in ("model", "modelName", "provider", "code"):
            if top.get(key) != inner.get(key):
                out.append(
                    finding(
                        ERROR,
                        "model-mismatch",
                        "modelConfiguration.%s differs between workflow and agent (%r vs %r)"
                        % (key, top.get(key), inner.get(key)),
                    )
                )
    model_name = inner.get("modelName") or top.get("modelName") or ""
    if model_name:
        out.append(finding(OK, "model", "inference model: %s / %s" % (top.get("model"), model_name)))
    if inner.get("code") and model_name:
        normalise = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
        if normalise(model_name) not in normalise(inner["code"]):
            out.append(
                finding(
                    WARNING,
                    "model-code",
                    "modelConfiguration.code (%s) does not name the effective model (%s); this code is assigned by"
                    " Oracle and is not what selects the model" % (inner["code"], model_name),
                )
            )

    # REST endpoints: one consistent API version, GET only, path/query agreement.
    versions = set()
    for entry in collect_endpoints(agent):
        path = entry["resourcePath"] or ""
        base = entry["base"] or ""
        match = ENDPOINT_RE.search(path)
        base_match = ENDPOINT_RE.search(base)
        if not match:
            out.append(
                finding(
                    ERROR,
                    "endpoint",
                    "tool %r resourcePath is not a recognised fscmRestApi path: %r" % (entry["tool"], path),
                )
            )
            continue
        versions.add(match.group(1))
        if base_match and base_match.group(1) != match.group(1):
            out.append(
                finding(
                    ERROR,
                    "endpoint",
                    "tool %r resourcePath version %s differs from RestResourcePath version %s"
                    % (entry["tool"], match.group(1), base_match.group(1)),
                )
            )
        if base and not path.startswith(base + "?"):
            out.append(
                finding(
                    ERROR,
                    "endpoint",
                    "tool %r resourcePath does not extend its RestResourcePath (%r vs %r)"
                    % (entry["tool"], base, path),
                )
            )
        if entry["operationType"] != "GET":
            out.append(
                finding(
                    ERROR,
                    "endpoint",
                    "tool %r uses operationType %r, expected GET" % (entry["tool"], entry["operationType"]),
                )
            )
        if not entry["params"]:
            out.append(finding(ERROR, "endpoint", "tool %r declares no parameters" % entry["tool"]))
    if len(versions) > 1:
        out.append(
            finding(ERROR, "api-version", "mixed SCM REST API versions in one agent: %s" % ", ".join(sorted(versions)))
        )
    elif versions:
        out.append(
            finding(OK, "api-version", "SCM REST API version consistent: %s" % next(iter(versions)))
        )

    # Documented output contract.
    summarization = (agent.get("Specification") or {}).get("summarizationPrompt") or ""
    if HIGHLIGHT_COLOR not in summarization:
        out.append(
            finding(
                ERROR,
                "highlight-color",
                "the documented highlight colour %s is absent from the summarization prompt" % HIGHLIGHT_COLOR,
            )
        )
    else:
        out.append(
            finding(OK, "highlight-color", "highlight colour %s present" % HIGHLIGHT_COLOR)
        )
    for needle, label in (
        ("<tr>", "an HTML row per attribute"),
        ("<table", "an HTML table"),
        ("RAW HTML", "an explicit raw-HTML output contract"),
    ):
        if needle not in summarization:
            out.append(
                finding(ERROR, "output-format", "summarization prompt no longer documents %s (%r)" % (label, needle))
            )
    return out


def check_guardrails(doc, raw, ctx):
    out = []
    agent = get_agent(doc)
    if agent is None:
        return out
    prompt = (agent.get("Prompt") or "").lower()
    summarization = ((agent.get("Specification") or {}).get("summarizationPrompt") or "").lower()
    combined = prompt + "\n" + summarization

    for code, label, groups in GUARDRAIL_CATEGORIES:
        missing = [g for g in groups if not any(alt in combined for alt in g)]
        if missing:
            out.append(
                finding(
                    ERROR,
                    "guardrail/" + code,
                    "missing prompt guardrail: %s (no match for %s)"
                    % (label, " / ".join(repr(m) for m in missing)),
                )
            )
        else:
            out.append(finding(OK, "guardrail/" + code, "guardrail present: %s" % label))

    # The system prompt (not just the summarizer) must forbid invention, so the
    # prohibition is in force while the agent is still choosing field values.
    if "never invent" not in prompt and "no fabrication" not in prompt:
        out.append(
            finding(
                ERROR,
                "guardrail/system-prompt",
                "the agent Prompt itself does not forbid inventing values; only the summarizer does",
            )
        )
    return out


def check_disclosure(doc, raw, ctx):
    out = []
    for label, pattern in SECRET_VALUE_PATTERNS:
        match = pattern.search(raw)
        if match:
            out.append(
                finding(
                    ERROR,
                    "secret/" + label,
                    "configuration appears to contain a %s (%r)" % (label, match.group(0)[:40]),
                )
            )
    match = SECRET_KEY_PATTERN.search(raw)
    if match:
        out.append(
            finding(ERROR, "secret/key", "configuration contains a credential-shaped key: %r" % match.group(1))
        )
    match = CUSTOMER_NAME_PATTERN.search(raw)
    if match:
        out.append(
            finding(
                ERROR,
                "customer-data",
                "configuration contains the customer name %r; the README disclaims customer data" % match.group(0),
            )
        )
    if not any(f.code.startswith(("secret/", "customer-data")) for f in out):
        out.append(
            finding(
                OK,
                "disclosure",
                "no credentials, tenancy identifiers, hosts, or customer data found in the configuration",
            )
        )

    readme = ctx.get("readme_text")
    if readme is not None:
        declared = re.search(r"It does not contain proprietary Oracle source code or sensitive client data", readme)
        if declared and CUSTOMER_NAME_PATTERN.search(raw):
            out.append(
                finding(ERROR, "customer-data", "the README disclaimer is contradicted by the configuration")
            )
    return out


def check_readme(doc, raw, ctx):
    out = []
    readme = ctx.get("readme_text")
    agent = get_agent(doc)
    if readme is None:
        out.append(finding(WARNING, "readme", "README.md not found; cross-document checks skipped"))
        return out
    if agent is None:
        return out

    for name in re.findall(r"PRODUCT_COMPARATOR_[A-Z0-9_]+\.json", readme):
        if not os.path.exists(os.path.join(REPO_ROOT, name)):
            out.append(
                finding(ERROR, "readme/file", "README references %s which does not exist" % name)
            )
    referenced_files = set(re.findall(r"PRODUCT_COMPARATOR_[A-Z0-9_]+\.json", readme))
    if referenced_files and os.path.basename(ctx["config_path"]) not in referenced_files:
        out.append(
            finding(
                ERROR,
                "readme/file",
                "README does not reference the configuration file being validated (%s)"
                % os.path.basename(ctx["config_path"]),
            )
        )

    json_paths = {(m.group(1), m.group(2)) for m in ENDPOINT_RE.finditer(raw)}
    readme_paths = set(README_ENDPOINT_RE.findall(readme))
    for version, resource in sorted(readme_paths - json_paths):
        out.append(
            finding(
                ERROR,
                "readme/endpoint",
                "README documents /%s/%s which the agent does not call" % (version, resource),
            )
        )
    for version, resource in sorted(json_paths - readme_paths):
        out.append(
            finding(
                WARNING,
                "readme/endpoint",
                "agent calls /%s/%s which the README does not document" % (version, resource),
            )
        )
    if readme_paths and readme_paths <= json_paths:
        out.append(
            finding(
                OK,
                "readme/endpoint",
                "all %d README endpoints match the configuration" % len(readme_paths),
            )
        )

    tool_names = collect_tool_names(agent)
    for token in re.findall(r"\b(?:Get_[A-Za-z_]+|get[A-Z][A-Za-z0-9]*)\b", readme):
        if token not in tool_names:
            out.append(
                finding(ERROR, "readme/tool", "README names tool %r which the agent does not define" % token)
            )
    if not any(f.code == "readme/tool" and f.level == ERROR for f in out):
        out.append(finding(OK, "readme/tool", "README tool names match the defined tools"))

    if HIGHLIGHT_COLOR not in readme:
        out.append(
            finding(
                ERROR,
                "readme/highlight",
                "README does not state the %s highlight colour used by the agent" % HIGHLIGHT_COLOR,
            )
        )
    else:
        out.append(finding(OK, "readme/highlight", "README states the %s highlight colour" % HIGHLIGHT_COLOR))

    model_name = ((agent.get("Specification") or {}).get("modelConfiguration") or {}).get("modelName") or ""
    if model_name and model_name.lower() not in readme.lower():
        out.append(
            finding(ERROR, "readme/model", "README does not name the configured model %r" % model_name)
        )
    elif model_name:
        out.append(finding(OK, "readme/model", "README names the configured model %s" % model_name))

    if "Show only the differences" not in readme and "show only differences" not in readme.lower():
        out.append(
            finding(
                WARNING,
                "readme/behaviour",
                "README no longer documents the show-only-differences behaviour",
            )
        )
    return out


def check_deployment(doc, raw, ctx):
    """Check the configuration work that only an operator can finish at import.

    The recipient of the pipeline error email and the endpoint contract of the
    REST trigger are both tenant facts: neither can be derived from this
    repository, and inventing a placeholder for either would be worse than
    leaving the field empty. They are therefore reported as acknowledged
    findings rather than errors.

    They are still asserted, because the moment the JSON stops declaring them
    the documented import steps stop being necessary and the README becomes
    misleading. That is what the README cross-check below enforces, so an
    accepted finding can never quietly turn into an undocumented gap.
    """
    out = []
    spec = doc.get("Specification") or {}

    for handler in (spec.get("dataPipeline") or {}).get("errorHandlers") or []:
        if handler.get("type") != "EMAIL":
            continue
        blank = sorted(
            entry.get("name")
            for entry in handler.get("inputs") or []
            if not (entry.get("value") or "").strip()
        )
        if blank:
            out.append(
                finding(
                    WARNING,
                    "pipeline/error-handler",
                    "the EMAIL error handler has no %s, so pipeline errors are discarded"
                    % ", ".join("'%s'" % name for name in blank),
                )
            )

    for trigger in spec.get("triggers") or []:
        if trigger.get("type") == "REST" and not trigger.get("inputs"):
            out.append(
                finding(
                    WARNING,
                    "trigger/rest-empty",
                    "the REST trigger declares no inputs, so the calling endpoint contract "
                    "must be chosen at import",
                )
            )

    readme = ctx.get("readme_text")
    if readme is None:
        return out
    lowered = readme.lower()
    undocumented = [
        label
        for needle, label in (
            ("errorhandlers", "the EMAIL error-handler recipient"),
            ("triggers", "the REST trigger endpoint"),
        )
        if needle not in lowered
    ]
    for label in undocumented:
        out.append(
            finding(
                ERROR,
                "readme/import-step",
                "README no longer documents the import-time step for %s" % label,
            )
        )
    if not undocumented:
        out.append(
            finding(
                OK,
                "readme/import-step",
                "README documents both import-time configuration steps",
            )
        )
    return out


CHECKS = [
    ("structure", check_structure),
    ("contract", check_contract),
    ("guardrails", check_guardrails),
    ("disclosure", check_disclosure),
    ("readme", check_readme),
    ("deployment", check_deployment),
]


def classify(findings):
    """Downgrade signed-off findings from WARN to ACCEPT, and police the list.

    A finding listed in `ACCEPTED_FINDINGS` that no longer fires means the
    underlying problem was fixed (or the check changed shape) and the list has
    become stale. That is reported as a real warning so the entry is removed
    rather than left behind as a dead blanket.
    """
    for item in findings:
        if item.level == WARNING and item.code in ACCEPTED_FINDINGS:
            item.level = ACCEPTED
            item.reason = ACCEPTED_FINDINGS[item.code]
    fired = {f.code for f in findings if f.level == ACCEPTED}
    for code in sorted(set(ACCEPTED_FINDINGS) - fired):
        findings.append(
            finding(
                WARNING,
                "accepted/stale",
                "ACCEPTED_FINDINGS lists %r but it no longer occurs; remove the entry" % code,
            )
        )
    return findings


def validate(doc, raw, config_path=DEFAULT_CONFIG, readme_text=None):
    ctx = {"config_path": config_path, "readme_text": readme_text}
    findings = []
    for _, check in CHECKS:
        try:
            findings.extend(check(doc, raw, ctx))
        except Exception as exc:  # a crashing check is itself a failure
            findings.append(finding(ERROR, "validator", "check raised %s: %s" % (type(exc).__name__, exc)))
    return classify(findings)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the Product Comparison Advisor agent configuration.")
    parser.add_argument("config", nargs="?", default=DEFAULT_CONFIG, help="path to the agent JSON")
    parser.add_argument("--readme", default=DEFAULT_README, help="path to the README to cross-check")
    parser.add_argument("--no-readme", action="store_true", help="skip the README cross-checks")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat unacknowledged warnings as errors (accepted findings do not count)",
    )
    parser.add_argument("--verbose", action="store_true", help="also print the passing OK checks")
    parser.add_argument(
        "--explain", action="store_true", help="print the accepted-findings list and its reasons"
    )
    parser.add_argument("--quiet", action="store_true", help="only print errors and the summary")
    args = parser.parse_args(argv)

    try:
        doc, raw = load_config(args.config)
    except FileNotFoundError:
        print("cannot read configuration: %s" % args.config, file=sys.stderr)
        return 2
    except ValueError as exc:
        print("invalid JSON in %s: %s" % (args.config, exc), file=sys.stderr)
        return 2

    readme_text = None
    if not args.no_readme:
        try:
            readme_text = read_text(args.readme)
        except OSError as exc:
            print("cannot read README: %s" % exc, file=sys.stderr)
            return 2

    print("validating %s" % os.path.relpath(args.config, REPO_ROOT))
    findings = validate(doc, raw, config_path=args.config, readme_text=readme_text)

    errors = [f for f in findings if f.level == ERROR]
    warnings = [f for f in findings if f.level == WARNING]
    accepted = [f for f in findings if f.level == ACCEPTED]
    confirmed = [f for f in findings if f.level == OK]

    for item in findings:
        if args.quiet and item.level != ERROR:
            continue
        if item.level == OK and not args.verbose:
            continue
        print("  " + str(item))

    if args.explain:
        print("")
        print("acknowledged findings (%d accepted, %d confirmed):" % (len(accepted), len(confirmed)))
        for code in sorted(ACCEPTED_FINDINGS):
            print("  %s [%s]" % (ACCEPTED.ljust(6), code))
            print("         %s" % ACCEPTED_FINDINGS[code])

    print("")
    print(
        "%d error(s), %d warning(s), %d accepted, %d confirmed"
        % (len(errors), len(warnings), len(accepted), len(confirmed))
    )
    if errors:
        print("FAILED: the configuration does not satisfy its own contract.")
        return 1
    if args.strict and warnings:
        print("FAILED (--strict): unacknowledged warnings treated as errors.")
        return 1
    print("OK: the configuration is valid and internally consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
