#!/usr/bin/env python3
"""
Populate the baseline/ directory by extracting plan zip files.

Usage:
    # Download the official zip files from PlanExe
    # From a URL prefix (each zip is downloaded from <url>/<filename>):
    python populate_baseline.py https://github.com/PlanExeOrg/PlanExe-web/raw/refs/heads/main/
    # or if that doesn't work, try this:
    python populate_baseline.py https://planexe.org/

    # From a local directory containing the zip files. In case you have your own plans you want to optimize:
    python populate_baseline.py /absolute/path/to/zips

    # Dry run — show what would be done without extracting:
    python populate_baseline.py --dry-run /absolute/path/to/zips

The script reads dataset.json to discover which zips belong to train vs verify,
then extracts each into baseline/train/<name>/ or baseline/verify/<name>/.
"""
import argparse
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_JSON = SCRIPT_DIR / "dataset.json"
BASELINE_DIR = SCRIPT_DIR / "baseline"


def load_dataset() -> dict:
    with open(DATASET_JSON) as f:
        return json.load(f)


def resolve_zip(source: str, zip_filename: str, tmp_dir: Path) -> Path:
    """Return a local path to the zip file, downloading if source is a URL."""
    if source.startswith("http://") or source.startswith("https://"):
        url = source.rstrip("/") + "/" + zip_filename
        dest = tmp_dir / zip_filename
        print(f"  Downloading {url}")
        urllib.request.urlretrieve(url, dest)
        return dest
    else:
        return Path(source) / zip_filename


def extract_zip(zip_path: Path, target_dir: Path) -> int:
    """Extract a zip file into target_dir. Returns number of files extracted."""
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        zf.extractall(target_dir)
        return len(members)


def populate(source: str, dry_run: bool = False, force: bool = False) -> None:
    dataset = load_dataset()

    splits = [
        ("train", dataset["train"]),
        ("verify", dataset["verify"]),
    ]

    total_entries = sum(len(entries) for _, entries in splits)
    found = 0
    skipped = 0
    errors = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        for split_name, entries in splits:
            for entry in entries:
                name = entry["name"]
                zip_filename = entry["zip"]
                target_dir = BASELINE_DIR / split_name / name

                if target_dir.exists() and not force:
                    print(f"  [{split_name}/{name}] already exists, skipping (use --force to overwrite)")
                    skipped += 1
                    continue

                if dry_run:
                    print(f"  [{split_name}/{name}] would extract from {zip_filename}")
                    found += 1
                    continue

                try:
                    zip_path = resolve_zip(source, zip_filename, tmp_path)
                except Exception as e:
                    print(f"  [{split_name}/{name}] ERROR: could not get {zip_filename}: {e}")
                    errors += 1
                    continue

                if not zip_path.exists():
                    print(f"  [{split_name}/{name}] ERROR: {zip_path} not found")
                    errors += 1
                    continue

                if target_dir.exists() and force:
                    shutil.rmtree(target_dir)

                try:
                    count = extract_zip(zip_path, target_dir)
                    print(f"  [{split_name}/{name}] extracted {count} files")
                    found += 1
                except Exception as e:
                    print(f"  [{split_name}/{name}] ERROR extracting: {e}")
                    errors += 1

    print()
    print(f"Done: {found} extracted, {skipped} skipped, {errors} errors (out of {total_entries} total)")

    if errors > 0:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate baseline/ from plan zip files.",
        epilog="Source can be a local directory path or an HTTP(S) URL prefix.",
    )
    parser.add_argument(
        "source",
        help="Local directory or URL prefix where zip files are located",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without extracting",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing baseline directories",
    )
    args = parser.parse_args()

    print(f"Source: {args.source}")
    print(f"Target: {BASELINE_DIR}")
    print()

    populate(args.source, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
