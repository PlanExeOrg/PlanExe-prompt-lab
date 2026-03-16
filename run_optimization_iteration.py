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
# Nemotron removed in 23797697 — excluded.
# StepFun removed from llm_config — excluded.
MODELS = [
    "ollama-llama3.1",
    "openrouter-openai-gpt-oss-20b",
    "openai-gpt-5-nano",
    "openrouter-qwen3-30b-a3b",
    "openrouter-openai-gpt-4o-mini",
    "anthropic-claude-haiku-4-5-pinned",
]

# Short aliases for --models convenience.
MODEL_ALIASES = {
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

def _dir_index(d: Path) -> int:
    """Extract the numeric index prefix from a directory name like '12_step'."""
    return int(d.name.split("_", 1)[0])


def get_latest_analysis_dir() -> Path:
    """Find the most recent analysis directory for this step.

    Sorts numerically by index prefix, not lexicographically — otherwise
    '9_step' sorts after '11_step'.
    """
    analysis_root = PROMPT_LAB_DIR / "analysis"
    dirs = [d for d in analysis_root.glob(f"*_{STEP_NAME}") if d.is_dir()]
    dirs.sort(key=_dir_index)
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

def detect_pr_number() -> int | None:
    """Detect the PR number for the current branch in PlanExe repo."""
    result = subprocess.run(
        ["gh", "pr", "view", "--json", "number", "-q", ".number"],
        cwd=PLANEXE_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip().isdigit():
        return int(result.stdout.strip())
    return None


def register_prompt() -> None:
    """Register the current system prompt so the runner uses the latest version."""
    print()
    print("Registering current system prompt...")
    result = subprocess.run(
        [
            PLANEXE_PYTHON, "-m", "prompt_optimizer.register_prompt",
            "--step", STEP_NAME,
            "--prompt-lab-dir", str(PROMPT_LAB_DIR),
        ],
        cwd=PLANEXE_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: register_prompt failed: {result.stderr.strip()}")
    else:
        print(result.stdout.strip())


def register_pr_in_meta(analysis_dir: Path, pr_number: int) -> None:
    """Register PR info in the analysis meta.json."""
    script = PROMPT_LAB_DIR / "analysis" / "update_meta_pr.py"
    rel_dir = str(analysis_dir.relative_to(PROMPT_LAB_DIR))
    result = subprocess.run(
        [sys.executable, str(script), rel_dir, str(pr_number)],
        cwd=PROMPT_LAB_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: update_meta_pr failed: {result.stderr.strip()}")
    else:
        print(result.stdout.strip())


def step_implement(synthesis: str, recommendation: str) -> int | None:
    """Use Claude Code to implement the recommendation on a feature branch.

    Returns the detected PR number, or None if not detected.
    """
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
6. Do NOT merge the PR. It will be merged after experiments confirm improvement.

Important:
- Do NOT commit to main directly.
- Do NOT merge the PR — it must be tested first.
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

    # Detect the PR number from the current branch.
    pr_number = detect_pr_number()
    if pr_number:
        print(f"\nDetected PR #{pr_number}")
    else:
        print("\nWARNING: Could not detect PR number. Register it manually with:")
        print("  python analysis/update_meta_pr.py <analysis_dir> <PR#>")

    # Register the (potentially updated) system prompt.
    register_prompt()

    print("\nImplementation step complete.")
    return pr_number


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

def create_analysis_dir() -> Path:
    """Run create_analysis_dir.py to create a new analysis directory with meta.json.

    The script diffs all history runs against previously analyzed runs to ensure
    nothing is missed.
    """
    script = PROMPT_LAB_DIR / "analysis" / "create_analysis_dir.py"
    result = subprocess.run(
        [sys.executable, str(script), STEP_NAME],
        cwd=PROMPT_LAB_DIR,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(f"ERROR: create_analysis_dir.py exited with code {result.returncode}")

    # Find the newly created directory (highest index for this step).
    analysis_root = PROMPT_LAB_DIR / "analysis"
    dirs = [d for d in analysis_root.glob(f"*_{STEP_NAME}") if d.is_dir()]
    dirs.sort(key=_dir_index)
    if not dirs:
        sys.exit("ERROR: No analysis directory found after create_analysis_dir.py")
    return dirs[-1]


def step_analysis(analysis_dir: Path) -> None:
    """Run insight → code review → synthesis → assessment in sequence."""
    rel_dir = str(analysis_dir.relative_to(PROMPT_LAB_DIR))

    # Assessment only makes sense from index 1 onward (needs a "before").
    index = int(analysis_dir.name.split("_", 1)[0])

    scripts = [
        ("run_insight.py", "Insight analysis (phase 1)"),
        ("run_code_review.py", "Code review (phase 2)"),
        ("run_synthesis.py", "Synthesis (phase 3)"),
    ]
    if index > 0:
        scripts.append(("run_assessment.py", "Assessment (phase 4)"))

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
    pr_number = None
    if not args.skip_implement:
        pr_number = step_implement(synthesis, recommendation)
    else:
        print("\n[Skipping implementation step]")
        # Try to detect PR from current branch even when skipping implement.
        pr_number = detect_pr_number()
        if pr_number:
            print(f"  Detected existing PR #{pr_number}")

    # Step 2: Run experiments.
    if not args.skip_runner:
        prompt_file = get_prompt_file()
        step_runner(models, prompt_file)
    else:
        print("\n[Skipping runner step]")

    # Step 3: Analysis pipeline.
    if not args.skip_analysis:
        print()
        print("=" * 60)
        print("Step 3: Analysis pipeline")
        print("=" * 60)

        new_analysis_dir = create_analysis_dir()

        # Register PR info in meta.json before running analysis agents.
        if pr_number:
            print(f"\nRegistering PR #{pr_number} in {new_analysis_dir.name}/meta.json")
            register_pr_in_meta(new_analysis_dir, pr_number)

        step_analysis(new_analysis_dir)
    else:
        print("\n[Skipping analysis step]")

    print()
    print("=" * 60)
    print("Optimization iteration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
