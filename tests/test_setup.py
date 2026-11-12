import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_setup_runs_uv_sync_with_lockfile(tmp_path, monkeypatch):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is required")

    repo_root = Path(__file__).resolve().parents[1]
    command_file = tmp_path / "command"
    monkeypatch.setenv("COMMAND_FILE", str(command_file))
    shell = 'uv() { printf "%s\\n" "$*" >> "$COMMAND_FILE"; }\nsource "$1"\n'
    result = subprocess.run(
        [bash, "-e", "-c", shell, "test", str(repo_root / "setup.sh")],
        cwd=tmp_path,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert command_file.read_text(encoding="utf-8").strip() == "sync --locked"
