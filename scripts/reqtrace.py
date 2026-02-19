#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

ID_RE = re.compile(r"^\s*ID:\s*([A-Z][A-Z0-9-]*)\s*$")
FIELD_RE = re.compile(r"^\s*(Parent|Verification|Satisfies|Verifies):\s*(.+?)\s*$")

@dataclass
class Item:
    id: str
    kind: str  # RQ / DSN / TST / UNKNOWN
    file: str
    line: int
    parent: List[str] = field(default_factory=list)
    satisfies: List[str] = field(default_factory=list)
    verifies: List[str] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)

def split_ids(s: str) -> List[str]:
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]

def infer_kind(item_id: str) -> str:
    # e.g. HW-010-RQ-001, HW-010-DSN-001, HW-010-TST-001
    for k in ("RQ", "DSN", "TST"):
        if f"-{k}-" in item_id:
            return k
    # fallback: SYS-001 etc
    if item_id.startswith("SYS-"):
        return "RQ"  # treat system-level as requirement-ish
    return "UNKNOWN"

def scan_markdown_files(roots: List[Path]) -> Tuple[Dict[str, Item], List[str]]:
    items: Dict[str, Item] = {}
    errors: List[str] = []

    md_files: List[Path] = []
    for root in roots:
        if root.exists():
            md_files.extend(root.rglob("*.md"))

    for f in sorted(set(md_files)):
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:
            errors.append(f"Failed to read {f}: {e}")
            continue

        current_id = None
        current_item: Item | None = None

        for i, line in enumerate(lines, start=1):
            m = ID_RE.match(line)
            if m:
                # commit previous
                if current_item:
                    if current_item.id in items:
                        prev = items[current_item.id]
                        errors.append(
                            f"Duplicate ID {current_item.id}:\n"
                            f"  - {prev.file}:{prev.line}\n"
                            f"  - {current_item.file}:{current_item.line}"
                        )
                    else:
                        items[current_item.id] = current_item

                current_id = m.group(1)
                current_item = Item(
                    id=current_id,
                    kind=infer_kind(current_id),
                    file=str(f),
                    line=i,
                )
                continue

            if current_item:
                fm = FIELD_RE.match(line)
                if fm:
                    key = fm.group(1)
                    vals = split_ids(fm.group(2))
                    if key == "Parent":
                        current_item.parent.extend(vals)
                    elif key == "Satisfies":
                        current_item.satisfies.extend(vals)
                    elif key == "Verifies":
                        current_item.verifies.extend(vals)
                    elif key == "Verification":
                        current_item.verification.extend(vals)

        # commit last
        if current_item:
            if current_item.id in items:
                prev = items[current_item.id]
                errors.append(
                    f"Duplicate ID {current_item.id}:\n"
                    f"  - {prev.file}:{prev.line}\n"
                    f"  - {current_item.file}:{current_item.line}"
                )
            else:
                items[current_item.id] = current_item

    return items, errors

def validate(items: Dict[str, Item]) -> List[str]:
    errors: List[str] = []
    all_ids: Set[str] = set(items.keys())

    # Basic: every item must have ID already guaranteed.
    # Link existence checks:
    def check_links(src: Item, field_name: str, targets: List[str]):
        for t in targets:
            if t not in all_ids:
                errors.append(f"{src.id} references missing {field_name} target: {t}  ({src.file}:{src.line})")

    for it in items.values():
        check_links(it, "Parent", it.parent)
        check_links(it, "Satisfies", it.satisfies)
        check_links(it, "Verifies", it.verifies)
        check_links(it, "Verification", it.verification)

    # Stronger rules by kind
    for it in items.values():
        if it.kind == "RQ":
            # Recommend Parent (except SYS-* top)
            if not it.id.startswith("SYS-") and len(it.parent) == 0:
                errors.append(f"Requirement missing Parent: {it.id}  ({it.file}:{it.line})")
            if len(it.verification) == 0:
                errors.append(f"Requirement missing Verification: {it.id}  ({it.file}:{it.line})")
        elif it.kind == "DSN":
            if len(it.satisfies) == 0:
                errors.append(f"Design item missing Satisfies: {it.id}  ({it.file}:{it.line})")
        elif it.kind == "TST":
            if len(it.verifies) == 0:
                errors.append(f"Test case missing Verifies: {it.id}  ({it.file}:{it.line})")

    # Cross-check: if a requirement claims Verification: TST-xxx, that test should Verifies: the requirement
    for it in items.values():
        if it.kind == "RQ":
            for tst_id in it.verification:
                tst = items.get(tst_id)
                if tst and it.id not in tst.verifies:
                    errors.append(
                        f"Trace mismatch: {it.id} says Verification {tst_id}, but {tst_id} does not Verifies {it.id} "
                        f"({it.file}:{it.line})"
                    )

    return errors

def generate_trace(items: Dict[str, Item]) -> List[Dict[str, str]]:
    # Build rows per requirement
    rows: List[Dict[str, str]] = []
    # Determine all requirements: kind RQ or SYS-*
    reqs = [it for it in items.values() if it.kind == "RQ"]
    reqs = sorted(reqs, key=lambda x: x.id)

    # Reverse indices for DSN/TST
    satisfies_map: Dict[str, List[str]] = {}
    verifies_map: Dict[str, List[str]] = {}

    for it in items.values():
        if it.kind == "DSN":
            for r in it.satisfies:
                satisfies_map.setdefault(r, []).append(it.id)
        if it.kind == "TST":
            for r in it.verifies:
                verifies_map.setdefault(r, []).append(it.id)

    for r in reqs:
        designs = sorted(set(satisfies_map.get(r.id, [])))
        tests = sorted(set(verifies_map.get(r.id, [])))
        rows.append({
            "RequirementID": r.id,
            "Parent": ",".join(r.parent),
            "DesignIDs": ",".join(designs),
            "VerificationClaim": ",".join(r.verification),
            "TestIDs": ",".join(tests),
            "Source": f"{r.file}:{r.line}",
        })
    return rows

def write_csv(rows: List[Dict[str, str]], out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["RequirementID","Parent","DesignIDs","VerificationClaim","TestIDs","Source"])
        w.writeheader()
        for row in rows:
            w.writerow(row)

def write_md(rows: List[Dict[str, str]], out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Traceability Report")
    lines.append("")
    lines.append("| Requirement | Parent | Design | Verification (Claim) | Tests (Actual) | Source |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['RequirementID']} | {r['Parent']} | {r['DesignIDs']} | {r['VerificationClaim']} | {r['TestIDs']} | {r['Source']} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", default=[".kiro", "spec", "docs"], help="Roots to scan for .md files")
    ap.add_argument("--outdir", default="ci_out", help="Output dir for generated reports")
    args = ap.parse_args()

    roots = [Path(r) for r in args.roots]
    items, scan_errors = scan_markdown_files(roots)

    val_errors = validate(items)
    errors = scan_errors + val_errors

    outdir = Path(args.outdir)
    rows = generate_trace(items)
    write_csv(rows, outdir / "traceability.csv")
    write_md(rows, outdir / "traceability.md")

    if errors:
        print("❌ Requirements/Traceability checks failed:\n")
        for e in errors:
            print(f"- {e}")
        print("\nGenerated reports are still available as artifacts.")
        return 1

    print("✅ Requirements/Traceability checks passed.")
    print(f"Generated: {outdir/'traceability.csv'} and {outdir/'traceability.md'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
