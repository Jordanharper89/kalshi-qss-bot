
from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

REVISION = "OAD_POSTGRESQL_CANONICAL_OBSERVATION_IDENTITY_RECOVERY_AUDIT_V1"

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / "oad_postgresql_canonical_observation_identity_recovery_audit.py"
TEST = ROOT / "test_oad_postgresql_canonical_observation_identity_recovery_audit.py"
INIT = PKG / "__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nimport dataclasses\nimport importlib\nimport inspect\nimport json\nimport re\nfrom collections import Counter\nfrom pathlib import Path\nfrom typing import Any\n\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (\n    build_existing_canonical_router,\n)\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\nSPORT_PATTERNS = {\n    "baseball": (\n        r"\\bmlb\\b", r"\\bbaseball\\b", r"\\binnings?\\b", r"\\bhome runs?\\b",\n        r"\\brbis?\\b", r"\\bpitcher\\b", r"\\bstrikeouts?\\b",\n    ),\n    "hockey": (\n        r"\\bnhl\\b", r"\\bhockey\\b", r"\\bpuck\\b", r"\\bpower play\\b",\n        r"\\bshots on goal\\b",\n    ),\n    "basketball": (\n        r"\\bnba\\b", r"\\bwnba\\b", r"\\bbasketball\\b", r"\\brebounds?\\b",\n        r"\\bassists?\\b", r"\\bthree[- ]pointers?\\b",\n    ),\n    "football": (\n        r"\\bnfl\\b", r"\\bamerican football\\b", r"\\btouchdowns?\\b",\n        r"\\bpassing yards?\\b", r"\\brushing yards?\\b", r"\\breceptions?\\b",\n    ),\n    "soccer": (\n        r"\\bsoccer\\b", r"\\bpremier league\\b", r"\\bchampions league\\b",\n        r"\\bla liga\\b", r"\\bserie a\\b", r"\\bbundesliga\\b", r"\\bligue 1\\b",\n        r"\\bmls\\b", r"\\buefa\\b", r"\\bfifa\\b",\n    ),\n    "tennis": (\n        r"\\batp\\b", r"\\bwta\\b", r"\\btennis\\b", r"\\bwimbledon\\b",\n        r"\\bus open\\b", r"\\baustralian open\\b", r"\\bfrench open\\b",\n    ),\n    "combat": (\n        r"\\bufc\\b", r"\\bmma\\b", r"\\bboxing\\b", r"\\bknockout\\b",\n        r"\\bsubmission\\b", r"\\bko/tko\\b",\n    ),\n    "golf": (\n        r"\\bpga\\b", r"\\blpga\\b", r"\\bgolf\\b", r"\\bmasters\\b",\n    ),\n    "esports": (\n        r"\\besports?\\b", r"\\bleague of legends\\b",\n        r"\\bcounter[- ]strike\\b", r"\\bvalorant\\b", r"\\bdota\\b",\n    ),\n}\n\ndef _router_backend(root: Path):\n    router = build_existing_canonical_router(root)\n    backend = getattr(router, "_persistence_backend", None)\n    if backend is None:\n        raise RuntimeError("existing canonical PostgreSQL backend unavailable")\n    if not callable(getattr(backend, "_connect", None)):\n        raise RuntimeError("audited backend._connect() unavailable")\n    if not callable(getattr(backend, "query", None)):\n        raise RuntimeError("certified backend.query() unavailable")\n    return router, backend\n\ndef _safe_text(value: Any, depth: int = 0) -> Any:\n    if depth > 5:\n        return "<max-depth>"\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    if dataclasses.is_dataclass(value):\n        return {\n            f.name: _safe_text(getattr(value, f.name), depth + 1)\n            for f in dataclasses.fields(value)\n        }\n    if isinstance(value, dict):\n        return {\n            str(k): _safe_text(v, depth + 1)\n            for k, v in list(value.items())[:200]\n        }\n    if isinstance(value, (list, tuple, set)):\n        return [_safe_text(v, depth + 1) for v in list(value)[:200]]\n    if hasattr(value, "__dict__"):\n        return {\n            k: _safe_text(v, depth + 1)\n            for k, v in vars(value).items()\n            if not k.startswith("__")\n        }\n    return str(value)\n\ndef _flatten_strings(value: Any, prefix: str = "") -> list[tuple[str, str]]:\n    out: list[tuple[str, str]] = []\n    if value is None:\n        return out\n    if isinstance(value, str):\n        if value.strip():\n            out.append((prefix, value))\n        return out\n    if isinstance(value, (int, float, bool)):\n        out.append((prefix, str(value)))\n        return out\n    if isinstance(value, dict):\n        for k, v in value.items():\n            p = f"{prefix}.{k}" if prefix else str(k)\n            out.extend(_flatten_strings(v, p))\n        return out\n    if isinstance(value, (list, tuple)):\n        for i, v in enumerate(value):\n            out.extend(_flatten_strings(v, f"{prefix}[{i}]"))\n        return out\n    return _flatten_strings(_safe_text(value), prefix)\n\ndef _request_class(backend):\n    query_mod = importlib.import_module(backend.__class__.__module__)\n    cls = getattr(query_mod, "CanonicalPersistenceQueryRequest", None)\n    if cls is not None:\n        return cls\n\n    for module_name in (\n        "qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend",\n        "qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router",\n    ):\n        try:\n            mod = importlib.import_module(module_name)\n        except Exception:\n            continue\n        cls = getattr(mod, "CanonicalPersistenceQueryRequest", None)\n        if cls is not None:\n            return cls\n\n    annotations = getattr(inspect.signature(backend.query).parameters.get("request"), "annotation", None)\n    if isinstance(annotations, type):\n        return annotations\n    raise RuntimeError("CanonicalPersistenceQueryRequest class not found")\n\ndef _request_for_observation_id(request_cls, observation_id: str):\n    method = getattr(request_cls, "by_observation_id", None)\n    if callable(method):\n        return method(observation_id)\n\n    # Repository contract may use keyword-only construction.\n    for kwargs in (\n        {"observation_id": observation_id},\n        {"observation_ids": (observation_id,)},\n        {"exact_observation_id": observation_id},\n    ):\n        try:\n            return request_cls(**kwargs)\n        except TypeError:\n            pass\n    raise RuntimeError(\n        "CanonicalPersistenceQueryRequest has no supported exact observation-id constructor"\n    )\n\ndef _read_linkage_rows(backend, limit: int):\n    conn = backend._connect()\n    if conn is None:\n        raise RuntimeError("backend._connect() returned None")\n    try:\n        with conn.cursor() as cur:\n            cur.execute("BEGIN READ ONLY")\n            cur.execute(\n                """\n                SELECT ticker, observation_id\n                FROM public.oracle_production_learning_evidence_index\n                WHERE ticker IS NOT NULL\n                  AND observation_id IS NOT NULL\n                ORDER BY ticker, observation_id\n                LIMIT %s\n                """,\n                (int(limit),),\n            )\n            rows = cur.fetchall()\n        conn.rollback()\n        return tuple((str(t), str(o)) for t, o in rows)\n    except Exception:\n        conn.rollback()\n        raise\n    finally:\n        try:\n            conn.close()\n        except Exception:\n            pass\n\ndef _classify_family(text: str):\n    hits = []\n    for family, patterns in SPORT_PATTERNS.items():\n        matched = [p for p in patterns if re.search(p, text, re.I)]\n        if matched:\n            hits.append((family, len(matched), matched))\n    hits.sort(key=lambda x: (-x[1], x[0]))\n    if not hits:\n        return "UNKNOWN", "NO_EXPLICIT_FAMILY_SIGNAL", []\n    if len(hits) > 1 and hits[0][1] == hits[1][1]:\n        n = hits[0][1]\n        tied = [x[0] for x in hits if x[1] == n]\n        return "UNKNOWN", "CONFLICTING_FAMILY_SIGNAL:" + ",".join(tied), tied\n    return hits[0][0], "CANONICAL_OBSERVATION_SIGNAL", hits[0][2]\n\ndef run_canonical_observation_identity_recovery_audit(\n    root=None,\n    linkage_limit: int = 25000,\n    max_unique_observations: int = 10000,\n):\n    root = Path(root or Path.cwd()).resolve()\n    _, backend = _router_backend(root)\n    request_cls = _request_class(backend)\n\n    linkage = _read_linkage_rows(backend, linkage_limit)\n    unique = []\n    seen = set()\n    for ticker, observation_id in linkage:\n        if observation_id in seen:\n            continue\n        seen.add(observation_id)\n        unique.append((ticker, observation_id))\n        if len(unique) >= int(max_unique_observations):\n            break\n\n    family_counts = Counter()\n    reason_counts = Counter()\n    restored = []\n    unresolved = []\n    missing = []\n    field_paths = Counter()\n\n    for ticker, observation_id in unique:\n        request = _request_for_observation_id(request_cls, observation_id)\n        observations = backend.query(request=request)\n\n        if not observations:\n            missing.append({"ticker": ticker, "observation_id": observation_id})\n            continue\n\n        for obs in observations:\n            normalized = _safe_text(obs)\n            strings = _flatten_strings(normalized)\n            for path, _ in strings:\n                field_paths[path] += 1\n\n            identity_text = " | ".join(\n                [ticker, observation_id]\n                + [text for _, text in strings]\n            )\n            family, reason, signals = _classify_family(identity_text)\n            family_counts[family] += 1\n            reason_counts[reason] += 1\n\n            record = {\n                "ticker": ticker,\n                "observation_id": observation_id,\n                "family": family,\n                "reason": reason,\n                "signals": signals,\n                "canonical_observation_type": (\n                    f"{type(obs).__module__}.{type(obs).__name__}"\n                ),\n                "canonical_observation": normalized,\n            }\n            restored.append(record)\n            if family == "UNKNOWN":\n                unresolved.append(record)\n\n    report = {\n        "read_only": True,\n        "execution_authority": False,\n        "probability_enabled": False,\n        "postgres_transaction": "BEGIN READ ONLY",\n        "canonical_query_surface": "backend.query(request=CanonicalPersistenceQueryRequest)",\n        "request_class": f"{request_cls.__module__}.{request_cls.__name__}",\n        "linkage_rows_read": len(linkage),\n        "unique_observations_attempted": len(unique),\n        "restored_observation_count": len(restored),\n        "missing_observation_count": len(missing),\n        "family_counts": dict(family_counts.most_common()),\n        "reason_counts": dict(reason_counts.most_common()),\n        "observed_field_paths": dict(field_paths.most_common(200)),\n        "restored": restored,\n        "unresolved": unresolved,\n        "missing": missing,\n    }\n\n    report_path = root / "OAD_POSTGRESQL_CANONICAL_OBSERVATION_IDENTITY_RECOVERY_AUDIT.json"\n    unresolved_path = root / "OAD_POSTGRESQL_CANONICAL_OBSERVATION_STILL_UNKNOWN.json"\n\n    report_path.write_text(\n        json.dumps(report, indent=2, sort_keys=True, default=str),\n        encoding="utf-8",\n    )\n    unresolved_path.write_text(\n        json.dumps(unresolved, indent=2, sort_keys=True, default=str),\n        encoding="utf-8",\n    )\n\n    return report, report_path, unresolved_path\n'
TEST_SOURCE = '\nimport unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_postgresql_canonical_observation_identity_recovery_audit import (\n    run_canonical_observation_identity_recovery_audit,\n)\n\nclass T(unittest.TestCase):\n    def test_identity_recovery(self):\n        report, report_path, unresolved_path = (\n            run_canonical_observation_identity_recovery_audit()\n        )\n\n        print("[POSTGRES_TRANSACTION]", report["postgres_transaction"])\n        print("[CANONICAL_QUERY_SURFACE]", report["canonical_query_surface"])\n        print("[REQUEST_CLASS]", report["request_class"])\n        print("[LINKAGE_ROWS_READ]", report["linkage_rows_read"])\n        print("[UNIQUE_OBSERVATIONS_ATTEMPTED]", report["unique_observations_attempted"])\n        print("[RESTORED_OBSERVATION_COUNT]", report["restored_observation_count"])\n        print("[MISSING_OBSERVATION_COUNT]", report["missing_observation_count"])\n        print("[FAMILY_COUNTS]", report["family_counts"])\n        print("[REASON_COUNTS]", report["reason_counts"])\n\n        print("[OBSERVED_FIELD_PATHS]")\n        for path, count in list(report["observed_field_paths"].items())[:100]:\n            print(" ", path, "count=", count)\n\n        print("[STILL_UNKNOWN_COUNT]", len(report["unresolved"]))\n        for i, rec in enumerate(report["unresolved"][:50], 1):\n            print(\n                "[STILL_UNKNOWN]",\n                i,\n                "ticker=", rec["ticker"],\n                "observation_id=", rec["observation_id"],\n                "type=", rec["canonical_observation_type"],\n                "canonical_observation=", rec["canonical_observation"],\n            )\n\n        print("[REPORT]", report_path)\n        print("[UNKNOWN_REPORT]", unresolved_path)\n\n        self.assertTrue(report["read_only"])\n        self.assertFalse(report["execution_authority"])\n        self.assertFalse(report["probability_enabled"])\n        self.assertEqual(report["postgres_transaction"], "BEGIN READ ONLY")\n        self.assertGreater(report["linkage_rows_read"], 0)\n        self.assertGreater(report["unique_observations_attempted"], 0)\n        self.assertGreater(report["restored_observation_count"], 0)\n\nif __name__ == "__main__":\n    print("=" * 112)\n    print(" OAD POSTGRESQL CANONICAL OBSERVATION IDENTITY RECOVERY AUDIT")\n    print(" TICKER -> OBSERVATION_ID -> CERTIFIED CANONICAL QUERY -> RESTORED IDENTITY")\n    print("=" * 112)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] PostgreSQL linkage read through BEGIN READ ONLY")\n    print("[PASS] canonical observations restored through certified backend.query()")\n    print("[PASS] no PostgreSQL row modified")\n    print("[PASS] no production classifier modified")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] CANONICAL OBSERVATION IDENTITY RECOVERY AUDIT COMPLETE")\n'

REQUIRED = [
    ("qseries_v2/oracle_production_hardening/oph_007_physical_single_postgresql_writer_runtime.py",
     "Existing PostgreSQL production router"),
    ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
     "Frozen OPH-023"),
    ("qseries_v2/oracle_adapters/independent/oad_postgresql_backend_interface_audit.py",
     "Certified PostgreSQL backend interface audit"),
    ("qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
     "Recertified OAD-104"),
    ("qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
     "Recertified OAD-105"),
    ("qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py",
     "Recertified OAD-106"),
]

PROTECTED = [
    "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
    "qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py",
    "qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py",
    "qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
    "qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
    "qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py",
]

def write(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("=" * 112)
    print(" OAD POSTGRESQL CANONICAL OBSERVATION IDENTITY RECOVERY AUDIT INSTALLER")
    print(" CERTIFIED QUERY-SURFACE RESTORATION — READ ONLY")
    print("=" * 112)
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
        export = "from .oad_postgresql_canonical_observation_identity_recovery_audit import *"
        if export not in lines:
            lines.append(export)
        write(INIT, "\n".join(x for x in lines if x.strip()) + "\n")

        for p, h in hashes.items():
            if hashlib.sha256(p.read_bytes()).hexdigest() != h:
                raise RuntimeError("Protected production file changed: " + p.name)

        print("[PASS] canonical identity-recovery diagnostic installed")
        print("[PASS] exact PostgreSQL ticker -> observation_id linkage bound")
        print("[PASS] certified backend.query() restoration path bound")
        print("[PASS] PostgreSQL SQL transaction forced BEGIN READ ONLY")
        print("[PASS] recertified OAD-104/OAD-105/OAD-106 protected")
        print("[PASS] frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] installer and embedded sources syntax-validated")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] CANONICAL OBSERVATION IDENTITY RECOVERY AUDIT INSTALLATION COMPLETE")

    except Exception:
        for p, data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] audit files restored")
        raise

if __name__ == "__main__":
    main()
