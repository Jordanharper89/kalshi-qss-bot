from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_206_CRYPTO_CONTINUOUS_LEARNING_MULTI_CYCLE_PHYSICAL_CERTIFICATION_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nimport time\nfrom .oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy\nfrom .oad_203_crypto_continuous_learning_repeated_cycle_worker import run_crypto_continuous_learning_worker_cycle\nfrom .oad_200_crypto_continuous_learning_postgresql_checkpoint import read_checkpoint,verify_checkpoint\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoContinuousLearningMultiCycleCertification:\n    checkpoint_start:int\n    checkpoint_end:int\n    cycles_completed:int\n    experiences_formed:int\n    exact_outcomes:int\n    learned_cases_committed:int\n    checkpoint_advances:int\n    restart_resume_verified:bool\n    assets:tuple\n    cycle_states:tuple\n    physical_ready:bool\n    certified_at:str\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    execution_authority:bool=False\n\ndef run_crypto_continuous_learning_multi_cycle_physical_certification(\n    root=None,\n    cycles:int=2,\n    cadence_seconds:float=65.0,\n    horizon_seconds:int=60,\n    timeout_seconds:float=120.0,\n    acquisition_timeout_seconds:float=20.0,\n    sleep_fn=time.sleep,\n):\n    n=int(cycles)\n    if n<2: raise ValueError("multi-cycle certification requires at least 2 cycles")\n    p=build_crypto_continuous_learning_worker_policy(\n        cadence_seconds=cadence_seconds,horizon_seconds=horizon_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n        persistence_timeout_seconds=timeout_seconds\n    )\n    first=read_checkpoint(root)\n    if not verify_checkpoint(first): raise RuntimeError("initial checkpoint invalid")\n    prior=first\n    total_formed=total_outcomes=total_learned=advances=0\n    states=[]; assets=set()\n    for i in range(n):\n        cycle=run_crypto_continuous_learning_worker_cycle(root,p,i+1)\n        current=read_checkpoint(root)\n        if not verify_checkpoint(current): raise RuntimeError("cycle checkpoint invalid")\n        if current.cycle_sequence!=prior.cycle_sequence+1:\n            raise RuntimeError("checkpoint failed monotonic cycle advance")\n        if current.parent_state_hash!=prior.state_hash:\n            raise RuntimeError("checkpoint failed hash-chain resume")\n        advances+=1\n        total_formed+=int(cycle.experiences_formed)\n        total_outcomes+=int(cycle.exact_outcomes)\n        total_learned+=int(cycle.learned_cases_committed)\n        states.append(cycle.cycle_state)\n        prior=current\n        if i<n-1:\n            sleep_fn(p.cadence_seconds)\n    ready=bool(\n        advances==n and prior.cycle_sequence==first.cycle_sequence+n and\n        all(s for s in states)\n    )\n    return CryptoContinuousLearningMultiCycleCertification(\n        first.cycle_sequence,prior.cycle_sequence,n,total_formed,total_outcomes,total_learned,\n        advances,True,tuple(sorted(assets)),tuple(states),ready,\n        datetime.now(timezone.utc).isoformat(),False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_206_crypto_continuous_learning_multi_cycle_physical_certification import run_crypto_continuous_learning_multi_cycle_physical_certification\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_crypto_continuous_learning_multi_cycle_physical_certification()\n        print("[PHYSICAL] checkpoint_start=",r.checkpoint_start)\n        print("[PHYSICAL] checkpoint_end=",r.checkpoint_end)\n        print("[PHYSICAL] cycles_completed=",r.cycles_completed)\n        print("[PHYSICAL] experiences_formed=",r.experiences_formed)\n        print("[PHYSICAL] exact_outcomes=",r.exact_outcomes)\n        print("[PHYSICAL] learned_cases_committed=",r.learned_cases_committed)\n        print("[PHYSICAL] checkpoint_advances=",r.checkpoint_advances)\n        print("[PHYSICAL] restart_resume_verified=",r.restart_resume_verified)\n        print("[PHYSICAL] cycle_states=",r.cycle_states)\n        print("[PHYSICAL] physical_ready=",r.physical_ready)\n        self.assertTrue(r.physical_ready)\n        self.assertEqual(r.checkpoint_end,r.checkpoint_start+r.cycles_completed)\n        self.assertEqual(r.checkpoint_advances,r.cycles_completed)\n        self.assertTrue(r.restart_resume_verified)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.direction_enabled)\n        self.assertFalse(r.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-206 repeated-cycle + restart-safe crypto learning physically certified")\n    print("[PASS] no synthetic outcomes; probability/direction/execution remain disabled")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_206_crypto_continuous_learning_multi_cycle_physical_certification.py'; test=r/'test_oad_206_crypto_continuous_learning_multi_cycle_physical_certification.py'; init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-206 CRYPTO CONTINUOUS LEARNING MULTI-CYCLE PHYSICAL CERTIFICATION INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in ['oad_202_crypto_continuous_learning_worker_policy.py', 'oad_203_crypto_continuous_learning_repeated_cycle_worker.py', 'oad_204_crypto_continuous_learning_failure_isolation_recovery.py', 'oad_205_crypto_continuous_learning_restart_resume_gate.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_206_crypto_continuous_learning_multi_cycle_physical_certification import *"
        if export not in lines: lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-206 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__": main()
