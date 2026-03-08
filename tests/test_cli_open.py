from __future__ import annotations

from pathlib import Path

from app.cli import main


def test_open_prints_solution_path_without_editor(isolated_env, monkeypatch, capsys):
    monkeypatch.delenv("EDITOR", raising=False)
    rc = main(["open", "sample_4"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "Solution:" in captured.out
    assert "sample_4.py" in captured.out


def test_open_works_with_numeric_id(isolated_env, monkeypatch, capsys):
    monkeypatch.delenv("EDITOR", raising=False)
    main(["list"])
    rc = main(["open", "4"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "Prompt:" in captured.out
