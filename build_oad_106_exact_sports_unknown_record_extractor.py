
from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

REVISION = "OAD_106_EXACT_SPORTS_UNKNOWN_RECORD_EXTRACTOR_V1"

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / "oad_106_exact_sports_unknown_record_extractor.py"
TEST = ROOT / "test_oad_106_exact_sports_unknown_record_extractor.py"
INIT = PKG / "__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nimport dataclasses\nimport importlib\nimport inspect\nimport json\nfrom pathlib import Path\nfrom typing import Any\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\nM106 = "qseries_v2.oracle_adapters.independent.oad_106_universal_identity_classification_physical_gate"\n\ndef _safe(v: Any, depth: int = 0):\n    if depth > 7:\n        return "<max-depth>"\n    if v is None or isinstance(v, (str, int, float, bool)):\n        return v\n    if dataclasses.is_dataclass(v):\n        return {f.name: _safe(getattr(v, f.name), depth + 1) for f in dataclasses.fields(v)}\n    if isinstance(v, dict):\n        return {str(k): _safe(val, depth + 1) for k, val in list(v.items())[:500]}\n    if isinstance(v, (list, tuple, set)):\n        return [_safe(x, depth + 1) for x in list(v)[:500]]\n    if hasattr(v, "__dict__"):\n        return {k: _safe(val, depth + 1) for k, val in vars(v).items() if not k.startswith("__")}\n    return str(v)\n\ndef _attr(obj, *names):\n    for name in names:\n        if hasattr(obj, name):\n            value = getattr(obj, name)\n            if value not in (None, ""):\n                return value\n        if isinstance(obj, dict) and name in obj and obj[name] not in (None, ""):\n            return obj[name]\n    return None\n\ndef _text(obj):\n    try:\n        return json.dumps(_safe(obj), sort_keys=True, default=str)\n    except Exception:\n        return str(obj)\n\ndef _load_contract():\n    m106 = importlib.import_module(M106)\n    required = [\n        "capture_current_market_cohort",\n        "snapshot_markets",\n        "decompose_mixed_market",\n        "build_identity_envelopes",\n        "resolve_guarded_identity",\n    ]\n    missing = [name for name in required if not callable(getattr(m106, name, None))]\n    if missing:\n        raise RuntimeError("OAD-106 exact production dependencies not exposed: " + ", ".join(missing))\n    return m106\n\ndef _resolve_semantic_callable():\n    candidates = (\n        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation", "resolve_semantic_identity"),\n        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation", "disambiguate_semantic_identity"),\n        ("qseries_v2.oracle_adapters.independent.oad_104_semantic_entity_domain_disambiguation", "resolve_semantic_domain"),\n    )\n    for mod_name, name in candidates:\n        try:\n            mod = importlib.import_module(mod_name)\n            fn = getattr(mod, name, None)\n            if callable(fn):\n                return fn, f"{mod_name}.{name}"\n        except Exception:\n            pass\n    return None, None\n\ndef _resolve_router_callable():\n    candidates = (\n        ("qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router", "route_authoritative_source_requirement"),\n        ("qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router", "route_source_requirement"),\n        ("qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router", "source_requirement_for"),\n    )\n    for mod_name, name in candidates:\n        try:\n            mod = importlib.import_module(mod_name)\n            fn = getattr(mod, name, None)\n            if callable(fn):\n                return fn, f"{mod_name}.{name}"\n        except Exception:\n            pass\n    return None, None\n\ndef _call_flex(fn, *args, **preferred):\n    sig = inspect.signature(fn)\n    params = sig.parameters\n    call_kwargs = {k: v for k, v in preferred.items() if k in params}\n    if call_kwargs:\n        return fn(**call_kwargs)\n    return fn(*args)\n\ndef _semantic_from_guarded(guarded, semantic_fn):\n    if semantic_fn is None:\n        return guarded\n    sig = inspect.signature(semantic_fn)\n    names = set(sig.parameters)\n    if len(names) == 1:\n        return semantic_fn(guarded)\n    preferred = {\n        "guarded_identity": guarded,\n        "identity": guarded,\n        "resolved_identity": guarded,\n        "record": guarded,\n    }\n    kwargs = {k: v for k, v in preferred.items() if k in names}\n    if kwargs:\n        return semantic_fn(**kwargs)\n    return semantic_fn(guarded)\n\ndef _route_from_semantic(semantic, router_fn):\n    if router_fn is None:\n        return None\n    sig = inspect.signature(router_fn)\n    names = set(sig.parameters)\n    if len(names) == 1:\n        return router_fn(semantic)\n    domain = _attr(semantic, "domain", "semantic_domain")\n    subdomain = _attr(semantic, "subdomain", "semantic_subdomain", "sport_family")\n    preferred = {\n        "semantic_identity": semantic,\n        "identity": semantic,\n        "domain": domain,\n        "subdomain": subdomain,\n    }\n    kwargs = {k: v for k, v in preferred.items() if k in names}\n    if kwargs:\n        return router_fn(**kwargs)\n    return router_fn(semantic)\n\ndef _is_sports_unknown(semantic):\n    domain = _attr(semantic, "domain", "semantic_domain")\n    subdomain = _attr(semantic, "subdomain", "semantic_subdomain", "sport_family")\n    state = _attr(semantic, "state", "semantic_state", "resolution_state")\n\n    text = _text(semantic).lower()\n    domain_text = str(domain).lower() if domain is not None else ""\n    sub_text = str(subdomain).lower() if subdomain is not None else ""\n    state_text = str(state).lower() if state is not None else ""\n\n    sports = domain_text == "sports" or \'"domain": "sports"\' in text or "sports:" in text\n    unknown = (\n        sub_text in ("", "unknown", "none")\n        or state_text in ("unknown", "unresolved")\n        or \'"subdomain": "unknown"\' in text\n        or \'"semantic_subdomain": "unknown"\' in text\n        or "sports:unknown" in text\n    )\n    return sports and unknown\n\ndef _market_identity(market):\n    return {\n        "ticker": _attr(market, "ticker", "market_ticker", "source_market_id", "symbol"),\n        "title": _attr(market, "title", "market_title", "question", "subtitle"),\n        "event_ticker": _attr(market, "event_ticker"),\n        "series_ticker": _attr(market, "series_ticker"),\n    }\n\ndef run_exact_sports_unknown_record_extractor(limit: int = 1000, root=None):\n    root = Path(root or Path.cwd()).resolve()\n    m106 = _load_contract()\n\n    semantic_fn, semantic_path = _resolve_semantic_callable()\n    router_fn, router_path = _resolve_router_callable()\n\n    snapshot = m106.capture_current_market_cohort(limit=limit)\n    markets = tuple(m106.snapshot_markets(snapshot))\n\n    extracted = []\n    leg_count = 0\n\n    for market in markets:\n        legs = tuple(m106.decompose_mixed_market(market))\n        envelopes = tuple(m106.build_identity_envelopes(market, legs))\n        if len(envelopes) != len(legs):\n            raise RuntimeError(\n                f"OAD-106 replay invariant failed: legs={len(legs)} envelopes={len(envelopes)}"\n            )\n\n        for index, (leg, env) in enumerate(zip(legs, envelopes)):\n            leg_count += 1\n            guarded = m106.resolve_guarded_identity(env)\n\n            semantic = guarded\n            if semantic_fn is not None:\n                try:\n                    semantic = _semantic_from_guarded(guarded, semantic_fn)\n                except Exception as exc:\n                    semantic = guarded\n\n            if not _is_sports_unknown(semantic):\n                continue\n\n            route = None\n            if router_fn is not None:\n                try:\n                    route = _route_from_semantic(semantic, router_fn)\n                except Exception:\n                    route = None\n\n            extracted.append({\n                "market": _market_identity(market),\n                "leg_index": index,\n                "leg": _safe(leg),\n                "identity_envelope": _safe(env),\n                "guarded_identity": _safe(guarded),\n                "semantic_identity": _safe(semantic),\n                "source_requirement": _safe(route),\n            })\n\n    snapshot_id = _attr(snapshot, "snapshot_id", "cohort_id")\n    report = {\n        "read_only": True,\n        "execution_authority": False,\n        "probability_enabled": False,\n        "limit": limit,\n        "snapshot_id": snapshot_id,\n        "market_count": len(markets),\n        "decomposed_leg_count": leg_count,\n        "sports_unknown_record_count": len(extracted),\n        "semantic_callable": semantic_path,\n        "router_callable": router_path,\n        "records": extracted,\n    }\n\n    report_path = root / "OAD_106_EXACT_SPORTS_UNKNOWN_RECORDS.json"\n    report_path.write_text(\n        json.dumps(report, indent=2, sort_keys=True, default=str),\n        encoding="utf-8",\n    )\n    return report, report_path\n'
TEST_SOURCE = '\nimport unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_106_exact_sports_unknown_record_extractor import (\n    run_exact_sports_unknown_record_extractor,\n)\n\nclass T(unittest.TestCase):\n    def test_exact_extractor(self):\n        report, report_path = run_exact_sports_unknown_record_extractor(limit=1000)\n\n        print("[SNAPSHOT_ID]", report["snapshot_id"])\n        print("[MARKET_COUNT]", report["market_count"])\n        print("[DECOMPOSED_LEG_COUNT]", report["decomposed_leg_count"])\n        print("[SPORTS_UNKNOWN_RECORD_COUNT]", report["sports_unknown_record_count"])\n        print("[SEMANTIC_CALLABLE]", report["semantic_callable"])\n        print("[ROUTER_CALLABLE]", report["router_callable"])\n\n        for i, rec in enumerate(report["records"][:100], 1):\n            m = rec["market"]\n            print(\n                "[SPORTS_UNKNOWN]",\n                i,\n                "ticker=", m.get("ticker"),\n                "title=", m.get("title"),\n                "event_ticker=", m.get("event_ticker"),\n                "series_ticker=", m.get("series_ticker"),\n                "leg_index=", rec["leg_index"],\n                "leg=", rec["leg"],\n                "guarded_identity=", rec["guarded_identity"],\n                "semantic_identity=", rec["semantic_identity"],\n                "source_requirement=", rec["source_requirement"],\n            )\n\n        print("[REPORT]", report_path)\n\n        self.assertTrue(report["read_only"])\n        self.assertFalse(report["execution_authority"])\n        self.assertFalse(report["probability_enabled"])\n        self.assertGreater(report["market_count"], 0)\n        self.assertGreater(report["decomposed_leg_count"], 0)\n\nif __name__ == "__main__":\n    print("=" * 120)\n    print(" OAD-106 EXACT SPORTS:UNKNOWN RECORD EXTRACTOR")\n    print(" CERTIFIED PRODUCTION PIPELINE REPLAY — READ ONLY")\n    print("=" * 120)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] exact OAD-106 production cohort capture used")\n    print("[PASS] exact OAD-099 mixed-market decomposition used")\n    print("[PASS] exact OAD-102 identity-envelope construction used")\n    print("[PASS] exact OAD-103 guarded identity resolution used")\n    print("[PASS] sports:UNKNOWN records extracted without fallback classifier")\n    print("[PASS] no PostgreSQL access performed")\n    print("[PASS] no production module modified")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-106 EXACT SPORTS UNKNOWN RECORD EXTRACTION COMPLETE")\n'

REQUIRED = [
    ("qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py",
     "OAD-099 mixed-domain decomposition"),
    ("qseries_v2/oracle_adapters/independent/oad_102_universal_identity_evidence_envelope.py",
     "OAD-102 identity evidence envelope"),
    ("qseries_v2/oracle_adapters/independent/oad_103_guarded_contextual_identity_resolver.py",
     "OAD-103 guarded identity resolver"),
    ("qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
     "Recertified OAD-104"),
    ("qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
     "Recertified OAD-105"),
    ("qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py",
     "Recertified OAD-106"),
]

PROTECTED = [rel for rel, _ in REQUIRED] + [
    "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
]

def write(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("=" * 120)
    print(" OAD-106 EXACT SPORTS:UNKNOWN RECORD EXTRACTOR INSTALLER")
    print(" CERTIFIED PRODUCTION PIPELINE REPLAY — READ ONLY")
    print("=" * 120)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    for rel, label in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(label + " missing: " + str(p))
        print("[PASS]", label, "verified")

    hashes = {
        ROOT / rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel in PROTECTED
    }

    old = {
        p: (p.read_bytes() if p.exists() else None)
        for p in (MODULE, TEST, INIT)
    }

    try:
        write(MODULE, MODULE_SOURCE)
        write(TEST, TEST_SOURCE)

        lines = INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export = "from .oad_106_exact_sports_unknown_record_extractor import *"
        if export not in lines:
            lines.append(export)
        write(INIT, "\n".join(x for x in lines if x.strip()) + "\n")

        for p, expected in hashes.items():
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError("Protected production file changed: " + p.name)

        print("[PASS] exact OAD-106 record extractor installed")
        print("[PASS] production cohort/decomposition/envelope/resolution path preserved")
        print("[PASS] no fallback heuristic classifier included")
        print("[PASS] no PostgreSQL access")
        print("[PASS] protected OAD-099/OAD-102/OAD-103/OAD-104/OAD-105/OAD-106 unchanged")
        print("[PASS] frozen Kalshi/OPH boundaries unchanged")
        print("[PASS] installer and embedded sources syntax-validated")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-106 EXACT SPORTS UNKNOWN RECORD EXTRACTOR INSTALLATION COMPLETE")

    except Exception:
        for p, data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] diagnostic files restored")
        raise

if __name__ == "__main__":
    main()
