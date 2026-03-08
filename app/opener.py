from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Tuple


def prompt_preview(prompt_path: Path, max_lines: int = 12) -> str:
    lines: list[str] = []
    with prompt_path.open("r", encoding="utf-8") as f:
        for _ in range(max_lines):
            line = f.readline()
            if not line:
                break
            lines.append(line.rstrip("\n"))
    return "\n".join(lines)


def prompt_preview_text(content: str, max_lines: int = 12) -> str:
    lines = content.splitlines()
    return "\n".join(lines[:max_lines])


def open_in_editor(solution_path: Path) -> bool:
    return launch_editor(solution_path)


def launch_editor(solution_path: Path, *, check: bool = False) -> bool:
    editor = os.environ.get("EDITOR")
    if not editor:
        return False
    base_cmd = shlex.split(editor)
    if not base_cmd:
        return False
    cmd = base_cmd + [str(solution_path)]
    subprocess.run(cmd, check=check)
    return True


def open_problem(solution_path: Path, prompt_path: Path) -> Tuple[bool, str]:
    opened = open_in_editor(solution_path)
    preview = prompt_preview(prompt_path)
    return opened, preview
