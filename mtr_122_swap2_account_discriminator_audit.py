from __future__ import annotations
import hashlib,json
from pathlib import Path

import mtr_118_target_only_24_route_scale as b118
import mtr_119_canonical_alt_atomic_preflight as m119

from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as sae

OUT=Path("mtr_122_swap2_account_discriminator_audit.json")

def disc(name):
    return hashlib.sha256(("account:"+name).encode()).digest()[:8]

EXPECTED={
    "LB_PAIR":disc("LbPair"),
    "ORACLE":disc("Oracle"),
    "BITMAP":disc("BinArrayBitmapExtension"),
    "BIN_ARRAY":disc("BinArray"),
}

def inspect(label,address,expected):
    if address==sae.q87.c.DLMM:
        return {
            "label":label,
            "address":address,
            "sentinel":True,
            "ok":True,
        }

    raw,owner=sae.q87.c.account(address)
    actual=raw[:8]

    row={
        "label":label,
        "address":address,
        "owner":owner,
        "bytes":len(raw),
        "actual":actual.hex(),
        "expected":expected.hex(),
        "ok":actual==expected,
    }

    print(
        "[MTR122_ACCOUNT] label=%s addr=%s owner=%s bytes=%d "
        "actual=%s expected=%s ok=%s"
        %(label,address[:12],owner[:12],len(raw),
          actual.hex(),expected.hex(),row["ok"]),
        flush=True,
    )
    return row

def main():
    print("[MTR-122] START",flush=True)
    print("[SCOPE] Swap2 typed-account discriminator audit only",flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)

    state,_=b118.prepare_once(Path.cwd())
    q25.bind_cached_state(state)
    warmed=q25.install_hot_math_and_prewarm(state)

    m119.prebuild_route_templates(
        state,
        m119.PUBLIC_USER,
        warmed,
    )

    rows=[]
    bad=[]

    for key,t in sorted(m119.ROUTE_METEORA.items()):
        fixed=list(t["fixed_accounts"])

        # Existing prebuild template positions:
        # 0 lb_pair
        # 1 optional bitmap/sentinel
        # 8 oracle
        pool=str(t["pool"])

        checks=[
            inspect("LB_PAIR",pool,EXPECTED["LB_PAIR"]),
            inspect("ORACLE",fixed[8][0],EXPECTED["ORACLE"]),
            inspect("BITMAP",fixed[1][0],EXPECTED["BITMAP"]),
        ]

        for i,(_,addr) in enumerate(t["arrays"]):
            checks.append(
                inspect(
                    "BIN_ARRAY_%d"%i,
                    str(addr),
                    EXPECTED["BIN_ARRAY"],
                )
            )

        failures=[
            x for x in checks
            if not x.get("sentinel") and not x["ok"]
        ]

        row={
            "route":key,
            "pool":pool,
            "checks":checks,
            "failures":failures,
        }
        rows.append(row)

        if failures:
            bad.append(row)
            print(
                "[MTR122_ROUTE_BAD] route=%s failures=%s"
                %(key[-24:],
                  ",".join(x["label"] for x in failures)),
                flush=True,
            )

    result={
        "mtr":"MTR-122",
        "routes":len(rows),
        "bad_routes":len(bad),
        "bad":bad,
        "expected":{
            k:v.hex() for k,v in EXPECTED.items()
        },
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(result,indent=2,sort_keys=True),
        encoding="utf-8",
    )

    print(
        "[SUMMARY] routes=%d bad_routes=%d"
        %(len(rows),len(bad)),
        flush=True,
    )

    if bad:
        print(
            "[RESULT] SWAP2_DISCRIMINATOR_MISMATCH_PHYSICALLY_IDENTIFIED",
            flush=True,
        )
    else:
        print(
            "[RESULT] SWAP2_TYPED_DISCRIMINATORS_ALL_MATCH",
            flush=True,
        )

    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-122] COMPLETE",flush=True)

if __name__=="__main__":
    main()
