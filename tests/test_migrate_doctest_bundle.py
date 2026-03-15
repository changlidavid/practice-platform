from __future__ import annotations

import json
import shutil
import subprocess
import sys


def test_migrate_doctest_bundle_continues_on_errors_and_writes_report(repo_root, tmp_path):
    source_bundle = tmp_path / "legacy_bundle"
    source_bundle.mkdir()
    shutil.copy(repo_root / "9021" / "sample_1.py", source_bundle / "sample_1.py")
    shutil.copy(repo_root / "9021" / "sample_2.py", source_bundle / "sample_2.py")

    output_root = tmp_path / "structured"
    report_path = tmp_path / "migration-report.json"
    script = repo_root / "scripts" / "migrate_doctest_bundle.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source_bundle),
            "--output-root",
            str(output_root),
            "--report",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    migrated_dir = output_root / "legacy_bundle__sample_1"
    assert migrated_dir.exists()
    assert not (output_root / "legacy_bundle__sample_2").exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["counts"]["migrated"] == 1
    assert report["counts"]["failed"] == 1
    statuses = {entry["slug"]: entry["status"] for entry in report["results"]}
    assert statuses["legacy_bundle__sample_1"] == "migrated"
    assert statuses["legacy_bundle__sample_2"] == "failed"


def test_migrate_doctest_bundle_dry_run_and_skip_existing(repo_root, tmp_path):
    source_bundle = tmp_path / "legacy_bundle"
    source_bundle.mkdir()
    shutil.copy(repo_root / "9021" / "sample_1.py", source_bundle / "sample_1.py")

    output_root = tmp_path / "structured"
    script = repo_root / "scripts" / "migrate_doctest_bundle.py"

    dry_run = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source_bundle),
            "--output-root",
            str(output_root),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert dry_run.returncode == 0
    assert "would_migrate=1" in dry_run.stdout
    assert "legacy_bundle__sample_1" in dry_run.stdout
    assert not (output_root / "legacy_bundle__sample_1").exists()

    first_run = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source_bundle),
            "--output-root",
            str(output_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert first_run.returncode == 0
    assert (output_root / "legacy_bundle__sample_1").exists()

    second_run = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source_bundle),
            "--output-root",
            str(output_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert second_run.returncode == 0
    assert "skipped=1" in second_run.stdout
