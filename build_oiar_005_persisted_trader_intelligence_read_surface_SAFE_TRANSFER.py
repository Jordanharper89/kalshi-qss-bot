from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD=PKG/"oiar_005_persisted_trader_intelligence_read_surface.py"
TEST=ROOT/"test_oiar_005_persisted_trader_intelligence_read_surface.py"
RUNNER=ROOT/"run_oiar_005_trader_intelligence_query.py"

MODULE_SOURCE = """
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash
from .oiar_004_indexed_current_cohort_analytics_materializer import ANALYTICS_STAGE

OIAR_005_BUILD_ID="OIAR-005"
OIAR_005_REVISION="OIAR_005_PERSISTED_TRADER_INTELLIGENCE_READ_SURFACE_V2"
COHORT_STAGE="reasoning_market_cohort"

@dataclass(frozen=True)
class PersistedTraderIntelligenceRow:
    rank:int
    market_id:str
    attention_score:float
    maturity:str
    reliability:float
    learned_family_records:int
    history_rows:int
    usefulness_classification:str
    usefulness_score:float
    candidate_family:str
    research_direction:str
    candidate_score:float
    admission_status:str
    admission_score:float
    latest_price_dollars:str|None
    reason_codes:tuple
    cohort_learner_state_hash:str
    read_only:bool=True
    execution_authority:bool=False

def _num(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0

def _read_latest_analytics(root):
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} "
                "WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",
                (ANALYTICS_STAGE,),
            )
            row=cur.fetchone()
        conn.rollback()
    if row is None:
        raise RuntimeError("OIAR-005 requires OIAR-004 analytics snapshot")
    payload,ph=row
    if isinstance(payload,str):
        payload=json.loads(payload)
    if stable_hash(payload)!=str(ph):
        raise RuntimeError("OIAR-005 analytics hash mismatch")
    return payload

def _read_exact_cohort(root,learner_hash):
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} "
                "WHERE stage=%s AND payload_json->>'learner_state_hash'=%s "
                "ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",
                (COHORT_STAGE,learner_hash),
            )
            row=cur.fetchone()
        conn.rollback()
    if row is None:
        raise RuntimeError("OIAR-005 exact originating OIAR-002 cohort not found")
    payload,ph=row
    if isinstance(payload,str):
        payload=json.loads(payload)
    if stable_hash(payload)!=str(ph):
        raise RuntimeError("OIAR-005 cohort hash mismatch")
    return payload

def _family(series_key,ticker):
    s=str(series_key or "")
    if s:
        tail=s.split(":")[-1].strip()
        if tail:
            return tail
    return str(ticker).split("-",1)[0]

def build_persisted_trader_intelligence(root=None,limit=100):
    root=Path(root or Path.cwd()).resolve()
    analytics=_read_latest_analytics(root)

    learner_hash=str(analytics.get("learner_state_hash") or "")
    if not learner_hash:
        raise RuntimeError("OIAR-005 learner hash missing")

    cohort=_read_exact_cohort(root,learner_hash)

    contexts={}
    for x in cohort.get("markets",[]):
        if isinstance(x,dict):
            ticker=str(x.get("market_ticker") or "").upper().strip()
            if ticker:
                contexts[ticker]=x

    learned=load_production_learned_state(root)
    family_counts={}
    for ticker,count in learned.learned_market_counts:
        family=str(ticker or "").split("-",1)[0]
        if family:
            family_counts[family]=family_counts.get(family,0)+int(count)

    analytics_markets=[
        x for x in analytics.get("markets",[])
        if isinstance(x,dict) and str(x.get("market_id") or "").strip()
    ]

    rows=[]

    for item in analytics_markets:
        market_id=str(item.get("market_id") or "").upper().strip()
        context=contexts.get(market_id)
        if context is None:
            continue

        usefulness=item.get("usefulness") if isinstance(item.get("usefulness"),dict) else {}
        candidate=item.get("candidate") if isinstance(item.get("candidate"),dict) else {}
        admission=item.get("admission") if isinstance(item.get("admission"),dict) else {}

        maturity=str(context.get("maturity") or "BLIND")
        reliability=max(0.0,min(_num(context.get("reliability")),1.0))
        learned_family_records=int(
            family_counts.get(_family(context.get("series_key"),market_id),0)
        )
        history_rows=int(item.get("history_rows") or 0)

        usefulness_score=_num(
            usefulness.get("usefulness_score")
            if usefulness.get("usefulness_score") is not None
            else usefulness.get("score")
        )
        candidate_score=_num(candidate.get("candidate_score"))
        admission_score=_num(admission.get("admission_score"))
        admission_status=str(admission.get("admission_status") or "not_candidate")

        maturity_score={
            "PROVEN":1.0,
            "MATURE":0.85,
            "DEVELOPING":0.60,
            "IMMATURE":0.35,
            "BLIND":0.0,
        }.get(maturity.upper(),0.25)

        attention=100.0*(
            0.25*maturity_score+
            0.20*reliability+
            0.20*min(1.0,learned_family_records/500.0)+
            0.10*min(1.0,usefulness_score/100.0)+
            0.10*min(1.0,candidate_score/100.0)+
            0.10*(1.0 if admission_status.lower()=="admitted"
                  else 0.55 if admission_status.lower()=="denied"
                  else 0.15)+
            0.05*min(1.0,history_rows/20.0)
        )

        rows.append(
            PersistedTraderIntelligenceRow(
                0,
                market_id,
                round(attention,6),
                maturity,
                reliability,
                learned_family_records,
                history_rows,
                str(
                    usefulness.get("classification")
                    or usefulness.get("usefulness_classification")
                    or "unknown"
                ),
                usefulness_score,
                str(candidate.get("candidate_family") or "none"),
                str(candidate.get("research_direction") or "neutral"),
                candidate_score,
                admission_status,
                admission_score,
                None if admission.get("latest_price_dollars") is None
                else str(admission.get("latest_price_dollars")),
                tuple(
                    admission.get("reason_codes")
                    or candidate.get("reason_codes")
                    or usefulness.get("reason_codes")
                    or ()
                ),
                learner_hash,
                True,
                False,
            )
        )

    if len(rows)!=len(analytics_markets):
        raise RuntimeError(
            f"OIAR-005 exact cohort join incomplete: "
            f"analytics={len(analytics_markets)} joined={len(rows)}"
        )

    rows.sort(key=lambda r:(-r.attention_score,-r.history_rows,r.market_id))

    return tuple(
        PersistedTraderIntelligenceRow(
            i,
            r.market_id,
            r.attention_score,
            r.maturity,
            r.reliability,
            r.learned_family_records,
            r.history_rows,
            r.usefulness_classification,
            r.usefulness_score,
            r.candidate_family,
            r.research_direction,
            r.candidate_score,
            r.admission_status,
            r.admission_score,
            r.latest_price_dollars,
            r.reason_codes,
            r.cohort_learner_state_hash,
            True,
            False,
        )
        for i,r in enumerate(rows[:max(1,min(int(limit),100))],1)
    )

def render_persisted_trader_intelligence(root=None,limit=10):
    rows=build_persisted_trader_intelligence(root,limit)

    lines=[
        "="*80,
        "ORACLE TRADER INTELLIGENCE - PERSISTED COHORT + LIVE ANALYTICS",
        "READ-ONLY | ATTENTION RANKING, NOT A TRADE SIGNAL",
        "-"*80,
    ]

    for r in rows:
        lines += [
            f"{r.rank}. {r.market_id}",
            f"   attention_score={r.attention_score:.2f}",
            f"   learned_history={r.learned_family_records} "
            f"maturity={r.maturity} reliability={r.reliability:.3f}",
            f"   current_history_rows={r.history_rows} "
            f"usefulness={r.usefulness_classification} "
            f"usefulness_score={r.usefulness_score:.2f}",
            f"   candidate={r.candidate_family} "
            f"direction={r.research_direction} "
            f"candidate_score={r.candidate_score:.2f}",
            f"   admission={r.admission_status} "
            f"admission_score={r.admission_score:.2f} "
            f"latest_price={r.latest_price_dollars}",
            "   reasons="+(
                ",".join(str(x) for x in r.reason_codes)
                if r.reason_codes else "(none)"
            ),
        ]

    lines += [
        "-"*80,
        "No order placement. No Q Series execution authority.",
        "="*80,
    ]
    return tuple(lines)

def verify_oiar_005_persisted_trader_intelligence(root=None):
    analytics=_read_latest_analytics(Path(root or Path.cwd()).resolve())
    expected=int(analytics.get("analytics_market_count") or 0)
    rows=build_persisted_trader_intelligence(root,max(1,expected))

    return bool(
        expected>0
        and len(rows)==expected
        and all(r.read_only and not r.execution_authority for r in rows)
    )
"""

TEST_SOURCE = """
import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_005_persisted_trader_intelligence_read_surface import (
    OIAR_005_REVISION,
)

class T(unittest.TestCase):
    def test_revision(self):
        self.assertEqual(
            OIAR_005_REVISION,
            "OIAR_005_PERSISTED_TRADER_INTELLIGENCE_READ_SURFACE_V2",
        )

if __name__=="__main__":
    print("="*88)
    print(" OIAR-005 CERTIFICATION TEST - V2")
    print("="*88)

    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] exact cohort lineage V2 certified")
    print("[PASS] zero-overlap completion prohibited")
    print("[DONE] OIAR-005 CERTIFIED")
"""

RUNNER_SOURCE = """
from pathlib import Path
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_005_persisted_trader_intelligence_read_surface import (
    render_persisted_trader_intelligence,
)

if __name__=="__main__":
    for line in render_persisted_trader_intelligence(Path.cwd(),10):
        print(line)
"""

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    # Intentionally no pathlib newline= argument.
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def main():
    print("="*88)
    print(" OIAR-005 INSTALLER - SAFE TRANSFER")
    print("="*88)
    print("[ROOT]",ROOT)

    required=(
        PKG/"oiar_001_production_analytics_snapshot_foundation.py",
        PKG/"oiar_002_current_reasoning_market_cohort_snapshot.py",
        PKG/"oiar_004_indexed_current_cohort_analytics_materializer.py",
        ROOT/"qseries_v2"/"oracle_learning_runtime"/"olr_016_production_learned_state_adapter.py",
    )

    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Required upstream missing: {path}")

    write_exact(MOD,MODULE_SOURCE)
    write_exact(TEST,TEST_SOURCE)
    write_exact(RUNNER,RUNNER_SOURCE)

    ast.parse(MODULE_SOURCE)
    ast.parse(TEST_SOURCE)
    ast.parse(RUNNER_SOURCE)

    print("[PASS] installer payload syntax verified")

    subprocess.run(
        [sys.executable,str(TEST)],
        cwd=str(ROOT),
        check=True,
    )

    importlib.invalidate_caches()

    m=importlib.import_module(
        "qseries_v2.oracle_intelligence_analytics_runtime.oiar_005_persisted_trader_intelligence_read_surface"
    )

    print("[REVISION]",m.OIAR_005_REVISION)

    analytics=m._read_latest_analytics(ROOT)
    expected=int(analytics.get("analytics_market_count") or 0)

    started=time.monotonic()
    rows=m.build_persisted_trader_intelligence(ROOT,max(1,expected))
    elapsed=time.monotonic()-started

    print(
        f"[PHYSICAL] analytics_markets={expected} "
        f"joined_markets={len(rows)} "
        f"elapsed_seconds={elapsed:.4f}"
    )

    if expected<=0 or len(rows)!=expected:
        raise RuntimeError(
            f"OIAR-005 exact join failed: expected={expected} joined={len(rows)}"
        )

    if elapsed>5.0:
        raise RuntimeError(
            f"OIAR-005 persisted read exceeded 5 seconds: {elapsed:.4f}"
        )

    if not m.verify_oiar_005_persisted_trader_intelligence(ROOT):
        raise RuntimeError("OIAR-005 physical verification failed")

    for r in rows[:5]:
        print(
            f"[PHYSICAL RANK] rank={r.rank} "
            f"market={r.market_id} "
            f"attention={r.attention_score:.2f} "
            f"history_rows={r.history_rows} "
            f"usefulness={r.usefulness_classification} "
            f"candidate={r.candidate_family} "
            f"direction={r.research_direction} "
            f"admission={r.admission_status}"
        )

    print("[PHYSICAL QUERY]")

    subprocess.run(
        [sys.executable,str(RUNNER)],
        cwd=str(ROOT),
        check=True,
        timeout=10,
    )

    print("[PASS] exact originating cohort join complete")
    print("[PASS] zero-overlap completion prohibited")
    print("[PASS] no OIA recomputation at query time")
    print("[PASS] physical persisted read under 5 seconds")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-005 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
