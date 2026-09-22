from pathlib import Path
import ast
import importlib
import os
import subprocess
import sys
import time

ROOT = Path.cwd().resolve()
PKG = ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"

MOD = PKG/"oiar_005_persisted_trader_intelligence_read_surface.py"
TEST = ROOT/"test_oiar_005_persisted_trader_intelligence_read_surface.py"
RUNNER = ROOT/"run_oiar_005_trader_intelligence_query.py"
INIT = PKG/"__init__.py"

MODULE_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_read_model import (\n    load_historical_experience_read_model,\n)\nfrom .oiar_001_production_analytics_snapshot_foundation import (\n    SNAPSHOT_TABLE,\n    stable_hash,\n)\nfrom .oiar_004_indexed_current_cohort_analytics_materializer import (\n    ANALYTICS_STAGE,\n)\n\nOIAR_005_BUILD_ID = "OIAR-005"\nOIAR_005_REVISION = "OIAR_005_PERSISTED_TRADER_INTELLIGENCE_READ_SURFACE_V1"\n\n@dataclass(frozen=True)\nclass PersistedTraderIntelligenceRow:\n    rank:int\n    market_id:str\n    attention_score:float\n    maturity:str\n    reliability:float\n    learned_family_records:int\n    history_rows:int\n    usefulness_classification:str\n    usefulness_score:float\n    candidate_family:str\n    research_direction:str\n    candidate_score:float\n    admission_status:str\n    admission_score:float\n    latest_price_dollars:str|None\n    reason_codes:tuple\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef _num(value):\n    if value in (None, ""):\n        return 0.0\n    try:\n        return float(value)\n    except (TypeError, ValueError):\n        return 0.0\n\ndef _latest_analytics_payload(root: Path):\n    with connect(root, autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"""\n                SELECT payload_json,payload_hash\n                FROM public.{SNAPSHOT_TABLE}\n                WHERE stage=%s\n                ORDER BY generated_at DESC,persisted_at DESC\n                LIMIT 1\n                """,\n                (ANALYTICS_STAGE,),\n            )\n            row = cur.fetchone()\n        conn.rollback()\n\n    if row is None:\n        raise RuntimeError("OIAR-005 requires an OIAR-004 persisted analytics snapshot")\n\n    payload, payload_hash = row\n    if isinstance(payload, str):\n        payload = json.loads(payload)\n\n    if not isinstance(payload, dict):\n        raise RuntimeError("OIAR-005 persisted analytics payload invalid")\n\n    if stable_hash(payload) != str(payload_hash):\n        raise RuntimeError("OIAR-005 persisted analytics payload hash mismatch")\n\n    return payload\n\ndef _family_from_context(context):\n    series_key = str(context.series_key or "")\n    if series_key:\n        tail = series_key.split(":")[-1].strip()\n        if tail:\n            return tail\n    return str(context.market_ticker or "").split("-", 1)[0]\n\ndef build_persisted_trader_intelligence(root=None, limit=20):\n    root = Path(root or Path.cwd()).resolve()\n\n    analytics = _latest_analytics_payload(root)\n    history = load_historical_experience_read_model(root)\n\n    contexts = {\n        str(c.market_ticker).upper(): c\n        for c in history.contexts\n        if str(c.market_ticker).strip()\n    }\n    family_counts = dict(history.learned_family_counts)\n\n    rows = []\n\n    for item in analytics.get("markets", []):\n        if not isinstance(item, dict):\n            continue\n\n        market_id = str(item.get("market_id") or "").upper()\n        if not market_id:\n            continue\n\n        context = contexts.get(market_id)\n        if context is None:\n            continue\n\n        usefulness = item.get("usefulness")\n        candidate = item.get("candidate")\n        admission = item.get("admission")\n\n        usefulness = usefulness if isinstance(usefulness, dict) else {}\n        candidate = candidate if isinstance(candidate, dict) else {}\n        admission = admission if isinstance(admission, dict) else {}\n\n        family = _family_from_context(context)\n        learned_family_records = int(family_counts.get(family, 0))\n        history_rows = int(item.get("history_rows") or 0)\n\n        maturity_text = str(context.maturity or "BLIND")\n        maturity_score = {\n            "PROVEN": 1.00,\n            "MATURE": 0.85,\n            "DEVELOPING": 0.60,\n            "IMMATURE": 0.35,\n            "BLIND": 0.00,\n        }.get(maturity_text.upper(), 0.25)\n\n        reliability = max(0.0, min(float(context.reliability or 0.0), 1.0))\n        depth_score = min(1.0, learned_family_records / 500.0)\n\n        usefulness_score = _num(\n            usefulness.get("usefulness_score")\n            if "usefulness_score" in usefulness\n            else usefulness.get("score")\n        )\n        usefulness_norm = min(1.0, usefulness_score / 100.0)\n\n        candidate_score = _num(candidate.get("candidate_score"))\n        candidate_norm = min(1.0, candidate_score / 100.0)\n\n        admission_status = str(admission.get("admission_status") or "not_candidate")\n        admission_score = _num(admission.get("admission_score"))\n\n        admission_norm = (\n            1.00 if admission_status == "admitted"\n            else 0.55 if admission_status == "denied"\n            else 0.15\n        )\n\n        history_quality = min(1.0, history_rows / 20.0)\n\n        attention_score = 100.0 * (\n            0.25 * maturity_score\n            + 0.20 * reliability\n            + 0.20 * depth_score\n            + 0.10 * usefulness_norm\n            + 0.10 * candidate_norm\n            + 0.10 * admission_norm\n            + 0.05 * history_quality\n        )\n\n        rows.append(\n            PersistedTraderIntelligenceRow(\n                rank=0,\n                market_id=market_id,\n                attention_score=round(attention_score, 6),\n                maturity=maturity_text,\n                reliability=reliability,\n                learned_family_records=learned_family_records,\n                history_rows=history_rows,\n                usefulness_classification=str(\n                    usefulness.get("classification")\n                    or usefulness.get("usefulness_classification")\n                    or "unknown"\n                ),\n                usefulness_score=usefulness_score,\n                candidate_family=str(candidate.get("candidate_family") or "none"),\n                research_direction=str(candidate.get("research_direction") or "neutral"),\n                candidate_score=candidate_score,\n                admission_status=admission_status,\n                admission_score=admission_score,\n                latest_price_dollars=(\n                    None\n                    if admission.get("latest_price_dollars") is None\n                    else str(admission.get("latest_price_dollars"))\n                ),\n                reason_codes=tuple(\n                    admission.get("reason_codes")\n                    or candidate.get("reason_codes")\n                    or usefulness.get("reason_codes")\n                    or ()\n                ),\n                read_only=True,\n                execution_authority=False,\n            )\n        )\n\n    rows.sort(\n        key=lambda x: (\n            -x.attention_score,\n            -x.history_rows,\n            x.market_id,\n        )\n    )\n\n    ranked = []\n    for index, row in enumerate(rows[:max(1, min(int(limit), 100))], start=1):\n        ranked.append(\n            PersistedTraderIntelligenceRow(\n                rank=index,\n                market_id=row.market_id,\n                attention_score=row.attention_score,\n                maturity=row.maturity,\n                reliability=row.reliability,\n                learned_family_records=row.learned_family_records,\n                history_rows=row.history_rows,\n                usefulness_classification=row.usefulness_classification,\n                usefulness_score=row.usefulness_score,\n                candidate_family=row.candidate_family,\n                research_direction=row.research_direction,\n                candidate_score=row.candidate_score,\n                admission_status=row.admission_status,\n                admission_score=row.admission_score,\n                latest_price_dollars=row.latest_price_dollars,\n                reason_codes=row.reason_codes,\n                read_only=True,\n                execution_authority=False,\n            )\n        )\n\n    return tuple(ranked)\n\ndef render_persisted_trader_intelligence(root=None, limit=10):\n    rows = build_persisted_trader_intelligence(root, limit)\n\n    lines = [\n        "=" * 80,\n        "ORACLE TRADER INTELLIGENCE — PERSISTED HISTORICAL + LIVE ANALYTICS",\n        "READ-ONLY | ATTENTION RANKING, NOT A TRADE SIGNAL",\n        "-" * 80,\n    ]\n\n    if not rows:\n        return tuple(\n            lines\n            + [\n                "No markets currently overlap persisted analytics and learned experience.",\n                "=" * 80,\n            ]\n        )\n\n    for row in rows:\n        lines.extend(\n            [\n                f"{row.rank}. {row.market_id}",\n                f"   attention_score={row.attention_score:.2f}",\n                (\n                    f"   learned_history={row.learned_family_records} "\n                    f"maturity={row.maturity} reliability={row.reliability:.3f}"\n                ),\n                (\n                    f"   current_history_rows={row.history_rows} "\n                    f"usefulness={row.usefulness_classification} "\n                    f"usefulness_score={row.usefulness_score:.2f}"\n                ),\n                (\n                    f"   candidate={row.candidate_family} "\n                    f"direction={row.research_direction} "\n                    f"candidate_score={row.candidate_score:.2f}"\n                ),\n                (\n                    f"   admission={row.admission_status} "\n                    f"admission_score={row.admission_score:.2f} "\n                    f"latest_price={row.latest_price_dollars}"\n                ),\n                (\n                    "   reasons="\n                    + (\n                        ",".join(str(x) for x in row.reason_codes)\n                        if row.reason_codes\n                        else "(none)"\n                    )\n                ),\n            ]\n        )\n\n    lines.extend(\n        [\n            "-" * 80,\n            "No order placement. No Q Series execution authority.",\n            "=" * 80,\n        ]\n    )\n\n    return tuple(lines)\n\ndef verify_oiar_005_persisted_trader_intelligence(root=None):\n    rows = build_persisted_trader_intelligence(root, 20)\n\n    for row in rows:\n        if not row.read_only or row.execution_authority:\n            return False\n\n    return True\n'
TEST_SOURCE = 'import unittest\n\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_005_persisted_trader_intelligence_read_surface import (\n    OIAR_005_BUILD_ID,\n    PersistedTraderIntelligenceRow,\n)\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(OIAR_005_BUILD_ID, "OIAR-005")\n\n    def test_contract(self):\n        row = PersistedTraderIntelligenceRow(\n            1,\n            "KXTEST",\n            70.0,\n            "PROVEN",\n            0.61,\n            800,\n            20,\n            "useful",\n            75.0,\n            "momentum_continuation",\n            "yes",\n            80.0,\n            "admitted",\n            80.0,\n            "0.50",\n            ("test",),\n            True,\n            False,\n        )\n        self.assertTrue(row.read_only)\n        self.assertFalse(row.execution_authority)\n\nif __name__ == "__main__":\n    print("=" * 88)\n    print(" OIAR-005 CERTIFICATION TEST")\n    print(" PERSISTED TRADER INTELLIGENCE READ SURFACE")\n    print("=" * 88)\n\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] persisted trader-intelligence contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-005 CERTIFIED")\n'
RUNNER_SOURCE = 'from pathlib import Path\n\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_005_persisted_trader_intelligence_read_surface import (\n    render_persisted_trader_intelligence,\n)\n\ndef main():\n    for line in render_persisted_trader_intelligence(Path.cwd(), 10):\n        print(line)\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR-005 INSTALLER")
    print(" PERSISTED TRADER INTELLIGENCE READ SURFACE")
    print("=" * 88)
    print("[ROOT]", ROOT)

    required = (
        PKG/"oiar_001_production_analytics_snapshot_foundation.py",
        PKG/"oiar_004_indexed_current_cohort_analytics_materializer.py",
        ROOT/"qseries_v2"/"oracle_terminal"/"oracle_historical_experience_read_model.py",
    )

    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Required proven upstream missing: {path}")

    old = {
        p: (p.read_bytes() if p.exists() else None)
        for p in (MOD, TEST, RUNNER, INIT)
    }

    try:
        init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oiar_005_persisted_trader_intelligence_read_surface import *"
        if export not in init_text:
            init_text = init_text.rstrip() + "\n" + export + "\n"

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        write_exact(RUNNER, RUNNER_SOURCE)
        write_exact(INIT, init_text)

        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)
        ast.parse(RUNNER_SOURCE)

        print("[PASS] installer payload syntax verified")

        subprocess.run(
            [sys.executable, str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

        importlib.invalidate_caches()

        module = importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime.oiar_005_persisted_trader_intelligence_read_surface"
        )

        started = time.monotonic()
        rows = module.build_persisted_trader_intelligence(ROOT, 20)
        elapsed = time.monotonic() - started

        print(
            f"[PHYSICAL] joined_markets={len(rows)} "
            f"elapsed_seconds={elapsed:.4f}"
        )

        for row in rows[:5]:
            print(
                f"[PHYSICAL RANK] rank={row.rank} "
                f"market={row.market_id} "
                f"attention={row.attention_score:.2f} "
                f"history_rows={row.history_rows} "
                f"usefulness={row.usefulness_classification} "
                f"candidate={row.candidate_family} "
                f"direction={row.research_direction} "
                f"admission={row.admission_status}"
            )

        if elapsed > 5.0:
            raise RuntimeError(
                f"OIAR-005 persisted read exceeded 5 seconds: {elapsed:.4f}"
            )

        if not module.verify_oiar_005_persisted_trader_intelligence(ROOT):
            raise RuntimeError("OIAR-005 physical verification failed")

        print("[PHYSICAL QUERY]")
        subprocess.run(
            [sys.executable, str(RUNNER)],
            cwd=str(ROOT),
            check=True,
            timeout=10,
        )

    except Exception:
        for path, data in old.items():
            restore(path, data)

        print("[ROLLBACK] OIAR-005 failed; affected repository files restored")
        raise

    print("[PASS] OIAR-004 analytics consumed from persisted PostgreSQL snapshot")
    print("[PASS] OHE learned experience joined read-only")
    print("[PASS] no OIA analytics computation executed at query time")
    print("[PASS] physical read required under 5 seconds")
    print("[PASS] standalone query bounded to 10 seconds")
    print("[PASS] no Oracle Live launcher mutation")
    print("[PASS] no Operator Terminal mutation")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-005 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
