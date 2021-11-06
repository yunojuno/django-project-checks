# Copied from django-extensions
from __future__ import annotations

import functools
import re
from argparse import ArgumentParser
from typing import Any, Callable, cast

from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.exceptions import ViewDoesNotExist
from django.core.management.base import CommandError
from django.template.loader import render_to_string
from django.urls import URLPattern, URLResolver

from project_checks.management.commands import DiffCheckCommand


class RegexURLPattern:
    pass


class RegexURLResolver:
    pass


class LocaleRegexURLResolver:
    pass


def describe_pattern(p: Any) -> str:
    return str(p.pattern)


class Command(DiffCheckCommand):
    help = "Displays all of the url matching routes for the project."

    def add_arguments(self, parser: ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--urlconf",
            "-c",
            dest="urlconf",
            default="ROOT_URLCONF",
            help="Set the settings URL conf variable to use",
        )

    def get_url_conf(self, urlconf: str) -> Any:
        if not hasattr(settings, urlconf):
            raise CommandError(
                f"Settings module {settings} does not have the attribute {urlconf}."
            )

        try:
            return __import__(getattr(settings, urlconf), {}, {}, [""])
        except Exception as e:  # noqa: B902
            raise CommandError(
                f"Error occurred while trying to load {getattr(settings, urlconf)}: {e}"
            )

    def get_func_name(self, func: Callable) -> str:
        if hasattr(func, "__name__"):
            return f"{func.__module__}.{func.__name__}"
        elif hasattr(func, "__class__"):
            return f"{func.__module__}.{func.__class__.__name__}"
        else:
            return re.sub(r" at 0x[0-9a-f]+", "", repr(func))

    def add_url(self, func_name: str, url: str, url_name: str) -> bool:
        """Return True if we want to log this url."""
        if url.startswith("/_admin"):
            return False
        if url.startswith("/test"):
            return False
        if url.startswith("/storybook"):
            return False
        if func_name.startswith("yunojuno"):
            return True
        if func_name.startswith("django.views.generic"):
            return True
        return False

    def write_to_file(self, filename: str, views: list) -> None:
        with open(filename, "w") as f:
            f.write("\n".join(views).lstrip("\n"))

    def get_content(self, *args: object, **options: object) -> list[str]:
        views = []
        url_conf = self.get_url_conf(cast(str, options["urlconf"]))
        view_functions = self.extract_views_from_urlpatterns(url_conf.urlpatterns)
        for (func, regex, url_name) in view_functions:
            if isinstance(func, functools.partial):
                func = func.func
            func_name = self.get_func_name(func)
            url = simplify_regex(regex)
            # we are only interested in YJ urls.
            if not self.add_url(func_name, url, url_name):
                continue
            self.stdout.write(url)
            txt = render_to_string(
                "project_checks/django_url.txt",
                {
                    "url": url,
                    "url_name": url_name or "",
                    "module": func_name,
                },
            )
            views.append(txt)
        self.stdout.write("---")
        self.stdout.write(f"Collected {len(views)} urls")
        return views

    def extract_views_from_urlpatterns(  # noqa: C901
        self,
        urlpatterns: list,
        base: str = "",
        namespace: str | None = None,
    ) -> list:
        """
        Return a list of views from a list of urlpatterns.

        Each object in the returned list is a three-tuple: (view_func, regex, name)
        """
        views = []
        for p in urlpatterns:
            if isinstance(p, (URLPattern, RegexURLPattern)):
                try:
                    if not p.name:
                        name = p.name
                    elif namespace:
                        name = "{}:{}".format(namespace, p.name)
                    else:
                        name = p.name
                    pattern = describe_pattern(p)
                    views.append((p.callback, base + pattern, name))
                except ViewDoesNotExist:
                    continue
            elif isinstance(p, (URLResolver, RegexURLResolver)):  # type: ignore
                try:
                    patterns = p.url_patterns
                except ImportError:
                    continue
                if namespace and p.namespace:
                    _namespace = "{}:{}".format(namespace, p.namespace)
                else:
                    _namespace = p.namespace or namespace
                pattern = describe_pattern(p)
                views.extend(
                    self.extract_views_from_urlpatterns(
                        patterns, base + pattern, namespace=_namespace
                    )
                )
            elif hasattr(p, "_get_callback"):
                try:
                    views.append(
                        (p._get_callback(), base + describe_pattern(p), p.name)
                    )
                except ViewDoesNotExist:
                    continue
            elif hasattr(p, "url_patterns") or hasattr(p, "_get_url_patterns"):
                try:
                    patterns = p.url_patterns
                except ImportError:
                    continue
                views.extend(
                    self.extract_views_from_urlpatterns(
                        patterns, base + describe_pattern(p), namespace=namespace
                    )
                )
            else:
                raise TypeError("%s does not appear to be a urlpattern object" % p)
        return sorted(views, key=lambda t: t[1])
