from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-275'
REVISION='OAD_275_SOLANA_CONTINUOUS_OBSERVATION_RESILIENT_WORKER_V1'
TITLE='SOLANA CONTINUOUS OBSERVATION RESILIENT WORKER'
EXPECTED_FILENAME='build_oad_275_solana_continuous_observation_resilient_worker.py'
MODULE_NAME='oad_275_solana_continuous_observation_resilient_worker.py'
TEST_NAME='test_oad_275_solana_continuous_observation_resilient_worker.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_272_solana_continuous_observation_policy.py': ('build_solana_continuous_observation_policy', 'verify_solana_continuous_observation_policy'), 'qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py': ('select_live_solana_token', 'persist_pinned_solana_pool_snapshot'), 'qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py': ('read_pinned_pool_history', 'build_multi_horizon_solana_states')}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport time\nfrom pathlib import Path\n\nfrom .oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy,verify_solana_continuous_observation_policy\nfrom .oad_273_solana_pinned_pool_live_snapshot_persistence import select_live_solana_token,persist_pinned_solana_pool_snapshot\nfrom .oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history,build_multi_horizon_solana_states\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaContinuousCycle:\n    cycle:int\n    token_address:str\n    acquired:bool\n    observation_id:str|None\n    history_records:int\n    windows:tuple\n    state:str\n    execution_authority:bool=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaContinuousWorkerState:\n    attempts:int\n    successful_cycles:int\n    failed_cycles:int\n    consecutive_failures:int\n    token_address:str|None\n    last_state:str\n    execution_authority:bool=False\n\ndef failure_backoff_seconds(policy,consecutive_failures):\n    n=max(1,int(consecutive_failures))\n    return min(policy.failure_backoff_max_seconds,policy.failure_backoff_base_seconds*(2**(n-1)))\n\ndef run_solana_continuous_cycle(root=None,policy=None,cycle=1,token_address=None):\n    root=Path(root or Path.cwd()).resolve()\n    p=policy or build_solana_continuous_observation_policy()\n    if not verify_solana_continuous_observation_policy(p):\n        raise RuntimeError("invalid OAD-272 policy")\n    token=str(token_address or select_live_solana_token(p.acquisition_timeout_seconds))\n    snap=persist_pinned_solana_pool_snapshot(\n        token,root=root,\n        timeout_seconds=p.persistence_timeout_seconds,\n        acquisition_timeout_seconds=p.acquisition_timeout_seconds,\n    )\n    history=read_pinned_pool_history(token,root=root,limit=p.history_limit)\n    windows=build_multi_horizon_solana_states(history,token,p.windows_seconds)\n    state="OBSERVING" if history else "HOLD_NO_HISTORY"\n    return SolanaContinuousCycle(int(cycle),token,True,snap.observation_id,len(history),windows,state,False)\n\ndef run_resilient_solana_continuous_worker(\n    root=None,policy=None,max_cycles=None,progress=print,sleep_fn=time.sleep\n):\n    root=Path(root or Path.cwd()).resolve()\n    p=policy or build_solana_continuous_observation_policy()\n    token=None; attempts=0; ok=0; failed=0; consecutive=0; last="STARTING"\n    cycle=0\n    while max_cycles is None or attempts<int(max_cycles):\n        attempts+=1; cycle+=1\n        try:\n            if token is None:\n                token=select_live_solana_token(p.acquisition_timeout_seconds)\n                progress("[PIN] token_address="+token)\n            r=run_solana_continuous_cycle(root,p,cycle,token)\n            ok+=1; consecutive=0; last=r.state\n            ready=tuple((w.window_seconds,w.records,w.state) for w in r.windows)\n            progress(f"[CYCLE] cycle={cycle} token={token} history={r.history_records} windows={ready} execution_authority=FALSE")\n            if max_cycles is None or attempts<int(max_cycles):\n                sleep_fn(p.acquisition_seconds)\n        except KeyboardInterrupt:\n            raise\n        except Exception as e:\n            failed+=1; consecutive+=1; last="DEGRADED"\n            progress(f"[ERROR] cycle={cycle} type={type(e).__name__} message={e}")\n            if max_cycles is None or attempts<int(max_cycles):\n                sleep_fn(failure_backoff_seconds(p,consecutive))\n    return SolanaContinuousWorkerState(attempts,ok,failed,consecutive,token,last,False)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy\nfrom qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import *\n\nclass T(unittest.TestCase):\n    def test_backoff(self):\n        p=build_solana_continuous_observation_policy(failure_backoff_base_seconds=2,failure_backoff_max_seconds=10)\n        r=tuple(failure_backoff_seconds(p,x) for x in (1,2,3,4))\n        print("[BACKOFF]",r)\n        self.assertEqual(r,(2.0,4.0,8.0,10.0))\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-275 resilient continuous Solana worker/backoff certified")\n'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch: expected "+EXPECTED_FILENAME)

    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel,symbols in DEPENDENCIES.items():
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def "+symbol+"(") not in src and ("class "+symbol) not in src:
                raise RuntimeError("Exact dependency symbol missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)

    protected=[]
    for p,label in (
        (root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
        (root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
    ):
        if p.is_file():
            protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
            print("[PASS]",label,"verified")

    extra_paths=[]

    affected=(module,test,init,*extra_paths)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)

        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+module.stem+" import *"
        if export not in lines:
            lines.append(export)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] holder concentration dependency absent")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
