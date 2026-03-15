from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExampleIssue:
    path: str
    example_id: str
    status: str
    reason: str


def _extract_function_from_starter(starter_path: Path) -> ast.FunctionDef:
    module = ast.parse(starter_path.read_text(encoding="utf-8"))
    functions = [node for node in module.body if isinstance(node, ast.FunctionDef)]
    if not functions:
        raise ValueError(f"No top-level function found in {starter_path}")
    return functions[0]


def _load_public_examples(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("public_examples.json must contain a list")
    return [item for item in payload if isinstance(item, dict)]


def _format_assignments_from_values(
    func_node: ast.FunctionDef,
    args: list[Any],
    kwargs: dict[str, Any],
) -> str:
    positional_names = [arg.arg for arg in func_node.args.posonlyargs + func_node.args.args]
    assignments: list[str] = []
    if len(args) > len(positional_names) and func_node.args.vararg is None:
        raise ValueError("Too many positional arguments for function signature.")

    for name, value in zip(positional_names, args):
        assignments.append(f"{name} = {value!r}")

    remaining_args = args[len(positional_names):]
    if remaining_args:
        assignments.append(f"{func_node.args.vararg.arg} = {remaining_args!r}")

    for key, value in kwargs.items():
        assignments.append(f"{key} = {value!r}")

    return "\n".join(assignments)


def _rewrite_function_call_input(raw_input: str, func_node: ast.FunctionDef) -> str | None:
    try:
        expr = ast.parse(raw_input.strip(), mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(expr, ast.Call):
        return None
    if not isinstance(expr.func, ast.Name) or expr.func.id != func_node.name:
        return None
    try:
        args = [ast.literal_eval(arg) for arg in expr.args]
        kwargs = {
            keyword.arg: ast.literal_eval(keyword.value)
            for keyword in expr.keywords
            if keyword.arg is not None
        }
    except Exception as exc:
        raise ValueError("Function-call public input uses non-literal arguments.") from exc
    if len(kwargs) != len(expr.keywords):
        raise ValueError("Starred keyword arguments are not supported.")
    return _format_assignments_from_values(func_node, args, kwargs)


def _rewrite_tuple_assignment_input(raw_input: str) -> str | None:
    try:
        module = ast.parse(raw_input, mode="exec")
    except SyntaxError:
        return _rewrite_comma_assignment_list(raw_input)
    if len(module.body) != 1 or not isinstance(module.body[0], ast.Assign):
        return None
    assign = module.body[0]
    if len(assign.targets) != 1:
        return None
    target = assign.targets[0]
    value = assign.value
    if not isinstance(target, ast.Tuple) or not isinstance(value, ast.Tuple):
        return None
    if len(target.elts) != len(value.elts):
        raise ValueError("Tuple assignment target/value length mismatch.")

    assignments: list[str] = []
    for target_elt, value_elt in zip(target.elts, value.elts):
        if not isinstance(target_elt, ast.Name):
            raise ValueError("Tuple assignment contains non-name target.")
        try:
            literal = ast.literal_eval(value_elt)
        except Exception as exc:
            raise ValueError("Tuple assignment contains non-literal value.") from exc
        assignments.append(f"{target_elt.id} = {literal!r}")
    return "\n".join(assignments)


def _rewrite_comma_assignment_list(raw_input: str) -> str | None:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False

    for char in raw_input:
        if quote is not None:
            buf.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            continue
        if char in "([{":
            depth += 1
            buf.append(char)
            continue
        if char in ")]}":
            depth = max(0, depth - 1)
            buf.append(char)
            continue
        if char == "," and depth == 0:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            continue
        buf.append(char)

    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)

    if len(parts) <= 1:
        return None
    if any("=" not in part for part in parts):
        return None
    return "\n".join(parts)


def _has_multiple_top_level_assignments(raw_input: str) -> bool:
    rewritten = _rewrite_comma_assignment_list(raw_input)
    return rewritten is not None


def normalize_example_input(raw_input: str, func_node: ast.FunctionDef) -> tuple[str, str] | None:
    normalized = raw_input.replace("\r\n", "\n").strip()
    if not normalized:
        return None

    comma_assignment_rewrite = _rewrite_comma_assignment_list(normalized)
    if comma_assignment_rewrite is not None:
        return comma_assignment_rewrite, "comma_assignment"

    call_rewrite = _rewrite_function_call_input(normalized, func_node)
    if call_rewrite is not None:
        return call_rewrite, "function_call"

    tuple_rewrite = _rewrite_tuple_assignment_input(normalized)
    if tuple_rewrite is not None:
        return tuple_rewrite, "tuple_assignment"

    return None


def normalize_public_examples_file(
    public_examples_path: Path,
    *,
    dry_run: bool,
) -> tuple[bool, list[ExampleIssue]]:
    problem_dir = public_examples_path.parent
    func_node = _extract_function_from_starter(problem_dir / "starter.py")
    examples = _load_public_examples(public_examples_path)
    changed = False
    issues: list[ExampleIssue] = []

    for example in examples:
        example_id = str(example.get("id") or "example")
        raw_input = example.get("input")
        if not isinstance(raw_input, str):
            issues.append(
                ExampleIssue(
                    path=str(public_examples_path),
                    example_id=example_id,
                    status="manual",
                    reason="Input is not a string.",
                )
            )
            continue
        try:
            normalized = normalize_example_input(raw_input, func_node)
        except Exception as exc:
            issues.append(
                ExampleIssue(
                    path=str(public_examples_path),
                    example_id=example_id,
                    status="manual",
                    reason=str(exc),
                )
            )
            continue
        if normalized is None:
            continue
        new_input, reason = normalized
        if new_input != raw_input:
            example["input"] = new_input
            changed = True
            issues.append(
                ExampleIssue(
                    path=str(public_examples_path),
                    example_id=example_id,
                    status="changed",
                    reason=reason,
                )
            )

    if changed and not dry_run:
        public_examples_path.write_text(
            json.dumps(examples, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return changed, issues


def _scan_public_example_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend(sorted(root.rglob("public_examples.json")))
    return files


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Normalize public_examples.json inputs across problems/ and structured/."
    )
    parser.add_argument("roots", nargs="*", help="Roots to scan. Defaults to problems and structured.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path, help="Optional JSON report output path.")
    args = parser.parse_args(argv)

    roots = [repo_root / "problems", repo_root / "structured"] if not args.roots else [
        (Path(raw).expanduser() if Path(raw).is_absolute() else (repo_root / raw)).resolve()
        for raw in args.roots
    ]

    all_issues: list[ExampleIssue] = []
    changed_files = 0
    rewritten_files: list[str] = []
    manual_files: set[str] = set()
    scanned = 0

    for public_examples_path in _scan_public_example_files(roots):
        scanned += 1
        changed, issues = normalize_public_examples_file(public_examples_path, dry_run=args.dry_run)
        if changed:
            changed_files += 1
            rewritten_files.append(str(public_examples_path))
        all_issues.extend(issues)
        if any(issue.status == "manual" for issue in issues):
            manual_files.add(str(public_examples_path))

    summary = {
        "roots": [str(path) for path in roots],
        "dry_run": args.dry_run,
        "scanned_files": scanned,
        "changed_files": changed_files,
        "rewritten_files": rewritten_files,
        "manual_files": len(manual_files),
        "issues": [asdict(issue) for issue in all_issues],
    }

    print(
        f"Scanned={summary['scanned_files']} changed={summary['changed_files']} manual={summary['manual_files']}"
    )
    for path in rewritten_files:
        print(f"- rewritten_file: {path}")
    for issue in all_issues:
        if issue.status == "changed":
            print(f"- changed: {issue.path} [{issue.example_id}] ({issue.reason})")
        elif issue.status == "manual":
            print(f"- manual: {issue.path} [{issue.example_id}] ({issue.reason})")

    if args.report is not None:
        report_path = args.report
        if not report_path.is_absolute():
            report_path = (repo_root / report_path).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Report written to {report_path}")

    return 1 if manual_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
