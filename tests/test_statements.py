from __future__ import annotations

from pathlib import Path

from app.statements import ensure_statement, generate_statement_from_prompt


class FakeRow(dict):
    pass


def test_generate_statement_extracts_examples(tmp_path: Path):
    prompt = tmp_path / "sample_1.py"
    prompt.write_text(
        '"""Compute sum.\n\n>>> add(1, 2)\n3\n"""\n\n\ndef add(a, b):\n    return a + b\n',
        encoding="utf-8",
    )

    statement = generate_statement_from_prompt(prompt, "sample_1")
    assert "## Problem" in statement.markdown
    assert "## Examples" in statement.markdown
    assert ">>> add(1, 2)" in statement.markdown


def test_ensure_statement_writes_file(tmp_path: Path):
    class Paths:
        repo_root = tmp_path

    row = FakeRow(slug="sample_2", template_code='"""Prompt text."""\n')
    out = ensure_statement(Paths(), row)

    assert out.exists()
    assert out.parent.name == "statements"
