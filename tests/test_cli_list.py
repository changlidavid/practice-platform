from __future__ import annotations

from app.cli import main


def test_list_bootstraps_and_shows_samples(isolated_env, capsys):
    rc = main(["list"])
    captured = capsys.readouterr()

    assert rc == 0
    assert "sample_1" in captured.out
    assert "sample_7" in captured.out
    assert "status" in captured.out
