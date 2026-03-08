from __future__ import annotations

import ast
import doctest
import textwrap
from dataclasses import dataclass
from pathlib import Path

from .config import Paths


@dataclass(frozen=True)
class StatementData:
    title: str
    markdown: str


def _safe_slug(slug: str) -> str:
    return slug.replace("/", "__").replace(":", "__")


def statement_path(paths: Paths, slug: str) -> Path:
    return paths.repo_root / "statements" / f"{_safe_slug(slug)}.md"


def _extract_functions(module: ast.Module) -> list[str]:
    signatures: list[str] = []
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        args: list[str] = []
        positional = list(node.args.args)
        defaults = list(node.args.defaults)
        default_start = len(positional) - len(defaults)

        for idx, arg in enumerate(positional):
            token = arg.arg
            if idx >= default_start:
                token += "=..."
            args.append(token)

        if node.args.vararg is not None:
            args.append(f"*{node.args.vararg.arg}")

        if node.args.kwonlyargs:
            if node.args.vararg is None:
                args.append("*")
            for kwarg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
                token = kwarg.arg
                if default is not None:
                    token += "=..."
                args.append(token)

        if node.args.kwarg is not None:
            args.append(f"**{node.args.kwarg.arg}")

        signatures.append(f"`{node.name}({', '.join(args)})`")
    return signatures


def _split_docstring(docstring: str) -> tuple[str, list[doctest.Example]]:
    parser = doctest.DocTestParser()
    pieces = parser.parse(docstring)
    examples = [piece for piece in pieces if isinstance(piece, doctest.Example)]
    description = textwrap.dedent("".join(piece for piece in pieces if isinstance(piece, str))).strip()
    return description, examples


def _format_example(example: doctest.Example, index: int) -> str:
    lines = example.source.rstrip("\n").splitlines()
    if lines:
        source = "\n".join([f">>> {lines[0]}"] + [f"... {line}" for line in lines[1:]])
    else:
        source = ">>> "
    want = example.want.rstrip("\n") or "(no output)"
    return (
        f"### Example {index}\n"
        f"```python\n{source}\n```\n\n"
        f"Expected output:\n"
        f"```text\n{want}\n```"
    )


def generate_statement_from_template(template_code: str, slug: str) -> StatementData:
    text = template_code
    module = ast.parse(text)
    module_doc = ast.get_docstring(module, clean=False) or ""
    description, examples = _split_docstring(module_doc)
    signatures = _extract_functions(module)

    title = slug.replace("_", " ").replace(":", " ").strip().title() or slug
    parts: list[str] = [f"# {title}"]

    if description:
        parts.extend(["## Problem", description])
    else:
        parts.extend(["## Problem", "Solve the function according to the doctest examples."])

    if signatures:
        parts.extend(["## Function Signature", "\n".join(f"- {sig}" for sig in signatures)])

    if examples:
        parts.append("## Examples")
        for idx, example in enumerate(examples, start=1):
            parts.append(_format_example(example, idx))

    parts.extend(
        [
            "## Notes",
            "- Write your code in the solution file on the right.",
            "- The runner executes `python -m doctest -v` against your solution.",
        ]
    )

    return StatementData(title=title, markdown="\n\n".join(parts).strip() + "\n")


def generate_statement_from_prompt(prompt_path: Path, slug: str) -> StatementData:
    return generate_statement_from_template(
        prompt_path.read_text(encoding="utf-8"),
        slug,
    )


def ensure_statement(paths: Paths, problem_row: dict[str, object] | object) -> Path:
    slug = str(problem_row["slug"])
    path = statement_path(paths, slug)
    if path.exists():
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    statement = generate_statement_from_template(
        str(problem_row["template_code"]),
        slug,
    )
    path.write_text(statement.markdown, encoding="utf-8")
    return path
