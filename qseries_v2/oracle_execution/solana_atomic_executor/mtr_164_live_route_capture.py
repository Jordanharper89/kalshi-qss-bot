"""MTR-164 read-only capture of physically persisted canonical routes.

Only accepts recent on-disk evidence; never starts runtime, polls wallet, signs or broadcasts.
"""
import argparse
import json
import time
from pathlib import Path
from .mtr_163_canonical_route_handoff import canonical_instructions, HandoffHold, core

REQUIRED=("pump_ixs","pump_index","meteora_ix","start_lamports",
          "pump_snapshot_base_out","pump_snapshot_net_out",
          "pump_snapshot_max_quote","pre_sim_net_lamports")

def verify(row):
    if not isinstance(row,dict) or any(k not in row for k in REQUIRED):
        raise HandoffHold("CANONICAL_ROUTE_FIELDS_MISSING")
    direction,ixs=canonical_instructions(row)
    if type(row["start_lamports"]) is not int or row["start_lamports"] != 10_000_000:
        raise HandoffHold("EXACT_010_SIZE_REQUIRED")
    for k in ("pump_snapshot_base_out","pump_snapshot_net_out","pump_snapshot_max_quote"):
        if type(row[k]) is not int or row[k] <= 0:
            raise HandoffHold("PROTECTED_BOUND_MISSING")
    if type(row["pre_sim_net_lamports"]) is not int or row["pre_sim_net_lamports"] <= 0:
        raise HandoffHold("NOT_POSITIVE_PRE_SIM")
    if row.get("execution_authority") is True:
        raise HandoffHold("UNSAFE_AUTHORITY_INPUT")
    if not isinstance(row.get("token"),str) or not row["token"]:
        raise HandoffHold("TOKEN_LINEAGE_MISSING")
    if not isinstance(row.get("pump_ix"),dict):
        raise HandoffHold("PUMP_INSTRUCTION_MISSING")
    if row["pump_ix"] != row["pump_ixs"][row["pump_index"]]:
        raise HandoffHold("PUMP_INSTRUCTION_DRIFT")
    # Structural screening only: cannot certify IDL data or protected economics.
    return {"direction":direction,"instruction_count":len(ixs),
            "token":row["token"],"size_lamports":row["start_lamports"],
            "protected_bounds_certified":False,"atomic_simulation_passed":False}

def _candidate(obj):
    if isinstance(obj,dict):
        if all(k in obj for k in ("pump_ixs","meteora_ix","pump_index")):
            yield obj
        for v in obj.values():
            if isinstance(v,(dict,list)):
                yield from _candidate(v)
    elif isinstance(obj,list):
        for v in obj:
            if isinstance(v,(dict,list)):
                yield from _candidate(v)

def capture(root, out, max_age=120, now=None):
    root=Path(root)
    if not root.is_dir():
        raise HandoffHold("STATE_DIRECTORY_NOT_FOUND")
    now=time.time() if now is None else now
    counts={"examined":0,"parseable":0,"candidate_routes":0,"accepted":0}
    valid=[]
    for file in root.rglob("*.json"):
        try:
            if counts["examined"]>=1500:
                break
            if file.is_symlink() or file.stat().st_size>2_000_000:
                continue
            if now-file.stat().st_mtime>max_age or file.stat().st_mtime>now+5:
                continue
            counts["examined"]+=1
            obj=json.loads(file.read_text(encoding="utf-8"))
            counts["parseable"]+=1
            for row in _candidate(obj):
                counts["candidate_routes"]+=1
                try:
                    evidence=verify(row)
                except (HandoffHold,TypeError,KeyError,ValueError):
                    continue
                counts["accepted"]+=1
                valid.append((file.stat().st_mtime,str(file),row,evidence))
        except (OSError,ValueError,RecursionError):
            continue
    if not valid:
        return {"status":"HOLD_NO_RECENT_CANONICAL_ROUTE","counts":counts},None
    valid.sort(key=lambda x:(x[0],x[1]),reverse=True)
    stamp,source,route,evidence=valid[0]
    dest=Path(out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(route,indent=2)+"\n",encoding="utf-8")
    return {"status":"ROUTE_CAPTURED_UNVERIFIED","counts":counts,
            "source":source,"source_age_seconds":round(now-stamp,3),
            "evidence":evidence,"output":str(dest)},dest

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--state-root",type=Path,default=Path.cwd()/"runtime_state")
    ap.add_argument("--max-age-seconds",type=int,default=120)
    ap.add_argument("--output",type=Path,default=Path.cwd()/
                    "runtime_state/oracle/oracle_live_execution/mtr_164_canonical_route.json")
    args=ap.parse_args(argv)
    if args.max_age_seconds<1 or args.max_age_seconds>3600:
        raise SystemExit("[HOLD] MAX_AGE_OUT_OF_BOUNDS")
    try:
        report,_=capture(args.state_root,args.output,args.max_age_seconds)
    except HandoffHold as exc:
        raise SystemExit("[HOLD] "+str(exc)) from exc
    print("[MTR164_RESULT]",report["status"])
    print("[MTR164_COUNTS]",json.dumps(report["counts"],sort_keys=True))
    if report.get("output"):
        print("[MTR164_CAPTURE]",report["output"])
        print("[MTR164_SOURCE]",report["source"])
        print("[MTR164_SOURCE_AGE_SECONDS]",report["source_age_seconds"])
    print("[PROTECTED_BOUNDS_VERIFIED] FALSE")
    print("[ATOMIC_SIMULATION] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
if __name__=="__main__":
    main()
