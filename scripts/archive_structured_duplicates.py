from __future__ import annotations

import argparse
import shutil
from pathlib import Path


DEFAULT_DUPLICATES = (
    "good_subsequences_2_sample_3",
    "good_subsequences_sample_3",
    "remove_consecutive_duplicates_1",
    "remove_consecutive_duplicates_2_sample_1",
    "remove_consecutive_duplicates_sample_1",
)


def archive_duplicates(*, repo_root: Path, names: list[str], dry_run: bool) -> list[dict[str, str]]:
    structured_root = repo_root / "structured"
    archive_root = repo_root / "structured_archive"
    archive_root.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, str]] = []
    for name in names:
        source = structured_root / name
        target = archive_root / name
        if not source.exists():
            results.append({"name": name, "status": "missing", "source": str(source), "target": str(target)})
            continue
        if target.exists():
            results.append({"name": name, "status": "target_exists", "source": str(source), "target": str(target)})
            continue
        if dry_run:
            results.append({"name": name, "status": "would_archive", "source": str(source), "target": str(target)})
            continue
        shutil.move(str(source), str(target))
        results.append({"name": name, "status": "archived", "source": str(source), "target": str(target)})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Move confirmed duplicate structured problems into structured_archive/.")
    parser.add_argument(
        "names",
        nargs="*",
        default=list(DEFAULT_DUPLICATES),
        help="Structured problem directories to archive.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview moves without changing anything.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    results = archive_duplicates(repo_root=repo_root, names=list(args.names), dry_run=args.dry_run)
    for result in results:
        print(f"{result['status']}: {result['name']} -> {result['target']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
