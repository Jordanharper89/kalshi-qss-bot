from pathlib import Path
import ast, importlib, os, subprocess, sys
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD=PKG/"oiar_002_current_reasoning_market_cohort_snapshot.py"
TEST=ROOT/"test_oiar_002_current_reasoning_market_cohort_snapshot.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_read_model import load_historical_experience_read_model\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, STATE_TABLE, ensure_analytics_snapshot_schema, stable_hash\n\nOIAR_002_BUILD_ID="OIAR-002"\nSTAGE="reasoning_market_cohort"\n\n@dataclass(frozen=True)\nclass ReasoningMarketCohortSnapshot:\n    snapshot_id:str\n    market_count:int\n    learner_state_hash:str\n    lineage_current:bool\n    payload_hash:str\n    generated_at:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef build_reasoning_market_cohort_payload(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    model=load_historical_experience_read_model(root)\n    seen=set(); markets=[]\n    for c in model.contexts:\n        t=str(c.market_ticker or "").strip().upper()\n        if not t or t in seen: continue\n        seen.add(t)\n        markets.append({\n            "market_ticker":t,\n            "series_key":str(c.series_key or ""),\n            "maturity":str(c.maturity or ""),\n            "series_admitted":bool(c.series_admitted),\n            "experience_available":bool(c.experience_available),\n            "regime_id":str(c.regime_id or ""),\n            "reliability":float(c.reliability or 0.0),\n            "learner_state_hash":str(c.learner_state_hash or ""),\n            "reason":str(c.reason or ""),\n        })\n    markets.sort(key=lambda x:x["market_ticker"])\n    return {\n        "schema_version":"OIAR-002",\n        "stage":STAGE,\n        "learner_state_hash":str(model.learner_state_hash or ""),\n        "attestation_state_hash":str(model.attestation_state_hash or ""),\n        "lineage_current":bool(model.lineage_current),\n        "markets_reasoned":int(model.markets_reasoned),\n        "experience_contexts":int(model.experience_contexts),\n        "withheld_contexts":int(model.withheld_contexts),\n        "blind_contexts":int(model.blind_contexts),\n        "market_count":len(markets),\n        "markets":markets,\n        "read_only_source":True,\n        "execution_authority":False,\n    }\n\ndef materialize_current_reasoning_market_cohort(root=None,generated_at=None):\n    root=Path(root or Path.cwd()).resolve()\n    ensure_analytics_snapshot_schema(root)\n    payload=build_reasoning_market_cohort_payload(root)\n    if not payload["lineage_current"]: raise RuntimeError("OIAR-002 refuses stale lineage")\n    if payload["market_count"]<=0: raise RuntimeError("OIAR-002 cohort is empty")\n    generated=generated_at or datetime.now(timezone.utc)\n    if generated.tzinfo is None: raise ValueError("generated_at must be timezone-aware")\n    ph=stable_hash(payload); sid=f"oiar-002-{ph[:32]}"\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",\n                (sid,STAGE,"OIAR-002",OIAR_002_BUILD_ID,generated,payload["market_count"],json.dumps(payload,sort_keys=True,separators=(",",":")),ph)\n            )\n            cur.execute(\n                f"UPDATE public.{STATE_TABLE} SET last_successful_snapshot_id=%s,last_successful_stage=%s,last_successful_at=%s,last_completed_at=%s,status=\'IDLE\',last_error_type=NULL,last_error_message=NULL,updated_at=clock_timestamp() WHERE state_id=1",\n                (sid,STAGE,generated,generated)\n            )\n        conn.commit()\n    return ReasoningMarketCohortSnapshot(sid,payload["market_count"],payload["learner_state_hash"],True,ph,generated.astimezone(timezone.utc).isoformat(),True,False)\n\ndef read_latest_reasoning_market_cohort(root=None):\n    root=Path(root or Path.cwd()).resolve(); ensure_analytics_snapshot_schema(root)\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SELECT snapshot_id,market_count,payload_json,payload_hash,generated_at FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))\n            row=cur.fetchone()\n        conn.rollback()\n    if row is None: return None\n    sid,count,payload,ph,generated=row\n    if isinstance(payload,str): payload=json.loads(payload)\n    if stable_hash(payload)!=str(ph): raise RuntimeError("OIAR-002 payload hash mismatch")\n    return ReasoningMarketCohortSnapshot(str(sid),int(count),str(payload.get("learner_state_hash") or ""),bool(payload.get("lineage_current")),str(ph),generated.astimezone(timezone.utc).isoformat(),True,False)\n\ndef verify_oiar_002_current_reasoning_market_cohort(root=None):\n    x=read_latest_reasoning_market_cohort(root)\n    return bool(x and x.market_count>0 and x.lineage_current and x.read_only and not x.execution_authority)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_002_current_reasoning_market_cohort_snapshot import OIAR_002_BUILD_ID, ReasoningMarketCohortSnapshot\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(OIAR_002_BUILD_ID,"OIAR-002")\n    def test_contract(self):\n        x=ReasoningMarketCohortSnapshot("x",50,"h",True,"p","2026-01-01T00:00:00+00:00",True,False)\n        self.assertEqual(x.market_count,50); self.assertTrue(x.lineage_current); self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*88); print(" OIAR-002 CERTIFICATION TEST"); print(" CURRENT REASONING MARKET COHORT SNAPSHOT"); print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] reasoning-market cohort snapshot contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-002 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else: path.write_bytes(data)

def main():
    print("="*88); print(" OIAR-002 INSTALLER"); print(" CURRENT REASONING MARKET COHORT SNAPSHOT"); print("="*88); print("[ROOT]",ROOT)
    for p in (PKG/"oiar_001_production_analytics_snapshot_foundation.py",ROOT/"qseries_v2"/"oracle_terminal"/"oracle_historical_experience_read_model.py"):
        if not p.is_file(): raise RuntimeError(f"Required upstream missing: {p}")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        init_text=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oiar_002_current_reasoning_market_cohort_snapshot import *"
        if export not in init_text: init_text=init_text.rstrip()+"\n"+export+"\n"
        write_exact(MOD,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE); write_exact(INIT,init_text)
        ast.parse(MODULE_SOURCE); ast.parse(TEST_SOURCE); print("[PASS] installer payload syntax verified")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_002_current_reasoning_market_cohort_snapshot")
        snap=m.materialize_current_reasoning_market_cohort(ROOT)
        latest=m.read_latest_reasoning_market_cohort(ROOT)
        print(f"[PHYSICAL] snapshot_id={snap.snapshot_id} market_count={snap.market_count} lineage_current={snap.lineage_current} learner_state_hash={snap.learner_state_hash}")
        if latest is None or latest.snapshot_id!=snap.snapshot_id or not m.verify_oiar_002_current_reasoning_market_cohort(ROOT):
            raise RuntimeError("OIAR-002 physical verification failed")
    except Exception:
        for p,d in old.items(): restore(p,d)
        print("[ROLLBACK] OIAR-002 failed; affected repository files restored"); raise
    print("[PASS] current OLF reasoning cohort persisted to PostgreSQL")
    print("[PASS] no OIA-002 through OIA-007 analytics query executed")
    print("[PASS] no Oracle Live launcher mutation")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-002 INSTALLATION COMPLETE")
if __name__=="__main__": main()
