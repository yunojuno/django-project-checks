from __future__ import annotations

import difflib
from argparse import ArgumentParser

from black import sys
from django.core.management.base import BaseCommand
from git import CommandError

# mypy hint for a text file
Lines = list[str]


def read_lines(inputfile: str) -> Lines | None:
    """Fetch the contents of the outputfile."""
    try:
        with open(inputfile, "r") as f:
            return [line.rstrip() for line in f.readlines()]
    except FileNotFoundError as ex:
        raise CommandError("Unable to read from 'inputfile' specified.") from ex


def write_lines(outputfile: str, lines: Lines) -> None:
    """Write the contents to the outputfile."""
    with open(outputfile, "w") as f:
        for line in lines:
            f.write(line + "\n")


def diff_lines(old_lines: str, new_lines: str) -> Lines:
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
            "--exit-code",
            action="store_true",
            dest="exit_code",
            default=False,
            help="Return non-zero exit code if a diff exists.",
        )

    def print_diff(self, diff: Lines) -> None:
        """Dump the diff to stderr."""
        if diff:
            self.stderr.writelines(diff)
        else:
            self.stdout.write("Empty diff - content is unchanged.")

    def handle(self, *args: object, **options: object) -> None:
        inputfile = options.pop("inputfile", None)
        outputfile = options.pop("outputfile", None)
        exit_code = options.pop("exit_code")
        new_lines = self.do_command(**options)
        self.stdout.writelines(new_lines)
        diff: Lines = []
        # if we have an inputfile, then run a diff comparison
        if inputfile:
            old_lines = read_lines(inputfile)
            diff = diff_lines(old_lines, new_lines)
            self.print_diff(diff)
        # if we have an outputfile, then dump the contents
        if outputfile:
            write_lines(outputfile, new_lines)
        # if we use --check then exit with a non-zero code if diff exists
        if exit_code:
            sys.exit(len(diff))

    def do_command(self, *args: object, **options: object) -> Lines:
        """Override in commands to generate the content you want to check."""
        raise NotImplementedError
