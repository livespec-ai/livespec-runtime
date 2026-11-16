"""The bare ``pytest --cov=<pkg>`` spelling combines its coverage data.

The repository enables branch coverage in ``pyproject.toml``.  pytest-cov
only gives subprocesses that configuration by path when ``--cov-config`` names
it, so a child whose current directory has no pyproject can otherwise produce
statement-only data.  Its parent then cannot combine that data with its own
branch data.

This builds a small project from the repository's real pytest configuration
and runs the bare spelling, covering the configuration contract without
depending on this repository's full suite.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE = "def f(x):\n    if x:\n        return 1\n    return 2\n"
_SUITE = """\
import subprocess
import sys


def test_subprocess_without_a_pyproject_in_view(tmp_path):
    code = "import pkg; pkg.f(1)"
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, check=True)


def test_main_process_measures_the_same_package():
    import pkg

    assert pkg.f(0) == 2
"""


def _pytest_section() -> str:
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"^\[tool\.pytest\.ini_options\]\n.*?(?=^\[)", text, re.DOTALL | re.MULTILINE)
    assert match is not None
    return match.group(0)


def test_bare_cov_spelling_combines_branch_and_subprocess_data(
    *, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A full run with the bare spelling ends green and prints a coverage report."""
    project = tmp_path / "project"
    (project / "pkg").mkdir(parents=True)
    (project / "tests").mkdir()
    _ = (project / "pkg" / "__init__.py").write_text(_PACKAGE, encoding="utf-8")
    _ = (project / "tests" / "test_demo.py").write_text(_SUITE, encoding="utf-8")
    _ = (project / "pyproject.toml").write_text(
        f"[tool.coverage.run]\nbranch = true\n\n{_pytest_section()}", encoding="utf-8"
    )
    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    monkeypatch.syspath_prepend(str(project))
    returncode = pytest.main(["-p", "no:cacheprovider", "--cov=pkg"])
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Can't combine" not in output, output
    assert returncode == 0, output
    assert "TOTAL" in output, output
