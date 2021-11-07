# Django Project Check

Django management command for monitoring file diffs.

## Background

With a large codebase, and a high velocity team making edits, it can be
difficult to keep track of how the codebase is changing over time. A
classic issue is people creating new modules / classes in unexpected
places, or ending up with a set of functions that should be in the same
place but are spread across multiple locations (often resulting in
`import` issues). In order to address this we build a small script to
parse the codebase and dump out a complete listing of all modules,
classes and functions. We commit this to the repo, and then run a CI
check to ensure that it's up to date. The net result is that each PR has
at least one file update which lists which functions have been edited,
and where. It's like a live update to the index.

This pattern - dump a text output and add a CI check to enforce its correctness - turns out to be a really useful pattern for keeping control of the codebase, and so we started adding new checks:

- Python functions
- Django URLs
- GraphQL schema
- FSM interactions

The original function check is a python script (using `ast`) and has no requirement for the Django scaffolding, but the others do, and so they run as management commands, which are then wrapped with a `git diff` script:

```yaml
- name: Run freeze_django_urls and check for any uncommitted diff
  run: |
    python manage.py freeze_django_urls
    git diff --exit-code 'django_urls.txt'
```

This project wraps this pattern into a base management command that can be subclassed for any such requirement. All you need to do is provide a function that returns the contents to be written to the file.
