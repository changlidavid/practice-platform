from __future__ import annotations

from pathlib import Path


HARNESS_NAME = "test_harness.py"


def write_harness(run_dir: Path, solution_filename: str = "solution.py") -> Path:
    harness_path = run_dir / HARNESS_NAME
    harness_path.write_text(
        """
import doctest
import importlib.util
from pathlib import Path


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("user_solution", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_doctests_pass():
    module = _load_module(Path(__file__).parent / """ + repr(solution_filename) + """)
    failures, _ = doctest.testmod(module, verbose=False)
    assert failures == 0
""".lstrip(),
        encoding="utf-8",
    )
    return harness_path
