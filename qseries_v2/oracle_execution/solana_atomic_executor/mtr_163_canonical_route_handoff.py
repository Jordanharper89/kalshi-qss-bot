"""MTR-163: convert canonical same_snapshot_route output to the MTR-161 envelope.

No live route production, signer, RPC, or scanner mutation.
"""
import argparse, hashlib, json
from pathlib import Path
from .mtr_161_two_leg_unsigned_assembly import stage, AssemblyHold, CANONICAL, core

class HandoffHold(ValueError):
    pass

def canonical_instructions(route):
    if not isinstance(route, dict):
        raise HandoffHold("CANONICAL_ROUTE_REQUIRED")
    keys=("pump_ixs","pump_index","meteora_ix","start_lamports")
    if any(k not in route for k in keys):
        raise HandoffHold("REQUIRED_ROUTE_FIELDS_MISSING")
    pump_ixs=route["pump_ixs"]
    if not isinstance(pump_ixs,list) or not pump_ixs:
        raise HandoffHold("PUMP_INSTRUCTIONS_MISSING")
    index=route["pump_index"]
    if type(index) is not int or not 0<=index<len(pump_ixs):
        raise HandoffHold("INVALID_PUMP_INDEX")
    pump=pump_ixs[index]
    meteora=route["meteora_ix"]
    if pump.get("programId")!=core.PUMP or meteora.get("programId")!=core.DLMM:
        raise HandoffHold("NATIVE_SWAP_PROGRAM_MISMATCH")
    if any(x.get("programId")==core.DLMM for x in pump_ixs):
        raise HandoffHold("DUPLICATED_METEORA_PROGRAM")
    direction=route.get("direction","PUMP_TO_METEORA")
    if direction=="PUMP_TO_METEORA":
        instructions=pump_ixs[:index+1]+[meteora]+pump_ixs[index+1:]
    elif direction=="METEORA_TO_PUMP":
        instructions=pump_ixs[:index]+[meteora]+pump_ixs[index:]
    else:
        raise HandoffHold("DIRECTION_NOT_CERTIFIED")
    return direction,instructions

def package(route,payer,blockhash,alt_snapshot):
    direction,ixs=canonical_instructions(route)
    lamports=route["start_lamports"]
    if type(lamports) is not int:
        raise HandoffHold("INTEGER_LAMPORTS_REQUIRED")
    if not isinstance(alt_snapshot,dict) or CANONICAL not in alt_snapshot:
        raise HandoffHold("PUBLIC_CANONICAL_ALT_SNAPSHOT_REQUIRED")
    return {"direction":direction,"size_lamports":lamports,
            "payer":payer,"blockhash":blockhash,
            "alt_snapshot":alt_snapshot,"instructions":ixs}

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--route-json",type=Path)
    p.add_argument("--public-context-json",type=Path)
    p.add_argument("--output",type=Path,default=Path.cwd()/
                   "runtime_state/oracle/oracle_live_execution")
    a=p.parse_args(argv)
    if a.route_json is None or a.public_context_json is None:
        print("[MTR163] CANONICAL_ROUTE_OFFLINE_HANDOFF_READY")
        print("[REAL_ROUTE] HOLD_EXPLICIT_CANONICAL_ROUTE_AND_PUBLIC_CONTEXT_REQUIRED")
    else:
        try:
            for f in (a.route_json,a.public_context_json):
                if not f.is_file() or f.stat().st_size>150000:
                    raise HandoffHold("INPUT_MISSING_OR_OVERSIZE")
            r=json.loads(a.route_json.read_text(encoding="utf-8"))
            c=json.loads(a.public_context_json.read_text(encoding="utf-8"))
            pack=package(r,c["payer"],c["blockhash"],c["alt_snapshot"])
            report,tx,ev=stage(pack,a.output)
        except (HandoffHold,AssemblyHold,KeyError,ValueError,TypeError,OSError) as exc:
            raise SystemExit("[HOLD] MTR163_CANONICAL_HANDOFF_REFUSED:"+type(exc).__name__) from exc
        print("[MTR163_TRANSACTION_HASH]",report["transaction_sha256"])
        print("[MTR163_UNSIGNED_TX]",tx)
        print("[MTR163_REPORT]",ev)
    print("[PROTECTED_BOUNDS_VERIFIED] FALSE")
    print("[ATOMIC_TWO_LEG_SIMULATED] FALSE")
    print("[SCANNER] FROZEN")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__=="__main__":main()
