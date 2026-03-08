from __future__ import annotations

import hashlib
import sqlite3
import ast
import doctest
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


def discover_bundle(source_root: Path) -> tuple[list[Path], list[Path]]:
    problem_files = sorted(
        p for p in source_root.rglob("*.py") if p.is_file() and not _is_hidden(p.relative_to(source_root))
    )
    asset_files = sorted(
        p
        for p in source_root.rglob("*")
        if p.is_file()
        and p.suffix != ".py"
        and not p.name.startswith(".")
        and not _is_hidden(p.relative_to(source_root))
    )
    return problem_files, asset_files


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

    problem_files, asset_files = discover_bundle(source_root)
    if not problem_files:
        raise RuntimeError(f"No problem files found in {source_root}")

    all_files = problem_files + asset_files
    snapshot_hash = bundle_snapshot_hash(source_root, all_files)

    existing_bundle = db.get_bundle_by_hash(conn, snapshot_hash)
    bundle_name = source_root.name
    if existing_bundle is None:
        bundle_id = db.insert_bundle(conn, bundle_name, str(source_root), snapshot_hash)
    else:
        bundle_id = int(existing_bundle["id"])

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

    return {
        "bundle_name": bundle_name,
        "snapshot_hash": snapshot_hash,
        "problem_count": len(problem_files),
        "asset_count": len(asset_files),
    }


def ensure_imported(conn: sqlite3.Connection, paths: Paths) -> None:
    existing = conn.execute("SELECT COUNT(*) AS c FROM problems").fetchone()
    if existing is not None and int(existing["c"]) > 0:
        return
    if not paths.source_bundle.exists():
        return
    import_bundle(conn, paths, paths.source_bundle)
