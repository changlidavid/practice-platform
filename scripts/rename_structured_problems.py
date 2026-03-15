from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_GENERIC_FUNCTION_NAMES = {
    "f",
    "g",
    "h",
    "solve",
    "solution",
    "display",
    "rectangle",
    "main",
}
_NOISE_TOKENS = {"structured", "final", "item", "problem", "question"}


@dataclass
class RenameResult:
    old_dir: str
    new_dir: str | None
    status: str
    reason: str = ""


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "problem"


def _read_meta(problem_dir: Path) -> dict[str, object]:
    meta_path = problem_dir / "meta.json"
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid metadata in {meta_path}")
    return payload


def _infer_entry_function(problem_dir: Path, meta: dict[str, object]) -> str:
    entry_function = str(meta.get("entry_function", "")).strip()
    if entry_function:
        return entry_function

    starter_path = problem_dir / "starter.py"
    module = ast.parse(starter_path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    raise ValueError(f"Could not infer entry function from {starter_path}")


def _is_generic_slug(slug: str) -> bool:
    return slug in _GENERIC_FUNCTION_NAMES or len(slug) <= 1


def _meaningful_tokens_from_name(raw: str) -> list[str]:
    normalized = _slugify(raw)
    tokens = [token for token in normalized.split("_") if token.strip()]
    filtered: list[str] = []
    for token in tokens:
        if not token:
            continue
        if token in _NOISE_TOKENS:
            continue
        if re.fullmatch(r"[0-9]{8,}", token):
            continue
        if len(token) >= 10 and any(char.isdigit() for char in token):
            continue
        filtered.append(token)
    return filtered


def _suffix_candidates(problem_dir: Path, meta: dict[str, object], base_slug: str) -> list[str]:
    candidates: list[str] = []

    name_tokens = _meaningful_tokens_from_name(problem_dir.name)
    title_tokens = _meaningful_tokens_from_name(str(meta.get("title", "")))

    def add_suffix(tokens: list[str]) -> None:
        filtered = [token for token in tokens if token != base_slug]
        if not filtered:
            return
        for width in (2, 3, 1):
            if len(filtered) >= width:
                suffix = "_".join(filtered[-width:])
                if suffix and suffix not in candidates:
                    candidates.append(suffix)

    add_suffix(name_tokens)
    add_suffix(title_tokens)
    return candidates


def _resolve_target_slug(
    problem_dir: Path,
    meta: dict[str, object],
    *,
    taken_names: set[str],
) -> str:
    base_slug = _slugify(_infer_entry_function(problem_dir, meta))
    generic = _is_generic_slug(base_slug)
    suffixes = _suffix_candidates(problem_dir, meta, base_slug)

    candidate_order: list[str] = []
    if not generic:
        candidate_order.append(base_slug)
    for suffix in suffixes:
        candidate = f"{base_slug}_{suffix}"
        if candidate not in candidate_order:
            candidate_order.append(candidate)
    if generic and not candidate_order:
        candidate_order.append(f"{base_slug}_{_slugify(problem_dir.name)}")

    for candidate in candidate_order:
        if candidate == problem_dir.name:
            return candidate
        if candidate not in taken_names:
            return candidate

    seed = candidate_order[0] if candidate_order else base_slug
    counter = 2
    while True:
        candidate = f"{seed}_{counter}"
        if candidate == problem_dir.name or candidate not in taken_names:
            return candidate
        counter += 1


def rename_structured_problems(*, structured_root: Path, dry_run: bool) -> dict[str, object]:
    results: list[RenameResult] = []
    if not structured_root.exists():
        raise FileNotFoundError(f"Structured root not found: {structured_root}")

    problem_dirs = sorted(
        path for path in structured_root.iterdir() if path.is_dir() and (path / "meta.json").exists()
    )
    seen_targets = {path.name for path in problem_dirs}

    for problem_dir in problem_dirs:
        try:
            meta = _read_meta(problem_dir)
            target_slug = _resolve_target_slug(
                problem_dir,
                meta,
                taken_names=seen_targets - {problem_dir.name},
            )
            target_dir = structured_root / target_slug
            if target_slug == problem_dir.name:
                results.append(
                    RenameResult(
                        old_dir=str(problem_dir),
                        new_dir=str(problem_dir),
                        status="unchanged",
                    )
                )
                continue

            if not dry_run:
                meta["slug"] = target_slug
                (problem_dir / "meta.json").write_text(
                    json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                problem_dir.rename(target_dir)
            seen_targets.discard(problem_dir.name)
            seen_targets.add(target_slug)
            results.append(
                RenameResult(
                    old_dir=str(problem_dir),
                    new_dir=str(target_dir),
                    status="renamed",
                )
            )
        except Exception as exc:
            results.append(
                RenameResult(
                    old_dir=str(problem_dir),
                    new_dir=None,
                    status="failed",
                    reason=str(exc),
                )
            )

    summary = {
        "structured_root": str(structured_root),
        "dry_run": dry_run,
        "counts": {
            "renamed": sum(1 for item in results if item.status == "renamed"),
            "unchanged": sum(1 for item in results if item.status == "unchanged"),
            "skipped": sum(1 for item in results if item.status == "skipped"),
            "failed": sum(1 for item in results if item.status == "failed"),
        },
        "results": [asdict(item) for item in results],
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Rename structured problems to cleaner entry-function-based slugs."
    )
    parser.add_argument("--root", type=Path, default=Path("structured"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path, help="Optional JSON report path.")
    args = parser.parse_args(argv)

    root = args.root
    if not root.is_absolute():
        root = (repo_root / root).resolve()

    summary = rename_structured_problems(structured_root=root, dry_run=args.dry_run)
    counts = summary["counts"]
    print(
        f"Structured root: {summary['structured_root']}\n"
        f"renamed={counts['renamed']} unchanged={counts['unchanged']} "
        f"skipped={counts['skipped']} failed={counts['failed']}"
    )
    for result in summary["results"]:
        if result["status"] == "renamed":
            print(f"- renamed: {result['old_dir']} -> {result['new_dir']}")
        elif result["status"] == "skipped":
            print(f"- skipped: {result['old_dir']} ({result['reason']})")
        elif result["status"] == "failed":
            print(f"- failed: {result['old_dir']} ({result['reason']})")

    if args.report is not None:
        report_path = args.report
        if not report_path.is_absolute():
            report_path = (repo_root / report_path).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Report written to {report_path}")

    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
