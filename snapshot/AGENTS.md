# Snapshot

Snapshots let you re-run a single pipeline step with a modified prompt and
compare the output against the baseline plans.

## How it works

1. **Copy baseline inputs.** Take the baseline/train plans and copy all files
   up to (but not including) the step you are exercising. This gives the
   modified step the same starting point as the baseline.

2. **Run the step.** Execute the pipeline step under test (e.g. via
   `run_optimization_iteration.py`). The step reads its inputs from the
   snapshot directory and writes its outputs to the history outputs directory.

3. **Capture outputs.** Use `copy_history_to_snapshot.py` to copy the generated
   output files back into the snapshot directory.

4. **Compare.** The snapshot now contains a complete plan built from baseline
   inputs + new step outputs. Compare against the baseline to measure how
   changes early in the pipeline propagate through the full plan.

## Directory layout

```
snapshot/
  0_identify_potential_levers/   # snapshot plan dirs (same names as baseline)
    20250321_silo/
    20250329_gta_game/
    ...
../copy_history_to_snapshot.py  # copies numeric-prefixed files from history
```

## copy_history_to_snapshot.py

Copies files whose names start with a numeric prefix (e.g. `002-10-...`) from
a history output directory into the matching snapshot subdirectories.

```
python copy_history_to_snapshot.py <source_dir> <dest_dir> [--dry-run]
```

Example:

```
python copy_history_to_snapshot.py \
    history/2/99_identify_potential_levers/outputs \
    snapshot/0_identify_potential_levers
```

Use `--dry-run` to preview which files would be copied.
