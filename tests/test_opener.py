from __future__ import annotations

import subprocess
from pathlib import Path

from app import opener


def test_launch_editor_returns_false_when_editor_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("EDITOR", raising=False)
    solution = tmp_path / "solution.py"
    solution.write_text("x=1\n", encoding="utf-8")

    assert opener.launch_editor(solution) is False


def test_launch_editor_runs_editor_command(monkeypatch, tmp_path):
    monkeypatch.setenv("EDITOR", "vim -u NONE")
    solution = tmp_path / "solution.py"
    solution.write_text("x=1\n", encoding="utf-8")

    recorded = {"cmd": None}

    def fake_run(cmd, check):
        recorded["cmd"] = cmd
        assert check is False
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("app.opener.subprocess.run", fake_run)

    assert opener.launch_editor(solution) is True
    assert recorded["cmd"] is not None
    assert recorded["cmd"][-1] == str(solution)
    assert recorded["cmd"][:2] == ["vim", "-u"]


def test_launch_editor_supports_editor_with_spaces(monkeypatch, tmp_path):
    monkeypatch.setenv("EDITOR", "code --wait")
    solution = tmp_path / "solution.py"
    solution.write_text("x=1\n", encoding="utf-8")

    recorded = {"cmd": None}

    def fake_run(cmd, check):
        recorded["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("app.opener.subprocess.run", fake_run)

    assert opener.launch_editor(solution) is True
    assert recorded["cmd"][:2] == ["code", "--wait"]
    assert recorded["cmd"][-1] == str(solution)


def test_launch_editor_propagates_file_not_found(monkeypatch, tmp_path):
    monkeypatch.setenv("EDITOR", "code --wait")
    solution = tmp_path / "solution.py"
    solution.write_text("x=1\n", encoding="utf-8")

    def fake_run(cmd, check):
        raise FileNotFoundError(2, "No such file or directory", cmd[0])

    monkeypatch.setattr("app.opener.subprocess.run", fake_run)

    try:
        opener.launch_editor(solution, check=True)
    except FileNotFoundError as exc:
        assert exc.filename == "code"
    else:
        raise AssertionError("FileNotFoundError was expected")
