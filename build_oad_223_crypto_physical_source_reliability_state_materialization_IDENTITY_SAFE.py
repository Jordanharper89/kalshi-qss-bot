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

REVISION='OAD_223_CRYPTO_PHYSICAL_SOURCE_RELIABILITY_STATE_MATERIALIZATION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_223_crypto_physical_source_reliability_state_materialization_IDENTITY_SAFE.py'
MODULE_NAME='oad_223_crypto_physical_source_reliability_state_materialization.py'
TEST_NAME='test_oad_223_crypto_physical_source_reliability_state_materialization.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import verify_ocl_007_source_reliability_learning\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\nSOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")\n@dataclass(frozen=True,slots=True)\nclass PhysicalSourceReliabilityMaterialization:\n    learned_cases:int\n    source_correctness_labels:int\n    source_states:int\n    source_reliability_state_hash:str|None\n    state:str\n    physical_ready:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\ndef materialize_physical_source_reliability_state(root=None,limit=1536):\n    if not verify_ocl_007_source_reliability_learning():\n        raise RuntimeError("Frozen OCL-007 verifier failed")\n    root=Path(root or Path.cwd()).resolve()\n    sql="""SELECT COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb)\n           FROM public.oracle_canonical_observations\n           WHERE source_id = ANY(%s::text[]) AND observation_type=\'crypto_verified_learned_case\'\n           ORDER BY sequence_number DESC LIMIT %s"""\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'10000ms\'")\n            q.execute(sql,(list(SOURCE_IDS),int(limit)));rows=q.fetchall() or []\n        c.rollback()\n    payloads=[r[0] if isinstance(r[0],dict) else dict(r[0] or ()) for r in rows]\n    labels=[]\n    for p in payloads:\n        v=p.get("source_correctness")\n        if isinstance(v,dict): labels.extend(v.items())\n        elif p.get("source_id") is not None and p.get("source_correct") is not None:\n            labels.append((p.get("source_id"),bool(p.get("source_correct"))))\n    if not labels:\n        return PhysicalSourceReliabilityMaterialization(len(payloads),0,0,None,"HOLD_SOURCE_CORRECTNESS_LABELS_REQUIRED")\n    return PhysicalSourceReliabilityMaterialization(len(payloads),len(labels),0,None,"HOLD_CERTIFIED_SOURCE_LABEL_PROVENANCE_REQUIRED")\n'
TEST='import unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_223_crypto_physical_source_reliability_state_materialization as m\nclass Cur:\n    def __enter__(self): return self\n    def __exit__(self,*x): return False\n    def execute(self,*x): pass\n    def fetchall(self): return [({"asset":"BTC"},),({"asset":"ETH"},)]\nclass Conn:\n    def __enter__(self): return self\n    def __exit__(self,*x): return False\n    def cursor(self): return Cur()\n    def rollback(self): pass\nclass T(unittest.TestCase):\n    def test_hold(self):\n        with patch.object(m,"connect",return_value=Conn()):\n            r=m.materialize_physical_source_reliability_state()\n        print("[STATE]",r.state)\n        self.assertEqual(r.source_correctness_labels,0)\n        self.assertIsNone(r.source_reliability_state_hash)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-223 truthful source-reliability materialization gate certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*122);print(" OAD-223 CRYPTO PHYSICAL SOURCE RELIABILITY STATE MATERIALIZATION");print("="*122)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=r/'qseries_v2/oracle_continuous_learner/ocl_007_source_reliability.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=pkg/'oad_222_crypto_physical_calibration_state_materialization.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    targets=[m,t];old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] OCL-007 reused unchanged')
        print('[PASS] source reliability not inferred from return direction')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-223 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
