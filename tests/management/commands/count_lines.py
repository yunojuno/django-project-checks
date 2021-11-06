from __future__ import annotations

from argparse import ArgumentParser
from typing import cast

from project_checks.management.commands import DiffCheckCommand


class Command(DiffCheckCommand):
    def add_arguments(self, parser: ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--lines",
            type=int,
            dest="lines",
            default=3,
            help="Number of lines to output",
        )

    def get_content(self, *args: object, **options: object) -> list[str]:
        lines = cast(int, options["lines"])
        return [f"line {i}" for i in range(1, lines + 1)]
