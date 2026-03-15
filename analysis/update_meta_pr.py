#!/usr/bin/env python3
"""
Update an analysis meta.json with PR info fetched from GitHub.

Register the PR *before* running phases 1-4 so that insight, code review,
synthesis, and assessment agents all know which change they are evaluating.
Without PR context, the agents produce generic analysis instead of targeted
before/after comparisons (e.g., "did removing max_length=7 reduce haiku
failures on gta_game?").

Usage:
    python analysis/update_meta_pr.py analysis/1_identify_potential_levers https://github.com/PlanExeOrg/PlanExe/pull/268
    python analysis/update_meta_pr.py analysis/1_identify_potential_levers 268
    python analysis/update_meta_pr.py analysis/1_identify_potential_levers 268 --repo PlanExeOrg/PlanExe
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_REPO = "PlanExeOrg/PlanExe"


def parse_pr_arg(pr_arg: str, repo: str) -> tuple[str, int]:
    """Parse a PR URL or number into (repo, pr_number)."""
    # Full URL: https://github.com/PlanExeOrg/PlanExe/pull/268
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_arg)
    if match:
        return match.group(1), int(match.group(2))

    # Bare number.
    if pr_arg.isdigit():
        return repo, int(pr_arg)

    sys.exit(f"ERROR: Cannot parse PR reference: {pr_arg!r}")


def fetch_pr(repo: str, pr_number: int) -> dict:
    """Fetch PR details using gh CLI."""
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo,
         "--json", "url,title,body"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"ERROR: gh pr view failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def summarize_body(body: str) -> str:
    """Extract the Summary section from the PR body, or use the first paragraph."""
    # Try to find a ## Summary section.
    match = re.search(
        r"^## Summary\s*\n(.*?)(?=^## |\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    text = match.group(1).strip() if match else body.strip()

    # Strip markdown bullet prefixes and join into flowing prose.
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Remove leading "- " bullet.
        line = re.sub(r"^- \*?\*?", "", line).strip()
        # Remove bold markers.
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        # Stop at test plan / checklist / emoji sections.
        if line.startswith("- [") or line.startswith("[") or line.startswith("\U0001f916"):
            break
        lines.append(line)

    return " ".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Update analysis meta.json with PR info from GitHub.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis directory (e.g. analysis/1_identify_potential_levers)",
    )
    parser.add_argument(
        "pr",
        help="PR URL (https://github.com/…/pull/N) or PR number",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repo (owner/name). Default: {DEFAULT_REPO}",
    )
    args = parser.parse_args()

    meta_path = REPO_ROOT / args.analysis_dir / "meta.json"
    if not meta_path.is_file():
        sys.exit(f"ERROR: meta.json not found at {meta_path}")

    repo, pr_number = parse_pr_arg(args.pr, args.repo)
    pr = fetch_pr(repo, pr_number)

    description = summarize_body(pr.get("body", ""))

    meta = json.loads(meta_path.read_text())
    meta["pr_url"] = pr["url"]
    meta["pr_title"] = pr["title"]
    meta["pr_description"] = description

    # Write with prompt first, then pr fields, then history last.
    ordered = {}
    for key in ["prompt", "pr_url", "pr_title", "pr_description"]:
        if key in meta:
            ordered[key] = meta.pop(key)
    ordered.update(meta)

    meta_path.write_text(json.dumps(ordered, indent=2) + "\n")

    print(f"Updated: {meta_path.relative_to(REPO_ROOT)}")
    print(f"  pr_url:         {ordered['pr_url']}")
    print(f"  pr_title:       {ordered['pr_title']}")
    print(f"  pr_description: {ordered['pr_description'][:80]}...")


if __name__ == "__main__":
    main()
