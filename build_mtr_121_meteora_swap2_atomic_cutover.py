from pathlib import Path

p = Path("mtr_121_meteora_swap2_atomic_cutover.py")

p.write_text(r'''from __future__ import annotations
import base64,json,struct
from pathlib import Path

import mtr_119_canonical_alt_atomic_preflight as m119
import mtr_120_unsigned_envelope_physical_proof as m120

OUT=Path("mtr_121_meteora_swap2_atomic_cutover.json")
SWAP2=bytes([65,75,63,76,235,91,91,136])

def swap2_hot(token,input_amount,quote):
    s=m119.sae
    t=s.METEORA_TEMPLATES.get(str(token))
    if t is None:
        raise RuntimeError("MTR121_TEMPLATE_MISSING")

    if bool(quote.get("swap_for_y")) != bool(t["swap_for_y"]):
        raise RuntimeError("MTR121_DIRECTION_MISMATCH")

    old=list(t["fixed_accounts"])
    if len(old)!=15:
        raise RuntimeError("MTR121_OLD_FIXED_COUNT:%d"%len(old))

    # Existing proven template fields:
    # 0 pool,1 bitmap,2 rx,3 ry,4 source,5 dest,6 xmint,7 ymint,
    # 8 oracle,9 host(None sentinel),10 user,11 xprog,12 yprog,
    # 13 event_authority,14 program.
    pool,bitmap,rx,ry,src,dst,xm,ym,oracle,host,user,xp,yp,event,program=old

    fixed=[
        pool,                 # lb_pair
        oracle,               # oracle
        bitmap,               # optional bitmap extension
        rx,ry,                # reserves
        src,dst,              # user token in/out
        xm,ym,                # token mints
        host,                 # optional host_fee_in
        user,                 # signer
        xp,yp,                # token programs
        program,              # DLMM program
        event,                # event authority
        (s.q87.c.MEMO,False,False),  # memo program
    ]

    arrays=list(t["arrays"])
    crossed=max(1,int(quote.get("bins_crossed") or 1))
    n=min(len(arrays),max(1,(crossed+69)//70))
    chosen=arrays[:n] if bool(quote["swap_for_y"]) else list(reversed(arrays))[:n]

    accounts=list(fixed)
    accounts.extend((addr,False,True) for _,addr in chosen)

    min_out=int(quote["raw_out"])*(10000-s.q87.las.q59.SLIPPAGE_BPS)//10000

    # Swap2 args:
    # amount_in: u64
    # min_amount_out: u64
    # RemainingAccountsInfo { slices: Vec<_> } -> empty Vec = u32(0)
    data=SWAP2+struct.pack("<QQI",int(input_amount),int(min_out),0)

    print(
        "[MTR121_SWAP2] token=%s fixed=%d bins=%d accounts=%d "
        "disc=%s min_out=%d"
        %(str(token)[:10],len(fixed),len(chosen),len(accounts),
          SWAP2.hex(),min_out),
        flush=True,
    )

    return {
        "programId":s.q87.c.DLMM,
        "accounts":[
            {"pubkey":pk,"isSigner":sg,"isWritable":wr}
            for pk,sg,wr in accounts
        ],
        "data":base64.b64encode(data).decode(),
    }

def main():
    print("[MTR-121] START",flush=True)
    print("[CUTOVER] Meteora legacy swap -> official Swap2 contract",flush=True)
    print("[SWAP2_DISC] "+SWAP2.hex(),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)

    m119.sae.build_meteora_ix_hot=swap2_hot
    m119.sae.simulate_current=m120.simulate_nonsecret_envelope
    m119.OUT=Path("mtr_121_underlying_atomic_preflight.json")
    m120.ST={"calls":0,"zero_before":0,"dummy_after":0}

    m119.main()

    r=json.loads(m119.OUT.read_text(encoding="utf-8"))
    rows=r.get("atomic_rows") or []

    errors=[x.get("sim_err") or x.get("error") for x in rows]
    still_3005=any("3005" in str(x) for x in errors)

    out={
        "mtr":"MTR-121",
        "swap2_discriminator":SWAP2.hex(),
        "atomic_attempts":r.get("atomic_attempts"),
        "compiled":r.get("compiled"),
        "simulated":r.get("simulated"),
        "atomic_pass":r.get("atomic_pass"),
        "still_3005":still_3005,
        "atomic_rows":rows[-20:],
        "private_key_used":False,
        "signing":False,
        "broadcast":False,
    }
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str),encoding="utf-8")

    print(
        "[MTR121_SUMMARY] attempts=%s compiled=%s simulated=%s "
        "atomic_pass=%s still_3005=%s"
        %(out["atomic_attempts"],out["compiled"],out["simulated"],
          out["atomic_pass"],out["still_3005"]),
        flush=True,
    )

    if int(out["atomic_pass"] or 0)>0:
        print("[RESULT] METEORA_SWAP2_ATOMIC_TWO_LEG_PASS",flush=True)
    elif int(out["atomic_attempts"] or 0)>0 and not still_3005:
        print("[RESULT] SWAP2_3005_CLEARED_NEXT_BLOCKER_EXPOSED",flush=True)
    elif int(out["atomic_attempts"] or 0)>0:
        print("[RESULT] SWAP2_ACCOUNT_CONTRACT_NOT_CERTIFIED",flush=True)
    else:
        print("[RESULT] NO_FRESH_P2M_010_POSITIVE_IN_WINDOW",flush=True)

    print("[OUTPUT] "+str(OUT),flush=True)
    print("[PRIVATE_KEY] NOT_USED",flush=True)
    print("[SIGNING] FALSE",flush=True)
    print("[BROADCAST] FALSE",flush=True)
    print("[MTR-121] COMPLETE",flush=True)

if __name__=="__main__":
    main()
''',encoding="utf-8")

print("[BUILD] wrote",p)
print("[BUILD] Meteora Swap2 atomic account/data cutover")
print("[SCOPE] canonical ALT + dummy simulation envelope; no key; no send")