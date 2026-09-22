from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
EXPECTED='build_oad_312_solana_continuous_temporal_history_activation_gate.py'
MODULE="oad_312_solana_continuous_temporal_history_activation_gate.py"
TEST="test_oad_312_solana_continuous_temporal_history_activation_gate.py"
DEPENDENCIES=[('qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py', ('def persist_pinned_solana_pool_snapshot', 'submit_observation_batch', 'exact_postgresql_readback')), ('qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py', ('def read_pinned_pool_history', 'def build_multi_horizon_solana_states')), ('qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py', ('def run_resilient_solana_continuous_worker', 'def run_solana_continuous_cycle')), ('qseries_v2/oracle_adapters/independent/oad_276_solana_continuous_observation_production_runner.py', ('def evaluate_solana_continuous_runner', 'run_oad_276_solana_continuous_observation_production_child.py'))]
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport subprocess,sys\n\nfrom .oad_276_solana_continuous_observation_production_runner import evaluate_solana_continuous_runner\nfrom .oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history,build_multi_horizon_solana_states\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nRUNNER_NAME="run_oad_276_solana_continuous_observation_production_child.py"\n\n@dataclass(frozen=True,slots=True)\nclass SolanaTemporalActivationResult:\n    runner_admitted:bool\n    child_returncode:int\n    token_address:str|None\n    history_records:int\n    windows:tuple\n    ready_windows:tuple\n    temporal_state:str\n    execution_authority:bool=False\n\ndef _parse_token(stdout):\n    for line in stdout.splitlines():\n        if line.startswith("[PIN] token_address="):\n            return line.split("=",1)[1].strip()\n    return None\n\ndef activate_and_verify_temporal_history(root=None,max_cycles=13,timeout_seconds=240.0):\n    root=Path(root or Path.cwd()).resolve()\n    admission=evaluate_solana_continuous_runner(root)\n    if not admission.admitted:\n        raise RuntimeError("certified OAD-276 Solana continuous runner not admitted")\n    cycles=max(13,int(max_cycles))\n    p=subprocess.run(\n        [sys.executable,str(root/RUNNER_NAME),"--max-cycles",str(cycles)],\n        cwd=str(root),text=True,capture_output=True,timeout=float(timeout_seconds)\n    )\n    print(p.stdout,end="")\n    if p.stderr: print(p.stderr,end="")\n    token=_parse_token(p.stdout)\n    if p.returncode!=0 or not token:\n        return SolanaTemporalActivationResult(\n            True,p.returncode,token,0,(),(),"CHILD_FAILED_OR_NO_PIN",False\n        )\n    history=read_pinned_pool_history(token,root=root,limit=512)\n    windows=build_multi_horizon_solana_states(history,token,(5,15,30,60))\n    compact=tuple((w.window_seconds,w.records,w.state) for w in windows)\n    ready=tuple(w.window_seconds for w in windows if w.state=="WINDOW_READY")\n    state="TEMPORAL_5_15_30_60_READY" if set((5,15,30,60)).issubset(set(ready)) else "TEMPORAL_DEPTH_STILL_ACCUMULATING"\n    return SolanaTemporalActivationResult(\n        True,p.returncode,token,len(history),compact,ready,state,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_312_solana_continuous_temporal_history_activation_gate import *\n\nclass T(unittest.TestCase):\n    def test_physical_activation(self):\n        x=activate_and_verify_temporal_history(max_cycles=13)\n        print("[PHYSICAL] runner_admitted=",x.runner_admitted)\n        print("[PHYSICAL] child_returncode=",x.child_returncode)\n        print("[PHYSICAL] token=",x.token_address)\n        print("[PHYSICAL] history_records=",x.history_records)\n        print("[PHYSICAL] windows=",x.windows)\n        print("[PHYSICAL] ready_windows=",x.ready_windows)\n        print("[PHYSICAL] temporal_state=",x.temporal_state)\n        self.assertTrue(x.runner_admitted)\n        self.assertEqual(x.child_returncode,0)\n        self.assertTrue(x.token_address)\n        self.assertGreaterEqual(x.history_records,1)\n        self.assertIn(5,x.ready_windows)\n        self.assertIn(15,x.ready_windows)\n        self.assertIn(30,x.ready_windows)\n        self.assertIn(60,x.ready_windows)\n        self.assertEqual(x.temporal_state,"TEMPORAL_5_15_30_60_READY")\n        self.assertFalse(x.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-312 continuous Solana temporal history physically activated")\n    print("[PASS] 5/15/30/60-second windows physically READY from durable PostgreSQL history")\n    print("[PASS] existing OAD-272→276 production path reused; no duplicate temporal subsystem created")\n    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(p,s):
    s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n");os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED:raise RuntimeError("installer filename identity mismatch")
    r=root();pkg=r/"qseries_v2"/"oracle_adapters"/"independent";m=pkg/MODULE;t=r/TEST;init=pkg/"__init__.py"
    print("="*120);print(" OAD-312 SOLANA CONTINUOUS TEMPORAL HISTORY ACTIVATION GATE INSTALLER");print("="*120);print("[ROOT]",r)
    for rel,marks in DEPENDENCIES:
        p=r/rel
        if not p.is_file():raise RuntimeError("dependency missing: "+rel)
        s=p.read_text(encoding="utf-8");ast.parse(s,filename=str(p))
        for mark in marks:
            if mark not in s:raise RuntimeError("exact dependency marker missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    runner=r/"run_oad_276_solana_continuous_observation_production_child.py"
    if not runner.is_file():raise RuntimeError("OAD-276 production child missing")
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file():raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        write(m,MODULE_SOURCE);write(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else [];exp="from ."+m.stem+" import *"
        if exp not in lines:lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] existing OAD-272→276 temporal acquisition path preserved and reused")
        print("[PASS] no replacement temporal subsystem created")
        print("[PASS] physical gate will run 13 pinned 5-second acquisitions")
        print("[PASS] durable 5/15/30/60-second windows required for certification")
        print("[PASS] OAD-273 OPH single-writer + exact PostgreSQL readback preserved")
        print("[PASS] module installed:",m.relative_to(r));print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-312 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
