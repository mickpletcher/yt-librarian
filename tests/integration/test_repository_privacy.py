import re
import shutil
import subprocess

import pytest


@pytest.mark.integration
def test_private_runtime_files_are_not_tracked() -> None:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git is required for the repository privacy test")
    result = subprocess.run(
        [git, "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode().split("\0")
    prohibited = re.compile(
        r"(^|/)(\.env$|browser-profile/|cookies?[^/]*\.json$|storage-state[^/]*\.json$|"
        r"transcripts?/|.*\.(sqlite|sqlite3|db)$)",
        re.IGNORECASE,
    )

    assert [path for path in paths if path and prohibited.search(path)] == []
