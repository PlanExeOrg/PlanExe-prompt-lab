#!/usr/bin/env python3
"""
Extract timestamps, durations, model id, and outcomes from
history/*/*_identify_potential_levers/ into a single JSONL file for charting.
"""
import json
import glob
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent / "history"
OUTPUT = Path(__file__).parent / "levers_chart_data.jsonl"

rows = []

for events_path in sorted(glob.glob(str(BASE / "*/*_identify_potential_levers/events.jsonl"))):
    run_dir = Path(events_path).parent
    # Extract history_group (0 or 1) and iteration number
    # run_dir is like .../history/0/50_identify_potential_levers
    rel = run_dir.relative_to(BASE)
    history_group = rel.parts[0]  # "0" or "1"
    iteration_dir = rel.parts[1]  # e.g. "50_identify_potential_levers"
    iteration = int(iteration_dir.split("_")[0])

    # Read meta.json for model info
    meta_path = run_dir / "meta.json"
    model = None
    prompt_sha256 = None
    workers = None
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
            model_info = meta.get("model", {})
            model = model_info.get("primary")
            prompt_sha256 = meta.get("system_prompt_sha256")
            workers = meta.get("workers")

    # Read events.jsonl
    events = []
    with open(events_path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    if not events:
        continue

    # Find the earliest start timestamp (the run start time)
    start_events = [e for e in events if e["event"] == "run_single_plan_start"]
    complete_events = [e for e in events if e["event"] == "run_single_plan_complete"]
    error_events = [e for e in events if e["event"] == "run_single_plan_error"]

    if not start_events:
        continue

    run_timestamp = min(e["timestamp"] for e in start_events)

    # Count outcomes per unique plan (a plan may be retried)
    plan_names = sorted(set(e["plan_name"] for e in start_events))
    num_plans = len(plan_names)
    # Count unique plans that succeeded vs failed (last attempt wins)
    num_ok = sum(1 for p in plan_names if any(e["plan_name"] == p for e in complete_events))
    num_error = sum(1 for p in plan_names if not any(e["plan_name"] == p for e in complete_events) and any(e["plan_name"] == p for e in error_events))

    # Durations from completed plans
    durations = [e["duration_seconds"] for e in complete_events]
    error_durations = [e["duration_seconds"] for e in error_events]
    all_durations = durations + error_durations

    # Wall clock: time from first start to last event
    all_timestamps = [e["timestamp"] for e in events]
    first_ts = min(all_timestamps)
    last_ts = max(all_timestamps)

    # Per-plan details
    plan_results = []
    for plan_name in plan_names:
        ok = [e for e in complete_events if e["plan_name"] == plan_name]
        err = [e for e in error_events if e["plan_name"] == plan_name]
        if ok:
            plan_results.append({
                "plan_name": plan_name,
                "status": "ok",
                "duration_seconds": ok[0]["duration_seconds"],
            })
        elif err:
            plan_results.append({
                "plan_name": plan_name,
                "status": "error",
                "duration_seconds": err[0]["duration_seconds"],
            })

    # Extract model from error if not in meta
    if not model:
        for e in error_events:
            m = re.search(r"LLMModelFromName\(name='([^']+)'\)", e.get("error", ""))
            if m:
                model = m.group(1)
                break

    row = {
        "history_group": int(history_group),
        "iteration": iteration,
        "timestamp": run_timestamp,
        "model": model,
        "prompt_sha256": prompt_sha256,
        "workers": workers,
        "num_plans": num_plans,
        "num_ok": num_ok,
        "num_error": num_error,
        "success_rate": round(num_ok / num_plans, 2) if num_plans > 0 else None,
        "avg_duration_seconds": round(sum(all_durations) / len(all_durations), 2) if all_durations else None,
        "min_duration_seconds": round(min(all_durations), 2) if all_durations else None,
        "max_duration_seconds": round(max(all_durations), 2) if all_durations else None,
        "wall_clock_start": first_ts,
        "wall_clock_end": last_ts,
        "plans": plan_results,
    }
    rows.append(row)

# Sort by history_group then iteration
rows.sort(key=lambda r: (r["history_group"], r["iteration"]))

with open(OUTPUT, "w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")

print(f"Wrote {len(rows)} rows to {OUTPUT}")
