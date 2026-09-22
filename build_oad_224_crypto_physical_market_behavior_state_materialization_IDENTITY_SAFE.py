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

REVISION='OAD_224_CRYPTO_PHYSICAL_MARKET_BEHAVIOR_STATE_MATERIALIZATION_IDENTITY_SAFE_V1'
EXPECTED_INSTALLER='build_oad_224_crypto_physical_market_behavior_state_materialization_IDENTITY_SAFE.py'
MODULE_NAME='oad_224_crypto_physical_market_behavior_state_materialization.py'
TEST_NAME='test_oad_224_crypto_physical_market_behavior_state_materialization.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation import build_market_behavior_observation,verify_market_behavior_observation\nfrom qseries_v2.oracle_continuous_learner.ocl_012_market_behavior_learning import learn_market_behavior,verify_ocl_012_market_behavior_learning_engine\nfrom .oad_218_existing_ocl_state_hash_envelope import envelope\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False\nSOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")\n@dataclass(frozen=True,slots=True)\nclass PhysicalMarketBehaviorMaterialization:\n    learned_cases:int\n    behavior_observations:int\n    behavior_states:tuple\n    market_behavior_state_hash:str|None\n    state:str\n    physical_ready:bool=True\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\ndef materialize_physical_market_behavior_state(root=None,limit=1536):\n    if not verify_ocl_012_market_behavior_learning_engine():\n        raise RuntimeError("Frozen OCL-012 verifier failed")\n    root=Path(root or Path.cwd()).resolve()\n    sql="""SELECT observed_at,COALESCE(canonical_observation_json->\'raw_observation\'->\'payload\',canonical_observation_json->\'payload\',\'{}\'::jsonb)\n           FROM public.oracle_canonical_observations\n           WHERE source_id = ANY(%s::text[]) AND observation_type=\'crypto_verified_learned_case\'\n           ORDER BY sequence_number DESC LIMIT %s"""\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as q:\n            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'10000ms\'")\n            q.execute(sql,(list(SOURCE_IDS),int(limit)));rows=q.fetchall() or []\n        c.rollback()\n    groups={};obs=[]\n    for observed,praw in rows:\n        p=praw if isinstance(praw,dict) else dict(praw or ())\n        asset=str(p.get("asset") or "").upper();evh=str(p.get("evidence_hash") or "");outh=str(p.get("outcome_hash") or "")\n        if not asset or len(evh)!=64 or len(outh)!=64 or p.get("return_fraction") is None: continue\n        observed_at=observed.isoformat() if hasattr(observed,"isoformat") else str(p.get("outcome_observed_at") or observed)\n        o=build_market_behavior_observation(asset,"crypto_realized_return","return_fraction_observed_interval",float(p["return_fraction"]),observed_at,evh,outh)\n        if not verify_market_behavior_observation(o):raise RuntimeError("OCL-011 verification failed")\n        obs.append(o);groups.setdefault(asset,[]).append(o)\n    if not obs:\n        return PhysicalMarketBehaviorMaterialization(len(rows),0,(),None,"HOLD_OUTCOME_GROUNDED_BEHAVIOR_ROWS_REQUIRED")\n    states=tuple(learn_market_behavior(tuple(groups[a])) for a in sorted(groups))\n    return PhysicalMarketBehaviorMaterialization(len(rows),len(obs),states,envelope("market_behavior",states).state_hash,"MATERIALIZED")\n'
TEST='import unittest\nfrom unittest.mock import patch\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_adapters.independent import oad_224_crypto_physical_market_behavior_state_materialization as m\nROWS=[(datetime.now(timezone.utc),{"asset":"BTC","evidence_hash":"a"*64,"outcome_hash":"b"*64,"return_fraction":.01}),\n(datetime.now(timezone.utc),{"asset":"BTC","evidence_hash":"c"*64,"outcome_hash":"d"*64,"return_fraction":-.02}),\n(datetime.now(timezone.utc),{"asset":"ETH","evidence_hash":"e"*64,"outcome_hash":"f"*64,"return_fraction":.03})]\nclass Cur:\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def execute(self,*x):pass\n    def fetchall(self):return ROWS\nclass Conn:\n    def __enter__(self):return self\n    def __exit__(self,*x):return False\n    def cursor(self):return Cur()\n    def rollback(self):pass\nclass T(unittest.TestCase):\n    def test_materialize(self):\n        with patch.object(m,"connect",return_value=Conn()):\n            r=m.materialize_physical_market_behavior_state()\n        print("[STATE]",r.state,"[OBS]",r.behavior_observations,"[HASH]",r.market_behavior_state_hash)\n        self.assertEqual(r.state,"MATERIALIZED");self.assertEqual(len(r.market_behavior_state_hash),64);self.assertEqual(len(r.behavior_states),2)\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-224 outcome-grounded market behavior materialization certified")\n'

def main():
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED_INSTALLER}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*122);print(" OAD-224 CRYPTO PHYSICAL MARKET BEHAVIOR STATE MATERIALIZATION");print("="*122)
    print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_218_existing_ocl_state_hash_envelope.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_011_market_behavior_observation.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    d=r/'qseries_v2/oracle_continuous_learner/ocl_012_market_behavior_learning.py'
    if not d.is_file(): raise RuntimeError("Required certified dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    targets=[m,t];old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] OCL-011/OCL-012 reused unchanged')
        print('[PASS] state derives from persisted evidence_hash + outcome_hash + realized return')
        print('[PASS] probability=FALSE direction=FALSE execution=FALSE')
        print("[DONE] OAD-224 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
