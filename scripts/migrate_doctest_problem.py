from __future__ import annotations

import argparse
import ast
import doctest
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedExample:
    source: str
    args: list[object]
    kwargs: dict[str, object]
    expected: object
    expected_display: str


def _titleize(slug: str) -> str:
    return slug.replace("_", " ").strip().title() or slug


def _placeholder_from_value(value: object) -> str:
    if isinstance(value, str):
        return '""'
    if isinstance(value, list):
        return "[]"
    if isinstance(value, dict):
        return "{}"
    if isinstance(value, tuple):
        return "()"
    if isinstance(value, bool):
        return "False"
    if isinstance(value, (int, float, complex)):
        return "0"
    if value is None:
        return "None"
    return "None"


def _render_arg(arg: ast.arg) -> str:
    rendered = arg.arg
    if arg.annotation is not None:
        rendered += f": {ast.unparse(arg.annotation)}"
    return rendered


def _render_signature(func_node: ast.FunctionDef) -> str:
    parts: list[str] = []
    posonly = list(func_node.args.posonlyargs)
    regular = list(func_node.args.args)
    defaults = list(func_node.args.defaults)
    default_offset = len(posonly) + len(regular) - len(defaults)

    all_named = posonly + regular
    for index, arg in enumerate(all_named):
        text = _render_arg(arg)
        if index >= default_offset:
            text += f" = {ast.unparse(defaults[index - default_offset])}"
        parts.append(text)
        if posonly and index == len(posonly) - 1:
            parts.append("/")

    if func_node.args.vararg is not None:
        parts.append(f"*{_render_arg(func_node.args.vararg)}")
    elif func_node.args.kwonlyargs:
        parts.append("*")

    for kwarg, default in zip(func_node.args.kwonlyargs, func_node.args.kw_defaults):
        text = _render_arg(kwarg)
        if default is not None:
            text += f" = {ast.unparse(default)}"
        parts.append(text)

    if func_node.args.kwarg is not None:
        parts.append(f"**{_render_arg(func_node.args.kwarg)}")

    signature = ", ".join(parts)
    if func_node.returns is not None:
        return f"def {func_node.name}({signature}) -> {ast.unparse(func_node.returns)}:"
    return f"def {func_node.name}({signature}):"


def _extract_function(module: ast.Module, function_name: str | None) -> ast.FunctionDef:
    functions = [node for node in module.body if isinstance(node, ast.FunctionDef)]
    if function_name:
        for func in functions:
            if func.name == function_name:
                return func
        raise ValueError(f"Function '{function_name}' not found.")
    if not functions:
        raise ValueError("No top-level function definition found.")
    return functions[0]


def _parse_literal_call(example: doctest.Example, function_name: str) -> tuple[list[object], dict[str, object]]:
    source = example.source.strip()
    try:
        expr = ast.parse(source, mode="eval").body
    except SyntaxError as exc:
        raise ValueError(f"Unsupported doctest source {source!r}: expected a direct function call.") from exc
    if not isinstance(expr, ast.Call):
        raise ValueError(f"Unsupported doctest source {source!r}: expected a direct function call.")
    if not isinstance(expr.func, ast.Name) or expr.func.id != function_name:
        raise ValueError(
            f"Unsupported doctest source {source!r}: expected call to '{function_name}'."
        )
    try:
        args = [ast.literal_eval(arg) for arg in expr.args]
        kwargs = {
            keyword.arg: ast.literal_eval(keyword.value)
            for keyword in expr.keywords
            if keyword.arg is not None
        }
    except Exception as exc:  # pragma: no cover - exact exception type is AST-shape dependent
        raise ValueError(
            f"Unsupported doctest source {source!r}: arguments must be Python literals."
        ) from exc
    if len(kwargs) != len(expr.keywords):
        raise ValueError(f"Unsupported doctest source {source!r}: starred keyword arguments are not supported.")
    return args, kwargs


def _parse_examples(docstring: str, function_name: str) -> tuple[str, list[ParsedExample]]:
    parser = doctest.DocTestParser()
    parsed = parser.parse(docstring)
    description = "".join(part for part in parsed if isinstance(part, str)).strip()
    examples = [part for part in parsed if isinstance(part, doctest.Example)]
    if not examples:
        raise ValueError("No doctest examples found in function docstring.")

    converted: list[ParsedExample] = []
    for example in examples:
        args, kwargs = _parse_literal_call(example, function_name)
        expected_display = example.want.strip()
        if not expected_display:
            raise ValueError(
                f"Doctest example {example.source.strip()!r} has no expected output. "
                "Print-based problems should be migrated manually."
            )
        try:
            expected = ast.literal_eval(expected_display)
        except Exception as exc:  # pragma: no cover - exact exception type is AST-shape dependent
            raise ValueError(
                f"Expected output for {example.source.strip()!r} is not a Python literal. "
                "Print-based or formatted-output problems should be migrated manually."
            ) from exc
        converted.append(
            ParsedExample(
                source=example.source.strip(),
                args=args,
                kwargs=kwargs,
                expected=expected,
                expected_display=expected_display,
            )
        )
    return description, converted


def _build_statement(title: str, function_name: str, description: str) -> str:
    lines = [f"# {title}", ""]
    if description:
        lines.extend([description, ""])
    else:
        lines.extend([f"Write a function `{function_name}`.", ""])
    lines.extend(
        [
            "## Function Signature",
            "",
            f"`{function_name}(...)`",
            "",
            "## Notes",
            "",
            "- `public_examples.json` is display-only.",
            "- `hidden_tests.json` is the official evaluation set.",
            "- After auto-conversion, review and add extra hidden edge cases where appropriate.",
            "",
        ]
    )
    return "\n".join(lines)


def _build_starter(func_node: ast.FunctionDef, placeholder: str) -> str:
    return (
        f"{_render_signature(func_node)}\n"
        f'    """TODO: implement."""\n'
        "    # TODO: implement\n"
        f"    return {placeholder}\n"
    )


def _format_public_input(func_node: ast.FunctionDef, args: list[object], kwargs: dict[str, object]) -> str:
    positional_names = [arg.arg for arg in func_node.args.posonlyargs + func_node.args.args]
    assignments: list[str] = []

    if len(args) > len(positional_names) and func_node.args.vararg is None:
        raise ValueError(
            f"Cannot render public example input for '{func_node.name}': too many positional arguments."
        )

    for name, value in zip(positional_names, args):
        assignments.append(f"{name} = {value!r}")

    remaining_args = args[len(positional_names):]
    if remaining_args:
        assignments.append(f"{func_node.args.vararg.arg} = {remaining_args!r}")

    for key, value in kwargs.items():
        assignments.append(f"{key} = {value!r}")

    return "\n".join(assignments)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def infer_problem_slug(
    source_path: Path,
    *,
    slug: str | None = None,
    function_name: str | None = None,
) -> str:
    source_text = source_path.read_text(encoding="utf-8")
    module = ast.parse(source_text)
    func_node = _extract_function(module, function_name)
    return (slug or func_node.name).strip()


def migrate_problem(
    source_path: Path,
    output_root: Path,
    *,
    slug: str | None,
    title: str | None,
    function_name: str | None,
    public_count: int,
    force: bool,
) -> Path:
    source_text = source_path.read_text(encoding="utf-8")
    module = ast.parse(source_text)
    func_node = _extract_function(module, function_name)
    target_slug = (slug or func_node.name).strip()
    target_title = (title or _titleize(target_slug)).strip()
    docstring = ast.get_docstring(func_node, clean=False) or ""
    description, examples = _parse_examples(docstring, func_node.name)
    if public_count < 0:
        raise ValueError("public_count must be non-negative.")

    problem_dir = output_root / target_slug
    if problem_dir.exists():
        if not force:
            raise FileExistsError(f"Target directory already exists: {problem_dir}")
    else:
        problem_dir.mkdir(parents=True, exist_ok=True)

    public_examples = [
        {
            "id": f"example-{index}",
            "input": _format_public_input(func_node, example.args, example.kwargs),
            "output": example.expected_display,
        }
        for index, example in enumerate(examples[:public_count], start=1)
    ]
    hidden_tests = {
        "version": 1,
        "cases": [
            {
                "id": f"case-{index}",
                "args": example.args,
                "kwargs": example.kwargs,
                "expected": example.expected,
            }
            for index, example in enumerate(examples, start=1)
        ],
    }

    placeholder = _placeholder_from_value(examples[0].expected)
    (problem_dir / "meta.json").write_text(
        json.dumps(
            {
                "slug": target_slug,
                "title": target_title,
                "entry_function": func_node.name,
                "evaluation_mode": "function_json",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (problem_dir / "statement.md").write_text(
        _build_statement(target_title, func_node.name, description),
        encoding="utf-8",
    )
    (problem_dir / "starter.py").write_text(
        _build_starter(func_node, placeholder),
        encoding="utf-8",
    )
    _write_json(problem_dir / "public_examples.json", public_examples)
    _write_json(problem_dir / "hidden_tests.json", hidden_tests)
    return problem_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a legacy doctest function problem into function_json problem files."
    )
    parser.add_argument("source", type=Path, help="Path to legacy doctest .py problem")
    parser.add_argument("--output-root", type=Path, default=Path("problems"))
    parser.add_argument("--slug", type=str)
    parser.add_argument("--title", type=str)
    parser.add_argument("--function", dest="function_name", type=str)
    parser.add_argument("--public-count", type=int, default=3)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    try:
        problem_dir = migrate_problem(
            args.source,
            args.output_root,
            slug=args.slug,
            title=args.title,
            function_name=args.function_name,
            public_count=args.public_count,
            force=args.force,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote function_json problem to {problem_dir}")
    print("Next step: review statement/starter text and add extra hidden edge cases if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
