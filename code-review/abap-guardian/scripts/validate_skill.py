#!/usr/bin/env python3
"""
Validation script for ABAP Guardian Skill.
Verifies frontmatter, character limits, structure, and internal reference links.

Author: Kallol Chakraborty
"""

import sys
import re
import pathlib
import yaml

def validate():
    root = pathlib.Path(__file__).parent.parent
    skill_file = root / "SKILL.md"

    if not skill_file.exists():
        print("❌ FAIL: SKILL.md not found")
        sys.exit(1)

    content = skill_file.read_text(encoding="utf-8")

    # 1. Check byte start
    if not content.startswith("---"):
        print("❌ FAIL: SKILL.md does not start with '---'")
        sys.exit(1)

    # 2. Check YAML closing tag
    m = re.search(r'\n---\s*\n', content[3:])
    if not m:
        print("❌ FAIL: SKILL.md missing closing '---'")
        sys.exit(1)

    # 3. Parse frontmatter
    try:
        fm = yaml.safe_load(content[3:m.start()+3])
    except Exception as e:
        print(f"❌ FAIL: YAML parsing error: {e}")
        sys.exit(1)

    # 4. Check required fields
    if "name" not in fm or not fm["name"]:
        print("❌ FAIL: Missing 'name' in frontmatter")
        sys.exit(1)

    if "description" not in fm or not fm["description"]:
        print("❌ FAIL: Missing 'description' in frontmatter")
        sys.exit(1)

    desc_len = len(fm["description"])
    if desc_len > 1024:
        print(f"❌ FAIL: Description length ({desc_len}) exceeds 1024 chars")
        sys.exit(1)

    if len(content) > 100000:
        print(f"❌ FAIL: SKILL.md size ({len(content)}) exceeds 100,000 chars limit")
        sys.exit(1)

    # 5. Check reference links existence
    ref_dir = root / "references"
    if not ref_dir.exists():
        print("❌ FAIL: references/ directory missing")
        sys.exit(1)

    ref_files = list(ref_dir.glob("*.md"))
    if not ref_files:
        print("❌ FAIL: No reference markdown files found")
        sys.exit(1)

    # ── Behavioral Guardrail Checks ─────────────────────────────────────────

    failures = []

    # G1. Guardrails section must exist
    if "## Behavioral Guardrails" not in content:
        failures.append("G1: '## Behavioral Guardrails' section is missing from SKILL.md")

    # G2. At least 3 NEVER directives required
    never_count = len(re.findall(r'\bNEVER\b', content))
    if never_count < 3:
        failures.append(
            f"G2: Insufficient 'NEVER' directives — found {never_count}, minimum is 3"
        )

    # G3. Step-skip prohibition must be present
    skip_prohibited = bool(
        re.search(r'(NEVER skip|must not skip|do not skip|MUST complete all four steps)', content, re.IGNORECASE)
    )
    if not skip_prohibited:
        failures.append(
            "G3: No step-skip prohibition found — add 'NEVER skip' or 'MUST complete all four steps'"
        )

    # G4. Version gate instruction must be present
    version_gate = bool(
        re.search(r'(release version|abap version|abap \d\.\d{2}|abap cloud)', content, re.IGNORECASE)
    )
    if not version_gate:
        failures.append(
            "G4: No version gate instruction found — add explicit ABAP release version guidance"
        )

    # G5. Output completeness gate must reference Before/After requirement
    completeness_gate = bool(
        re.search(r'(before.{0,20}after|after.{0,20}before|refactoring code block)', content, re.IGNORECASE)
    )
    if not completeness_gate:
        failures.append(
            "G5: No output completeness gate found — Before/After code block requirement must be stated"
        )

    # G6. Scope rejection language must be present
    scope_rejection = bool(
        re.search(r'(scope.{0,40}reject|non.abap|outside this skill.s scope|not review non.abap)', content, re.IGNORECASE)
    )
    if not scope_rejection:
        failures.append(
            "G6: No scope rejection instruction found — add non-ABAP refusal guidance"
        )

    if failures:
        for f in failures:
            print(f"❌ FAIL [Guardrail]: {f}")
        sys.exit(1)

    # ── Summary ─────────────────────────────────────────────────────────────
    print("✅ PASS: SKILL.md frontmatter & structure valid.")
    print(f"  - Name: {fm['name']}")
    print(f"  - Description length: {desc_len}/1024 chars")
    print(f"  - File size: {len(content):,} chars")
    print(f"  - Reference files validated: {len(ref_files)}")
    for rf in sorted(ref_files):
        print(f"    • references/{rf.name}")
    print("✅ PASS: All behavioral guardrail checks passed.")
    print(f"  - 'NEVER' directives found: {never_count}")
    print(f"  - Step-skip prohibition:    {'✓' if skip_prohibited else '✗'}")
    print(f"  - Version gate:             {'✓' if version_gate else '✗'}")
    print(f"  - Completeness gate:        {'✓' if completeness_gate else '✗'}")
    print(f"  - Scope rejection:          {'✓' if scope_rejection else '✗'}")

if __name__ == "__main__":
    validate()
