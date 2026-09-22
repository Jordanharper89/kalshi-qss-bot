from pathlib import Path
import inspect, json, importlib

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_source_network/runtime/sports_supervised_child.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn087_sports_supervised_child.json"
TEST=ROOT/"test_osn_087_sports_supervised_child_EXACT_RUN_CYCLE_SIGNATURE_REPAIR.py"

def main():
    print("="*120)
    print(" OSN-087 SPORTS SUPERVISED CHILD — EXACT RUN_CYCLE SIGNATURE REPAIR")
    print("="*120)

    deps=(
        ROOT/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json",
        ROOT/"qseries_v2/oracle_source_network/runtime/six_league_durable_runtime_cycle.py",
        ROOT/"qseries_v2/oracle_source_network/state/osn085_durable_runtime_cycle.json",
    )
    for dep in deps:
        if not dep.exists():
            raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    mod=importlib.import_module("qseries_v2.oracle_source_network.runtime.six_league_durable_runtime_cycle")
    run_cycle=getattr(mod,"run_cycle")
    sig=inspect.signature(run_cycle)
    params=sig.parameters

    print("[RUN_CYCLE_SIGNATURE]",sig)

    allowed=[]
    for key in ("root","timeout","commit_timeout_seconds"):
        if key in params:
            allowed.append(key)

    if "root" not in allowed:
        raise SystemExit("[FAIL] certified run_cycle exposes no root parameter; refusing to guess runtime call contract")

    source = f"""from pathlib import Path
from datetime import datetime, timezone
import inspect, json, time

from qseries_v2.oracle_source_network.runtime.six_league_durable_runtime_cycle import run_cycle

RUN_CYCLE_SIGNATURE={inspect.signature(run_cycle)!r}
HEARTBEAT_REL="qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json"

def _heartbeat(root,status,cycles,last_error=None):
    p=Path(root)/HEARTBEAT_REL
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({
        "status":status,
        "cycles":cycles,
        "last_heartbeat":datetime.now(timezone.utc).isoformat(),
        "last_error":last_error,
        "terminal_dependency":"NONE",
        "execution_authority":False
    },indent=2),encoding="utf-8")
    return p

def _run_cycle_exact(base,timeout,commit_timeout_seconds):
    kwargs={"root":base}
"""
    if "timeout" in allowed:
        source += '    kwargs["timeout"]=timeout\n'
    if "commit_timeout_seconds" in allowed:
        source += '    kwargs["commit_timeout_seconds"]=commit_timeout_seconds\n'
    source += """    return run_cycle(**kwargs)

def run_once(root=None,timeout=15,commit_timeout_seconds=45.0):
    base=Path(root or Path.cwd()).resolve()
    rows,state=_run_cycle_exact(base,timeout,commit_timeout_seconds)
    _heartbeat(base,"HEALTHY",1,None)
    return rows,state

def run_forever(root=None,cadence_seconds=30.0,timeout=15,commit_timeout_seconds=45.0,max_cycles=None):
    base=Path(root or Path.cwd()).resolve()
    cycles=0
    while True:
        try:
            rows,state=_run_cycle_exact(base,timeout,commit_timeout_seconds)
            cycles+=1
            _heartbeat(base,"HEALTHY",cycles,None)
        except KeyboardInterrupt:
            _heartbeat(base,"STOPPED",cycles,None)
            raise
        except Exception as exc:
            _heartbeat(base,"DEGRADED",cycles,repr(exc))
            raise
        if max_cycles is not None and cycles>=max_cycles:
            return cycles
        time.sleep(max(1.0,float(cadence_seconds)))
"""

    TARGET.write_text(source,encoding="utf-8")
    compile(source,str(TARGET),"exec")

    state={
        "child_module":"qseries_v2.oracle_source_network.runtime.sports_supervised_child",
        "run_cycle_signature":str(sig),
        "forwarded_parameters":allowed,
        "cadence_seconds":30.0,
        "terminal_dependency":"NONE",
        "execution_authority":False
    }
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,indent=2),encoding="utf-8")
    TEST.write_text('from pathlib import Path\nfrom qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_once, RUN_CYCLE_SIGNATURE\n\nrows,state=run_once(root=Path.cwd(),timeout=15,commit_timeout_seconds=45.0)\n\nprint("[RUN_CYCLE_SIGNATURE]",RUN_CYCLE_SIGNATURE)\nprint("[ROWS]",len(rows))\nassert len(rows)==6\nassert all(getattr(x,"readback_count",0)>0 for x in rows)\nassert all(getattr(x,"checkpoint_written",False) for x in rows)\nassert all(getattr(x,"execution_authority",False) is False for x in rows)\n\nprint("[PASS] supervised child calls certified run_cycle only with supported parameters")\nprint("[PASS] six-league durable cycle completed")\nprint("[PASS] OSN-087 exact run_cycle signature repair certified")\n',encoding="utf-8")

    print("[WRITE]",TARGET.relative_to(ROOT))
    print("[STATE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] unsupported run_cycle keywords retired")
    print("[PASS] supervised child now binds to exact certified signature")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
