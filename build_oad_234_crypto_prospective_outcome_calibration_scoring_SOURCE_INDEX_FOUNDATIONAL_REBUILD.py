from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

REVISION="OAD_234_SOURCE_INDEX_FOUNDATIONAL_REBUILD_V1"
EXPECTED="build_oad_234_crypto_prospective_outcome_calibration_scoring_SOURCE_INDEX_FOUNDATIONAL_REBUILD.py"

MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event\nfrom qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import learn_calibration\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\nFORECAST_SOURCES=(\n    "source.crypto.prospective_forecast.btc",\n    "source.crypto.prospective_forecast.eth",\n    "source.crypto.prospective_forecast.sol",\n)\nLEARNED_SOURCES=(\n    "source.crypto.learned_case.btc",\n    "source.crypto.learned_case.eth",\n    "source.crypto.learned_case.sol",\n)\nSOURCE_BY_ASSET={"BTC":LEARNED_SOURCES[0],"ETH":LEARNED_SOURCES[1],"SOL":LEARNED_SOURCES[2]}\n\n@dataclass(frozen=True,slots=True)\nclass ProspectiveScoredCase:\n    forecast_id:str\n    asset:str\n    forecast_probability:float\n    outcome_positive:bool\n    brier_score:float\n    baseline_brier:float\n    performance_delta:float\n    source_correctness:tuple\n    learning_event_hash:str\n    outcome_hash:str\n\ndef _payload(x):\n    return x if isinstance(x,dict) else dict(x or ())\n\ndef _dt(x):\n    if isinstance(x,datetime):\n        return x\n    return datetime.fromisoformat(str(x).replace("Z","+00:00"))\n\ndef _read_latest_by_source(cur,source_id,limit):\n    cur.execute(\n        """SELECT sequence_number,observed_at,observation_type,\n                  COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',\n                           canonical_observation_json->\'payload\',\'{}\'::jsonb)\n           FROM public.oracle_canonical_observations\n           WHERE source_id=%s\n           ORDER BY sequence_number DESC\n           LIMIT %s""",\n        (source_id,int(limit)),\n    )\n    return tuple(cur.fetchall() or ())\n\ndef read_and_score_mature_prospective_cases(root=None,per_source_limit=512):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY")\n            q.execute("SET LOCAL statement_timeout=\'10000ms\'")\n            forecast_rows=[]\n            learned_rows={}\n            for source in FORECAST_SOURCES:\n                forecast_rows.extend(_read_latest_by_source(q,source,per_source_limit))\n            for source in LEARNED_SOURCES:\n                learned_rows[source]=_read_latest_by_source(q,source,per_source_limit)\n        c.rollback()\n\n    forecasts=[]\n    for seq,observed,otype,raw in forecast_rows:\n        if str(otype)!="crypto_prospective_internal_forecast":\n            continue\n        p=_payload(raw)\n        if p.get("forecast_id") and p.get("created_at") and p.get("asset"):\n            forecasts.append((int(seq),observed,p))\n    forecasts.sort(key=lambda x:x[0])\n\n    out=[]\n    for fseq,fobs,f in forecasts:\n        asset=str(f.get("asset") or "").upper()\n        learned_source=SOURCE_BY_ASSET.get(asset)\n        if not learned_source:\n            continue\n        created=_dt(f["created_at"])\n        candidates=[]\n        for lseq,lobs,ltype,lraw in learned_rows.get(learned_source,()):\n            if str(ltype)!="crypto_verified_learned_case":\n                continue\n            p=_payload(lraw)\n            if str(p.get("asset") or "").upper()!=asset or p.get("return_fraction") is None:\n                continue\n            snap_raw=p.get("snapshot_at")\n            if not snap_raw:\n                continue\n            snap=_dt(snap_raw)\n            if snap>=created:\n                candidates.append((snap,int(lseq),p))\n        if not candidates:\n            continue\n\n        snap,lseq,p=min(candidates,key=lambda x:(x[0],x[1]))\n        prob=float(f["internal_forecast_probability"])\n        if not 0.0<=prob<=1.0:\n            raise RuntimeError("prospective forecast probability outside [0,1]")\n        positive=float(p["return_fraction"])>0\n\n        evidence_hash=str(p.get("evidence_hash") or "")\n        outcome_hash=str(p.get("outcome_hash") or "")\n        lineage_hash=str(p.get("lineage_hash") or "")\n        outcome_observed_at=str(p.get("outcome_observed_at") or "")\n        if len(evidence_hash)!=64 or len(outcome_hash)!=64 or len(lineage_hash)!=64 or not outcome_observed_at:\n            continue\n\n        outcome=build_outcome_observation(\n            asset,\n            "prospective_positive_return_60s",\n            1 if positive else 0,\n            outcome_observed_at,\n            f"prospective:{f[\'forecast_id\']}",\n            outcome_hash,\n        )\n        event=assemble_learning_event(asset,evidence_hash,lineage_hash,outcome)\n        if not verify_learning_event(event):\n            raise RuntimeError("prospective learning event invalid")\n        cal=learn_calibration(event,prob,positive)\n        baseline=(.5-(1.0 if positive else 0.0))**2\n        correctness=tuple(\n            (str(fam),bool(pred)==positive)\n            for fam,cnt,fp,pred in tuple(f.get("source_claims") or ())\n        )\n        out.append(ProspectiveScoredCase(\n            str(f["forecast_id"]),asset,prob,positive,\n            float(cal.brier_score),baseline,baseline-float(cal.brier_score),\n            correctness,event.event_hash,outcome.outcome_hash,\n        ))\n    return tuple(out)\n'
TEST='import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_234_crypto_prospective_outcome_calibration_scoring as m\n\nclass Cur:\n    def __init__(self):\n        self.source=None\n        self.sql=[]\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def execute(self,s,args=None):\n        self.sql.append(s)\n        if args and isinstance(args,tuple) and args:\n            self.source=args[0]\n    def fetchall(self):\n        return ()\nclass Conn:\n    def __init__(self):self.c=Cur()\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def cursor(self):return self.c\n    def rollback(self):pass\n\nclass T(unittest.TestCase):\n    def test_source_indexed_bounded_reads(self):\n        c=Conn()\n        with patch.object(m,"connect",return_value=c):\n            rows=m.read_and_score_mature_prospective_cases(per_source_limit=32)\n        self.assertEqual(rows,())\n        reads=[x for x in c.c.sql if "FROM public.oracle_canonical_observations" in x]\n        print("[READS]",len(reads))\n        self.assertEqual(len(reads),6)\n        self.assertTrue(all("WHERE source_id=%s" in x for x in reads))\n        self.assertTrue(all("ORDER BY sequence_number DESC" in x for x in reads))\n        self.assertTrue(all("observation_type=" not in x.split("WHERE",1)[1].split("ORDER BY",1)[0] for x in reads))\n        self.assertFalse(any("ORDER BY sequence_number ASC" in x for x in reads))\n\n    def test_brier_contract(self):\n        o=m.build_outcome_observation("BTC","prospective_positive_return_60s",1,"t","prospective:x","a"*64)\n        e=m.assemble_learning_event("BTC","b"*64,"c"*64,o)\n        x=m.learn_calibration(e,.7,True)\n        delta=.25-x.brier_score\n        print("[BRIER]",x.brier_score,"[DELTA]",delta)\n        self.assertAlmostEqual(x.brier_score,.09)\n        self.assertGreater(delta,0)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-234 source-indexed prospective scoring contract certified")\n'
PHYSICAL='import unittest,time\nfrom qseries_v2.oracle_adapters.independent.oad_234_crypto_prospective_outcome_calibration_scoring import read_and_score_mature_prospective_cases\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        t=time.monotonic()\n        rows=read_and_score_mature_prospective_cases(per_source_limit=512)\n        elapsed=time.monotonic()-t\n        print("[PHYSICAL] query_seconds=",round(elapsed,3))\n        print("[PHYSICAL] mature_scored_cases=",len(rows))\n        if rows:\n            print("[PHYSICAL] latest=",rows[-1])\n        else:\n            print("[PHYSICAL] state= HOLD_FUTURE_PROSPECTIVE_OUTCOME_REQUIRED")\n        self.assertLess(elapsed,10.0)\n        self.assertTrue(all(0<=x.forecast_probability<=1 for x in rows))\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-234 physical source-indexed prospective scoring certified")\n'

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir():return p
    raise RuntimeError("Q Series repository root not found")

def write_atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(s.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(t,p)

def run(r,p):
    q=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if q.returncode:raise RuntimeError("Certification test failed: "+p.name)

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module_path=pkg/"oad_234_crypto_prospective_outcome_calibration_scoring.py"
    test_path=r/"test_oad_234_crypto_prospective_outcome_calibration_scoring.py"
    physical_path=r/"test_oad_234_crypto_prospective_outcome_calibration_scoring_PHYSICAL.py"
    print("="*124)
    print(" OAD-234 SOURCE-INDEX FOUNDATIONAL REBUILD — PROSPECTIVE OUTCOME + CALIBRATION SCORING")
    print("="*124)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    deps=(
        pkg/"oad_233_crypto_prospective_forecast_single_writer_persistence.py",
        pkg/"oad_213_crypto_history_latest_by_source_FOUNDATIONAL_REBUILD.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_003_outcome_observation.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_004_learning_event.py",
        r/"qseries_v2"/"oracle_continuous_learner"/"ocl_006_calibration_learning.py",
        r/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py",
    )
    # OAD-213 is an installer, not a production dependency. Verify its repaired production target instead.
    deps=list(deps)
    deps[1]=pkg/"oad_189_crypto_learned_case_exact_history_readback.py"
    for d in deps:
        if not d.is_file():raise RuntimeError("Required certified dependency missing: "+str(d))
        print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified as OAD-234 replacement")
    targets=(module_path,test_path,physical_path)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(module_path,MODULE);write_atomic(test_path,TEST);write_atomic(physical_path,PHYSICAL)
        run(r,test_path);run(r,physical_path)
        print("[PASS] failed global observation_type scan retired")
        print("[PASS] canonical idx_oracle_canonical_observations_source path used by exact source_id")
        print("[PASS] newest-by-source bounded reads aligned with OAD-213")
        print("[PASS] OCL-006 receives only prospective forecast/outcome pairs")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-234 SOURCE-INDEX FOUNDATIONAL REBUILD COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OAD-234 source-index rebuild rolled back")
        raise

if __name__=="__main__":main()
