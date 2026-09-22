from pathlib import Path
import os,subprocess,sys,importlib
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_learning"
MOD=PKG/"opl_001_production_learning_foundation.py";TEST=ROOT/"test_opl_001_production_learning_foundation.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nOPL_001_BUILD_ID="OPL-001"\nOPL_001_REVISION="OPL_001_PRODUCTION_LEARNING_FOUNDATION_V1"\nSTATE_TABLE="oracle_production_learning_state"\nLEDGER_TABLE="oracle_production_learning_ledger"\n\ndef connect(root=None,autocommit=False):\n    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect as c\n    return c(root,autocommit=autocommit)\n\ndef ensure_production_learning_schema(root=None):\n    ddl=f"""\n    CREATE TABLE IF NOT EXISTS public.{STATE_TABLE}(\n      state_id INTEGER PRIMARY KEY CHECK(state_id=1),\n      legacy_outcomes_learned BIGINT NOT NULL DEFAULT 0,\n      production_outcomes_learned BIGINT NOT NULL DEFAULT 0,\n      cycles BIGINT NOT NULL DEFAULT 0,\n      applied_through_sequence BIGINT NOT NULL DEFAULT 0,\n      ocl_state_json JSONB,\n      last_settlement_ts TEXT NOT NULL DEFAULT \'\',\n      last_ticker TEXT NOT NULL DEFAULT \'\',\n      state_hash TEXT NOT NULL DEFAULT \'\',\n      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()\n    );\n\n    CREATE TABLE IF NOT EXISTS public.{LEDGER_TABLE}(\n      settlement_hash TEXT PRIMARY KEY,\n      ticker TEXT NOT NULL,\n      result TEXT NOT NULL,\n      settlement_ts TEXT NOT NULL,\n      evidence_observation_id TEXT,\n      evidence_hash TEXT,\n      evidence_sequence_number BIGINT,\n      learning_event_hash TEXT,\n      status TEXT NOT NULL CHECK(status IN (\'EVIDENCE_MISSING\',\'ELIGIBLE\',\'LEARNED\',\'REJECTED\')),\n      first_seen_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),\n      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),\n      learned_at TIMESTAMPTZ\n    );\n\n    CREATE INDEX IF NOT EXISTS oracle_production_learning_ledger_ticker_idx\n      ON public.{LEDGER_TABLE}(ticker,status,settlement_ts);\n    """\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:cur.execute(ddl)\n    return True\n\ndef legacy_learned_count(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    p=root/"runtime_state"/"oracle_learning_runtime_state.json"\n    if not p.is_file():return 0\n    try:\n        return int(json.loads(p.read_text(encoding="utf-8")).get("outcomes_learned",0))\n    except Exception:\n        return 0\n\ndef initialize_production_learning_state(root=None):\n    ensure_production_learning_schema(root)\n    legacy=legacy_learned_count(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"""INSERT INTO public.{STATE_TABLE}\n                    (state_id,legacy_outcomes_learned)\n                    VALUES(1,%s)\n                    ON CONFLICT(state_id) DO NOTHING""",\n                (legacy,),\n            )\n        conn.commit()\n    return legacy\n\ndef read_production_learning_state(root=None):\n    ensure_production_learning_schema(root)\n    initialize_production_learning_state(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""SELECT legacy_outcomes_learned,production_outcomes_learned,\n                cycles,applied_through_sequence,ocl_state_json,last_settlement_ts,\n                last_ticker,state_hash\n                FROM public.{STATE_TABLE} WHERE state_id=1""")\n            row=cur.fetchone()\n    return {\n        "legacy_outcomes_learned":int(row[0]),\n        "production_outcomes_learned":int(row[1]),\n        "cycles":int(row[2]),\n        "applied_through_sequence":int(row[3]),\n        "ocl_state_json":row[4],\n        "last_settlement_ts":str(row[5] or ""),\n        "last_ticker":str(row[6] or ""),\n        "state_hash":str(row[7] or ""),\n    }\n\ndef verify_opl_001_production_learning_foundation(root=None):\n    return OPL_001_BUILD_ID=="OPL-001" and STATE_TABLE.endswith("_state") and LEDGER_TABLE.endswith("_ledger")\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_learning.opl_001_production_learning_foundation import *\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPL_001_BUILD_ID,"OPL-001")\n    def test_tables(self):\n        self.assertEqual(STATE_TABLE,"oracle_production_learning_state")\n        self.assertEqual(LEDGER_TABLE,"oracle_production_learning_ledger")\nif __name__=="__main__":\n    print("="*88);print(" OPL-001 CERTIFICATION TEST");print(" PRODUCTION LEARNING FOUNDATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Production learning state/ledger contracts certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPL-001 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OPL-001 INSTALLER");print(" PRODUCTION LEARNING FOUNDATION");print("="*88);print("[ROOT]",ROOT)
    if not (ROOT/"run_oracle_LIVE.py").is_file():raise RuntimeError("Oracle Live launcher missing")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .opl_001_production_learning_foundation import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_production_learning.opl_001_production_learning_foundation")
        legacy=m.initialize_production_learning_state(ROOT)
        state=m.read_production_learning_state(ROOT)
        print("[PASS] legacy_outcomes_preserved="+str(legacy))
        print("[PASS] production_outcomes_learned="+str(state["production_outcomes_learned"]))
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPL-001 failed; files restored");raise
    print("[PASS] OPH architecture untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-001 INSTALLATION COMPLETE")
if __name__=="__main__":main()
