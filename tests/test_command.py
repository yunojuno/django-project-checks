from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command


@pytest.fixture
def stdout() -> StringIO:
    return StringIO()


@pytest.fixture
def stderr() -> StringIO:
    return StringIO()


@pytest.fixture
def filename() -> str:
    return "temp.txt"


class TestDiffCheckCommand:
    def test_no_options(self, stdout: StringIO) -> None:
        call_command("count_lines", lines=3, stdout=stdout)
        assert stdout.getvalue().strip() == ""

    def test_show_contents(self, stdout: StringIO) -> None:
        # print contents out to stdout - no diff
        call_command("count_lines", lines=3, show_contents=True, stdout=stdout)
        assert "line 1\nline 2\nline 3" in stdout.getvalue()

    def test_outputfile(self, filename: str) -> None:
        # print contents out to stdout - no diff
        call_command("count_lines", lines=3, outputfile=filename)
        with open("foo.txt", "r") as f:
            assert f.readlines() == ["line 1\n", "line 2\n", "line 3\n"]

    def test_inputfile__no_diff(self, filename: str, stdout: StringIO) -> None:
        call_command("count_lines", lines=3, outputfile=filename)
        call_command("count_lines", lines=3, inputfile=filename, stdout=stdout)
        assert "Empty diff - content is unchanged." in stdout.getvalue()

    def test_inputfile__diff(self, filename: str, stderr: StringIO) -> None:
        call_command("count_lines", lines=3, outputfile=filename)
        call_command("count_lines", lines=4, inputfile=filename, stderr=stderr)
        assert "+ line 4" in stderr.getvalue()

    def test_exit_code(self, filename: str, stdout: StringIO) -> None:
        call_command("count_lines", lines=3, outputfile=filename)
        with pytest.raises(SystemExit):
            call_command("count_lines", lines=4, inputfile=filename, exit_code=True)
