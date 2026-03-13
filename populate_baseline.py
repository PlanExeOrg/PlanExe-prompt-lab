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
then extracts each into baseline/train/<zip_stem>/ or baseline/verify/<zip_stem>/.
Skips __MACOSX directories and .DS_Store files.
Flattens any single top-level directory inside the zip.
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


REQUIRED_SUFFIXES = ("plan.txt", "report.html")
OPTIONAL_SUFFIXES = ("planexe_metadata.json",)

SKIP_PREFIXES = ("__MACOSX/",)
SKIP_NAMES = (".DS_Store",)


def _should_skip(name: str) -> bool:
    """Return True if this zip member should be skipped."""
    if any(name.startswith(p) for p in SKIP_PREFIXES):
        return True
    if Path(name).name in SKIP_NAMES:
        return True
    return False


def _has_suffix(filenames: set[str], suffix: str) -> bool:
    """Check if any filename matches the suffix (exact or after a '-')."""
    return any(f == suffix or f.endswith("-" + suffix) for f in filenames)


def _check_required_files(members: list[str], strip_prefix: str, label: str) -> list[str]:
    """Check that the zip contains required files. Returns list of missing required suffixes.

    Prints warnings for missing optional files.
    """
    filenames = set()
    for m in members:
        rel = m[len(strip_prefix):] if strip_prefix else m
        if rel and not rel.endswith("/"):
            filenames.add(rel)

    for suffix in OPTIONAL_SUFFIXES:
        if not _has_suffix(filenames, suffix):
            print(f"  [{label}] WARNING: missing optional file: {suffix}")

    missing = []
    for suffix in REQUIRED_SUFFIXES:
        if not _has_suffix(filenames, suffix):
            missing.append(suffix)
    return missing


def extract_zip(zip_path: Path, target_dir: Path, label: str = "") -> int:
    """Extract a zip file into target_dir, flattening a single top-level dir.

    Skips __MACOSX and .DS_Store. If all members share a common top-level
    directory, that level is stripped so files land directly in target_dir.
    Validates that required files (plan.txt, report.html) are present.
    Returns number of files extracted.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [m for m in zf.namelist() if not _should_skip(m)]

        # Detect common top-level directory to flatten
        top_dirs = {m.split("/")[0] for m in members if "/" in m}
        strip_prefix = ""
        if len(top_dirs) == 1:
            strip_prefix = top_dirs.pop() + "/"

        missing = _check_required_files(members, strip_prefix, label)
        if missing:
            raise ValueError(f"zip is missing required files: {', '.join(missing)}")

        target_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for member in members:
            rel_path = member[len(strip_prefix):] if strip_prefix else member
            if not rel_path or rel_path.endswith("/"):
                continue
            dest = target_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1
        return count


def populate(source: str, dry_run: bool = False, force: bool = False) -> None:
    dataset = load_dataset()

    splits = [
        ("train", dataset["train"]),
        ("verify", dataset["verify"]),
    ]

    total_entries = sum(len(zips) for _, zips in splits)
    found = 0
    skipped = 0
    errors = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        for split_name, zip_filenames in splits:
            for zip_filename in zip_filenames:
                dir_name = Path(zip_filename).stem
                label = f"{split_name}/{dir_name}"
                target_dir = BASELINE_DIR / split_name / dir_name

                if target_dir.exists() and not force:
                    print(f"  [{label}] already exists, skipping (use --force to overwrite)")
                    skipped += 1
                    continue

                if dry_run:
                    print(f"  [{label}] would extract from {zip_filename}")
                    found += 1
                    continue

                try:
                    zip_path = resolve_zip(source, zip_filename, tmp_path)
                except Exception as e:
                    print(f"  [{label}] ERROR: could not get {zip_filename}: {e}")
                    errors += 1
                    continue

                if not zip_path.exists():
                    print(f"  [{label}] ERROR: {zip_path} not found")
                    errors += 1
                    continue

                if target_dir.exists() and force:
                    shutil.rmtree(target_dir)

                try:
                    count = extract_zip(zip_path, target_dir, label)
                    print(f"  [{label}] extracted {count} files")
                    found += 1
                except Exception as e:
                    print(f"  [{label}] ERROR extracting: {e}")
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
