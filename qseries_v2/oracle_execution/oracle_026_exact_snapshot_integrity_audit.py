from __future__ import annotations
import argparse,inspect,json,re
from pathlib import Path

from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q60b2

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

TOKENS=("snapshot","submit","pending","dlmm_state","last_slot","generation","deepcopy","copy(")

def source_report():
    src=inspect.getsource(q20)
    hits={}
    lines=src.splitlines()
    for tok in TOKENS:
        rows=[]
        for i,line in enumerate(lines,1):
            if tok.lower() in line.lower():
                rows.append({"line":i,"text":line.rstrip()})
        hits[tok]=rows
    return src,hits

def live_identity_probe(root):
    state,_=q60b2.prepare_once(Path(root))
    pairs=list(state.get("pairs") or [])
    if not pairs:
        raise RuntimeError("ORACLE026_NO_EXACT_PAIRS")
    p=pairs[0]
    row={
        "token":str(p.token),
        "pair_id":id(p),
        "dlmm_state_id":id(p.dlmm_state),
        "arrays_id":id(p.arrays),
        "last_slot":int(getattr(p,"last_slot",0) or 0),
        "last_event_ns":int(getattr(p,"last_event_ns",0) or 0),
    }
    # Structural proof: a plain dict snapshot retaining these objects is shared.
    probe={
        "token":p.token,
        "dlmm_state":p.dlmm_state,
        "arrays":p.arrays,
        "last_slot":getattr(p,"last_slot",0),
    }
    row["plain_snapshot_dlmm_shared"]=probe["dlmm_state"] is p.dlmm_state
    row["plain_snapshot_arrays_shared"]=probe["arrays"] is p.arrays
    return state,row

def run():
    src,hits=source_report()
    state,ident=live_identity_probe(Path.cwd())

    direct_dlmm=bool(re.search(r'["\']dlmm_state["\']\s*:\s*[^,\n]+\.dlmm_state',src))
    has_deepcopy="deepcopy" in src
    has_generation=bool(re.search(r"\bgeneration\b",src,re.I))
    has_end_slot_check=bool(re.search(r"(end|current|latest).{0,40}(slot|generation)|(slot|generation).{0,40}(end|current|latest)",src,re.I|re.S))

    report={
        "oracle_build":"ORACLE-026",
        "exact_pairs":len(state.get("pairs") or []),
        "identity_probe":ident,
        "q20_direct_dlmm_reference_pattern":direct_dlmm,
        "q20_has_deepcopy":has_deepcopy,
        "q20_has_generation_term":has_generation,
        "q20_has_end_state_guard_pattern":has_end_slot_check,
        "source_hits":hits,
        "execution_authority":False,
        "paper_only":True,
        "real_money_moved":False,
        "broadcast":False,
    }

    Path("ORACLE_026_Q20_SNAPSHOT_SOURCE.txt").write_text(src,encoding="utf-8")
    out=Path("runtime_state/oracle/oracle_live_execution/oracle_026_exact_snapshot_integrity_audit.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("[ORACLE-026] EXACT SNAPSHOT INTEGRITY AUDIT",flush=True)
    print("[PAIR] token=%s pair_id=%s dlmm_state_id=%s arrays_id=%s"%(
        ident["token"][:12],ident["pair_id"],ident["dlmm_state_id"],ident["arrays_id"]
    ),flush=True)
    print("[IDENTITY] plain_dlmm_shared=%s plain_arrays_shared=%s"%(
        ident["plain_snapshot_dlmm_shared"],ident["plain_snapshot_arrays_shared"]
    ),flush=True)
    print("[Q20_SOURCE] direct_dlmm_reference=%s deepcopy=%s generation_term=%s end_guard_pattern=%s"%(
        direct_dlmm,has_deepcopy,has_generation,has_end_slot_check
    ),flush=True)
    for tok in ("snapshot","submit","pending","dlmm_state","last_slot","generation","deepcopy"):
        print("[Q20_HITS] %s=%d"%(tok,len(hits.get(tok) or [])),flush=True)
    print("[SOURCE_REPORT] ORACLE_026_Q20_SNAPSHOT_SOURCE.txt",flush=True)
    print("[REPORT] %s"%out,flush=True)
    print("[PRIVATE_KEY] not required",flush=True)
    print("[BROADCAST] disabled",flush=True)
    return 0

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.parse_args(argv)
    return run()

if __name__=="__main__":
    raise SystemExit(main())
