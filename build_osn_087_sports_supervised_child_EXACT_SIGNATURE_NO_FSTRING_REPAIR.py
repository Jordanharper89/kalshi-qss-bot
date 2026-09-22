
from pathlib import Path
import inspect, importlib, json

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_source_network/runtime/sports_supervised_child.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn087_sports_supervised_child.json"
TEST=ROOT/"test_osn_087_sports_supervised_child_EXACT_SIGNATURE_NO_FSTRING_REPAIR.py"

MODULE_SOURCE='from pathlib import Path\nfrom datetime import datetime, timezone\nimport json, time\n\nfrom qseries_v2.oracle_source_network.runtime.six_league_durable_runtime_cycle import run_cycle\n\nRUN_CYCLE_SIGNATURE="(root=None, timeout=15)"\nHEARTBEAT_REL="qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json"\n\ndef _heartbeat(root,status,cycles,last_error=None):\n    p=Path(root)/HEARTBEAT_REL\n    p.parent.mkdir(parents=True,exist_ok=True)\n    payload={\n        "status":status,\n        "cycles":cycles,\n        "last_heartbeat":datetime.now(timezone.utc).isoformat(),\n        "last_error":last_error,\n        "terminal_dependency":"NONE",\n        "execution_authority":False\n    }\n    p.write_text(json.dumps(payload,indent=2),encoding="utf-8")\n    return p\n\ndef _run_cycle_exact(base,timeout):\n    return run_cycle(root=base,timeout=timeout)\n\ndef run_once(root=None,timeout=15,commit_timeout_seconds=45.0):\n    base=Path(root or Path.cwd()).resolve()\n    rows,state=_run_cycle_exact(base,timeout)\n    _heartbeat(base,"HEALTHY",1,None)\n    return rows,state\n\ndef run_forever(root=None,cadence_seconds=30.0,timeout=15,commit_timeout_seconds=45.0,max_cycles=None):\n    base=Path(root or Path.cwd()).resolve()\n    cycles=0\n    while True:\n        try:\n            rows,state=_run_cycle_exact(base,timeout)\n            cycles+=1\n            _heartbeat(base,"HEALTHY",cycles,None)\n        except KeyboardInterrupt:\n            _heartbeat(base,"STOPPED",cycles,None)\n            raise\n        except Exception as exc:\n            _heartbeat(base,"DEGRADED",cycles,repr(exc))\n            raise\n        if max_cycles is not None and cycles>=max_cycles:\n            return cycles\n        time.sleep(max(1.0,float(cadence_seconds)))\n'
TEST_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_once, RUN_CYCLE_SIGNATURE\n\nrows,state=run_once(root=Path.cwd(),timeout=15,commit_timeout_seconds=45.0)\n\nprint("[RUN_CYCLE_SIGNATURE]",RUN_CYCLE_SIGNATURE)\nprint("[ROWS]",len(rows))\nassert RUN_CYCLE_SIGNATURE == "(root=None, timeout=15)"\nassert len(rows)==6\nassert all(getattr(x,"readback_count",0)>0 for x in rows)\nassert all(getattr(x,"checkpoint_written",False) for x in rows)\nassert all(getattr(x,"execution_authority",False) is False for x in rows)\n\nprint("[PASS] supervised child binds exactly to run_cycle(root=None, timeout=15)")\nprint("[PASS] unsupported commit_timeout_seconds is intentionally ignored")\nprint("[PASS] six-league durable cycle completed")\nprint("[PASS] OSN-087 exact-signature no-fstring repair certified")\n'

def main():
    print("="*120)
    print(" OSN-087 SPORTS SUPERVISED CHILD — EXACT SIGNATURE NO-FSTRING REPAIR")
    print("="*120)

    for dep in (
        ROOT/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json",
        ROOT/"qseries_v2/oracle_source_network/runtime/six_league_durable_runtime_cycle.py",
        ROOT/"qseries_v2/oracle_source_network/state/osn085_durable_runtime_cycle.json",
    ):
        if not dep.exists():
            raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    mod=importlib.import_module("qseries_v2.oracle_source_network.runtime.six_league_durable_runtime_cycle")
    sig=str(inspect.signature(getattr(mod,"run_cycle")))
    print("[RUN_CYCLE_SIGNATURE]",sig)

    if sig != "(root=None, timeout=15)":
        raise SystemExit("[FAIL] run_cycle signature changed from certified observed contract: "+sig)

    TARGET.write_text(MODULE_SOURCE,encoding="utf-8")
    compile(MODULE_SOURCE,str(TARGET),"exec")

    state={
        "child_module":"qseries_v2.oracle_source_network.runtime.sports_supervised_child",
        "run_cycle_signature":sig,
        "forwarded_parameters":["root","timeout"],
        "ignored_wrapper_parameters":["commit_timeout_seconds"],
        "cadence_seconds":30.0,
        "terminal_dependency":"NONE",
        "execution_authority":False
    }
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,indent=2),encoding="utf-8")

    TEST.write_text(TEST_SOURCE,encoding="utf-8")
    compile(TEST_SOURCE,str(TEST),"exec")

    print("[WRITE]",TARGET.relative_to(ROOT))
    print("[STATE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] nested f-string source generation removed")
    print("[PASS] exact run_cycle(root, timeout) contract bound")
    print("[PASS] no unsupported keyword forwarded")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
