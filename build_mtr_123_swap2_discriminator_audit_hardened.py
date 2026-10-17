from pathlib import Path

p=Path("mtr_123_swap2_discriminator_audit_hardened.py")

p.write_text(r'''from __future__ import annotations
import hashlib,json,time
from pathlib import Path

import mtr_118_target_only_24_route_scale as b118
import mtr_119_canonical_alt_atomic_preflight as m119

from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as sae

OUT=Path("mtr_123_swap2_discriminator_audit_hardened.json")

def disc(name):
    return hashlib.sha256(("account:"+name).encode()).digest()[:8]

EXPECTED={
    "LB_PAIR":disc("LbPair"),
    "ORACLE":disc("Oracle"),
    "BITMAP":disc("BinArrayBitmapExtension"),
    "BIN_ARRAY":disc("BinArray"),
}

def account_retry(address):
    last=None
    for attempt in range(1,9):
        try:
            return sae.q87.c.account(address)
        except Exception as e:
            last=e
            if "429" not in str(e):
                raise
            delay=min(.75*(2**(attempt-1)),6.0)
            print(
                "[MTR123_429] addr=%s attempt=%d sleep=%.2f"
                %(address[:12],attempt,delay),
                flush=True,
            )
            time.sleep(delay)
    raise last

def inspect(label,address,expected):
    if address==sae.q87.c.DLMM:
        return {
            "label":label,
            "address":address,
            "sentinel":True,
            "ok":True,
        }

    raw,owner=account_retry(address)
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
        "[MTR123_ACCOUNT] label=%s addr=%s actual=%s expected=%s ok=%s"
        %(label,address[:12],actual.hex(),expected.hex(),row["ok"]),
        flush=True,
    )
    return row

def main():
    print("[MTR-123] START",flush=True)
    print("[SCOPE] hardened Swap2 discriminator audit",flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
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

    for n,(key,t) in enumerate(sorted(m119.ROUTE_METEORA.items()),1):
        fixed=list(t["fixed_accounts"])
        checks=[
            inspect("LB_PAIR",str(t["pool"]),EXPECTED["LB_PAIR"]),
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
            time.sleep(.12)

        failures=[
            x for x in checks
            if not x.get("sentinel") and not x["ok"]
        ]

        row={
            "route":key,
            "pool":str(t["pool"]),
            "checks":checks,
            "failures":failures,
        }
        rows.append(row)

        print(
            "[MTR123_ROUTE] %d/%d failures=%d"
            %(n,len(m119.ROUTE_METEORA),len(failures)),
            flush=True,
        )

        if failures:
            bad.append(row)
            print(
                "[MTR123_ROUTE_BAD] route=%s failures=%s"
                %(key[-24:],",".join(x["label"] for x in failures)),
                flush=True,
            )

        time.sleep(.35)

    out={
        "mtr":"MTR-123",
        "routes":len(rows),
        "bad_routes":len(bad),
        "bad":bad,
        "expected":{k:v.hex() for k,v in EXPECTED.items()},
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }

    OUT.write_text(
        json.dumps(out,indent=2,sort_keys=True),
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
    elif len(rows)==24:
        print(
            "[RESULT] SWAP2_TYPED_DISCRIMINATORS_ALL_MATCH",
            flush=True,
        )
    else:
        print(
            "[RESULT] SWAP2_DISCRIMINATOR_AUDIT_INCOMPLETE",
            flush=True,
        )

    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-123] COMPLETE",flush=True)

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] hardened Swap2 typed-account discriminator audit")
print("[SCOPE] retry/backoff only; no transaction; no signing; no send")