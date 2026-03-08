from __future__ import annotations

from pathlib import Path

from app.cli import main


def test_import_command_registers_bundle_and_problems(isolated_env, tmp_path, capsys):
    bundle = tmp_path / "my_bundle"
    bundle.mkdir()

    (bundle / "prob_a.py").write_text(
        """
def f(x):
    '''
    >>> f(1)
    2
    '''
    return x + 1
""".lstrip(),
        encoding="utf-8",
    )
    (bundle / "data.txt").write_text("hello\n", encoding="utf-8")

    rc = main(["import", str(bundle)])
    captured = capsys.readouterr()

    assert rc == 0
    assert "Imported bundle" in captured.out
    assert "Problems: 1" in captured.out
    assert "Assets:" in captured.out

    rc = main(["list"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "my_bundle" in captured.out
    assert "my_bundle:prob_a" in captured.out


def test_open_and_run_on_imported_problem(isolated_env, tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("EDITOR", raising=False)

    bundle = tmp_path / "my_bundle"
    bundle.mkdir()
    (bundle / "prob_a.py").write_text(
        """
def f(x):
    '''
    >>> f(1)
    2
    >>> f(3)
    4
    '''
    return x + 1
""".lstrip(),
        encoding="utf-8",
    )

    assert main(["import", str(bundle)]) == 0

    rc_open = main(["open", "my_bundle:prob_a"])
    open_out = capsys.readouterr().out
    assert rc_open == 0
    assert "Solution:" in open_out

    rc_run = main(["run", "my_bundle:prob_a"])
    run_out = capsys.readouterr().out
    assert rc_run == 0
    assert "Status:  pass" in run_out
    assert "Passed:" in run_out
