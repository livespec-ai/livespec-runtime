"""Regression coverage for the staged-file pre-check's pre-aggregate ordering."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SCRIPT = _ROOT / ".github/scripts/check-pre-commit.sh"

_FAKE_GIT = """#!/usr/bin/env bash
if [ "$1" = diff ]; then
    printf '%s\\n' 'livespec_runtime/example.py'
fi
"""

_FAKE_UV = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$VERDICT_LOG"
"""

_FAKE_JUST = """#!/usr/bin/env bash
printf 'just %s\\n' "$*" >> "$VERDICT_LOG"
"""


def test_staged_python_precheck_runs_before_the_pre_commit_aggregate(tmp_path: Path) -> None:
    """A Python-staged commit runs staged_precheck before `just check`."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("git", _FAKE_GIT), ("uv", _FAKE_UV), ("just", _FAKE_JUST)):
        stub = bin_dir / name
        _ = stub.write_text(body, encoding="utf-8")
        _ = stub.chmod(0o755)
    log = tmp_path / "verdict.log"

    _ = subprocess.run(
        ["bash", str(_SCRIPT)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "VERDICT_LOG": str(log),
        },
    )

    assert log.read_text(encoding="utf-8").splitlines() == [
        "run python -m livespec_dev_tooling.workflow_checks.staged_precheck",
        "just check",
    ]
