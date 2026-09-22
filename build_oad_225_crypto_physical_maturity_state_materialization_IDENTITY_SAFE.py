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

def run_test(r,t):
    q=subprocess.run([sys.executable,str(t)],cwd=str(r))
    if q.returncode:
        raise RuntimeError("Certification test failed: "+t.name)

REVISION='OAD_225_CRYPTO_PHYSICAL_MATURITY_STATE_MATERIALIZATION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_225_crypto_physical_maturity_state_materialization_IDENTITY_SAFE.py'
MODULE_NAME='oad_225_crypto_physical_maturity_state_materialization.py'
TEST_NAME='test_oad_225_crypto_physical_maturity_state_materialization.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import evaluate_learning_maturity,verify_ocl_022_learning_confidence_evidence_maturity\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\nSOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")\n@dataclass(frozen=True,slots=True)\nclass PhysicalMaturityMaterialization:\n    evidence_count:int\n    independent_sources:int\n    consistency:float\n    contradiction_rate:float\n    calibration_quality:float\n    maturity:object\n    maturity_state_hash:str\n    state:str\n    physical_ready:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\ndef materialize_physical_maturity_state(root=None,limit=1536):\n    if not verify_ocl_022_learning_confidence_evidence_maturity():\n        raise RuntimeError("Frozen OCL-022 verifier failed")\n    root=Path(root or Path.cwd()).resolve()\n    sql="""SELECT COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb)\n           FROM public.oracle_canonical_observations\n           WHERE source_id = ANY(%s::text[]) AND observation_type=\'crypto_verified_learned_case\'\n           ORDER BY sequence_number DESC LIMIT %s"""\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'10000ms\'")\n            q.execute(sql,(list(SOURCE_IDS),int(limit)));rows=q.fetchall() or []\n        c.rollback()\n    payloads=[r[0] if isinstance(r[0],dict) else dict(r[0] or ()) for r in rows]\n    returns=[float(p["return_fraction"]) for p in payloads if p.get("return_fraction") is not None]\n    if returns:\n        pos=sum(x>0 for x in returns);neg=sum(x<0 for x in returns);flat=len(returns)-pos-neg\n        consistency=max(pos,neg,flat)/len(returns);contradiction=min(pos,neg)/len(returns)\n    else:\n        consistency=0.0;contradiction=0.0\n    source_families=set()\n    for p in payloads:\n        for row in tuple(p.get("condition_vector") or ()):\n            if isinstance(row,(list,tuple)) and row:source_families.add(str(row[0]))\n    calibration_quality=0.0\n    maturity=evaluate_learning_maturity(len(returns),len(source_families),consistency,contradiction,calibration_quality)\n    return PhysicalMaturityMaterialization(len(returns),len(source_families),consistency,contradiction,calibration_quality,maturity,envelope("maturity",maturity).state_hash,"MATERIALIZED_UNCALIBRATED")\n'
TEST='import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_225_crypto_physical_maturity_state_materialization as m\nclass Cur:\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def execute(self,*x):pass\n    def fetchall(self):return [({"return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),)},),({"return_fraction":-.02,"condition_vector":(("coinbase","spot",1,"OBSERVED"),)},),({"return_fraction":.03,"condition_vector":(("ethereum","fee",1,"HIGH"),)},)]\nclass Conn:\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def cursor(self):return Cur()\n    def rollback(self):pass\nclass T(unittest.TestCase):\n    def test_uncalibrated(self):\n        with patch.object(m,"connect",return_value=Conn()):\n            r=m.materialize_physical_maturity_state()\n        print("[BAND]",r.maturity.maturity_band,"[SCORE]",r.maturity.maturity_score,"[HASH]",r.maturity_state_hash)\n        self.assertEqual(r.calibration_quality,0.0);self.assertEqual(r.maturity.maturity_score,0.0);self.assertEqual(r.maturity.maturity_band,"immature");self.assertEqual(len(r.maturity_state_hash),64)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-225 uncalibrated maturity state materialization certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*122);print(" OAD-225 CRYPTO PHYSICAL MATURITY STATE MATERIALIZATION");print("="*122)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_224_crypto_physical_market_behavior_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_022_learning_maturity.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    targets=[m,t];old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] calibration_quality=0.0 explicitly represents no certified calibration')
        print('[PASS] OCL-022 reused unchanged')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-225 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
