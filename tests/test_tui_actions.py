from __future__ import annotations

from app import db
from app.config import get_paths
from app import tui_actions


def test_prepare_problem_view_does_not_launch_editor(isolated_env):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = db.get_problem(conn, "sample_1")
        assert row is not None
    finally:
        conn.close()

    preview, solution_path, prompt_path = tui_actions.prepare_problem_view(row)

    assert "def remove_consecutive_duplicates" in preview
    assert solution_path.exists()
    assert str(prompt_path).endswith("_virtual_prompt.py")


def test_launch_editor_for_solution_uses_opener(monkeypatch, tmp_path):
    solution = tmp_path / "solution.py"
    solution.write_text("print('x')\n", encoding="utf-8")

    called = {"value": False}

    def fake_launch_editor(path: Path, *, check: bool = False) -> bool:
        called["value"] = True
        assert path == solution
        assert check is True
        return True

    monkeypatch.setattr("app.tui_actions.opener.launch_editor", fake_launch_editor)

    assert tui_actions.launch_editor_for_solution(solution) is True
    assert called["value"] is True
