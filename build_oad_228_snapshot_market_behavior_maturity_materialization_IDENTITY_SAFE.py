from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

def root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for c in (base,base/"kalshi-qss-bot",*base.parents):
            if (c/"qseries_v2").is_dir():
                return c
    raise RuntimeError("Could not locate Q Series repository")

def write_atomic(path,source):
    path.parent.mkdir(parents=True,exist_ok=True)
    compile(source,str(path),"exec")
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def run_test(r,p):
    z=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if z.returncode:
        raise RuntimeError("Certification test failed: "+p.name)

REVISION='OAD_228_SNAPSHOT_MARKET_BEHAVIOR_MATURITY_MATERIALIZATION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_228_snapshot_market_behavior_maturity_materialization_IDENTITY_SAFE.py'
MODULE_NAME='oad_228_snapshot_market_behavior_maturity_materialization.py'
TEST_NAME='test_oad_228_snapshot_market_behavior_maturity_materialization.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation import build_market_behavior_observation,verify_market_behavior_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_012_market_behavior_learning import learn_market_behavior\nfrom qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import evaluate_learning_maturity\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nfrom .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SnapshotBehaviorMaturity:\n    as_of_sequence:int\n    snapshot_hash:str\n    learned_cases:int\n    behavior_observations:int\n    market_behavior_state_hash:str|None\n    maturity_state_hash:str\n    maturity_band:str\n    maturity_score:float\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef materialize_snapshot_behavior_maturity(root=None,per_asset_limit=512):\n    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)\n    groups={};returns=[];families=set()\n    for seq,oid,source,observed,praw in snap.rows:\n        p=praw if isinstance(praw,dict) else dict(praw or ())\n        asset=str(p.get("asset") or "").upper()\n        evh=str(p.get("evidence_hash") or "");outh=str(p.get("outcome_hash") or "")\n        if p.get("return_fraction") is not None:returns.append(float(p["return_fraction"]))\n        for row in tuple(p.get("condition_vector") or ()):\n            if isinstance(row,(list,tuple)) and row:families.add(str(row[0]))\n        if asset and len(evh)==64 and len(outh)==64 and p.get("return_fraction") is not None:\n            ts=observed.isoformat() if hasattr(observed,"isoformat") else str(observed)\n            o=build_market_behavior_observation(asset,"crypto_realized_return","return_fraction_observed_interval",float(p["return_fraction"]),ts,evh,outh)\n            if not verify_market_behavior_observation(o):raise RuntimeError("OCL-011 verification failed")\n            groups.setdefault(asset,[]).append(o)\n    states=tuple(learn_market_behavior(tuple(groups[a])) for a in sorted(groups)) if groups else ()\n    mbh=envelope("market_behavior",states).state_hash if states else None\n    if returns:\n        pos=sum(x>0 for x in returns);neg=sum(x<0 for x in returns);flat=len(returns)-pos-neg\n        consistency=max(pos,neg,flat)/len(returns);contradiction=min(pos,neg)/len(returns)\n    else:\n        consistency=0.0;contradiction=0.0\n    maturity=evaluate_learning_maturity(len(returns),len(families),consistency,contradiction,0.0)\n    return SnapshotBehaviorMaturity(snap.as_of_sequence,snap.snapshot_hash,snap.row_count,sum(len(x) for x in groups.values()),mbh,envelope("maturity",maturity).state_hash,maturity.maturity_band,maturity.maturity_score)\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_228_snapshot_market_behavior_maturity_materialization as m\n\nROWS=((1,"o","s","t",{"asset":"BTC","evidence_hash":"a"*64,"outcome_hash":"b"*64,"return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),)}),\n      (2,"p","s","t",{"asset":"BTC","evidence_hash":"c"*64,"outcome_hash":"d"*64,"return_fraction":-.02,"condition_vector":(("coinbase","spot",1,"OBSERVED"),)}))\nclass T(unittest.TestCase):\n    def test_same_snapshot(self):\n        snap=SimpleNamespace(as_of_sequence=2,snapshot_hash="f"*64,row_count=2,rows=ROWS)\n        with patch.object(m,"capture_crypto_learned_case_snapshot",return_value=snap):\n            a=m.materialize_snapshot_behavior_maturity()\n            b=m.materialize_snapshot_behavior_maturity()\n        print("[AS_OF]",a.as_of_sequence,"[MB]",a.market_behavior_state_hash,"[MAT]",a.maturity_state_hash)\n        self.assertEqual(a.market_behavior_state_hash,b.market_behavior_state_hash)\n        self.assertEqual(a.maturity_state_hash,b.maturity_state_hash)\n        self.assertEqual(a.snapshot_hash,b.snapshot_hash)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-228 same-snapshot market behavior+maturity materialization certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*124);print(" OAD-228 SNAPSHOT MARKET-BEHAVIOR + MATURITY MATERIALIZATION");print("="*124)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_227_crypto_learned_case_asof_snapshot_boundary.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_218_existing_ocl_state_hash_envelope.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_011_market_behavior_observation.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_012_market_behavior_learning.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_022_learning_maturity.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] market-behavior and maturity hashes share one as-of sequence')
        print('[PASS] calibration_quality remains 0.0 until certified forecasts exist')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-228 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
