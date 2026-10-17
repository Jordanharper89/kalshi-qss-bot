from __future__ import annotations
import base64,json,struct
from pathlib import Path

import mtr_119_canonical_alt_atomic_preflight as m119
import mtr_120_unsigned_envelope_physical_proof as m120
import mtr_128_fresh_official_two_leg_revalidation as m128

from qseries_v2.solana_live_execution import (
    qarb_097_official_meteora_sdk_executor as q97
)

OUT=Path("mtr_130_official_buy_atomic_revalidation.json")
ST={"routes":0,"holds":0,"buy":0,"exact_quote":0}

def route(user,snap,opp):
    if opp.get("direction")!="PUMP_TO_METEORA":
        raise RuntimeError("MTR130_DIRECTION_NOT_CERTIFIED")

    token=str(snap["token"])
    start=int(opp["start"])
    pool=str(snap["pump_pool"])

    p_ixs,pump_quote=m128.retry(
        lambda:m119.sae.q87.las.q59.native_pump_buy_ixs(
            user,pool,start
        ),
        "PUMP",
    )

    pp=[
        i for i,x in enumerate(p_ixs)
        if x.get("programId")==m119.sae.q87.c.PUMP
    ]
    if len(pp)!=1:
        raise RuntimeError("MTR130_PUMP_IX_COUNT:"+str(len(pp)))

    pi=pp[0]
    pix=p_ixs[pi]
    raw=base64.b64decode(pix.get("data") or "")

    if len(raw)<24:
        raise RuntimeError("MTR130_PUMP_DATA_SHORT")

    disc=raw[:8]

    if disc==m119.sae.BUY_DISC:
        base_for_meteora=struct.unpack("<Q",raw[8:16])[0]
        max_quote=struct.unpack("<Q",raw[16:24])[0]
        ST["buy"]+=1
        family="BUY"

    elif disc==m119.sae.BUY_EXACT_QUOTE_IN_DISC:
        max_quote=struct.unpack("<Q",raw[8:16])[0]
        base_for_meteora=struct.unpack("<Q",raw[16:24])[0]
        ST["exact_quote"]+=1
        family="BUY_EXACT_QUOTE_IN"

    else:
        raise RuntimeError(
            "MTR130_UNKNOWN_PUMP_DISC:"+disc.hex()
        )

    if base_for_meteora<=0 or max_quote<=0:
        raise RuntimeError("MTR130_BAD_PUMP_BOUNDS")

    rk="%s|%s|%s"%(
        token,
        snap["pump_pool"],
        snap["meteora"]["address"],
    )
    mt=m119.ROUTE_METEORA.get(rk)

    if mt is None:
        raise RuntimeError("MTR130_METEORA_TEMPLATE_MISSING")

    mb=m128.retry(
        lambda:q97.native_meteora_swap_ixs(
            user,
            str(mt["pool"]),
            token,
            m119.sae.q87.c.WSOL,
            int(base_for_meteora),
        ),
        "METEORA",
    )

    dlmm=[
        x for x in mb["instructions"]
        if x.get("programId")==m119.sae.q87.c.DLMM
    ]
    if len(dlmm)!=1:
        raise RuntimeError(
            "MTR130_DLMM_IX_COUNT:"+str(len(dlmm))
        )

    meteora_min=int(mb.get("min_out") or 0)
    floor_net=meteora_min-max_quote
    floor_bps=floor_net/max_quote*10000.0

    print(
        "[MTR130_REVALIDATE] token=%s family=%s "
        "pump_quote=%d base_out=%d max_quote=%d "
        "meteora_min=%d floor_net=%+d floor_bps=%+.2f"
        %(
            token[:10],family,int(pump_quote),
            base_for_meteora,max_quote,
            meteora_min,floor_net,floor_bps,
        ),
        flush=True,
    )

    if floor_net<=0:
        ST["holds"]+=1
        raise RuntimeError(
            "MTR130_WORST_CASE_NOT_POSITIVE:"
            +str(floor_net)
        )

    ST["routes"]+=1

    return {
        "token":token,
        "start_lamports":max_quote,
        "pre_sim_net_lamports":floor_net,
        "pre_sim_bps":floor_bps,
        "pump_snapshot_base_out":base_for_meteora,
        "pump_snapshot_net_out":base_for_meteora,
        "pump_snapshot_max_quote":max_quote,
        "pump_ixs":p_ixs,
        "pump_index":pi,
        "pump_ix":pix,
        "meteora_ix":dlmm[0],
        "base_alts":[],
        "original_candidates":
            m119.sae.q87.las.q59.candidate_instruction_sets(
                p_ixs,dlmm[0]
            ),
    }

def main():
    print("[MTR-130] START",flush=True)
    print("[CUTOVER] official Pump BUY semantics -> official Meteora",flush=True)
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

    m119.sae.same_snapshot_route=route
    m119.sae.simulate_current=m120.simulate_nonsecret_envelope
    m120.ST={"calls":0,"zero_before":0,"dummy_after":0}
    m119.OUT=Path("mtr_130_underlying_atomic_preflight.json")

    m119.main()

    src=json.loads(m119.OUT.read_text(encoding="utf-8"))
    rows=src.get("atomic_rows") or []
    errors=[x.get("sim_err") or x.get("error") for x in rows]

    out={
        "mtr":"MTR-130",
        **ST,
        "atomic_attempts":src.get("atomic_attempts"),
        "compiled":src.get("compiled"),
        "simulated":src.get("simulated"),
        "atomic_pass":src.get("atomic_pass"),
        "still_6040":any("6040" in str(x) for x in errors),
        "rows":rows[-20:],
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    print(
        "[MTR130_SUMMARY] routes=%d holds=%d buy=%d exact=%d "
        "attempts=%s compiled=%s simulated=%s atomic_pass=%s "
        "still_6040=%s"
        %(
            ST["routes"],ST["holds"],ST["buy"],ST["exact_quote"],
            out["atomic_attempts"],out["compiled"],out["simulated"],
            out["atomic_pass"],out["still_6040"],
        ),
        flush=True,
    )

    if int(out["atomic_pass"] or 0)>0:
        print("[RESULT] ATOMIC_TWO_LEG_PREFLIGHT_PASS",flush=True)
    elif ST["holds"]>0 and ST["routes"]==0:
        print("[RESULT] FRESH_WORST_CASE_ECONOMICS_HOLD",flush=True)
    elif int(out["atomic_attempts"] or 0)>0:
        print("[RESULT] OFFICIAL_BUY_NEXT_BLOCKER_EXPOSED",flush=True)
    else:
        print("[RESULT] NO_FRESH_P2M_POSITIVE_IN_WINDOW",flush=True)

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-130] COMPLETE")

if __name__=="__main__":
    main()
