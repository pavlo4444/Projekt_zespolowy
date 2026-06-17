from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import Component

def _by_slug(selection: dict[str, int | None]) -> dict[str, Component | None]:
    out: dict[str, Component | None] = {}
    for slug, pk in selection.items():
        if not pk:
            out[slug] = None
            continue
        try:
            out[slug] = Component.objects.select_related("category").get(pk=pk)
        except Component.DoesNotExist:
            out[slug] = None
    return out


def _spec(c: Component | None, key: str, default: Any = None) -> Any:
    if not c:
        return default
    return (c.specs or {}).get(key, default)


def _empty_category_issues(slugs: list[str] | dict) -> dict[str, list[str]]:
    keys = slugs if isinstance(slugs, list) else list(slugs.keys())
    return {slug: [] for slug in keys}


def _add_issue(by_cat: dict[str, list[str]], slugs: list[str], msg: str) -> None:
    for slug in slugs:
        if slug in by_cat and msg not in by_cat[slug]:
            by_cat[slug].append(msg)
