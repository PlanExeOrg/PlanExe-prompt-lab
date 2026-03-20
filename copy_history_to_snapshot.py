"""
Transfer files with numeric prefixes from history output dirs to snapshot dirs.

Traverses subdirectories common to both source and destination, and copies
files whose names start with a digit-underscore pattern (e.g. "002-10-potential_levers.json").

Usage:
    python transfer_outputs.py <source_dir> <dest_dir>

Example:
```bash
python copy_history_to_snapshot.py history/2/99_identify_potential_levers/outputs snapshot/0_identify_potential_levers
  copying: 20250321_silo/002-10-potential_levers.json
  copying: 20250321_silo/002-9-potential_levers_raw.json
  copying: 20250329_gta_game/002-10-potential_levers.json
  copying: 20250329_gta_game/002-9-potential_levers_raw.json
  copying: 20260308_sovereign_identity/002-10-potential_levers.json
  copying: 20260308_sovereign_identity/002-9-potential_levers_raw.json
  copying: 20260310_hong_kong_game/002-10-potential_levers.json
  copying: 20260310_hong_kong_game/002-9-potential_levers_raw.json
  copying: 20260311_parasomnia_research_unit/002-10-potential_levers.json
  copying: 20260311_parasomnia_research_unit/002-9-potential_levers_raw.json

Copied 10 files across 5 subdirectories.
```

"""
import argparse
import re
import shutil
from pathlib import Path

FILE_PATTERN = re.compile(r"^\d+")


def transfer_outputs(source_dir: Path, dest_dir: Path, *, dry_run: bool = False) -> int:
    if not source_dir.is_dir():
        raise SystemExit(f"Source dir does not exist: {source_dir}")
    if not dest_dir.is_dir():
        raise SystemExit(f"Destination dir does not exist: {dest_dir}")

    source_subdirs = {d.name for d in source_dir.iterdir() if d.is_dir()}
    dest_subdirs = {d.name for d in dest_dir.iterdir() if d.is_dir()}
    common = sorted(source_subdirs & dest_subdirs)

    if not common:
        print("No common subdirectories found.")
        return 0

    copied = 0
    for subdir_name in common:
        src_sub = source_dir / subdir_name
        dst_sub = dest_dir / subdir_name

        for src_file in sorted(src_sub.iterdir()):
            if not src_file.is_file():
                continue
            if not FILE_PATTERN.match(src_file.name):
                continue

            dst_file = dst_sub / src_file.name
            action = "would copy" if dry_run else "copying"
            print(f"  {action}: {subdir_name}/{src_file.name}")

            if not dry_run:
                shutil.copy2(src_file, dst_file)
            copied += 1

    print(f"\n{'Would copy' if dry_run else 'Copied'} {copied} files across {len(common)} subdirectories.")
    return copied


def main():
    parser = argparse.ArgumentParser(description="Transfer numeric-prefixed files from history outputs to snapshot.")
    parser.add_argument("source_dir", type=Path, help="Source directory (e.g. history/2/99_.../outputs)")
    parser.add_argument("dest_dir", type=Path, help="Destination directory (e.g. snapshot/0_identify_potential_levers)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without copying")
    args = parser.parse_args()

    transfer_outputs(args.source_dir, args.dest_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
