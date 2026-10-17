from pathlib import Path

p=Path("mtr_128_fresh_official_two_leg_revalidation.py")

p.write_text(r'''from __future__ import annotations
import base64,json,struct,time
from pathlib import Path

import mtr_119_canonical_alt_atomic_preflight as m119
import mtr_120_unsigned_envelope_physical_proof as m120

from qseries_v2.solana_live_execution import (
    qarb_097_official_meteora_sdk_executor as q97
)

OUT=Path("mtr_128_fresh_official_two_leg_revalidation.json")
ST={"routes":0,"pump_builds":0,"meteora_builds":0,"holds":0}

def retry(fn,label):
    last=None
    for n in range(1,6):
        try:
            return fn()
        except Exception as e:
            last=e
            if "429" not in str(e):
                raise
            d=min(.6*(2**(n-1)),5.0)
            print("[MTR128_429] stage=%s attempt=%d sleep=%.1f"%(label,n,d),flush=True)
            time.sleep(d)
    raise last

def fresh_official_route(user,snap,opp):
    if opp.get("direction")!="PUMP_TO_METEORA":
        raise RuntimeError("MTR128_DIRECTION_NOT_CERTIFIED")

    token=str(snap["token"])
    start=int(opp["start"])
    pool=str(snap["pump_pool"])

    pump_ixs,pump_quote_out=retry(
        lambda:m119.sae.q87.las.q59.native_pump_buy_ixs(
            user,pool,start
        ),
        "PUMP",
    )
    ST["pump_builds"]+=1

    pump_indexes=[
        i for i,x in enumerate(pump_ixs)
        if x.get("programId")==m119.sae.q87.c.PUMP
    ]
    if len(pump_indexes)!=1:
        raise RuntimeError("MTR128_PUMP_IX_COUNT:"+str(len(pump_indexes)))

    pi=pump_indexes[0]
    pump_ix=pump_ixs[pi]
    raw=base64.b64decode(pump_ix.get("data") or "")

    if len(raw)<24:
        raise RuntimeError("MTR128_PUMP_DATA_SHORT")

    if raw[:8]!=m119.sae.BUY_EXACT_QUOTE_IN_DISC:
        raise RuntimeError(
            "MTR128_PUMP_NOT_EXACT_QUOTE_IN:"+raw[:8].hex()
        )

    spendable=struct.unpack("<Q",raw[8:16])[0]
    pump_min_base=struct.unpack("<Q",raw[16:24])[0]

    if spendable!=start:
        raise RuntimeError(
            "MTR128_SPEND_DRIFT:%d:%d"%(spendable,start)
        )

    if pump_min_base<=0:
        raise RuntimeError("MTR128_PUMP_MIN_BASE_ZERO")

    mt=m119.ROUTE_METEORA.get(
        "%s|%s|%s"%(
            token,
            snap["pump_pool"],
            snap["meteora"]["address"],
        )
    )
    if mt is None:
        raise RuntimeError("MTR128_METEORA_ROUTE_TEMPLATE_MISSING")

    meteora_pool=str(mt["pool"])

    built=retry(
        lambda:q97.native_meteora_swap_ixs(
            user,
            meteora_pool,
            token,
            m119.sae.q87.c.WSOL,
            pump_min_base,
        ),
        "METEORA",
    )
    ST["meteora_builds"]+=1

    dlmm=[
        x for x in built["instructions"]
        if x.get("programId")==m119.sae.q87.c.DLMM
    ]
    if len(dlmm)!=1:
        raise RuntimeError("MTR128_DLMM_IX_COUNT:"+str(len(dlmm)))

    meteora_min=int(built.get("min_out") or 0)
    floor_net=meteora_min-start
    floor_bps=floor_net/start*10000.0

    print(
        "[MTR128_REVALIDATE] token=%s pump_quote=%d pump_min=%d "
        "meteora_min=%d floor_net=%+d floor_bps=%+.2f"
        %(token[:10],int(pump_quote_out),pump_min_base,
          meteora_min,floor_net,floor_bps),
        flush=True,
    )

    if floor_net<=0:
        ST["holds"]+=1
        raise RuntimeError(
            "MTR128_WORST_CASE_NOT_POSITIVE:"
            +str(floor_net)
        )

    ST["routes"]+=1

    return {
        "token":token,
        "start_lamports":start,
        "pre_sim_net_lamports":floor_net,
        "pre_sim_bps":floor_bps,
        "pump_snapshot_base_out":int(pump_quote_out),
        "pump_snapshot_net_out":pump_min_base,
        "pump_snapshot_max_quote":start,
        "pump_ixs":pump_ixs,
        "pump_index":pi,
        "pump_ix":pump_ix,
        "meteora_ix":dlmm[0],
        "base_alts":[],
        "original_candidates":
            m119.sae.q87.las.q59.candidate_instruction_sets(
                pump_ixs,
                dlmm[0],
            ),
    }

def main():
    print("[MTR-128] START",flush=True)
    print("[CUTOVER] fresh official PumpSwap + official Meteora worst-case chain",flush=True)
    print("[ALT] "+m119.ALT,flush=True)
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

    m119.sae.same_snapshot_route=fresh_official_route
    m119.sae.simulate_current=m120.simulate_nonsecret_envelope
    m120.ST={"calls":0,"zero_before":0,"dummy_after":0}
    m119.OUT=Path("mtr_128_underlying_atomic_preflight.json")

    m119.main()

    src=json.loads(m119.OUT.read_text(encoding="utf-8"))
    rows=src.get("atomic_rows") or []
    errors=[x.get("sim_err") or x.get("error") for x in rows]

    still_6040=any("6040" in str(x) for x in errors)

    out={
        "mtr":"MTR-128",
        **ST,
        "atomic_attempts":src.get("atomic_attempts"),
        "compiled":src.get("compiled"),
        "simulated":src.get("simulated"),
        "atomic_pass":src.get("atomic_pass"),
        "still_6040":still_6040,
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
        "[MTR128_SUMMARY] routes=%d holds=%d attempts=%s "
        "compiled=%s simulated=%s atomic_pass=%s still_6040=%s"
        %(ST["routes"],ST["holds"],out["atomic_attempts"],
          out["compiled"],out["simulated"],
          out["atomic_pass"],out["still_6040"]),
        flush=True,
    )

    if int(out["atomic_pass"] or 0)>0:
        print("[RESULT] ATOMIC_TWO_LEG_PREFLIGHT_PASS",flush=True)
    elif int(out["atomic_attempts"] or 0)>0 and not still_6040:
        print("[RESULT] PUMP_6040_CLEARED_NEXT_BLOCKER_EXPOSED",flush=True)
    elif ST["holds"]>0:
        print("[RESULT] FRESH_WORST_CASE_ECONOMICS_HOLD",flush=True)
    else:
        print("[RESULT] ATOMIC_TWO_LEG_NOT_CERTIFIED",flush=True)

    print("[OUTPUT] "+str(OUT))
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[MTR-128] COMPLETE")

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] fresh official Pump -> guaranteed minimum -> official Meteora")
print("[SCOPE] unsigned atomic simulation only; no key; no send")