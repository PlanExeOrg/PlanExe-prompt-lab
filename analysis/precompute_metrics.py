#!/usr/bin/env python3
"""
Pre-compute quantitative metrics for JSON output files.

Produces a metrics report that can be embedded directly in a Claude prompt,
eliminating the need for Claude to read and manually count/measure every file.
"""
import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# String analysis helpers (adapted from json_string_analysis)
# ---------------------------------------------------------------------------

def _string_stats(s: str) -> dict:
    return {
        "bytes": len(s.encode("utf-8")),
        "chars": len(s),
        "words": len(s.split()),
    }


def _agg(values: list[int | float]) -> dict:
    if not values:
        return {"min": 0, "max": 0, "avg": 0.0}
    return {
        "min": min(values),
        "max": max(values),
        "avg": round(sum(values) / len(values), 1),
    }


# ---------------------------------------------------------------------------
# Template leakage detection
# ---------------------------------------------------------------------------

_LEAKAGE_SUBJECTS = re.compile(
    r"\bthe options\b", re.IGNORECASE
)
_LEAKAGE_VERBS = re.compile(
    r"\b(don't|do not|fail to|miss |overlook|neglect|lack |assume|ignore)\b",
    re.IGNORECASE,
)


def _has_template_leakage(review: str) -> bool:
    """Detect 'the options [verb]' template leakage pattern."""
    return bool(_LEAKAGE_SUBJECTS.search(review) and _LEAKAGE_VERBS.search(review))


# ---------------------------------------------------------------------------
# Per-file lever analysis
# ---------------------------------------------------------------------------

def analyze_levers(levers: list[dict]) -> dict:
    """Compute metrics for a single lever file (list of lever dicts)."""
    count = len(levers)

    names = [lv.get("name", "") for lv in levers]
    unique_names = len(set(n.lower() for n in names))

    option_counts = [len(lv.get("options", [])) for lv in levers]
    option_violations = sum(1 for c in option_counts if c != 3)

    consequences_chars = [len(lv.get("consequences", "")) for lv in levers]
    review_chars = [len(lv.get("review", "")) for lv in levers]

    # Flatten all option strings
    all_options = [opt for lv in levers for opt in lv.get("options", []) if isinstance(opt, str)]
    option_chars = [len(opt) for opt in all_options]

    # Template leakage
    reviews = [lv.get("review", "") for lv in levers]
    leaky_count = sum(1 for r in reviews if _has_template_leakage(r))

    return {
        "lever_count": count,
        "name_uniqueness": round(unique_names / count, 2) if count else 0,
        "unique_names": unique_names,
        "option_violations": option_violations,
        "template_leakage": leaky_count,
        "template_leakage_pct": round(100 * leaky_count / count, 1) if count else 0,
        "consequences_chars": _agg(consequences_chars),
        "review_chars": _agg(review_chars),
        "option_chars": _agg(option_chars),
    }


# ---------------------------------------------------------------------------
# Per-file document analysis
# ---------------------------------------------------------------------------

def analyze_documents(docs: list[dict]) -> dict:
    """Compute metrics for a single document file (list of document dicts)."""
    count = len(docs)

    names = [d.get("document_name", "") for d in docs]
    unique_names = len(set(n.lower() for n in names))

    desc_chars = [len(d.get("description", "")) for d in docs]

    # Nested list counts
    steps_counts = []
    keywords_counts = []
    for d in docs:
        for key in ("steps_to_find", "steps_to_create"):
            if key in d and isinstance(d[key], list):
                steps_counts.append(len(d[key]))
        if "search_keywords" in d and isinstance(d["search_keywords"], list):
            keywords_counts.append(len(d["search_keywords"]))

    # Field completeness
    optional_fields = [
        "document_template_primary", "document_template_secondary",
        "search_keywords", "document_url",
    ]
    total_optional = 0
    filled_optional = 0
    for d in docs:
        for f in optional_fields:
            if f in d:
                total_optional += 1
                if d[f] is not None and d[f] != "" and d[f] != []:
                    filled_optional += 1

    return {
        "document_count": count,
        "name_uniqueness": round(unique_names / count, 2) if count else 0,
        "description_chars": _agg(desc_chars),
        "steps_per_doc": _agg(steps_counts) if steps_counts else None,
        "keywords_per_doc": _agg(keywords_counts) if keywords_counts else None,
        "field_completeness_pct": round(100 * filled_optional / total_optional, 1) if total_optional else None,
    }


# ---------------------------------------------------------------------------
# Success rates from outputs.jsonl
# ---------------------------------------------------------------------------

def read_success_rates(outputs_jsonl: Path) -> dict:
    """Parse outputs.jsonl and return success/failure summary."""
    if not outputs_jsonl.is_file():
        return {"error": "outputs.jsonl not found"}

    plans = []
    for line in outputs_jsonl.read_text().strip().splitlines():
        plans.append(json.loads(line))

    total = len(plans)
    succeeded = sum(1 for p in plans if p.get("status") == "ok")
    failed = [p for p in plans if p.get("status") != "ok"]
    partial = [p for p in plans if p.get("calls_succeeded") is not None and
               p.get("calls_succeeded", 3) < 3 and p.get("status") == "ok"]

    result = {
        "total": total,
        "succeeded": succeeded,
        "failed": total - succeeded,
    }
    if failed:
        result["failures"] = [
            {"name": p["name"], "error": p.get("error", "unknown")}
            for p in failed
        ]
    if partial:
        result["partial"] = [
            {"name": p["name"], "calls_succeeded": p["calls_succeeded"]}
            for p in partial
        ]
    return result


# ---------------------------------------------------------------------------
# Full metrics report
# ---------------------------------------------------------------------------

STEP_OUTPUT_FILES = {
    "identify_potential_levers": [
        ("002-10-potential_levers.json", "levers", analyze_levers),
    ],
    "identify_documents": [
        ("017-5-identified_documents_to_find.json", "documents_to_find", analyze_documents),
        ("017-6-identified_documents_to_create.json", "documents_to_create", analyze_documents),
    ],
}


def _analyze_outputs(outputs_dir: Path, step_name: str) -> dict:
    """Analyze all plan outputs under an outputs directory."""
    file_configs = STEP_OUTPUT_FILES.get(step_name, [])
    if not file_configs:
        return {"error": f"unknown step: {step_name}"}

    plan_dirs = sorted(
        [d for d in outputs_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    results = {}
    for plan_dir in plan_dirs:
        plan_name = plan_dir.name
        plan_metrics = {}
        for filename, label, analyze_fn in file_configs:
            filepath = plan_dir / filename
            if filepath.is_file():
                data = json.loads(filepath.read_text())
                plan_metrics[label] = analyze_fn(data)
            else:
                plan_metrics[label] = {"error": f"{filename} not found"}
        results[plan_name] = plan_metrics

    return results


def compute_metrics(
    repo_root: Path,
    step_name: str,
    history_runs: list[str],
) -> dict:
    """Compute the full metrics report for all runs + baseline."""
    report = {"step": step_name}

    # Baseline
    baseline_dir = repo_root / "baseline" / "train"
    if baseline_dir.is_dir():
        report["baseline"] = _analyze_outputs(baseline_dir, step_name)
    else:
        report["baseline"] = {"error": "baseline/train not found"}

    # History runs
    runs = {}
    for run_path in history_runs:
        run_dir = repo_root / "history" / run_path
        run_meta_path = run_dir / "meta.json"

        run_info = {}

        # Model name
        if run_meta_path.is_file():
            run_meta = json.loads(run_meta_path.read_text())
            run_info["model"] = run_meta.get("model", {}).get("primary", "unknown")
        else:
            run_info["model"] = "unknown"

        # Success rates
        outputs_jsonl = run_dir / "outputs.jsonl"
        run_info["success"] = read_success_rates(outputs_jsonl)

        # Per-plan metrics
        outputs_dir = run_dir / "outputs"
        if outputs_dir.is_dir():
            run_info["plans"] = _analyze_outputs(outputs_dir, step_name)
        else:
            run_info["plans"] = {"error": "outputs dir not found"}

        runs[run_path] = run_info

    report["runs"] = runs
    return report


def format_metrics_text(report: dict) -> str:
    """Format the metrics report as compact JSON for prompt embedding."""
    return json.dumps(report, separators=(",", ":"), ensure_ascii=False)
