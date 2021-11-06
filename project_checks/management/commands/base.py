from __future__ import annotations

import difflib
import sys
from argparse import ArgumentParser
from typing import cast

from django.core.management.base import BaseCommand, CommandError


def read_lines(inputfile: str) -> list[str]:
    """Fetch the contents of the outputfile."""
    try:
        with open(inputfile, "r") as f:
            return [line.rstrip() for line in f.readlines()]
    except FileNotFoundError as ex:
        raise CommandError("Unable to read from 'inputfile' specified.") from ex


def write_lines(outputfile: str, lines: list[str]) -> None:
    """Write the contents to the outputfile."""
    with open(outputfile, "w") as f:
        for line in lines:
            f.write(line + "\n")


def diff_lines(old_lines: list[str], new_lines: list[str]) -> list[str]:
    """Return list of all different lines as returned by difflib."""
    differ = difflib.Differ()
    diff = differ.compare(old_lines, new_lines)
    return [line for line in diff if line.startswith("+ ") or line.startswith("- ")]


class DiffCheckCommand(BaseCommand):
    help = """
        Base Command for commands that generate / check for file diffs.

        This command supports a common pattern that can be used to
        manage change within a Django project. It calls a function to
        return a str that can be written to a file, which is then
        committed to the repo. During CI the command can be rerun with
        the --check-only option and it will return a non-zero exit code
        if the output has changed.

        """

    def add_arguments(self, parser: ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--inputfile",
            type=str,
            dest="inputfile",
            help="Input source filename.",
        )
        parser.add_argument(
            "--outputfile",
            type=str,
            dest="outputfile",
            help="Output destination filename.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            dest="check_changes",
            default=False,
            help="Exit with a non-zero status if a diff exists (use for CI).",
        )
        parser.add_argument(
            "--show-contents",
            action="store_true",
            dest="show_contents",
            default=False,
            help="Print out the contents generated to stdout.",
        )

    def print_diff(self, diff: list[str]) -> None:
        """Dump the diff to stderr."""
        if diff:
            self.stdout.write("--- Diff ---")
            self.stderr.writelines(diff)
        else:
            self.stdout.write("Empty diff - content is unchanged.")
        self.stdout.write("")

    def print_contents(self, contents: list[str]) -> None:
        """Dump the contents to stdout."""
        if contents:
            self.stdout.write("--- Contents ---")
            self.stdout.writelines(contents)
        else:
            self.stdout.write("No contents found.")
        self.stdout.write("")

    def print_header(self) -> None:
        self.stdout.write("")
        if self.inputfile:
            self.stdout.write(f"Reading contents from: {self.inputfile}")
        if self.inputfile:
            self.stdout.write(f"Writing contents to:   {self.inputfile}")
        self.stdout.write("")

    def handle(self, *args: object, **options: object) -> None:
        self.inputfile = cast(str, options.pop("inputfile", None))
        self.outputfile = cast(str, options.pop("outputfile", None))
        self.check_changes = options.pop("check_changes")
        self.print_header()
        new_lines = self.get_content(*args, **options)
        # if we have an outputfile, then dump the contents
        if self.outputfile:
            write_lines(self.outputfile, new_lines)
        if options["show_contents"]:
            self.print_contents(new_lines)
        # if we have an inputfile, then run a diff comparison
        if self.inputfile:
            diff = diff_lines(read_lines(self.inputfile), new_lines)
            # always print the diff
            self.print_diff(diff)
            # if we use --check then exit with a non-zero code if diff exists
            if self.check_changes and diff:
                sys.exit(1)

    def get_content(self, *args: object, **options: object) -> list[str]:
        """Override in commands to generate the content you want to check."""
        raise NotImplementedError
