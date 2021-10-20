from project_checks.management.base import DiffCheckCommand, Lines


class Command(DiffCheckCommand):
    def do_command(self, *args: object, **options: object) -> Lines:
        return [
            "line 1",
            "line 2",
            "line 3",
        ]
