from pathlib import Path

p=Path("mtr_126_official_sdk_atomic_swap2_cutover.py")

p.write_text(r'''from __future__ import annotations
import json
from pathlib import Path

import mtr_119_canonical_alt_atomic_preflight as m119
import mtr_120_unsigned_envelope_physical_proof as m120

from qseries_v2.solana_live_execution import (
    qarb_097_official_meteora_sdk_executor as q97
)

OUT=Path("mtr_126_official_sdk_atomic_swap2_cutover.json")
ST={"official_builds":0,"failures":0}

def official_swap2_hot(token,input_amount,quote):
    t=m119.sae.METEORA_TEMPLATES.get(str(token))
    if t is None:
        raise RuntimeError("MTR126_TEMPLATE_MISSING")

    pool=str(t["pool"])

    try:
        built=q97.native_meteora_swap_ixs(
            m119.PUBLIC_USER,
            pool,
            str(token),
            m119.sae.q87.c.WSOL,
            int(input_amount),
        )
    except Exception:
        ST["failures"]+=1
        raise

    ixs=[
        x for x in built["instructions"]
        if x.get("programId")==m119.sae.q87.c.DLMM
    ]

    if len(ixs)!=1:
        raise RuntimeError(
            "MTR126_OFFICIAL_DLMM_IX_COUNT:%d"%len(ixs)
        )

    ix=ixs[0]

    if built.get("builder")!="OFFICIAL_SWAP2":
        raise RuntimeError(
            "MTR126_NOT_OFFICIAL_SWAP2:"
            +str(built.get("builder"))
        )

    if len(ix.get("accounts") or [])<16:
        raise RuntimeError("MTR126_OFFICIAL_ACCOUNT_COUNT_SHORT")

    ST["official_builds"]+=1

    print(
        "[MTR126_OFFICIAL_SWAP2] token=%s pool=%s "
        "accounts=%d sdk=%s version=%s input=%d min_out=%s"
        %(
            str(token)[:10],
            pool[:12],
            len(ix["accounts"]),
            built.get("sdk"),
            built.get("sdk_version"),
            int(input_amount),
            built.get("min_out"),
        ),
        flush=True,
    )

    return ix

def main():
    print("[MTR-126] START",flush=True)
    print(
        "[CUTOVER] official Meteora SDK Swap2 instruction "
        "inside canonical atomic transaction",
        flush=True,
    )
    print(
        "[ALT] "+m119.ALT,
        flush=True,
    )
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)

    # Replace only the defective handwritten Meteora instruction seam.
    m119.sae.build_meteora_ix_hot=official_swap2_hot

    # Preserve MTR-120's physically proven unsigned simulation envelope.
    m119.sae.simulate_current=m120.simulate_nonsecret_envelope
    m120.ST={
        "calls":0,
        "zero_before":0,
        "dummy_after":0,
    }

    m119.OUT=Path(
        "mtr_126_underlying_atomic_preflight.json"
    )

    m119.main()

    src=json.loads(
        m119.OUT.read_text(encoding="utf-8")
    )

    rows=src.get("atomic_rows") or []

    errors=[
        x.get("sim_err") or x.get("error")
        for x in rows
    ]

    still_3002=any(
        "3002" in str(x)
        for x in errors
    )

    out={
        "mtr":"MTR-126",
        "official_swap2_builds":
            ST["official_builds"],
        "official_build_failures":
            ST["failures"],
        "atomic_attempts":
            src.get("atomic_attempts"),
        "compiled":
            src.get("compiled"),
        "simulated":
            src.get("simulated"),
        "atomic_pass":
            src.get("atomic_pass"),
        "still_3002":
            still_3002,
        "atomic_rows":
            rows[-20:],
        "alt":
            m119.ALT,
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(
            out,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    print(
        "[MTR126_SUMMARY] official=%d failures=%d "
        "attempts=%s compiled=%s simulated=%s "
        "atomic_pass=%s still_3002=%s"
        %(
            ST["official_builds"],
            ST["failures"],
            out["atomic_attempts"],
            out["compiled"],
            out["simulated"],
            out["atomic_pass"],
            out["still_3002"],
        ),
        flush=True,
    )

    if int(out["atomic_pass"] or 0)>0:
        print(
            "[RESULT] ATOMIC_TWO_LEG_PREFLIGHT_PASS",
            flush=True,
        )
    elif int(out["atomic_attempts"] or 0)>0 and not still_3002:
        print(
            "[RESULT] OFFICIAL_SWAP2_3002_CLEARED_NEXT_BLOCKER_EXPOSED",
            flush=True,
        )
    elif int(out["atomic_attempts"] or 0)>0:
        print(
            "[RESULT] OFFICIAL_SWAP2_ATOMIC_NOT_CERTIFIED",
            flush=True,
        )
    else:
        print(
            "[RESULT] NO_FRESH_P2M_010_POSITIVE_IN_WINDOW",
            flush=True,
        )

    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-126] COMPLETE",flush=True)

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] official SDK Swap2 atomic cutover")
print("[SCOPE] canonical ALT + official Meteora instruction; no key; no send")