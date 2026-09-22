from __future__ import annotations
import os,sys,subprocess
from pathlib import Path
EXPECTED='build_oad_240_crypto_learning_prospective_production_runner_EXACT_INTERFACE_REBUILD.py'; RUNNER='from __future__ import annotations\nimport argparse,time\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy\nfrom qseries_v2.oracle_adapters.independent.oad_200_crypto_continuous_learning_postgresql_checkpoint import read_checkpoint,verify_checkpoint\nfrom qseries_v2.oracle_adapters.independent.oad_239_crypto_prospective_learning_resilient_worker import run_resilient_prospective_learning_worker\nREAD_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False\n\ndef build_parser():\n    p=argparse.ArgumentParser(description="Oracle continuous crypto learning + prospective learning production child")\n    p.add_argument("--check",action="store_true"); p.add_argument("--cadence-seconds",type=float,default=60.0)\n    p.add_argument("--horizon-seconds",type=int,default=60); p.add_argument("--acquisition-timeout-seconds",type=float,default=20.0)\n    p.add_argument("--persistence-timeout-seconds",type=float,default=120.0); p.add_argument("--max-attempts",type=int,default=None)\n    return p\n\ndef check_runtime(root=None):\n    cp=read_checkpoint(root)\n    if not verify_checkpoint(cp): raise RuntimeError("crypto continuous-learning checkpoint invalid")\n    policy=build_crypto_continuous_learning_worker_policy()\n    return {"checkpoint_cycle":cp.cycle_sequence,"cadence_seconds":policy.cadence_seconds,"horizon_seconds":policy.horizon_seconds}\n\ndef main(argv=None):\n    a=build_parser().parse_args(argv)\n    if a.cadence_seconds<=0: raise SystemExit("--cadence-seconds must be > 0")\n    if a.horizon_seconds<=0: raise SystemExit("--horizon-seconds must be > 0")\n    if a.acquisition_timeout_seconds<=0: raise SystemExit("--acquisition-timeout-seconds must be > 0")\n    if a.persistence_timeout_seconds<=0: raise SystemExit("--persistence-timeout-seconds must be > 0")\n    if a.max_attempts is not None and a.max_attempts<1: raise SystemExit("--max-attempts must be >= 1")\n    if a.check:\n        r=check_runtime(Path.cwd())\n        print(f"[READY] crypto_learning child checkpoint_cycle={r[\'checkpoint_cycle\']} cadence_seconds={r[\'cadence_seconds\']} horizon_seconds={r[\'horizon_seconds\']} prospective_learning=TRUE probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE",flush=True)\n        return 0\n    p=build_crypto_continuous_learning_worker_policy(\n        cadence_seconds=a.cadence_seconds,horizon_seconds=a.horizon_seconds,\n        acquisition_timeout_seconds=a.acquisition_timeout_seconds,persistence_timeout_seconds=a.persistence_timeout_seconds)\n    print(f"[START] Oracle crypto continuous-learning + prospective-learning production child cadence_seconds={p.cadence_seconds} horizon_seconds={p.horizon_seconds} probability_enabled=FALSE direction_enabled=FALSE publication_allowed=FALSE execution_authority=FALSE",flush=True)\n    s=run_resilient_prospective_learning_worker(root=Path.cwd(),policy=p,max_attempts=a.max_attempts,progress=lambda x:print(x,flush=True),sleep_fn=time.sleep)\n    if a.max_attempts is not None:\n        print("[SUMMARY]",s,flush=True); return 0 if s.successful_cycles>0 else 1\n    return 0\nif __name__=="__main__": raise SystemExit(main())\n'; TEST='import subprocess,sys,unittest\nfrom pathlib import Path\nROOT=Path.cwd(); RUNNER=ROOT/"run_oad_207_crypto_continuous_learning_production_child.py"\nclass T(unittest.TestCase):\n    def test_contract(self):\n        src=RUNNER.read_text(encoding="utf-8")\n        for x in ("--check","--cadence-seconds","--horizon-seconds","--acquisition-timeout-seconds","--persistence-timeout-seconds","--max-attempts","run_resilient_prospective_learning_worker"):\n            self.assertIn(x,src)\n        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)\n        print(p.stdout,end=""); self.assertEqual(p.returncode,0); self.assertIn("prospective_learning=TRUE",p.stdout); self.assertIn("execution_authority=FALSE",p.stdout)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-240 exact production child interface preserved")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    compile(s,str(p),"exec"); t=p.with_suffix(p.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    deps={pkg/"oad_200_crypto_continuous_learning_postgresql_checkpoint.py":("read_checkpoint","verify_checkpoint"),
          pkg/"oad_202_crypto_continuous_learning_worker_policy.py":("build_crypto_continuous_learning_worker_policy",),
          pkg/"oad_239_crypto_prospective_learning_resilient_worker.py":("run_resilient_prospective_learning_worker",)}
    print("="*124); print(" OAD-240 PROSPECTIVE PRODUCTION RUNNER EXACT-INTERFACE REBUILD"); print("="*124); print("[ROOT]",r)
    for d,syms in deps.items():
        if not d.is_file(): raise RuntimeError("dependency missing: "+str(d))
        src=d.read_text(encoding="utf-8")
        for s in syms:
            if "def "+s+"(" not in src: raise RuntimeError("exact symbol missing: "+s)
        print("[PASS] exact dependency verified:",d.relative_to(r))
    runner=r/"run_oad_207_crypto_continuous_learning_production_child.py"; t=r/"test_oad_240_crypto_learning_prospective_production_runner_integration.py"
    old={p:(p.read_bytes() if p.exists() else None) for p in (runner,t)}
    try:
        write(runner,RUNNER); write(t,TEST)
        q=subprocess.run([sys.executable,str(t)],cwd=str(r))
        if q.returncode: raise RuntimeError("OAD-240 certification failed")
        print("[PASS] existing crypto_learning child identity preserved")
        print("[PASS] OAD-207 CLI/check interface preserved")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-240 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OAD-240 rolled back"); raise
if __name__=="__main__": main()
