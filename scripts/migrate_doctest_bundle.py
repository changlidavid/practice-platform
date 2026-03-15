from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from migrate_doctest_problem import infer_problem_slug, migrate_problem


@dataclass
class MigrationResult:
    source: str
    slug: str
    status: str
    output_dir: str | None = None
    error: str | None = None


def _discover_problem_files(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*.py")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(source_root).parts)
    )


def _default_sources(repo_root: Path) -> list[Path]:
    return [repo_root / "9021", repo_root / "final"]


def _resolve_sources(repo_root: Path, raw_sources: list[str]) -> list[Path]:
    if not raw_sources:
        return _default_sources(repo_root)
    resolved: list[Path] = []
    for raw in raw_sources:
        source = Path(raw).expanduser()
        if not source.is_absolute():
            source = repo_root / source
        resolved.append(source.resolve())
    return resolved


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slugify_part(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "item"


def structured_slug_for_source(source_root: Path, source_path: Path) -> str:
    rel = source_path.relative_to(source_root).with_suffix("")
    parts = [_slugify_part(source_root.name), *(_slugify_part(part) for part in rel.parts)]
    return "__".join(parts)


def batch_migrate(
    *,
    source_roots: list[Path],
    output_root: Path,
    public_count: int,
    force: bool,
    dry_run: bool,
) -> dict[str, object]:
    results: list[MigrationResult] = []

    for source_root in source_roots:
        if not source_root.exists() or not source_root.is_dir():
            results.append(
                MigrationResult(
                    source=str(source_root),
                    slug="",
                    status="error",
                    error=f"Source bundle not found: {source_root}",
                )
            )
            continue

        for source_path in _discover_problem_files(source_root):
            rel_source = source_path.relative_to(source_root)
            slug = ""
            try:
                _ = infer_problem_slug(source_path)
                slug = structured_slug_for_source(source_root, source_path)
                target_dir = output_root / slug
                if target_dir.exists() and not force:
                    results.append(
                        MigrationResult(
                            source=f"{source_root.name}/{rel_source.as_posix()}",
                            slug=slug,
                            status="skipped",
                            output_dir=str(target_dir),
                        )
                    )
                    continue

                if dry_run:
                    results.append(
                        MigrationResult(
                            source=f"{source_root.name}/{rel_source.as_posix()}",
                            slug=slug,
                            status="would_migrate",
                            output_dir=str(target_dir),
                        )
                    )
                    continue

                problem_dir = migrate_problem(
                    source_path,
                    output_root,
                    slug=slug,
                    title=None,
                    function_name=None,
                    public_count=public_count,
                    force=force,
                )
                results.append(
                    MigrationResult(
                        source=f"{source_root.name}/{rel_source.as_posix()}",
                        slug=slug,
                        status="migrated",
                        output_dir=str(problem_dir),
                    )
                )
            except Exception as exc:
                results.append(
                    MigrationResult(
                        source=f"{source_root.name}/{rel_source.as_posix()}",
                        slug=slug,
                        status="failed",
                        error=str(exc),
                    )
                )

    summary = {
        "source_roots": [str(path) for path in source_roots],
        "output_root": str(output_root),
        "dry_run": dry_run,
        "force": force,
        "public_count": public_count,
        "counts": {
            "migrated": sum(1 for result in results if result.status == "migrated"),
            "would_migrate": sum(1 for result in results if result.status == "would_migrate"),
            "skipped": sum(1 for result in results if result.status == "skipped"),
            "failed": sum(1 for result in results if result.status in {"failed", "error"}),
        },
        "results": [asdict(result) for result in results],
    }
    return summary


def _print_summary(summary: dict[str, object]) -> None:
    counts = summary["counts"]
    print(f"Output root: {summary['output_root']}")
    print(
        "Summary:"
        f" migrated={counts['migrated']}"
        f" would_migrate={counts['would_migrate']}"
        f" skipped={counts['skipped']}"
        f" failed={counts['failed']}"
    )
    for result in summary["results"]:
        status = result["status"]
        source = result["source"]
        slug = result["slug"] or "(unknown)"
        label = f"{source} -> {slug}"
        if result.get("error"):
            print(f"- {status}: {label} ({result['error']})")
        else:
            print(f"- {status}: {label}")


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Batch-migrate legacy doctest bundles into a staged structured bundle."
    )
    parser.add_argument(
        "sources",
        nargs="*",
        help="Bundle roots to scan. Defaults to 9021 and final.",
    )
    parser.add_argument("--output-root", type=Path, default=Path("structured"))
    parser.add_argument("--public-count", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path, help="Optional JSON report output path.")
    args = parser.parse_args(argv)

    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = (repo_root / output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    source_roots = _resolve_sources(repo_root, args.sources)
    summary = batch_migrate(
        source_roots=source_roots,
        output_root=output_root,
        public_count=args.public_count,
        force=args.force,
        dry_run=args.dry_run,
    )
    _print_summary(summary)

    if args.report is not None:
        report_path = args.report
        if not report_path.is_absolute():
            report_path = (repo_root / report_path).resolve()
        _write_report(report_path, summary)
        print(f"Report written to {report_path}")

    counts = summary["counts"]
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
