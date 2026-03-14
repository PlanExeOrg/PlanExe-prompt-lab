#!/usr/bin/env python3
"""
Run one optimization iteration: read synthesis → implement fix → run experiments → analyze.

Reads the latest synthesis.md, extracts the top recommendation, uses Claude Code
to implement it (branch + PR), then re-runs the experimental pipeline and
analysis chain.

Usage:
    python run_optimization_iteration.py
    python run_optimization_iteration.py --skip-implement
    python run_optimization_iteration.py --skip-implement --skip-runner
    python run_optimization_iteration.py --models nemotron,stepfun
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROMPT_LAB_DIR = SCRIPT_DIR
PLANEXE_DIR = Path("/Users/neoneye/git/PlanExeGroup/PlanExe")
BASELINE_DIR = PROMPT_LAB_DIR / "baseline" / "train"
STEP_NAME = "identify_potential_levers"

# Python interpreter that has PlanExe dependencies (llama_index, etc.).
# sys.executable may point to a different Python version without these packages.
PLANEXE_PYTHON = "/opt/homebrew/bin/python3.11"

# Models ordered: failed/partial first, then successful.
# GLM removed in PR #266 — excluded.
# StepFun removed from llm_config — excluded.
MODELS = [
    # Failed (0/5 in previous batch — model-level issues)
    "openrouter-nvidia-nemotron-3-nano-30b-a3b",
    # Successful (5/5 in previous batch)
    "ollama-llama3.1",
    "openrouter-openai-gpt-oss-20b",
    "openai-gpt-5-nano",
    "openrouter-qwen3-30b-a3b",
    "openrouter-openai-gpt-4o-mini",
    "anthropic-claude-haiku-4-5-pinned",
]

# Short aliases for --models convenience.
MODEL_ALIASES = {
    "nemotron": "openrouter-nvidia-nemotron-3-nano-30b-a3b",
    "llama": "ollama-llama3.1",
    "gpt-oss": "openrouter-openai-gpt-oss-20b",
    "gpt5-nano": "openai-gpt-5-nano",
    "qwen": "openrouter-qwen3-30b-a3b",
    "gpt4o-mini": "openrouter-openai-gpt-4o-mini",
    "haiku": "anthropic-claude-haiku-4-5-pinned",
}

# Models that require PLANEXE_MODEL_PROFILE=custom and a specific llm_config file.
# These are not in the default baseline.json config.
CUSTOM_PROFILE_MODELS = {
    "anthropic-claude-haiku-4-5-pinned": "anthropic_claude.json",
    "anthropic-claude-haiku-4-5": "anthropic_claude.json",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_latest_analysis_dir() -> Path:
    """Find the most recent analysis directory for this step."""
    analysis_root = PROMPT_LAB_DIR / "analysis"
    dirs = sorted(analysis_root.glob(f"*_{STEP_NAME}"))
    if not dirs:
        sys.exit(f"ERROR: No analysis directories found for {STEP_NAME}")
    return dirs[-1]


def read_synthesis(analysis_dir: Path) -> str:
    path = analysis_dir / "synthesis.md"
    if not path.is_file():
        sys.exit(f"ERROR: synthesis.md not found at {path}")
    return path.read_text()


def extract_recommendation(synthesis: str) -> str:
    """Extract the ## Recommendation section from synthesis."""
    match = re.search(
        r"^## Recommendation\s*\n(.*?)(?=^## |\Z)",
        synthesis,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        sys.exit("ERROR: Could not find ## Recommendation section in synthesis.md")
    return match.group(1).strip()


def get_highest_history_counter() -> int:
    """Scan history/ to find the highest existing run counter."""
    history_root = PROMPT_LAB_DIR / "history"
    if not history_root.exists():
        return -1
    highest = -1
    for bucket_dir in history_root.iterdir():
        if not bucket_dir.is_dir() or not bucket_dir.name.isdigit():
            continue
        bucket_num = int(bucket_dir.name)
        for run_dir in bucket_dir.iterdir():
            if not run_dir.is_dir():
                continue
            parts = run_dir.name.split("_", 1)
            if parts[0].isdigit():
                counter = bucket_num * 100 + int(parts[0])
                highest = max(highest, counter)
    return highest


def get_prompt_file() -> Path:
    """Find the registered prompt file for this step."""
    prompts_dir = PROMPT_LAB_DIR / "prompts" / STEP_NAME
    prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
    if not prompt_files:
        sys.exit(f"ERROR: No prompt files found in {prompts_dir}")
    return prompt_files[-1]


def get_prompt_ref(prompt_file: Path) -> str:
    """Get the prompt reference string (relative to prompts/)."""
    return f"{STEP_NAME}/{prompt_file.name}"


def collect_new_runs(start_counter: int) -> list[str]:
    """Collect history run paths created after start_counter."""
    history_root = PROMPT_LAB_DIR / "history"
    runs = []
    for bucket_dir in sorted(history_root.iterdir()):
        if not bucket_dir.is_dir() or not bucket_dir.name.isdigit():
            continue
        bucket_num = int(bucket_dir.name)
        for run_dir in sorted(bucket_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            parts = run_dir.name.split("_", 1)
            if parts[0].isdigit():
                counter = bucket_num * 100 + int(parts[0])
                if counter > start_counter:
                    rel = f"{bucket_dir.name}/{run_dir.name}"
                    runs.append(rel)
    return runs


def get_next_analysis_index() -> int:
    """Find the next available analysis directory index."""
    analysis_root = PROMPT_LAB_DIR / "analysis"
    existing = sorted(analysis_root.glob(f"*_{STEP_NAME}"))
    if not existing:
        return 0
    last_name = existing[-1].name
    parts = last_name.split("_", 1)
    return int(parts[0]) + 1


def resolve_models(models_arg: str | None) -> list[str]:
    """Resolve model names from CLI argument or return defaults."""
    if not models_arg:
        return MODELS
    result = []
    for name in models_arg.split(","):
        name = name.strip()
        resolved = MODEL_ALIASES.get(name, name)
        result.append(resolved)
    return result


# ---------------------------------------------------------------------------
# Step 1: Implement recommendation
# ---------------------------------------------------------------------------

def step_implement(synthesis: str, recommendation: str) -> None:
    """Use Claude Code to implement the recommendation on a feature branch."""
    prompt = f"""\
Read the following recommendation from the latest analysis synthesis and
implement it in the PlanExe codebase.

## Recommendation

{recommendation}

## Full synthesis context (for reference)

{synthesis}

## Instructions

1. Create a new git branch from main (e.g., `fix/B1-double-user-prompt`).
2. Implement the recommended fix — make only the minimal change described.
3. Commit the change with a descriptive message.
4. Push the branch.
5. Create a PR with a clear title and description.

Important:
- Do NOT commit to main directly.
- Make only the minimal change described in the recommendation.
- The PlanExe repo is at: {PLANEXE_DIR}
"""

    print("=" * 60)
    print("Step 1: Implementing recommendation via Claude Code")
    print("=" * 60)
    print()

    result = subprocess.run(
        [
            "claude",
            "-p", prompt,
            "--allowedTools", "Read,Edit,Write,Bash,Glob,Grep",
            "--model", "sonnet",
        ],
        cwd=PLANEXE_DIR,
    )
    if result.returncode != 0:
        sys.exit(f"ERROR: Claude Code exited with code {result.returncode}")

    print("\nImplementation step complete.")


# ---------------------------------------------------------------------------
# Step 2: Run experiments
# ---------------------------------------------------------------------------

def step_runner(models: list[str], prompt_file: Path) -> list[str]:
    """Run runner.py for each model. Returns list of new history run paths."""
    start_counter = get_highest_history_counter()

    print()
    print("=" * 60)
    print(f"Step 2: Running experiments ({len(models)} models)")
    print("=" * 60)

    for i, model in enumerate(models, 1):
        print(f"\n--- [{i}/{len(models)}] {model} ---")

        cmd = [
            PLANEXE_PYTHON, "-m", "prompt_optimizer.runner",
            "--system-prompt-file", str(prompt_file),
            "--baseline-dir", str(BASELINE_DIR),
            "--prompt-lab-dir", str(PROMPT_LAB_DIR),
            "--model", model,
        ]

        # Set custom model profile env vars for Anthropic and other non-baseline models.
        env = os.environ.copy()
        config_file = CUSTOM_PROFILE_MODELS.get(model)
        if config_file:
            env["PLANEXE_MODEL_PROFILE"] = "custom"
            env["PLANEXE_LLM_CONFIG_CUSTOM_FILENAME"] = config_file
            print(f"  (using custom profile: {config_file})")

        result = subprocess.run(cmd, cwd=PLANEXE_DIR, env=env)
        if result.returncode != 0:
            print(f"WARNING: runner.py for {model} exited with code {result.returncode}")
        else:
            print(f"runner.py for {model} completed successfully")

    new_runs = collect_new_runs(start_counter)
    print(f"\nNew history runs created: {len(new_runs)}")
    for run in new_runs:
        print(f"  history/{run}")

    return new_runs


# ---------------------------------------------------------------------------
# Step 3: Analysis pipeline
# ---------------------------------------------------------------------------

def create_analysis_dir(new_runs: list[str], prompt_ref: str) -> Path:
    """Create a new analysis directory with meta.json."""
    index = get_next_analysis_index()
    analysis_dir = PROMPT_LAB_DIR / "analysis" / f"{index}_{STEP_NAME}"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "prompt": prompt_ref,
        "history": new_runs,
    }
    meta_path = analysis_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"\nCreated analysis directory: {analysis_dir.relative_to(PROMPT_LAB_DIR)}")
    print(f"  meta.json references {len(new_runs)} new runs")

    return analysis_dir


def step_analysis(analysis_dir: Path) -> None:
    """Run insight → code review → synthesis in sequence."""
    rel_dir = str(analysis_dir.relative_to(PROMPT_LAB_DIR))

    scripts = [
        ("run_insight.py", "Insight analysis (phase 1)"),
        ("run_code_review.py", "Code review (phase 2)"),
        ("run_synthesis.py", "Synthesis (phase 3)"),
    ]

    for script_name, label in scripts:
        print()
        print("=" * 60)
        print(f"Analysis: {label}")
        print("=" * 60)

        script_path = PROMPT_LAB_DIR / "analysis" / script_name
        result = subprocess.run(
            [sys.executable, str(script_path), str(rel_dir)],
            cwd=PROMPT_LAB_DIR,
        )
        if result.returncode != 0:
            print(f"WARNING: {script_name} exited with code {result.returncode}")
        else:
            print(f"{label} completed successfully")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run one optimization iteration: implement fix → run experiments → analyze.",
    )
    parser.add_argument(
        "--skip-implement",
        action="store_true",
        help="Skip the Claude Code implementation step (use when fix is already applied).",
    )
    parser.add_argument(
        "--skip-runner",
        action="store_true",
        help="Skip runner.py experiments (use when runs already exist).",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip the analysis pipeline.",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help=(
            "Comma-separated list of models to run. Supports aliases: "
            + ", ".join(f"{k}" for k in MODEL_ALIASES)
            + ". Default: all models, failed first."
        ),
    )
    args = parser.parse_args()

    models = resolve_models(args.models)

    # Read the latest synthesis.
    latest_analysis_dir = get_latest_analysis_dir()
    synthesis = read_synthesis(latest_analysis_dir)
    recommendation = extract_recommendation(synthesis)

    print("Latest analysis: " + str(latest_analysis_dir.relative_to(PROMPT_LAB_DIR)))
    print()
    print("Top recommendation:")
    print("-" * 40)
    for line in recommendation.split("\n")[:8]:
        print(f"  {line}")
    print("  ...")
    print("-" * 40)

    # Step 1: Implement the recommendation.
    if not args.skip_implement:
        step_implement(synthesis, recommendation)
    else:
        print("\n[Skipping implementation step]")

    # Step 2: Run experiments.
    new_runs: list[str] = []
    if not args.skip_runner:
        prompt_file = get_prompt_file()
        new_runs = step_runner(models, prompt_file)
    else:
        print("\n[Skipping runner step]")

    # Step 3: Analysis pipeline.
    if not args.skip_analysis:
        if not new_runs:
            sys.exit(
                "ERROR: No new runs to analyze. "
                "Run without --skip-runner first, or re-run the runner step."
            )

        prompt_file = get_prompt_file()
        prompt_ref = get_prompt_ref(prompt_file)
        new_analysis_dir = create_analysis_dir(new_runs, prompt_ref)

        print()
        print("=" * 60)
        print("Step 3: Analysis pipeline")
        print("=" * 60)

        step_analysis(new_analysis_dir)
    else:
        print("\n[Skipping analysis step]")

    print()
    print("=" * 60)
    print("Optimization iteration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
