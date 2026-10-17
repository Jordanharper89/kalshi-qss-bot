from __future__ import annotations
import base64,json
from pathlib import Path

import mtr_118_target_only_24_route_scale as b118
import mtr_119_canonical_alt_atomic_preflight as m119
import mtr_121_meteora_swap2_atomic_cutover as m121

from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as sae
from qseries_v2.solana_live_execution import qarb_097_official_meteora_sdk_executor as q97

OUT=Path("mtr_125_warm_official_sdk_swap2_diff.json")
TARGET="98kfF7rmsg"

def key(s):
    return "%s|%s|%s"%(s["token"],s["pump_pool"],s["meteora"]["address"])

def metas(ix):
    return [
        (x["pubkey"],bool(x["isSigner"]),bool(x["isWritable"]))
        for x in ix["accounts"]
    ]

def main():
    print("[MTR-125] START",flush=True)
    print("[SCOPE] warm-repaired MTR-121 Swap2 vs official SDK",flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[BROADCAST] FALSE",flush=True)

    state,_=b118.prepare_once(Path.cwd())
    q25.bind_cached_state(state)
    warmed=q25.install_hot_math_and_prewarm(state)
    m119.prebuild_route_templates(state,m119.PUBLIC_USER,warmed)

    pairs=[p for p in state["pairs"] if str(p.token).startswith(TARGET)]
    if not pairs:
        raise RuntimeError("MTR125_TARGET_NOT_FOUND")

    # MTR-124 omission: exact Pump worker must be warm before q18 pricing.
    pumps=sorted({str(p.pump_pool) for p in pairs})
    for pool in pumps:
        q18.worker().warm(pool)
        print("[MTR125_PUMP_WARM] pool="+pool,flush=True)

    rows=[]

    for p in pairs:
        snap=sae.immutable_snapshot(p)
        rk=key(snap)

        template=m119.ROUTE_METEORA.get(rk)
        if template is None:
            raise RuntimeError("ROUTE_TEMPLATE_MISSING")

        sae.METEORA_TEMPLATES[str(p.token)]=template

        opps=q18.exact_snapshot_opportunities(snap,0.010)
        opp=next(
            x for x in opps
            if x["direction"]=="PUMP_TO_METEORA"
        )

        amount=int(opp["pump_base_out_net"])
        quote=dict(opp["mq"])

        ours=m121.swap2_hot(str(p.token),amount,quote)

        official=q97.native_meteora_swap_ixs(
            m119.PUBLIC_USER,
            str(p.meteora_pool),
            str(p.token),
            sae.q87.c.WSOL,
            amount,
        )

        dlmm=[
            x for x in official["instructions"]
            if x["programId"]==sae.q87.c.DLMM
        ]
        if len(dlmm)!=1:
            raise RuntimeError(
                "OFFICIAL_DLMM_IX_COUNT:"+str(len(dlmm))
            )

        sdk=dlmm[0]
        a=metas(ours)
        b=metas(sdk)
        diffs=[]

        for i in range(max(len(a),len(b))):
            av=a[i] if i<len(a) else None
            bv=b[i] if i<len(b) else None
            if av!=bv:
                diffs.append({"index":i,"ours":av,"sdk":bv})
                print(
                    "[MTR125_META_DIFF] index=%d ours=%s sdk=%s"
                    %(i,av,bv),
                    flush=True,
                )

        od=base64.b64decode(ours["data"])
        sd=base64.b64decode(sdk["data"])

        row={
            "route":rk,
            "pool":str(p.meteora_pool),
            "amount":amount,
            "ours_accounts":len(a),
            "sdk_accounts":len(b),
            "meta_diffs":diffs,
            "ours_data_hex":od.hex(),
            "sdk_data_hex":sd.hex(),
            "data_equal":od==sd,
            "ours_data_len":len(od),
            "sdk_data_len":len(sd),
            "sdk_builder":official.get("builder"),
            "sdk_version":official.get("sdk_version"),
        }
        rows.append(row)

        print(
            "[MTR125_ROUTE] pool=%s ours=%d sdk=%d "
            "meta_diffs=%d data_equal=%s data_len=%d/%d"
            %(str(p.meteora_pool)[:12],len(a),len(b),
              len(diffs),od==sd,len(od),len(sd)),
            flush=True,
        )

    out={
        "mtr":"MTR-125",
        "routes":rows,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,default=str),
        encoding="utf-8",
    )

    meta_diff=sum(len(x["meta_diffs"]) for x in rows)
    data_diff=sum(not x["data_equal"] for x in rows)

    print(
        "[SUMMARY] routes=%d meta_diffs=%d data_diffs=%d"
        %(len(rows),meta_diff,data_diff),
        flush=True,
    )

    if meta_diff or data_diff:
        print(
            "[RESULT] OFFICIAL_SWAP2_CONTRACT_DIFFERENCE_PHYSICALLY_IDENTIFIED",
            flush=True,
        )
    else:
        print(
            "[RESULT] OUR_SWAP2_MATCHES_OFFICIAL_SDK",
            flush=True,
        )

    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-125] COMPLETE",flush=True)

if __name__=="__main__":
    main()
