from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


_UGLY_TITLE_RE = re.compile(r"(1754923206907|^\s*final\b|^\s*9021\b|\bitem\b|\bsample\b)", re.IGNORECASE)
_GENERIC_ENTRY_FUNCTIONS = {"f", "g", "h", "main", "solve", "solution"}
_MANUAL_TITLE_OVERRIDES = {
    "f_24t3": "Remove Even Digits",
    "f_dfs_a": "Increasing Subsequences",
    "upp": "Increasing Subsequences From First Element",
}


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON object in {path}")
    return payload


def _titleize(value: str) -> str:
    cleaned = re.sub(r"[_\-]+", " ", value.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return ""
    return cleaned.title()


def _is_ugly_title(title: str) -> bool:
    return bool(_UGLY_TITLE_RE.search(title.strip()))


def _first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def _replace_first_heading(markdown: str, new_heading: str) -> str:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            prefix = line[: len(line) - len(line.lstrip())]
            lines[index] = f"{prefix}# {new_heading}"
            return "\n".join(lines).rstrip() + "\n"
    return f"# {new_heading}\n\n{markdown.lstrip()}"


def _first_meaningful_sentence(markdown: str) -> str:
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("##") or line.startswith("- "):
            continue
        if line.lower().startswith("write a function"):
            continue
        sentence = line.split(".", 1)[0].strip()
        if len(sentence) < 8:
            continue
        return sentence
    return ""


def _sentence_to_title(sentence: str) -> str:
    normalized = re.sub(r"`([^`]*)`", r"\1", sentence)
    normalized = re.sub(r"^[A-Z][a-z]+\s+", "", normalized)
    normalized = re.sub(r"\b(a|an|the)\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-zA-Z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return ""
    words = normalized.split()
    return " ".join(words[:6]).title()


def _preferred_base_name(problem_dir: Path, meta: dict[str, object]) -> str:
    slug = str(meta.get("slug", "")).strip() or problem_dir.name
    entry_function = str(meta.get("entry_function", "")).strip()
    for key in (problem_dir.name, slug, entry_function):
        override = _MANUAL_TITLE_OVERRIDES.get(key)
        if override:
            return override

    if entry_function and entry_function not in _GENERIC_ENTRY_FUNCTIONS:
        return _titleize(entry_function)

    statement_md = (problem_dir / "statement.md").read_text(encoding="utf-8")
    sentence = _first_meaningful_sentence(statement_md)
    candidate = _sentence_to_title(sentence)
    if candidate:
        return candidate

    if slug and slug not in _GENERIC_ENTRY_FUNCTIONS:
        base_slug = re.sub(r"_(sample|final)?_?\d.*$", "", slug)
        return _titleize(base_slug or slug)

    return _titleize(problem_dir.name)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _proposed_suffix(problem_dir: Path, base_slug: str) -> str:
    suffix = problem_dir.name
    if suffix.startswith(base_slug):
        suffix = suffix[len(base_slug) :].lstrip("_")
    if not suffix:
        return ""
    if re.fullmatch(r"\d+", suffix):
        return f"final{suffix}"
    if suffix.startswith("sample_"):
        return suffix
    if re.fullmatch(r"\d+_sample_\d+", suffix):
        leading, sample_word, sample_num = suffix.split("_", 2)
        return f"final{leading}_{sample_word}_{sample_num}"
    exam_tokens = re.findall(r"\d{2}t\d+", suffix, flags=re.IGNORECASE)
    if exam_tokens:
        return "_".join(token.lower() for token in exam_tokens)
    return suffix.lower()


def cleanup_structured_metadata(structured_root: Path, *, apply: bool) -> dict[str, object]:
    updated_titles: list[dict[str, object]] = []
    exact_duplicate_groups: list[dict[str, object]] = []
    collision_groups: list[dict[str, object]] = []

    problem_dirs = sorted(path for path in structured_root.iterdir() if (path / "meta.json").exists())
    entries: list[dict[str, object]] = []

    for problem_dir in problem_dirs:
        meta_path = problem_dir / "meta.json"
        statement_path = problem_dir / "statement.md"
        meta = _load_json(meta_path)
        old_title = str(meta.get("title", "")).strip()
        statement_md = statement_path.read_text(encoding="utf-8")
        old_heading = _first_heading(statement_md)
        new_title = _preferred_base_name(problem_dir, meta)

        if new_title and new_title != old_title and _is_ugly_title(old_title):
            meta["title"] = new_title
            new_statement_md = statement_md
            if not old_heading or _is_ugly_title(old_heading):
                new_statement_md = _replace_first_heading(statement_md, new_title)
            if apply:
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                if new_statement_md != statement_md:
                    statement_path.write_text(new_statement_md, encoding="utf-8")
            updated_titles.append(
                {
                    "dir": problem_dir.name,
                    "slug": str(meta.get("slug", "")).strip(),
                    "old_title": old_title,
                    "new_title": new_title,
                    "old_heading": old_heading,
                    "new_heading": new_title if (not old_heading or _is_ugly_title(old_heading)) else old_heading,
                }
            )

        entries.append(
            {
                "dir": problem_dir.name,
                "slug": str(meta.get("slug", "")).strip(),
                "entry_function": str(meta.get("entry_function", "")).strip(),
                "title": str(meta.get("title", "")).strip() if not apply else new_title or str(meta.get("title", "")).strip(),
                "base_title": new_title or old_title,
                "starter_hash": _sha256(problem_dir / "starter.py"),
                "public_hash": _sha256(problem_dir / "public_examples.json"),
                "hidden_hash": _sha256(problem_dir / "hidden_tests.json") if (problem_dir / "hidden_tests.json").exists() else "",
                "statement_hash": _sha256(problem_dir / "statement.md"),
            }
        )

    groups_by_entry: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        groups_by_entry.setdefault(str(entry["entry_function"]), []).append(entry)

    for entry_function, group in sorted(groups_by_entry.items()):
        if len(group) < 2:
            continue

        exact_key_map: dict[tuple[str, str, str, str], list[dict[str, object]]] = {}
        for item in group:
            key = (
                str(item["entry_function"]),
                str(item["starter_hash"]),
                str(item["public_hash"]),
                str(item["hidden_hash"]),
            )
            exact_key_map.setdefault(key, []).append(item)

        for duplicates in exact_key_map.values():
            if len(duplicates) < 2:
                continue
            representative = min(
                duplicates,
                key=lambda item: (
                    0 if str(item["slug"]) == str(item["entry_function"]) else 1,
                    len(str(item["dir"])),
                    str(item["dir"]),
                ),
            )
            exact_duplicate_groups.append(
                {
                    "entry_function": entry_function,
                    "representative": representative["dir"],
                    "members": [
                        {
                            "dir": item["dir"],
                            "slug": item["slug"],
                            "title": item["title"],
                        }
                        for item in duplicates
                    ],
                    "recommendation": (
                        f"These entries share identical starter/public/hidden assets. "
                        f"Keep '{representative['dir']}' as the representative copy, or rename the others only if "
                        f"you intentionally need multiple labeled variants."
                    ),
                }
            )

        if len(group) >= 2:
            base_slug = str(group[0]["entry_function"]).strip() or str(group[0]["slug"]).strip()
            collision_groups.append(
                {
                    "entry_function": entry_function,
                    "clean_title": str(group[0]["base_title"]),
                    "members": [
                        {
                            "dir": item["dir"],
                            "slug": item["slug"],
                            "title": item["title"],
                            "proposed_suffix": _proposed_suffix(Path(str(item["dir"])), base_slug),
                            "proposed_slug": (
                                f"{base_slug}_{_proposed_suffix(Path(str(item['dir'])), base_slug)}"
                                if _proposed_suffix(Path(str(item["dir"])), base_slug)
                                else base_slug
                            ),
                        }
                        for item in group
                    ],
                    "recommendation": (
                        "Do not rename automatically. If these are true duplicates, keep one representative copy. "
                        "If you need multiple variants, use a readable suffix such as sample_3, final2_sample_3, or 22t1."
                    ),
                }
            )

    return {
        "structured_root": str(structured_root),
        "applied": apply,
        "updated_titles": updated_titles,
        "likely_duplicate_groups": exact_duplicate_groups,
        "collision_groups": collision_groups,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean structured metadata titles and report collisions.")
    parser.add_argument("--root", type=Path, default=Path("structured"))
    parser.add_argument("--apply", action="store_true", help="Write updated titles/headings back to disk.")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("structured/metadata-cleanup-report.json"),
        help="JSON report path.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    root = args.root if args.root.is_absolute() else (repo_root / args.root).resolve()
    report_path = args.report if args.report.is_absolute() else (repo_root / args.report).resolve()

    report = cleanup_structured_metadata(root, apply=args.apply)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"Updated {len(report['updated_titles'])} structured titles; "
        f"found {len(report['likely_duplicate_groups'])} likely duplicate groups and "
        f"{len(report['collision_groups'])} collision groups."
    )
    print(f"Report written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
