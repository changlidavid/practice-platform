from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    workspace_root: Path
    db_path: Path
    bundles_dir: Path
    solutions_dir: Path
    assets_dir: Path
    runs_dir: Path
    source_bundle: Path
    hidden_tests_root: Path


def load_env_file(repo_root: Path) -> None:
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        # `.env` is the local source of truth for this app. Apply its values
        # on startup so bundle-path changes take effect after a restart.
        os.environ[key] = value


def get_paths() -> Paths:
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = Path(os.environ.get("PRACTICE_HOME", repo_root / ".practice")).resolve()
    source_bundle = Path(os.environ.get("PRACTICE_BUNDLE_PATH", repo_root / "9021")).resolve()
    hidden_tests_root = Path(
        os.environ.get("PRACTICE_HIDDEN_TESTS_ROOT", "/opt/practice-hidden-tests")
    ).resolve()
    return Paths(
        repo_root=repo_root,
        workspace_root=workspace_root,
        db_path=workspace_root / "practice.db",
        bundles_dir=workspace_root / "bundles",
        solutions_dir=workspace_root / "solutions",
        assets_dir=workspace_root / "assets",
        runs_dir=workspace_root / "runs",
        source_bundle=source_bundle,
        hidden_tests_root=hidden_tests_root,
    )


def hidden_tests_filename_for_slug(slug: str) -> str:
    safe_slug = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "__" for ch in slug.strip())
    if not safe_slug:
        raise ValueError("Problem slug is required for hidden test lookup")
    return f"{safe_slug}.json"


def hidden_tests_path_for_slug(slug: str, hidden_tests_root: Path) -> Path:
    return hidden_tests_root / hidden_tests_filename_for_slug(slug)


def ensure_workspace(paths: Paths) -> None:
    paths.workspace_root.mkdir(parents=True, exist_ok=True)
    paths.bundles_dir.mkdir(parents=True, exist_ok=True)
    paths.solutions_dir.mkdir(parents=True, exist_ok=True)
    paths.assets_dir.mkdir(parents=True, exist_ok=True)
    paths.runs_dir.mkdir(parents=True, exist_ok=True)
