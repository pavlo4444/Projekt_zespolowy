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

def validate_build_by_category(selection: dict[str, int | None]) -> dict[str, list[str]]:

    parts = _by_slug(selection)
    by_cat = _empty_category_issues(selection)

    cpu = parts.get("cpu")
    mb = parts.get("motherboard")
    ram = parts.get("ram")
    storage = parts.get("storage")
    psu = parts.get("psu")
    case = parts.get("case")
    cooler = parts.get("cooler")

    if cpu and mb:
        s_cpu = _spec(cpu, "socket")
        s_mb = _spec(mb, "socket")
        if s_cpu and s_mb and str(s_cpu).upper() != str(s_mb).upper():
            msg = (
                f"Płyta główna ({mb.name}) ma socket {_fmt(s_mb)}, a procesor ({cpu.name}) — {_fmt(s_cpu)}. "
                "Te elementy nie są ze sobą zgodne."
            )
            _add_issue(by_cat, ["cpu", "motherboard"], msg)

    if ram and mb:
        rt_ram = _spec(ram, "ram_type")
        rt_mb = _spec(mb, "ram_type")
        if rt_ram and rt_mb and str(rt_ram).upper() != str(rt_mb).upper():
            msg = f"Pamięć RAM ({ram.name}) to {_fmt(rt_ram)}, a płyta ({mb.name}) wymaga {_fmt(rt_mb)}."
            _add_issue(by_cat, ["ram", "motherboard"], msg)

    if mb and case:
        ff = _spec(mb, "form_factor")
        supported = _spec(case, "supported_mb") or []
        if isinstance(supported, str):
            supported = [x.strip() for x in supported.split(",") if x.strip()]
        if ff and supported and str(ff) not in supported:
            msg = (
                f"Format płyty ({ff}) nie mieści się w obudowie ({case.name}). "
                f"Obsługiwane formaty: {', '.join(map(str, supported))}."
            )
            _add_issue(by_cat, ["motherboard", "case"], msg)

    if cooler and cpu:
        sock = _spec(cpu, "socket")
        sockets = _spec(cooler, "sockets") or []
        if isinstance(sockets, str):
            sockets = [x.strip() for x in sockets.split(",") if x.strip()]
        universal = bool(_spec(cooler, "universal"))
        if sock and sockets and not universal:
            if str(sock) not in sockets:
                msg = (
                    f"Chłodzenie ({cooler.name}) nie obsługuje socketu procesora ({sock}). "
                    f"Obsługiwane: {', '.join(map(str, sockets))}."
                )
                _add_issue(by_cat, ["cooler", "cpu"], msg)

    if storage and mb:
        m2_slots = int(_spec(mb, "m2_slots") or 0)
        needs_m2 = str(_spec(storage, "interface") or "").upper() == "NVME"
        if needs_m2 and m2_slots == 0:
            msg = (
                f"Dysk NVMe ({storage.name}) wymaga slotu M.2 na płycie, a wybrana płyta ({mb.name}) "
                "nie deklaruje dostępnego M.2 w zestawie (sprawdź specyfikację)."
            )
            _add_issue(by_cat, ["storage", "motherboard"], msg)

    if psu:
        psu_w = int(_spec(psu, "wattage") or psu.power_watts or 0)
        load = 0
        for key, part in parts.items():
            if not part or key == "psu":
                continue
            if key == "motherboard":
                load += int(_spec(part, "extra_w") or 15)
            else:
                load += int(part.power_watts or 0)
        margin = int(load * 0.2) if load else 0
        recommended = load + margin
        if psu_w and recommended > psu_w:
            msg = (
                f"Szacowany pobór zestawu (~{load} W + zapas) przekracza moc zasilacza ({psu_w} W). "
                "Wybierz mocniejszy zasilacz."
            )
            _add_issue(by_cat, ["psu"], msg)

    return by_cat