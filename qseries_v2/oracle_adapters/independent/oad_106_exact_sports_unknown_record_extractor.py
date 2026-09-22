from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
from pathlib import Path
from typing import Any

READ_ONLY = True
EXECUTION_AUTHORITY = False
PROBABILITY_ENABLED = False

M106 = "qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate"

def _safe(v: Any, depth: int = 0):
    if depth > 7:
        return "<max-depth>"
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if dataclasses.is_dataclass(v):
        return {f.name: _safe(getattr(v, f.name), depth + 1) for f in dataclasses.fields(v)}
    if isinstance(v, dict):
        return {str(k): _safe(val, depth + 1) for k, val in list(v.items())[:500]}
    if isinstance(v, (list, tuple, set)):
        return [_safe(x, depth + 1) for x in list(v)[:500]]
    if hasattr(v, "__dict__"):
        return {k: _safe(val, depth + 1) for k, val in vars(v).items() if not k.startswith("__")}
    return str(v)

def _attr(obj, *names):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value not in (None, ""):
                return value
        if isinstance(obj, dict) and name in obj and obj[name] not in (None, ""):
            return obj[name]
    return None

def _text(obj):
    try:
        return json.dumps(_safe(obj), sort_keys=True, default=str)
    except Exception:
        return str(obj)

def _load_contract():
    m106 = importlib.import_module(M106)
    required = [
        "capture_current_market_cohort",
        "snapshot_markets",
        "decompose_mixed_market",
        "build_identity_envelopes",
        "resolve_guarded_identity",
    ]
    missing = [name for name in required if not callable(getattr(m106, name, None))]
    if missing:
        raise RuntimeError("OAD-106 exact production dependencies not exposed: " + ", ".join(missing))
    return m106

def _resolve_semantic_callable():
    candidates = (
        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation", "resolve_semantic_identity"),
        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation", "disambiguate_semantic_identity"),
        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation", "resolve_semantic_domain"),
    )
    for mod_name, name in candidates:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn, f"{mod_name}.{name}"
        except Exception:
            pass
    return None, None

def _resolve_router_callable():
    candidates = (
        ("qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router", "route_authoritative_source_requirement"),
        ("qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router", "route_source_requirement"),
        ("qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router", "source_requirement_for"),
    )
    for mod_name, name in candidates:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn, f"{mod_name}.{name}"
        except Exception:
            pass
    return None, None

def _call_flex(fn, *args, **preferred):
    sig = inspect.signature(fn)
    params = sig.parameters
    call_kwargs = {k: v for k, v in preferred.items() if k in params}
    if call_kwargs:
        return fn(**call_kwargs)
    return fn(*args)

def _semantic_from_guarded(guarded, semantic_fn):
    if semantic_fn is None:
        return guarded
    sig = inspect.signature(semantic_fn)
    names = set(sig.parameters)
    if len(names) == 1:
        return semantic_fn(guarded)
    preferred = {
        "guarded_identity": guarded,
        "identity": guarded,
        "resolved_identity": guarded,
        "record": guarded,
    }
    kwargs = {k: v for k, v in preferred.items() if k in names}
    if kwargs:
        return semantic_fn(**kwargs)
    return semantic_fn(guarded)

def _route_from_semantic(semantic, router_fn):
    if router_fn is None:
        return None
    sig = inspect.signature(router_fn)
    names = set(sig.parameters)
    if len(names) == 1:
        return router_fn(semantic)
    domain = _attr(semantic, "domain", "semantic_domain")
    subdomain = _attr(semantic, "subdomain", "semantic_subdomain", "sport_family")
    preferred = {
        "semantic_identity": semantic,
        "identity": semantic,
        "domain": domain,
        "subdomain": subdomain,
    }
    kwargs = {k: v for k, v in preferred.items() if k in names}
    if kwargs:
        return router_fn(**kwargs)
    return router_fn(semantic)

def _is_sports_unknown(semantic):
    domain = _attr(semantic, "domain", "semantic_domain")
    subdomain = _attr(semantic, "subdomain", "semantic_subdomain", "sport_family")
    state = _attr(semantic, "state", "semantic_state", "resolution_state")

    text = _text(semantic).lower()
    domain_text = str(domain).lower() if domain is not None else ""
    sub_text = str(subdomain).lower() if subdomain is not None else ""
    state_text = str(state).lower() if state is not None else ""

    sports = domain_text == "sports" or '"domain": "sports"' in text or "sports:" in text
    unknown = (
        sub_text in ("", "unknown", "none")
        or state_text in ("unknown", "unresolved")
        or '"subdomain": "unknown"' in text
        or '"semantic_subdomain": "unknown"' in text
        or "sports:unknown" in text
    )
    return sports and unknown

def _market_identity(market):
    return {
        "ticker": _attr(market, "ticker", "market_ticker", "source_market_id", "symbol"),
        "title": _attr(market, "title", "market_title", "question", "subtitle"),
        "event_ticker": _attr(market, "event_ticker"),
        "series_ticker": _attr(market, "series_ticker"),
    }

def run_exact_sports_unknown_record_extractor(limit: int = 1000, root=None):
    root = Path(root or Path.cwd()).resolve()
    m106 = _load_contract()

    semantic_fn, semantic_path = _resolve_semantic_callable()
    router_fn, router_path = _resolve_router_callable()

    snapshot = m106.capture_current_market_cohort(limit=limit)
    markets = tuple(m106.snapshot_markets(snapshot))

    extracted = []
    leg_count = 0

    for market in markets:
        legs = tuple(m106.decompose_mixed_market(market))
        envelopes = tuple(m106.build_identity_envelopes(market, legs))
        if len(envelopes) != len(legs):
            raise RuntimeError(
                f"OAD-106 replay invariant failed: legs={len(legs)} envelopes={len(envelopes)}"
            )

        for index, (leg, env) in enumerate(zip(legs, envelopes)):
            leg_count += 1
            guarded = m106.resolve_guarded_identity(env)

            semantic = guarded
            if semantic_fn is not None:
                try:
                    semantic = _semantic_from_guarded(guarded, semantic_fn)
                except Exception as exc:
                    semantic = guarded

            if not _is_sports_unknown(semantic):
                continue

            route = None
            if router_fn is not None:
                try:
                    route = _route_from_semantic(semantic, router_fn)
                except Exception:
                    route = None

            extracted.append({
                "market": _market_identity(market),
                "leg_index": index,
                "leg": _safe(leg),
                "identity_envelope": _safe(env),
                "guarded_identity": _safe(guarded),
                "semantic_identity": _safe(semantic),
                "source_requirement": _safe(route),
            })

    snapshot_id = _attr(snapshot, "snapshot_id", "cohort_id")
    report = {
        "read_only": True,
        "execution_authority": False,
        "probability_enabled": False,
        "limit": limit,
        "snapshot_id": snapshot_id,
        "market_count": len(markets),
        "decomposed_leg_count": leg_count,
        "sports_unknown_record_count": len(extracted),
        "semantic_callable": semantic_path,
        "router_callable": router_path,
        "records": extracted,
    }

    report_path = root / "OAD_106_EXACT_SPORTS_UNKNOWN_RECORDS.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return report, report_path
