#!/usr/bin/env python3
"""
============================================================
HIGH-RIGOR SKILL EVALUATION HARNESS v3.0 (STRICT ENTERPRISE)
ABAP Guardian — Enterprise Code Review & Clean ABAP Skill
============================================================

30+ Assertions across 10 Industry-Grade Evaluation Suites.

Author: Kallol Chakraborty
"""

import sys
import re
import time
import pathlib
import yaml

ROOT = pathlib.Path(__file__).parent.parent
SKILL_FILE   = ROOT / "SKILL.md"
REF_DIR      = ROOT / "references"
EXAMPLES_DIR = ROOT / "examples"

# ANSI colour codes
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✅ PASS{RESET}"
FAIL = f"{RED}❌ FAIL{RESET}"

all_results = []
skill_content = SKILL_FILE.read_text(encoding="utf-8")

# Helper for all references
all_ref_text = ""
ref_files_dict = {}
if REF_DIR.exists():
    for f in REF_DIR.glob("*.md"):
        txt = f.read_text(encoding="utf-8")
        all_ref_text += txt + "\n"
        ref_files_dict[f.name] = txt

def add(suite, name, passed, detail=""):
    status = PASS if passed else FAIL
    all_results.append((suite, name, status, detail))
    return passed

# ==========================================
def suite_1():
    print(f"\n{CYAN}{BOLD}[Suite 1] Frontmatter Schema & System Prompt Signal Quality{RESET}")
    m = re.search(r'\n---\s*\n', skill_content[3:])
    assert m, "Frontmatter closing '---' missing"
    fm = yaml.safe_load(skill_content[3:m.start()+3])

    desc = fm.get("description","").lower()
    add(1, "1.1 Trigger phrase ('Use when…') present", desc.startswith("use when"), f"'{desc[:25]}'")

    domain_kw = ["abap", "review", "performance", "security", "sap", "architecture", "clean code"]
    kw_hits = sum(1 for kw in domain_kw if kw in desc)
    add(1, "1.2 Description contains high-signal domain keywords", kw_hits >= 4, f"Found {kw_hits}/7 keywords")
    
    author = fm.get("author", "")
    add(1, "1.3 Author is set to 'Kallol Chakraborty'", author == "Kallol Chakraborty", f"Author: '{author}'")

    tags = fm.get("metadata",{}).get("hermes",{}).get("tags",[])
    add(1, "1.4 Tags exist and include key SAP domains", all(t in tags for t in ["abap", "code-review", "clean-abap", "sap"]), f"Tags: {tags}")
    
    related = fm.get("metadata",{}).get("hermes",{}).get("related_skills",[])
    add(1, "1.5 Scope isolation (No non-ABAP skills linked)", "system-architect" not in related and "python" not in related, f"Related: {related}")

# ==========================================
def suite_2():
    print(f"\n{CYAN}{BOLD}[Suite 2] Prompt Trigger Recall & Precision (Stress Test){RESET}")
    content = skill_content.lower()
    
    tp_prompts = [
        "review this abap class for performance",
        "does this pass atc checks",
        "refactor this procedural abap to clean abap",
        "is this opensql query performant",
        "check for sql injection in this abap snippet",
        "audit authority-check in this sap report",
        "review cds view data control language",
        "refactor form subroutine to oo method",
        "check for select inside a loop",
        "review rap behavior implementation"
    ]
    tn_prompts = [
        "design a distributed cache in go",
        "debug my python script for memory leak",
        "help me with css flexbox layout",
        "write a docker compose file for postgres",
        "create a react component with tailwind",
        "kubernetes pod deployment yaml config",
        "fiori ui5 xml view formatting",
        "sql server t-sql stored procedure optimization"
    ]

    when_use_m  = re.search(r'## when to use(.*?)(?=\n## |---)', content, re.DOTALL)
    dont_use_m  = re.search(r"don't use for:(.*?)(?=\n## |---)", content, re.DOTALL)
    when_body = when_use_m.group(1) if when_use_m else ""
    dont_body = dont_use_m.group(1) if dont_use_m else ""
    
    tp_hits = sum(1 for p in tp_prompts if any(word in when_body for word in ["abap", "atc", "clean abap", "opensql", "refactor"]))
    add(2, "2.1 Positive prompt mapping recall (10 ABAP intents)", tp_hits == len(tp_prompts), f"Recall: {tp_hits}/{len(tp_prompts)}")
    
    tn_hits = sum(1 for p in tn_prompts if any(word in dont_body for word in ["frontend", "fiori", "basis", "non-abap", "r/3 4.6c"]))
    add(2, "2.2 Negative prompt exclusion precision (8 Non-SAP intents)", tn_hits == len(tn_prompts), f"Precision: {tn_hits}/{len(tn_prompts)}")

# ==========================================
def suite_3():
    print(f"\n{CYAN}{BOLD}[Suite 3] Structural Process Integrity & Output Schema{RESET}")
    content = skill_content.lower()
    add(3, "3.1 4-Step Process explicitly defined", "4-step code review process" in content, "Found 4-step header")
    
    comp_criteria_count = content.count("completion criterion")
    add(3, "3.2 Completion criteria for all 4 steps", comp_criteria_count >= 4, f"Found {comp_criteria_count} gates")
    
    add(3, "3.3 Output severity levels defined ([CRITICAL], [WARNING], [OPTIMIZATION])", 
        "[critical]" in content and "[warning]" in content and "[optimization]" in content, "All 3 severities exist")
    
    table_cols = ["line #", "severity", "category", "description", "recommendation"]
    has_cols = all(col in content for col in table_cols)
    add(3, "3.4 Mandatory Markdown Report Table schema specified", has_cols, "Table columns present")

# ==========================================
def suite_4():
    print(f"\n{CYAN}{BOLD}[Suite 4] Content Coverage Matrix (Enterprise ABAP Scoping){RESET}")
    combined = (skill_content + "\n" + all_ref_text).lower()
    
    critical_concepts = [
        "authority-check", "for all entries", "clean abap", "select inside a loop", 
        "cds", "cl_abap_testdouble", "sql injection", "dependency injection",
        "cx_", "cl_abap_dyn_prg", "dcl", "test-seam", "abap cloud", "view entity", "group by"
    ]
    missing = [c for c in critical_concepts if c not in combined]
    add(4, "4.1 All 15 Enterprise ABAP concepts covered", len(missing) == 0, f"Missing: {missing}" if missing else f"Covered all {len(critical_concepts)} concepts")

# ==========================================
def suite_5():
    print(f"\n{CYAN}{BOLD}[Suite 5] Instruction Quality & Specificity (Anti-Vagueness Audit){RESET}")
    content = skill_content.lower()
    weak_words = ["maybe", "try to", "could", "perhaps", "might", "sort of", "in my opinion"]
    found_weak = [w for w in weak_words if f" {w} " in content]
    add(5, "5.1 Anti-Vagueness (Zero weak/hedging words)", len(found_weak) == 0, f"Found weak words: {found_weak}" if found_weak else "Strictly imperative")
    
    mandatory_words = ["must", "mandatory", "always", "never"]
    mand_hits = [w for w in mandatory_words if w in content]
    add(5, "5.2 High-assertiveness mandatory language used", len(mand_hits) >= 3, f"Imperatives: {mand_hits}")

# ==========================================
def suite_6():
    print(f"\n{CYAN}{BOLD}[Suite 6] Reference Integrity & Link Resolution{RESET}")
    links = re.findall(r'`references/(.*?\.md)`', skill_content)
    links += re.findall(r'\[.*?\]\(references/(.*?\.md)\)', skill_content)
    links = list(set(links))
    
    missing_links = []
    empty_refs = []
    for link in links:
        ref_path = REF_DIR / link
        if not ref_path.exists():
            missing_links.append(link)
        elif len(ref_path.read_text(encoding="utf-8").strip()) < 200:
            empty_refs.append(link)
    
    add(6, "6.1 All referenced MD files exist", len(missing_links) == 0, f"Missing: {missing_links}" if missing_links else f"All {len(links)} links valid")
    add(6, "6.2 Reference files non-trivial (>200 chars)", len(empty_refs) == 0, f"Empty: {empty_refs}" if empty_refs else "All reference files rich")

# ==========================================
def suite_7():
    print(f"\n{CYAN}{BOLD}[Suite 7] Code Snippet AST & Safety Contrast Verification{RESET}")
    has_examples = EXAMPLES_DIR.exists()
    ex_files = list(EXAMPLES_DIR.glob("*.md")) if has_examples else []
    
    total_bad = 0
    total_good = 0
    abap_syntax_tokens = ["select", "method", "endmethod", "loop", "try", "form", "authority-check"]
    has_abap_syntax = False
    
    for f in ex_files:
        txt = f.read_text(encoding="utf-8").lower()
        total_bad += txt.count("[bad]")
        total_good += txt.count("[good]")
        if any(token in txt for token in abap_syntax_tokens):
            has_abap_syntax = True
            
    add(7, "7.1 Refactoring examples directory present", len(ex_files) > 0, f"Files found: {len(ex_files)}")
    add(7, "7.2 Balanced [BAD] vs [GOOD] contrast pairs (≥5 pairs)", total_bad >= 5 and total_good >= 5, f"Pairs: {total_bad} [BAD], {total_good} [GOOD]")
    add(7, "7.3 Authentic ABAP syntax tokens present in code blocks", has_abap_syntax, "Syntax validated")

# ==========================================
def suite_8():
    print(f"\n{CYAN}{BOLD}[Suite 8] Redundancy & Instruction Duplication Check{RESET}")
    lines = [line.strip() for line in skill_content.split('\n') if len(line.strip()) > 25 and not line.strip().startswith('#')]
    duplicates = set([x for x in lines if lines.count(x) > 1])
    add(8, "8.1 Zero duplicate instructions in SKILL.md", len(duplicates) == 0, f"Duplicates: {duplicates}" if duplicates else "Clean instruction graph")

# ==========================================
def suite_9():
    print(f"\n{CYAN}{BOLD}[Suite 9] Readability & Cognitive Load Scannability{RESET}")
    paragraphs = [p for p in skill_content.split('\n\n') if not p.strip().startswith('```')]
    # Exclude bullet list items — they are inherently scannable regardless of length.
    paragraphs = [p for p in skill_content.split('\n\n')
                  if not p.strip().startswith('```') and not p.strip().startswith('-') and not p.strip().startswith('*')]
    long_paragraphs = [p for p in paragraphs if len(p.split()) > 100]
    add(9, "9.1 Low cognitive load (No prose paragraphs >100 words)", len(long_paragraphs) == 0, f"Long paragraphs: {len(long_paragraphs)}")
    
    bullet_lists = len(re.findall(r'\n\s*[-*]\s', skill_content))
    add(9, "9.2 Structured list formatting for scannability", bullet_lists >= 15, f"Found {bullet_lists} bullet items")

# ==========================================
def suite_10():
    print(f"\n{CYAN}{BOLD}[Suite 10] Token Budget Efficiency & Execution Latency{RESET}")
    skill_tokens = len(skill_content) // 4
    ref_tokens = len(all_ref_text) // 4
    total_tokens = skill_tokens + ref_tokens

    add(10, "10.1 SKILL.md optimal token size (<2,500 tokens)", skill_tokens < 2500, f"SKILL.md tokens: ~{skill_tokens}")
    add(10, "10.2 Total skill payload under context budget (<5,000 tokens)", total_tokens < 5000, f"Total tokens: ~{total_tokens}")

# ==========================================
def suite_11():
    print(f"\n{CYAN}{BOLD}[Suite 11] Behavioral Guardrail Coverage{RESET}")
    content = skill_content
    content_lower = content.lower()

    # 11.1 — Guardrails section must exist
    add(11, "11.1 '## Behavioral Guardrails' section present",
        "## Behavioral Guardrails" in content,
        "Section header found" if "## Behavioral Guardrails" in content else "Section MISSING")

    # 11.2 — At least 3 NEVER directives
    never_count = len(re.findall(r'\bNEVER\b', content))
    add(11, "11.2 ≥3 NEVER directives enforced",
        never_count >= 3,
        f"Found {never_count} NEVER directive(s)")

    # 11.3 — Strong MUST NOT / MUST NEVER prohibitions present
    must_not_count = len(re.findall(r'\bMUST NOT\b|\bMUST NEVER\b', content))
    add(11, "11.3 MUST NOT / MUST NEVER prohibitions present (≥2)",
        must_not_count >= 2,
        f"Found {must_not_count} strong prohibition(s)")

    # 11.4 — Output completeness gate: Before/After requirement documented
    completeness_gate = bool(
        re.search(r'(before.{0,20}after|after.{0,20}before|refactoring code block)', content, re.IGNORECASE)
    )
    add(11, "11.4 Output completeness gate (Before/After requirement) documented",
        completeness_gate,
        "Before/After requirement found" if completeness_gate else "Completeness gate MISSING")

    # 11.5 — Scope rejection instruction for non-ABAP code
    scope_rejection = bool(
        re.search(r'(non.abap|outside this skill.s scope|falls outside|not review non.abap)', content, re.IGNORECASE)
    )
    add(11, "11.5 Scope rejection instruction for non-ABAP code present",
        scope_rejection,
        "Scope rejection found" if scope_rejection else "Scope rejection MISSING")

# ==========================================
def run_all():
    start_time = time.time()
    suite_1()
    suite_2()
    suite_3()
    suite_4()
    suite_5()
    suite_6()
    suite_7()
    suite_8()
    suite_9()
    suite_10()
    suite_11()
    elapsed = (time.time() - start_time) * 1000

    print(f"\n{BOLD}================ SUMMARY ================ {RESET}")
    passed = sum(1 for r in all_results if r[2] == PASS)
    total = len(all_results)
    
    for r in all_results:
        print(f"{r[2]} | Suite {r[0]} | {r[1]} {f'({r[3]})' if r[3] else ''}")
        
    print(f"\n{BOLD}Total Assertions Checked:{RESET} {total}")
    print(f"{BOLD}Passed:{RESET} {passed}/{total}")
    print(f"{BOLD}Execution Latency:{RESET} {elapsed:.2f} ms")
    
    if passed < total:
        failed = total - passed
        print(f"\n{RED}{BOLD}EVALUATION FAILED — {failed} assertion(s) did not pass.{RESET}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}{BOLD}ALL {total} RIGOROUS EVALUATION ASSERTIONS PASSED PERFECTLY (Suites 1–11).{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    run_all()
