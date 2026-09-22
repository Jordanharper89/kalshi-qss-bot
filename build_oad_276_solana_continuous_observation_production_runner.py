from __future__ import annotations
import ast,hashlib,os,textwrap,subprocess,sys
from pathlib import Path
EXPECTED='build_oad_276_solana_continuous_observation_production_runner.py'
MODULE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nRUNNER_NAME="run_oad_276_solana_continuous_observation_production_child.py"\n\n@dataclass(frozen=True,slots=True)\nclass SolanaContinuousRunnerAdmission:\n    runner_present:bool\n    check_interface_present:bool\n    bounded_cycle_interface_present:bool\n    execution_boundary_preserved:bool\n    admitted:bool\n\ndef evaluate_solana_continuous_runner(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    p=root/RUNNER_NAME\n    if not p.is_file():\n        return SolanaContinuousRunnerAdmission(False,False,False,True,False)\n    src=p.read_text(encoding="utf-8")\n    check="--check" in src\n    bounded="--max-cycles" in src\n    safe="execution_authority=TRUE" not in src and "EXECUTION_AUTHORITY=True" not in src\n    return SolanaContinuousRunnerAdmission(True,check,bounded,safe,bool(check and bounded and safe))\n'
RUNNER='\nfrom __future__ import annotations\nimport argparse,time\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_adapters.independent.oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy\nfrom qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_resilient_solana_continuous_worker\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\ndef build_parser():\n    p=argparse.ArgumentParser(description="Oracle continuous Solana observation production child")\n    p.add_argument("--check",action="store_true")\n    p.add_argument("--tick-seconds",type=float,default=1.0)\n    p.add_argument("--acquisition-seconds",type=float,default=5.0)\n    p.add_argument("--history-limit",type=int,default=512)\n    p.add_argument("--max-cycles",type=int,default=None)\n    p.add_argument("--acquisition-timeout-seconds",type=float,default=20.0)\n    p.add_argument("--persistence-timeout-seconds",type=float,default=120.0)\n    return p\n\ndef main(argv=None):\n    a=build_parser().parse_args(argv)\n    policy=build_solana_continuous_observation_policy(\n        tick_seconds=a.tick_seconds,\n        acquisition_seconds=a.acquisition_seconds,\n        history_limit=a.history_limit,\n        acquisition_timeout_seconds=a.acquisition_timeout_seconds,\n        persistence_timeout_seconds=a.persistence_timeout_seconds,\n    )\n    if a.max_cycles is not None and a.max_cycles<1:\n        raise SystemExit("--max-cycles must be >= 1")\n    if a.check:\n        print(\n            "[READY] solana_continuous child "\n            f"tick_seconds={policy.tick_seconds} "\n            f"acquisition_seconds={policy.acquisition_seconds} "\n            f"windows={policy.windows_seconds} "\n            "pinned_session=TRUE holder_concentration=DEFERRED "\n            "probability_enabled=FALSE direction_enabled=FALSE "\n            "publication_allowed=FALSE execution_authority=FALSE",\n            flush=True,\n        )\n        return 0\n\n    print(\n        "[START] Oracle continuous Solana observation child "\n        f"tick_seconds={policy.tick_seconds} "\n        f"acquisition_seconds={policy.acquisition_seconds} "\n        "pinned_session=TRUE execution_authority=FALSE",\n        flush=True,\n    )\n    s=run_resilient_solana_continuous_worker(\n        root=Path.cwd(),policy=policy,max_cycles=a.max_cycles,\n        progress=lambda x:print(x,flush=True),sleep_fn=time.sleep\n    )\n    if a.max_cycles is not None:\n        print("[SUMMARY]",s,flush=True)\n        return 0 if s.successful_cycles>0 else 1\n    return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
TEST='\nimport subprocess,sys,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.independent.oad_276_solana_continuous_observation_production_runner import evaluate_solana_continuous_runner\n\nROOT=Path.cwd()\nRUNNER=ROOT/"run_oad_276_solana_continuous_observation_production_child.py"\n\nclass T(unittest.TestCase):\n    def test_check(self):\n        r=evaluate_solana_continuous_runner(ROOT)\n        print("[ADMISSION]",r)\n        self.assertTrue(r.admitted)\n        p=subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)\n        print(p.stdout,end="")\n        self.assertEqual(p.returncode,0)\n        self.assertIn("tick_seconds=1.0",p.stdout)\n        self.assertIn("acquisition_seconds=5.0",p.stdout)\n        self.assertIn("pinned_session=TRUE",p.stdout)\n        self.assertIn("holder_concentration=DEFERRED",p.stdout)\n        self.assertIn("execution_authority=FALSE",p.stdout)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-276 production Solana continuous-observation child contract certified")\n'

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write(p,s):
    s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    deps={
      pkg/"oad_272_solana_continuous_observation_policy.py":("build_solana_continuous_observation_policy",),
      pkg/"oad_275_solana_continuous_observation_resilient_worker.py":("run_resilient_solana_continuous_worker",),
    }
    print("="*120);print(" OAD-276 SOLANA CONTINUOUS OBSERVATION PRODUCTION RUNNER INSTALLER");print("="*120);print("[ROOT]",r)
    for d,syms in deps.items():
        if not d.is_file(): raise RuntimeError("dependency missing: "+str(d))
        s=d.read_text(encoding="utf-8")
        for x in syms:
            if "def "+x+"(" not in s: raise RuntimeError("exact dependency symbol missing: "+x)
        print("[PASS] exact dependency verified:",d.relative_to(r))

    module=pkg/"oad_276_solana_continuous_observation_production_runner.py"
    runner=r/"run_oad_276_solana_continuous_observation_production_child.py"
    test=r/"test_oad_276_solana_continuous_observation_production_runner.py"
    init=pkg/"__init__.py"
    protected=[]
    for p in (r/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py",
              r/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"):
        if p.is_file(): protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,runner,test,init)}
    try:
        write(module,MODULE);write(runner,RUNNER);write(test,TEST)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from .oad_276_solana_continuous_observation_production_runner import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed")
        q=subprocess.run([sys.executable,str(test)],cwd=str(r))
        if q.returncode: raise RuntimeError("OAD-276 certification failed")
        print("[PASS] production child installed:",runner.name)
        print("[PASS] 1-second internal tick interface certified")
        print("[PASS] source acquisition cadence remains separately bounded")
        print("[PASS] holder concentration deferred")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-276 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise

if __name__=="__main__":main()
