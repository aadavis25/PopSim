import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_setup_prefers_python3_over_unversioned_python(tmp_path, monkeypatch):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is required")

    repo_root = Path(__file__).resolve().parents[1]
    selection_file = tmp_path / "selected"
    monkeypatch.setenv("SELECTION_FILE", str(selection_file))
    shell = (
        "python() { printf 'python\\n' >> \"$SELECTION_FILE\"; return 77; }\n"
        "python3() { printf 'python3\\n' >> \"$SELECTION_FILE\"; return 77; }\n"
        'source "$1"\n'
    )
    result = subprocess.run(
        [bash, "-e", "-c", shell, "test", str(repo_root / "setup.sh")],
        cwd=tmp_path,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 77, f"{result.stdout}\n{result.stderr}"
    assert selection_file.read_text(encoding="utf-8").strip() == "python3"
