from __future__ import annotations

import ast
import doctest
import hashlib
import json
import sqlite3
from pathlib import Path

from . import db
from .config import Paths


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


_REQUIRED_FUNCTION_PROBLEM_FILES = (
    "meta.json",
    "statement.md",
    "starter.py",
    "public_examples.json",
    "hidden_tests.json",
)


def _is_under_dirs(path: Path, dirs: set[Path]) -> bool:
    for parent in dirs:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            continue
    return False


def discover_bundle(
    source_root: Path,
) -> tuple[list[Path], list[Path], list[Path], list[Path]]:
    function_problem_dirs = sorted(
        p.parent
        for p in source_root.rglob("meta.json")
        if p.is_file() and not _is_hidden(p.relative_to(source_root))
    )
    function_dir_set = {p.resolve() for p in function_problem_dirs}

    problem_files = sorted(
        p
        for p in source_root.rglob("*.py")
        if p.is_file()
        and not _is_hidden(p.relative_to(source_root))
        and not _is_under_dirs(p.resolve(), function_dir_set)
    )
    asset_files = sorted(
        p
        for p in source_root.rglob("*")
        if p.is_file()
        and p.suffix != ".py"
        and not p.name.startswith(".")
        and not _is_hidden(p.relative_to(source_root))
        and not _is_under_dirs(p.resolve(), function_dir_set)
    )
    function_problem_files = sorted(
        p
        for problem_dir in function_problem_dirs
        for p in problem_dir.rglob("*")
        if p.is_file() and not _is_hidden(p.relative_to(source_root))
    )
    return problem_files, asset_files, function_problem_dirs, function_problem_files


def bundle_snapshot_hash(source_root: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        rel = path.relative_to(source_root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(_sha256_file(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _slug_for_problem(
    source_root: Path, default_source_root: Path, relpath: Path
) -> str:
    stem = relpath.with_suffix("").as_posix().replace("/", ".")
    if source_root.resolve() == default_source_root.resolve():
        # Keep backward-compatible slugs for the default bundle.
        return relpath.stem
    return f"{source_root.name}:{stem}"


def _extract_doctest_text(source: str) -> tuple[str, str]:
    module = ast.parse(source)
    module_doc = ast.get_docstring(module, clean=False) or ""
    parser = doctest.DocTestParser()
    parts = parser.parse(module_doc)
    description = "".join(part for part in parts if isinstance(part, str)).strip()
    return description, module_doc


def _statement_summary(statement_md: str, fallback: str) -> str:
    for raw_line in statement_md.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        return line
    return fallback


def _content_hash_for_files(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256_file(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _slug_for_function_problem(
    source_root: Path,
    default_source_root: Path,
    rel_dir: Path,
    meta: dict[str, object],
) -> str:
    configured = str(meta.get("slug", "")).strip()
    if configured:
        if source_root.resolve() == default_source_root.resolve():
            return configured
        if ":" in configured:
            return configured
        return f"{source_root.name}:{configured}"
    stem = rel_dir.as_posix().replace("/", ".")
    if source_root.resolve() == default_source_root.resolve():
        return rel_dir.name
    return f"{source_root.name}:{stem}"


def _safe_template_code(source_text: str, module_doctest: str) -> str:
    if source_text.strip():
        return source_text
    if module_doctest.strip():
        return f"__doc__ = {module_doctest!r}\n"
    return "# Starter code unavailable for this problem.\n"


def import_bundle(conn: sqlite3.Connection, paths: Paths, source_root: Path) -> dict[str, str | int]:
    source_root = source_root.resolve()
    if not source_root.exists() or not source_root.is_dir():
        raise FileNotFoundError(f"Bundle folder not found: {source_root}")

    problem_files, asset_files, function_problem_dirs, function_problem_files = discover_bundle(source_root)
    if not problem_files and not function_problem_dirs:
        raise RuntimeError(f"No problem files found in {source_root}")

    all_files = problem_files + asset_files + function_problem_files
    snapshot_hash = bundle_snapshot_hash(source_root, all_files)

    existing_bundle = db.get_bundle_by_hash(conn, snapshot_hash)
    bundle_name = source_root.name
    if existing_bundle is None:
        bundle_id = db.insert_bundle(conn, bundle_name, str(source_root), snapshot_hash)
    else:
        bundle_id = int(existing_bundle["id"])
    db.prune_bundles_for_source_root_except(
        conn,
        source_root=str(source_root),
        keep_bundle_id=bundle_id,
    )

    asset_manifest = [p.relative_to(source_root).as_posix() for p in asset_files]
    for asset in asset_files:
        db.upsert_bundle_asset(
            conn,
            bundle_id=bundle_id,
            relpath=asset.relative_to(source_root).as_posix(),
            content=asset.read_bytes(),
        )

    for src in problem_files:
        rel = src.relative_to(source_root)
        slug = _slug_for_problem(source_root, paths.source_bundle, rel)
        source_text = src.read_text(encoding="utf-8")
        description, module_doctest = _extract_doctest_text(source_text)
        title = rel.stem.replace("_", " ").strip().title() or rel.stem

        db.upsert_problem(
            conn,
            bundle_id=bundle_id,
            slug=slug,
            title=title,
            description=description or f"Solve problem '{slug}'.",
            template_code=_safe_template_code(source_text, module_doctest),
            doctest=module_doctest,
            source_relpath=rel.as_posix(),
            assets_manifest=asset_manifest,
            content_hash=_sha256_file(src),
        )

    for problem_dir in function_problem_dirs:
        rel_dir = problem_dir.relative_to(source_root)
        required_paths = [problem_dir / name for name in _REQUIRED_FUNCTION_PROBLEM_FILES]
        missing_files = [path.name for path in required_paths if not path.exists()]
        if missing_files:
            raise RuntimeError(
                f"Incomplete function problem '{rel_dir.as_posix()}': missing {', '.join(sorted(missing_files))}"
            )

        meta_raw = (problem_dir / "meta.json").read_text(encoding="utf-8")
        statement_md = (problem_dir / "statement.md").read_text(encoding="utf-8")
        starter_code = (problem_dir / "starter.py").read_text(encoding="utf-8")
        public_examples_raw = (problem_dir / "public_examples.json").read_text(encoding="utf-8")

        try:
            meta = json.loads(meta_raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {problem_dir / 'meta.json'}: {exc}") from exc
        if not isinstance(meta, dict):
            raise RuntimeError(f"Invalid metadata in {problem_dir / 'meta.json'}: expected object")

        try:
            public_examples = json.loads(public_examples_raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {problem_dir / 'public_examples.json'}: {exc}") from exc
        if not isinstance(public_examples, (list, dict)):
            raise RuntimeError(
                f"Invalid public examples in {problem_dir / 'public_examples.json'}: expected list or object"
            )

        hidden_tests_raw = (problem_dir / "hidden_tests.json").read_text(encoding="utf-8")
        try:
            hidden_tests = json.loads(hidden_tests_raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {problem_dir / 'hidden_tests.json'}: {exc}") from exc
        if not isinstance(hidden_tests, dict) or not isinstance(hidden_tests.get("cases"), list):
            raise RuntimeError(
                f"Invalid hidden tests in {problem_dir / 'hidden_tests.json'}: expected object with list 'cases'"
            )

        entry_function = str(meta.get("entry_function", "")).strip()
        if not entry_function:
            raise RuntimeError(
                f"Invalid metadata in {problem_dir / 'meta.json'}: missing non-empty 'entry_function'"
            )

        slug = _slug_for_function_problem(source_root, paths.source_bundle, rel_dir, meta)
        title = str(meta.get("title", "")).strip() or rel_dir.name.replace("_", " ").title()
        description = _statement_summary(statement_md, f"Solve problem '{slug}'.")

        db.upsert_problem(
            conn,
            bundle_id=bundle_id,
            slug=slug,
            title=title,
            description=description,
            template_code=starter_code,
            doctest="",
            evaluation_mode="function_json",
            entry_function=entry_function,
            problem_dir_relpath=rel_dir.as_posix(),
            public_examples_json=json.dumps(public_examples, ensure_ascii=False),
            statement_md=statement_md,
            source_relpath=(rel_dir / "starter.py").as_posix(),
            assets_manifest=[],
            content_hash=_content_hash_for_files(required_paths),
        )

    return {
        "bundle_name": bundle_name,
        "snapshot_hash": snapshot_hash,
        "problem_count": len(problem_files) + len(function_problem_dirs),
        "asset_count": len(asset_files),
    }


def ensure_imported(conn: sqlite3.Connection, paths: Paths) -> None:
    existing = conn.execute("SELECT COUNT(*) AS c FROM problems").fetchone()
    if existing is not None and int(existing["c"]) > 0:
        return
    if not paths.source_bundle.exists():
        return
    import_bundle(conn, paths, paths.source_bundle)
