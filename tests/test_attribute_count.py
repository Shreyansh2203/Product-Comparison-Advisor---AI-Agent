"""Pins the advertised attribute count to what the agent config actually whitelists.

The README headline used to claim "~120 attributes" while the shipped whitelist held
62, and the same README stated 62 in its own Known Limitations. Nothing tested the
number, so the inflation survived every review. These tests make the claim checkable.
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "PRODUCT_COMPARATOR_V13.json"
README = REPO / "README.md"

SECTION_HEADING = "STANDARD COMPARISON ATTRIBUTES"
# A group bullet looks like "- <Group name>: attr, attr, attr" and the group name is
# followed by a colon. The rule bullets in the same block have the same shape, so
# they are told apart by case: a group name is written in title case ("Overview",
# "Sales & Order Management", "Product Details (ITEM_EXTENDED_ATTRIBUTES)") while a
# rule label is written in capitals ("LOOKUP CODES", "IDENTIFIER ROW", "UNKNOWN
# MARKERS"). Listing the rule names here instead would be a second copy that goes
# stale the next time a rule is added, and a rule parsed as a group inflates the
# count this file exists to pin.
GROUP_BULLET = re.compile(r"^-\s*([^:]+):\s*(.+)$")
RULE_LABEL_SHAPE = re.compile(r"^[A-Z][A-Z0-9 &/-]*$")


def _whitelist_groups() -> list[tuple[str, list[str]]]:
    prompt = json.loads(CONFIG.read_text(encoding="utf-8"))["agents"][0]["Prompt"]
    lines = prompt.split("\n")
    start = next(i for i, line in enumerate(lines) if SECTION_HEADING in line)
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].strip()
        if stripped and stripped == stripped.upper() and len(stripped) > 12 and not stripped.startswith("-"):
            end = j
            break

    groups: list[tuple[str, list[str]]] = []
    for line in lines[start:end]:
        match = GROUP_BULLET.match(line.strip())
        if not match:
            continue
        name, rest = match.group(1).strip(), match.group(2)
        if RULE_LABEL_SHAPE.match(name):
            continue
        groups.append((name, [item.strip() for item in rest.split(",") if item.strip()]))
    return groups


class TestAdvertisedAttributeCount(unittest.TestCase):
    def setUp(self) -> None:
        self.groups = _whitelist_groups()
        self.total = sum(len(attrs) for _, attrs in self.groups)
        self.readme = README.read_text(encoding="utf-8")

    def test_the_whitelist_is_parsed_at_all(self) -> None:
        # Guards the parser itself: if the section heading moves or the bullet format
        # changes, every count assertion below would silently pass on zero.
        self.assertGreaterEqual(len(self.groups), 8)
        self.assertGreater(self.total, 50)

    def test_the_total_matches_the_number_the_readme_advertises(self) -> None:
        # 62 -> 63 when `Item Number` joined the whitelist as the identifier row.
        # The pin stays exact on purpose: a whitelist edit that forgets to update
        # this number, or this number, is a build failure either way.
        self.assertEqual(
            self.total,
            63,
            f"whitelist holds {self.total} attributes across {len(self.groups)} groups",
        )
        for stale in ("~120", "120+", "62 whitelisted", "62 product and manufacturing"):
            self.assertNotIn(
                stale,
                self.readme,
                f"README still advertises {stale}; the shipped whitelist holds {self.total}",
            )
        self.assertIn(f"{self.total} product and manufacturing attributes", self.readme)

    def test_the_operational_field_count_the_readme_claims_is_consistent(self) -> None:
        # README: "Supplies the 30 operational-attribute fields the whitelist draws from"
        # while the ITEM_EXTENDED_ATTRIBUTES group holds 33; 63 - 33 == 30.
        extended = next(attrs for name, attrs in self.groups if "ITEM_EXTENDED_ATTRIBUTES" in name)
        self.assertEqual(len(extended), 33, "the extended-attribute group is the documented 33")
        self.assertEqual(self.total - len(extended), 30)
        self.assertIn("the 30 operational-attribute fields", self.readme)
        self.assertNotIn("the 29 operational-attribute fields", self.readme)

    def test_the_identifier_row_is_inside_the_whitelist(self) -> None:
        # The defect this count test could not see: the summarizer mandated an
        # Item Number row the whitelist did not list, so the count was right and
        # the rendered table was still wrong.
        self.assertEqual(self.groups[0][0], "Overview")
        self.assertEqual(self.groups[0][1][0], "Item Number")
        self.assertNotIn("LOOKUP CODES", dict(self.groups))
        self.assertNotIn("DIFFERENCE RENDERING", dict(self.groups))
        self.assertNotIn("IDENTIFIER ROW", dict(self.groups))
        self.assertNotIn("UNKNOWN MARKERS", dict(self.groups))


if __name__ == "__main__":
    unittest.main()
