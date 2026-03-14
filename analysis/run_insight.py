#!/usr/bin/env python3
"""
Run Claude Code and Codex in parallel to produce insight files for an analysis step.

Usage:
    python analysis/run_insight.py analysis/0_identify_potential_levers
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

PROMPT_TEMPLATE = """\
You are an analysis agent ("{agent_name}").

## Instructions

1. Read `analysis/AGENTS.md` for the full conventions you must follow.
2. The meta.json for this analysis step is shown below — it tells you which
   prompt and history runs to examine.
3. Produce a single insight file at `{output_file}`.

## Repository layout

The repo root is: {repo_root}

Key paths relative to the repo root:
- Baseline training data: `baseline/train/`
- Runner history outputs: `history/`
- Registered prompts: `prompts/`
- Analysis directory: `{analysis_dir}/`

## meta.json contents

```json
{meta_json}
```

## Requirements

- Follow the section structure from AGENTS.md (Negative Things, Positive Things,
  Comparison, Quantitative Metrics, Evidence Notes, Questions For Later Synthesis,
  Reflect, Potential Code Changes, Summary, etc.).
- Compute quantitative metrics: uniqueness counts, average field lengths,
  constraint violations, template leakage. Present them in tables.
- Label prompt hypotheses H1, H2, … and code hypotheses C1, C2, …
- Cite evidence from specific files (history run outputs, baseline data, prompt
  files). Do not rely on memory alone.
- Compare the history runs against the baseline training data.
- Keep claims auditable — quote or reference the exact artifact paths.

## Output

Write your analysis to: `{output_file}`
Do not write any other files. Do not modify meta.json.
"""


def build_prompt(agent_name: str, analysis_dir: str, meta_json: str) -> str:
    output_file = f"{analysis_dir}/insight_{agent_name}.md"
    return PROMPT_TEMPLATE.format(
        agent_name=agent_name,
        output_file=output_file,
        repo_root=REPO_ROOT,
        analysis_dir=analysis_dir,
        meta_json=meta_json,
    )



def main():
    parser = argparse.ArgumentParser(
        description="Run analysis agents (Claude Code + Codex) in parallel.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis step directory (e.g. analysis/0_identify_potential_levers)",
    )
    args = parser.parse_args()

    analysis_dir: str = args.analysis_dir
    meta_path = REPO_ROOT / analysis_dir / "meta.json"
    if not meta_path.is_file():
        sys.exit(f"ERROR: No meta.json found at {meta_path}")

    meta_json = meta_path.read_text()
    # Validate it's valid JSON while we have it.
    json.loads(meta_json)

    claude_prompt = build_prompt("claude", analysis_dir, meta_json)
    codex_prompt = build_prompt("codex", analysis_dir, meta_json)

    print(f"Starting analysis for: {analysis_dir}")
    print(f"  Claude insight → {analysis_dir}/insight_claude.md")
    print(f"  Codex  insight → {analysis_dir}/insight_codex.md")
    print()

    # Launch both agents in parallel.
    claude_proc = subprocess.Popen(
        [
            "claude",
            "-p", claude_prompt,
            "--allowedTools", "Read,Glob,Grep,Write",
            "--add-dir", str(REPO_ROOT),
            "--model", "sonnet",
        ],
        cwd=REPO_ROOT,
    )
    codex_proc = subprocess.Popen(
        [
            "codex",
            "exec", codex_prompt,
            "-C", str(REPO_ROOT),
            "--full-auto",
        ],
        cwd=REPO_ROOT,
    )

    print(f"PIDs: claude={claude_proc.pid}  codex={codex_proc.pid}")
    print("Waiting for both agents to finish...")
    print()

    claude_exit = claude_proc.wait()
    codex_exit = codex_proc.wait()

    # Report results.
    print()
    print("═" * 50)
    print("Results")
    print("═" * 50)

    for name, exit_code in [("Claude Code", claude_exit), ("Codex", codex_exit)]:
        if exit_code != 0:
            print(f"  {name} exited with code {exit_code}")
        else:
            print(f"  {name} finished successfully")

    print()
    print("Insight files:")
    insight_dir = REPO_ROOT / analysis_dir
    insight_files = sorted(insight_dir.glob("insight_*.md"))
    if insight_files:
        for f in insight_files:
            size = f.stat().st_size
            print(f"  {f.relative_to(REPO_ROOT)}  ({size} bytes)")
    else:
        print("  (no insight files found)")


if __name__ == "__main__":
    main()
