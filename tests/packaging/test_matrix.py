"""The sequential installation matrix must not hide failures or skip later cases."""

import subprocess
import sys

import pytest

from tests.packaging import check_matrix


@pytest.mark.parametrize("failure", [False, True])
@pytest.mark.parametrize("explicit_versions", [False, True])
def test_matrix_collects_all_results(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: bool,
    explicit_versions: bool,
) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
        assert timeout > 0
        calls.append(command)
        return subprocess.CompletedProcess(command, int(failure and len(calls) == 1))

    args = ["check_matrix", "--wheel-dir", "."]
    if explicit_versions:
        args += ["--python-versions", "3.11", "3.14"]
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setattr(subprocess, "run", run)
    assert check_matrix.main() == int(failure)
    versions = 2 if explicit_versions else 4
    assert len(calls) == versions * 2
    assert [command[-1] for command in calls] == ["base", "minimum"] * versions
    report = capsys.readouterr().out
    assert "3.14 | minimum | PASS" in report
    assert ("3.11 | base | FAIL" in report) == failure
