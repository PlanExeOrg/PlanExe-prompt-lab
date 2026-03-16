#!/usr/bin/env python3
"""
Prepare an optimization iteration: verify PR, resolve prompt, pre-create
history dirs (one per model), and create the analysis directory with full
metadata -- all before any experiments or agents start.

Replaces the former create_analysis_dir.py and update_meta_pr.py.

Usage:
    python analysis/prepare_iteration.py identify_potential_levers 316
    python analysis/prepare_iteration.py identify_potential_levers 316 --dry-run
    python analysis/prepare_iteration.py identify_potential_levers 316 --models llama,haiku
"""
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_REPO = "PlanExeOrg/PlanExe"

# Models ordered: failed/partial first, then successful.
# Keep in sync with run_optimization_iteration.py.
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

# Models that require PLANEXE_MODEL_PROFILE=custom.
CUSTOM_PROFILE_MODELS = {
    "anthropic-claude-haiku-4-5-pinned": "anthropic_claude.json",
    "anthropic-claude-haiku-4-5": "anthropic_claude.json",
}


# ---------------------------------------------------------------------------
# PR helpers (from update_meta_pr.py)
# ---------------------------------------------------------------------------

def parse_pr_arg(pr_arg: str, repo: str) -> tuple[str, int]:
    """Parse a PR URL or number into (repo, pr_number)."""
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_arg)
    if match:
        return match.group(1), int(match.group(2))
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
    match = re.search(
        r"^## Summary\s*\n(.*?)(?=^## |\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    text = match.group(1).strip() if match else body.strip()
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^- \*?\*?", "", line).strip()
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        if line.startswith("- [") or line.startswith("[") or line.startswith("\U0001f916"):
            break
        lines.append(line)
    return " ".join(lines)


# ---------------------------------------------------------------------------
# Analysis dir helpers (from create_analysis_dir.py)
# ---------------------------------------------------------------------------

def _dir_index(d: Path) -> int:
    """Extract the numeric index prefix from a directory name like '12_step'."""
    return int(d.name.split("_", 1)[0])


def find_analysis_dirs(step_name: str) -> list[Path]:
    """Find all existing analysis directories for this step, sorted by index."""
    analysis_root = REPO_ROOT / "analysis"
    dirs = [d for d in analysis_root.glob(f"*_{step_name}") if d.is_dir()]
    dirs.sort(key=_dir_index)
    return dirs


def collect_analyzed_runs(analysis_dirs: list[Path]) -> set[str]:
    """Read meta.json from each analysis dir and collect all history run paths."""
    analyzed = set()
    for d in analysis_dirs:
        meta_path = d / "meta.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text())
        for run in meta.get("history", []):
            analyzed.add(run)
    return analyzed


def find_all_history_runs(step_name: str) -> list[str]:
    """Scan history/ for all runs matching the step name, sorted by counter."""
    history_root = REPO_ROOT / "history"
    if not history_root.exists():
        return []
    runs = []
    for bucket_dir in sorted(history_root.iterdir()):
        if not bucket_dir.is_dir() or not bucket_dir.name.isdigit():
            continue
        for run_dir in sorted(bucket_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            parts = run_dir.name.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit() and parts[1] == step_name:
                rel = f"{bucket_dir.name}/{run_dir.name}"
                runs.append(rel)
    return runs


def get_next_analysis_index(step_name: str) -> int:
    """Find the next available analysis directory index."""
    analysis_dirs = find_analysis_dirs(step_name)
    if not analysis_dirs:
        return 0
    return _dir_index(analysis_dirs[-1]) + 1


def resolve_prompt_ref(step_name: str, history_runs: list[str]) -> str:
    """Determine the prompt reference from history runs' meta.json files.

    Reads the system_prompt_sha256 from each run and finds the matching
    prompt file under prompts/{step_name}/. If runs use different prompts,
    uses the one from the most recent run.
    """
    sha256 = None
    for run in reversed(history_runs):
        run_meta = REPO_ROOT / "history" / run / "meta.json"
        if run_meta.is_file():
            meta = json.loads(run_meta.read_text())
            sha256 = meta.get("system_prompt_sha256")
            if sha256:
                break

    if not sha256:
        prompts_dir = REPO_ROOT / "prompts" / step_name
        prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
        if not prompt_files:
            sys.exit(f"ERROR: No prompt files found in {prompts_dir}")
        return f"{step_name}/{prompt_files[-1].name}"

    prompts_dir = REPO_ROOT / "prompts" / step_name
    matches = list(prompts_dir.glob(f"prompt_*_{sha256}.txt"))
    if matches:
        return f"{step_name}/{matches[0].name}"

    prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
    if not prompt_files:
        sys.exit(f"ERROR: No prompt files found in {prompts_dir}")
    return f"{step_name}/{prompt_files[-1].name}"


# ---------------------------------------------------------------------------
# History dir helpers (ported from runner.py)
# ---------------------------------------------------------------------------

def _next_history_counter(history_dir: Path) -> int:
    """Scan history/ for the highest existing run number and return +1."""
    max_counter = -1
    if not history_dir.exists():
        return 0
    for bucket in history_dir.iterdir():
        if not bucket.is_dir() or not bucket.name.isdigit():
            continue
        bucket_base = int(bucket.name) * 100
        for run_dir in bucket.iterdir():
            if not run_dir.is_dir():
                continue
            try:
                idx = int(run_dir.name.split("_")[0])
                max_counter = max(max_counter, bucket_base + idx)
            except (IndexError, ValueError):
                pass
    return max_counter + 1


def _run_cmd(cmd: list[str]) -> str | None:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def _collect_system_info() -> dict:
    """Collect basic system info (simplified port from runner.py)."""
    info: dict = {
        "os": platform.system(),
        "os_version": platform.platform(),
        "arch": platform.machine(),
        "cpu_count": os.cpu_count(),
    }
    system = platform.system()
    if system == "Darwin":
        mac_ver = platform.mac_ver()[0]
        if mac_ver:
            info["os_version"] = f"macOS {mac_ver}"
        info["cpu_model"] = _run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"])
        memsize = _run_cmd(["sysctl", "-n", "hw.memsize"])
        if memsize:
            info["memory_gb"] = round(int(memsize) / (1024 ** 3), 1)
    elif system == "Linux":
        info["cpu_model"] = _run_cmd(
            ["bash", "-c", "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2"]
        )
        meminfo = _run_cmd(
            ["bash", "-c", "grep MemTotal /proc/meminfo | awk '{print $2}'"]
        )
        if meminfo:
            info["memory_gb"] = round(int(meminfo) / (1024 ** 2), 1)
    return info


# ---------------------------------------------------------------------------
# Prompt resolution
# ---------------------------------------------------------------------------

def resolve_prompt(step_name: str) -> tuple[str, str]:
    """Find the latest registered prompt; return (relative ref, sha256)."""
    prompts_dir = REPO_ROOT / "prompts" / step_name
    prompt_files = sorted(prompts_dir.glob("prompt_*.txt"))
    if not prompt_files:
        sys.exit(f"ERROR: No prompt files found in {prompts_dir}")
    latest = prompt_files[-1]
    content = latest.read_text()
    sha256 = hashlib.sha256(content.encode()).hexdigest()
    return f"{step_name}/{latest.name}", sha256


# ---------------------------------------------------------------------------
# Model resolution
# ---------------------------------------------------------------------------

def resolve_models(models_arg: str | None) -> list[str]:
    """Resolve model names from CLI argument or return defaults."""
    if not models_arg:
        return list(MODELS)
    result = []
    for name in models_arg.split(","):
        name = name.strip()
        resolved = MODEL_ALIASES.get(name, name)
        result.append(resolved)
    return result


# ---------------------------------------------------------------------------
# Core: prepare full iteration (pre-creates history dirs)
# ---------------------------------------------------------------------------

def prepare(
    step_name: str,
    pr_arg: str | None,
    models: list[str],
    repo: str = DEFAULT_REPO,
    dry_run: bool = False,
) -> dict | None:
    """Prepare an optimization iteration.

    1. Verify PR (optional)
    2. Resolve prompt
    3. Pre-create history dirs (one per model)
    4. Create analysis dir
    5. Write analysis meta.json with PR info + history list
    6. Print summary

    Returns dict with 'analysis_dir' and 'history_dirs' on success,
    None on dry-run.
    """
    # 1. Verify PR (optional).
    pr_url = pr_title = pr_description = None
    if pr_arg:
        pr_repo, pr_number = parse_pr_arg(pr_arg, repo)
        pr = fetch_pr(pr_repo, pr_number)
        pr_url = pr["url"]
        pr_title = pr["title"]
        pr_description = summarize_body(pr.get("body", ""))
        print(f"PR #{pr_number}: {pr_title}")
        print(f"  {pr_url}")

    # 2. Resolve prompt.
    prompt_ref, prompt_sha256 = resolve_prompt(step_name)
    print(f"Prompt: {prompt_ref}")
    print(f"  sha256: {prompt_sha256}")

    # 3. Pre-create history dirs.
    history_dir = REPO_ROOT / "history"
    counter = _next_history_counter(history_dir)
    system_info = _collect_system_info()

    history_entries: list[str] = []
    history_dirs: dict[str, Path] = {}

    print(f"\nHistory dirs ({len(models)} models):")
    for model in models:
        bucket = str(counter // 100)
        entry = f"{counter % 100:02d}_{step_name}"
        run_dir = history_dir / bucket / entry
        rel = f"{bucket}/{entry}"

        meta = {
            "step": step_name,
            "system_prompt_sha256": prompt_sha256,
            "model": {"primary": model},
            "workers": 1,
            "system": system_info,
        }

        print(f"  history/{rel}  ({model})")

        if not dry_run:
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "outputs").mkdir(exist_ok=True)
            (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

        history_entries.append(rel)
        history_dirs[model] = run_dir
        counter += 1

    # 4-5. Create analysis dir + write meta.json.
    index = get_next_analysis_index(step_name)
    analysis_dir = REPO_ROOT / "analysis" / f"{index}_{step_name}"

    analysis_meta: dict = {"prompt": prompt_ref}
    if pr_url:
        analysis_meta["pr_url"] = pr_url
        analysis_meta["pr_title"] = pr_title
        analysis_meta["pr_description"] = pr_description
    analysis_meta["history"] = history_entries

    print(f"\nAnalysis dir: analysis/{index}_{step_name}")

    if dry_run:
        print("\n(dry run -- nothing written)")
        print(json.dumps(analysis_meta, indent=2))
        return None

    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "meta.json").write_text(json.dumps(analysis_meta, indent=2) + "\n")
    print(f"Created: analysis/{index}_{step_name}/meta.json")

    # 6. Summary.
    return {
        "analysis_dir": analysis_dir,
        "history_dirs": history_dirs,
    }


# ---------------------------------------------------------------------------
# Core: prepare analysis from existing runs (for --skip-runner)
# ---------------------------------------------------------------------------

def prepare_analysis_from_existing(
    step_name: str,
    pr_arg: str | None = None,
    repo: str = DEFAULT_REPO,
    dry_run: bool = False,
) -> dict | None:
    """Create analysis dir from existing unanalyzed history runs.

    For use when experiments have already been run (e.g. --skip-runner).
    """
    # 1. Verify PR (optional).
    pr_url = pr_title = pr_description = None
    if pr_arg:
        pr_repo, pr_number = parse_pr_arg(pr_arg, repo)
        pr = fetch_pr(pr_repo, pr_number)
        pr_url = pr["url"]
        pr_title = pr["title"]
        pr_description = summarize_body(pr.get("body", ""))
        print(f"PR #{pr_number}: {pr_title}")
        print(f"  {pr_url}")

    # 2. Find unanalyzed runs.
    all_runs = find_all_history_runs(step_name)
    if not all_runs:
        sys.exit(f"ERROR: No history runs found for step '{step_name}'")

    analysis_dirs = find_analysis_dirs(step_name)
    analyzed = collect_analyzed_runs(analysis_dirs)
    new_runs = [r for r in all_runs if r not in analyzed]

    if not new_runs:
        print(f"No new history runs to analyze for '{step_name}'.")
        print(f"  Total: {len(all_runs)}, analyzed: {len(analyzed)}")
        return None

    # 3. Resolve prompt ref from runs.
    prompt_ref = resolve_prompt_ref(step_name, new_runs)

    # 4. Create analysis dir.
    index = get_next_analysis_index(step_name)
    analysis_dir = REPO_ROOT / "analysis" / f"{index}_{step_name}"

    # 5. Build meta.
    meta: dict = {"prompt": prompt_ref}
    if pr_url:
        meta["pr_url"] = pr_url
        meta["pr_title"] = pr_title
        meta["pr_description"] = pr_description
    meta["history"] = new_runs

    print(f"Step: {step_name}")
    print(f"Total history runs:   {len(all_runs)}")
    print(f"Already analyzed:     {len(analyzed)}")
    print(f"New runs to analyze:  {len(new_runs)}")
    for run in new_runs:
        print(f"  history/{run}")
    print(f"Prompt: {prompt_ref}")
    print(f"Analysis dir: analysis/{index}_{step_name}")

    if dry_run:
        print("\n(dry run -- nothing written)")
        print(json.dumps(meta, indent=2))
        return None

    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Created: analysis/{index}_{step_name}/meta.json")

    return {"analysis_dir": analysis_dir, "history_dirs": {}}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Prepare an optimization iteration: verify PR, resolve prompt, "
        "pre-create history dirs, and create the analysis directory.",
    )
    parser.add_argument(
        "step_name",
        help="Pipeline step name (e.g. identify_potential_levers)",
    )
    parser.add_argument(
        "pr",
        help="PR number or full URL (e.g. 316 or https://github.com/.../pull/316)",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help=(
            "Comma-separated list of models. Supports aliases: "
            + ", ".join(MODEL_ALIASES)
            + ". Default: all models."
        ),
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repo (owner/name). Default: {DEFAULT_REPO}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing anything.",
    )
    args = parser.parse_args()

    models = resolve_models(args.models)
    prepare(
        step_name=args.step_name,
        pr_arg=args.pr,
        models=models,
        repo=args.repo,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
