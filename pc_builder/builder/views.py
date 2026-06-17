import json
from typing import Any

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .compatibility import (
    category_status,
    recommended_ids_for_components,
    totals,
    validate_build,
    validate_build_by_category,
)
from .forms import PlUserCreationForm
from .models import Category, Component, SavedBuild

SESSION_KEY = "pc_build_selection"

CATEGORY_ORDER = [
    "cpu",
    "motherboard",
    "ram",
    "gpu",
    "storage",
    "cooler",
    "case",
    "psu",
]

def index(request: HttpRequest):
    return render(request, "builder/index.html")

def register_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("builder:builder")
    if request.method == "POST":
        form = PlUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("builder:builder")
    else:
        form = PlUserCreationForm()
    return render(request, "registration/register.html", {"form": form})

def _serialize_component(c: Component) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "price_pln": str(c.price_pln),
        "power_watts": c.power_watts,
        "specs": c.specs or {},
        "category_slug": c.category.slug,
        "category_name": c.category.name_pl,
    }

def _empty_selection() -> dict[str, int | None]:
    return {slug: None for slug in CATEGORY_ORDER}


def get_selection(request: HttpRequest) -> dict[str, int | None]:
    raw = request.session.get(SESSION_KEY)
    base = _empty_selection()
    if isinstance(raw, dict):
        for k in CATEGORY_ORDER:
            v = raw.get(k)
            base[k] = int(v) if v not in (None, "", 0) else None
    return base

def set_selection(request: HttpRequest, data: dict[str, int | None]) -> None:
    clean = _empty_selection()
    for k in CATEGORY_ORDER:
        v = data.get(k)
        clean[k] = int(v) if v not in (None, "", 0) else None
    request.session[SESSION_KEY] = clean
    request.session.modified = True

def builder_view(request: HttpRequest):
    categories = list(Category.objects.all().order_by("sort_order", "slug"))
    selection = get_selection(request)
    price, power = totals(selection)
    by_category = validate_build_by_category(selection)
    statuses = category_status(selection, by_category)
    issues = validate_build(selection)
    icon_tiles = [
        {
            "slug": cat.slug,
            "abbr": cat.slug[:2].upper(),
            "name_pl": cat.name_pl,
            "status": statuses.get(cat.slug, "empty"),
            "issues": by_category.get(cat.slug, []),
        }
        for cat in categories
    ]
    return render(
        request,
        "builder/builder.html",
        {
            "categories": categories,
            "icon_tiles": icon_tiles,
            "selection": selection,
            "total_price": price,
            "total_power": power,
            "issues": issues,
            "has_psu_error": bool(by_category.get("psu")),
            "category_order": CATEGORY_ORDER,
        },
    )


def _build_summary_payload(request: HttpRequest) -> dict[str, Any]:
    """Dane podsumowania zestawu (bez sprawdzania metody HTTP)."""
    selection = get_selection(request)
    price, power = totals(selection)
    by_category = validate_build_by_category(selection)
    issues = validate_build(selection)
    parts: dict[str, Any] = {}
    for slug in CATEGORY_ORDER:
        pk = selection.get(slug)
        if pk:
            try:
                c = Component.objects.select_related("category").get(pk=pk)
                parts[slug] = _serialize_component(c)
            except Component.DoesNotExist:
                parts[slug] = None
        else:
            parts[slug] = None
    return {
        "selection": selection,
        "parts": parts,
        "total_price_pln": str(price),
        "total_power_w": power,
        "issues": issues,
        "category_issues": by_category,
        "category_status": category_status(selection, by_category),
    }


@require_POST
def api_set_part(request: HttpRequest):
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Niepoprawny JSON."}, status=400)
    slug = payload.get("category")
    comp_id = payload.get("component_id")
    if slug not in CATEGORY_ORDER:
        return JsonResponse({"ok": False, "error": "Nieznana kategoria."}, status=400)
    sel = get_selection(request)
    if comp_id in (None, "", 0):
        sel[slug] = None
    else:
        if not Component.objects.filter(pk=int(comp_id), category__slug=slug).exists():
            return JsonResponse({"ok": False, "error": "Komponent nie istnieje w tej kategorii."}, status=400)
        sel[slug] = int(comp_id)
    set_selection(request, sel)
    return JsonResponse(_build_summary_payload(request))

@require_POST
def api_clear_build(request: HttpRequest):
    set_selection(request, _empty_selection())
    return JsonResponse(_build_summary_payload(request))

@login_required
@require_POST
def api_save_build(request: HttpRequest):
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Niepoprawny JSON."}, status=400)
    title = (payload.get("title") or "Mój zestaw").strip()[:160]
    sel = get_selection(request)
    price, power = totals(sel)
    build = SavedBuild.objects.create(
        user=request.user,
        title=title,
        components={k: v for k, v in sel.items() if v},
        total_price_pln=price,
        total_power_w=power,
    )
    return JsonResponse({"ok": True, "id": build.id, "title": build.title})