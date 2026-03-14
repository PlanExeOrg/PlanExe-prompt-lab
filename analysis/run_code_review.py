#!/usr/bin/env python3
"""
Run Claude Code and Codex in parallel to review PlanExe source code for bugs
and improvements informed by the insight files from a previous analysis step.

Usage:
    python analysis/run_code_review.py analysis/0_identify_potential_levers
"""
import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PLANEXE_ROOT = Path("/Users/neoneye/git/PlanExeGroup/PlanExe")

# PlanExe source files to review.
SOURCE_FILES = [
    "worker_plan/worker_plan_internal/lever/identify_potential_levers.py",
    "prompt_optimizer/runner.py",
]

PROMPT_TEMPLATE = """\
You are a code-review agent ("{agent_name}").

## Goal

Find bugs, logic errors, and improvement opportunities in the PlanExe source
code that could explain quality problems described in the insight files below.

## Source files to review

The PlanExe repo is at: {planexe_root}

Read these files carefully:
{source_file_list}

## Insight files (from prior analysis)

The following insight files describe quality problems observed when running the
`identify_potential_levers` pipeline step across multiple models and plans.
Use them to guide your code review — look for code-level root causes of the
issues they describe.

{insight_content}

## What to look for

- **Prompt construction bugs**: Is the prompt assembled correctly? Are messages
  duplicated, missing, or in the wrong order?
- **Chat history management**: Are system/user/assistant messages appended
  correctly across multi-call loops?
- **JSON parsing / validation**: Are outputs validated properly? Are schema
  errors caught or silently dropped?
- **Merge logic**: When multiple LLM calls are merged into a final output,
  is deduplication handled? Are duplicate lever names possible?
- **Error handling**: Are retries, fallbacks, and error messages correct?
- **Configuration issues**: Could model-name resolution fail silently?
- **Template leakage vectors**: Does the prompt include examples that models
  might copy verbatim? Is there a guard against that?

## Output format

Write your findings to: `{output_file}`

Use this structure:
- `# Code Review ({agent_name})`
- `## Bugs Found` — confirmed bugs with file:line references
- `## Suspect Patterns` — code that looks wrong but needs more context
- `## Improvement Opportunities` — changes that could boost output quality
- `## Trace to Insight Findings` — map each code issue to the insight-file
  observations it explains (e.g., "The double user-prompt bug explains the
  template leakage in run 00")
- `## Summary`

Label bugs B1, B2, … and improvements I1, I2, …
Cite exact file paths and line numbers.
Do not modify any source files. Only write the output file.
"""


def build_prompt(agent_name: str, analysis_dir: str, insight_content: str) -> str:
    output_file = f"{analysis_dir}/code_{agent_name}.md"
    source_file_list = "\n".join(
        f"- `{PLANEXE_ROOT / f}`" for f in SOURCE_FILES
    )
    return PROMPT_TEMPLATE.format(
        agent_name=agent_name,
        planexe_root=PLANEXE_ROOT,
        source_file_list=source_file_list,
        insight_content=insight_content,
        output_file=output_file,
    )


def load_insight_files(analysis_path: Path) -> str:
    """Concatenate all insight_*.md files from the analysis directory."""
    parts = []
    for f in sorted(analysis_path.glob("insight_*.md")):
        parts.append(f"### {f.name}\n\n{f.read_text()}")
    if not parts:
        sys.exit(f"ERROR: No insight_*.md files found in {analysis_path}")
    return "\n\n---\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Run code-review agents (Claude Code + Codex) in parallel.",
    )
    parser.add_argument(
        "analysis_dir",
        help="Relative path to the analysis step directory (e.g. analysis/0_identify_potential_levers)",
    )
    args = parser.parse_args()

    analysis_dir: str = args.analysis_dir
    analysis_path = REPO_ROOT / analysis_dir
    if not analysis_path.is_dir():
        sys.exit(f"ERROR: Directory not found: {analysis_path}")

    # Validate that the PlanExe source files exist.
    for f in SOURCE_FILES:
        path = PLANEXE_ROOT / f
        if not path.is_file():
            sys.exit(f"ERROR: PlanExe source file not found: {path}")

    insight_content = load_insight_files(analysis_path)

    claude_prompt = build_prompt("claude", analysis_dir, insight_content)
    codex_prompt = build_prompt("codex", analysis_dir, insight_content)

    print(f"Starting code review for: {analysis_dir}")
    print(f"  Claude → {analysis_dir}/code_claude.md")
    print(f"  Codex  → {analysis_dir}/code_codex.md")
    print()

    # Launch both agents in parallel.
    claude_proc = subprocess.Popen(
        [
            "claude",
            "-p", claude_prompt,
            "--allowedTools", "Read,Glob,Grep,Write",
            "--add-dir", str(REPO_ROOT),
            "--add-dir", str(PLANEXE_ROOT),
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
    print("Code review files:")
    code_files = sorted(analysis_path.glob("code_*.md"))
    if code_files:
        for f in code_files:
            size = f.stat().st_size
            print(f"  {f.relative_to(REPO_ROOT)}  ({size} bytes)")
    else:
        print("  (no code review files found)")


if __name__ == "__main__":
    main()
