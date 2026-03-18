#!/usr/bin/env python3
"""
Run one optimization iteration: read synthesis → implement fix → run experiments → analyze.

Reads the latest synthesis.md, extracts the top recommendation, uses Claude Code
to implement it (branch + PR), then re-runs the experimental pipeline and
analysis chain.

Usage:
    python run_optimization_iteration.py --pr 316
    python run_optimization_iteration.py --skip-implement --pr 316
    python run_optimization_iteration.py --skip-implement --skip-runner --pr 316
    python run_optimization_iteration.py --pr 316 --models nemotron,stepfun
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
DEFAULT_STEP_NAME = "identify_potential_levers"

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
    "openrouter-gemini-2.0-flash-001",
    "anthropic-claude-haiku-4-5-pinned",
]

# Short aliases for --models convenience.
MODEL_ALIASES = {
    "llama": "ollama-llama3.1",
    "gpt-oss": "openrouter-openai-gpt-oss-20b",
    "gpt5-nano": "openai-gpt-5-nano",
    "qwen": "openrouter-qwen3-30b-a3b",
    "gpt4o-mini": "openrouter-openai-gpt-4o-mini",
    "gemini-flash": "openrouter-gemini-2.0-flash-001",
    "haiku": "anthropic-claude-haiku-4-5-pinned",
}

# Models that require PLANEXE_MODEL_PROFILE=custom and a specific llm_config file.
# These are not in the default baseline.json config.
CUSTOM_PROFILE_MODELS = {
    "anthropic-claude-haiku-4-5-pinned": "anthropic_claude.json",
    "anthropic-claude-haiku-4-5": "anthropic_claude.json",
}

# Import prepare_iteration and event_log from the analysis directory.
sys.path.insert(0, str(PROMPT_LAB_DIR / "analysis"))
from prepare_iteration import prepare, prepare_analysis_from_existing  # noqa: E402
from event_log import EventTimer, emit_event  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dir_index(d: Path) -> int:
    """Extract the numeric index prefix from a directory name like '12_step'."""
    return int(d.name.split("_", 1)[0])


def get_latest_analysis_dir(step_name: str) -> Path | None:
    """Find the most recent analysis directory for this step.

    Sorts numerically by index prefix, not lexicographically — otherwise
    '9_step' sorts after '11_step'.

    Returns None if no analysis directories exist (e.g. first run of a new step).
    """
    analysis_root = PROMPT_LAB_DIR / "analysis"
    dirs = [d for d in analysis_root.glob(f"*_{step_name}") if d.is_dir()]
    dirs.sort(key=_dir_index)
    if not dirs:
        return None
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


def verify_planexe_branch(pr_arg: str) -> None:
    """Verify that PLANEXE_DIR is checked out to the PR's head branch.

    Prevents running experiments on the wrong branch (e.g. main instead of
    the PR branch), which would produce invalid results.
    """
    # Get the PR's head branch name.
    pr_ref = pr_arg if not pr_arg.isdigit() else pr_arg
    gh_result = subprocess.run(
        ["gh", "pr", "view", pr_ref, "--json", "headRefName", "-q", ".headRefName"],
        cwd=PLANEXE_DIR,
        capture_output=True,
        text=True,
    )
    if gh_result.returncode != 0:
        sys.exit(
            f"ERROR: Could not look up PR {pr_arg}. "
            f"gh pr view failed: {gh_result.stderr.strip()}"
        )
    pr_branch = gh_result.stdout.strip()

    # Get the current branch at PLANEXE_DIR.
    git_result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=PLANEXE_DIR,
        capture_output=True,
        text=True,
    )
    if git_result.returncode != 0:
        sys.exit(
            f"ERROR: Could not determine current branch at {PLANEXE_DIR}. "
            f"git branch --show-current failed: {git_result.stderr.strip()}"
        )
    current_branch = git_result.stdout.strip()

    if current_branch != pr_branch:
        sys.exit(
            f"ERROR: Branch mismatch!\n"
            f"  PR {pr_arg} branch: {pr_branch}\n"
            f"  {PLANEXE_DIR} is on: {current_branch}\n"
            f"\n"
            f"The runner imports code from {PLANEXE_DIR}, so it must be on the\n"
            f"PR branch to test the PR's changes. Run:\n"
            f"  cd {PLANEXE_DIR} && git checkout {pr_branch}"
        )

    print(f"Branch check OK: {PLANEXE_DIR} is on '{current_branch}' (matches PR {pr_arg})")


# ---------------------------------------------------------------------------
# Step 1: Implement recommendation
# ---------------------------------------------------------------------------

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
    gh_result = subprocess.run(
        ["gh", "pr", "view", "--json", "number", "-q", ".number"],
        cwd=PLANEXE_DIR,
        capture_output=True,
        text=True,
    )
    pr_number = None
    if gh_result.returncode == 0 and gh_result.stdout.strip().isdigit():
        pr_number = int(gh_result.stdout.strip())
        print(f"\nDetected PR #{pr_number}")
    else:
        print("\nWARNING: Could not detect PR number. Use --pr to specify.")

    print("\nImplementation step complete.")
    return pr_number


# ---------------------------------------------------------------------------
# Step 2: Run experiments
# ---------------------------------------------------------------------------

def _load_model_configs() -> dict:
    """Load all llm_config JSON files from PLANEXE_DIR and merge into one dict."""
    config_dir = PLANEXE_DIR / "llm_config"
    merged = {}
    for json_file in sorted(config_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text())
            merged.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return merged


def _build_runner_cmd(model: str, history_dirs: dict[str, Path] | None, step_name: str = DEFAULT_STEP_NAME) -> list[str]:
    """Build the runner subprocess command for a model."""
    cmd = [
        PLANEXE_PYTHON, "-m", "self_improve.runner",
        "--step", step_name,
        "--baseline-dir", str(BASELINE_DIR),
        "--model", model,
    ]
    if history_dirs and model in history_dirs:
        output_dir = history_dirs[model] / "outputs"
        cmd += ["--output-dir", str(output_dir)]
    else:
        cmd += ["--prompt-lab-dir", str(PROMPT_LAB_DIR)]
    return cmd


def _build_runner_env(model: str) -> dict:
    """Build the environment dict for a model, adding custom profile vars if needed."""
    env = os.environ.copy()
    config_file = CUSTOM_PROFILE_MODELS.get(model)
    if config_file:
        env["PLANEXE_MODEL_PROFILE"] = "custom"
        env["PLANEXE_LLM_CONFIG_CUSTOM_FILENAME"] = config_file
    return env


def step_runner(
    models: list[str],
    history_dirs: dict[str, Path] | None = None,
    events_path: Path | None = None,
    step_name: str = DEFAULT_STEP_NAME,
) -> None:
    """Run runner.py for each model.

    Phase 1: run local models (self_improve_sequential=true) one at a time.
    Phase 2: run cloud models in parallel.

    When history_dirs is provided (from prepare_iteration), uses --output-dir
    to write into the pre-created directories. Otherwise falls back to
    --prompt-lab-dir for auto-creation.
    """
    configs = _load_model_configs()
    sequential = [m for m in models if configs.get(m, {}).get("self_improve_sequential", False)]
    parallel = [m for m in models if not configs.get(m, {}).get("self_improve_sequential", False)]

    print()
    print("=" * 60)
    print(f"Step 2: Running experiments ({len(models)} models)")
    if sequential:
        print(f"  Phase 1: {len(sequential)} local model(s) — sequential")
    if parallel:
        print(f"  Phase 2: {len(parallel)} cloud model(s) — parallel")
    print("=" * 60)

    if events_path:
        emit_event(
            events_path, "runner_plan",
            model_count=len(models),
            sequential_count=len(sequential),
            parallel_count=len(parallel),
            sequential_models=sequential,
            parallel_models=parallel,
        )

    idx = 0

    # Phase 1: local models, one at a time.
    for model in sequential:
        idx += 1
        print(f"\n--- [{idx}/{len(models)}] {model} (sequential) ---")

        cmd = _build_runner_cmd(model, history_dirs, step_name)
        env = _build_runner_env(model)
        if CUSTOM_PROFILE_MODELS.get(model):
            print(f"  (using custom profile: {CUSTOM_PROFILE_MODELS[model]})")

        if events_path:
            emit_event(events_path, "model_start", model=model, phase="sequential")

        result = subprocess.run(cmd, cwd=PLANEXE_DIR, env=env)

        if result.returncode != 0:
            print(f"WARNING: runner.py for {model} exited with code {result.returncode}")
            if events_path:
                emit_event(events_path, "model_error", model=model, returncode=result.returncode)
        else:
            print(f"runner.py for {model} completed successfully")
            if events_path:
                emit_event(events_path, "model_complete", model=model)

    # Phase 2: cloud models, all in parallel.
    if parallel:
        procs: list[tuple[str, subprocess.Popen]] = []
        for model in parallel:
            idx += 1
            print(f"\n--- [{idx}/{len(models)}] {model} (parallel) ---")

            cmd = _build_runner_cmd(model, history_dirs, step_name)
            env = _build_runner_env(model)
            if CUSTOM_PROFILE_MODELS.get(model):
                print(f"  (using custom profile: {CUSTOM_PROFILE_MODELS[model]})")

            if events_path:
                emit_event(events_path, "model_start", model=model, phase="parallel")

            proc = subprocess.Popen(cmd, cwd=PLANEXE_DIR, env=env)
            procs.append((model, proc))

        print(f"\nWaiting for {len(procs)} parallel model(s) to finish...")
        for model, proc in procs:
            proc.wait()
            if proc.returncode != 0:
                print(f"WARNING: runner.py for {model} exited with code {proc.returncode}")
                if events_path:
                    emit_event(events_path, "model_error", model=model, returncode=proc.returncode)
            else:
                print(f"runner.py for {model} completed successfully")
                if events_path:
                    emit_event(events_path, "model_complete", model=model)

    if events_path:
        emit_event(events_path, "all_models_complete", model_count=len(models))


# ---------------------------------------------------------------------------
# Step 3: Analysis pipeline
# ---------------------------------------------------------------------------

def step_analysis(analysis_dir: Path) -> None:
    """Run the full analysis pipeline via run_analysis.py."""
    rel_dir = str(analysis_dir.relative_to(PROMPT_LAB_DIR))
    script_path = PROMPT_LAB_DIR / "analysis" / "run_analysis.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(rel_dir)],
        cwd=PROMPT_LAB_DIR,
    )
    if result.returncode != 0:
        print(f"WARNING: run_analysis.py exited with code {result.returncode}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run one optimization iteration: implement fix → run experiments → analyze.",
    )
    parser.add_argument(
        "--pr",
        type=str,
        default=None,
        help="PR number or URL. Required when --skip-implement is used.",
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
        "--step",
        type=str,
        default=DEFAULT_STEP_NAME,
        choices=["identify_potential_levers", "identify_documents"],
        help=f"Pipeline step to optimize (default: {DEFAULT_STEP_NAME}).",
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

    step_name = args.step
    models = resolve_models(args.models)

    # Read the latest synthesis (only required when implementing).
    latest_analysis_dir = get_latest_analysis_dir(step_name)

    synthesis = None
    recommendation = None
    if latest_analysis_dir:
        print("Latest analysis: " + str(latest_analysis_dir.relative_to(PROMPT_LAB_DIR)))
        synthesis_path = latest_analysis_dir / "synthesis.md"
        if synthesis_path.is_file():
            synthesis = synthesis_path.read_text()
            recommendation = extract_recommendation(synthesis)
            print()
            print("Top recommendation:")
            print("-" * 40)
            for line in recommendation.split("\n")[:8]:
                print(f"  {line}")
            print("  ...")
            print("-" * 40)
        elif not args.skip_implement:
            sys.exit(f"ERROR: synthesis.md not found at {synthesis_path} (required for implement step)")
        else:
            print("  (no synthesis.md — skipped, not needed with --skip-implement)")
    elif not args.skip_implement:
        sys.exit(f"ERROR: No analysis directories found for {step_name} (required for implement step)")
    else:
        print(f"  (no prior analysis for {step_name} — first run)")

    # Step 1: Implement the recommendation.
    pr_arg = args.pr
    if not args.skip_implement:
        pr_number = step_implement(synthesis, recommendation)
        if not pr_arg and pr_number:
            pr_arg = str(pr_number)
    else:
        print("\n[Skipping implementation step]")

    # Prerequisite: verify PLANEXE_DIR is on the PR's branch.
    # Without this check, the runner would import code from whatever branch
    # PLANEXE_DIR happens to be on (often main), producing invalid results.
    if pr_arg and not args.skip_runner:
        verify_planexe_branch(pr_arg)

    # Prepare iteration: create analysis dir + pre-create history dirs.
    # This runs BEFORE the runner so all metadata (including PR info) is
    # available when insight agents start.
    analysis_dir = None
    history_dirs = None

    if not args.skip_analysis or not args.skip_runner:
        print()
        print("=" * 60)
        print("Preparing iteration")
        print("=" * 60)

        if not args.skip_runner:
            result = prepare(
                step_name=step_name,
                pr_arg=pr_arg,
                models=models,
            )
        else:
            # Skipping runner: create analysis dir from existing unanalyzed runs.
            result = prepare_analysis_from_existing(
                step_name=step_name,
                pr_arg=pr_arg,
            )

        if result:
            analysis_dir = result["analysis_dir"]
            history_dirs = result.get("history_dirs", {})

    # Compute events_path for logging.
    events_path = None
    if analysis_dir:
        events_path = analysis_dir / "events.jsonl"

    # Step 2: Run experiments.
    if not args.skip_runner:
        if events_path:
            with EventTimer(events_path, "runner", model_count=len(models)):
                step_runner(models, history_dirs, events_path, step_name)
        else:
            step_runner(models, history_dirs, step_name=step_name)
    else:
        print("\n[Skipping runner step]")

    # Step 3: Analysis pipeline.
    if not args.skip_analysis:
        print()
        print("=" * 60)
        print("Step 3: Analysis pipeline")
        print("=" * 60)

        if analysis_dir:
            if events_path:
                with EventTimer(events_path, "analysis"):
                    step_analysis(analysis_dir)
            else:
                step_analysis(analysis_dir)
        else:
            print("No analysis directory to process (no new runs found).")
    else:
        print("\n[Skipping analysis step]")

    if events_path:
        emit_event(events_path, "iteration_complete")

    print()
    print("=" * 60)
    print("Optimization iteration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
