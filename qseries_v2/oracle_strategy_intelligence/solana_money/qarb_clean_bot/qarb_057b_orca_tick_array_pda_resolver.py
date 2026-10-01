from __future__ import annotations
import hashlib,json,struct,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
PROGRAM="whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_056c_orca_tick_fee_state.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_057b_orca_tick_array_pda_resolver.json")
TICK_ARRAY_SIZE=88
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
P=2**255-19
D=(-121665*pow(121666,P-2,P))%P
I=pow(2,(P-1)//4,P)

def b58d(s):
    n=0
    for ch in s:n=n*58+ALPH.index(ch)
    h=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    z=0
    for ch in s:
        if ch=="1":z+=1
        else:break
    return b"\0"*z+h

def b58e(b):
    n=int.from_bytes(b,"big");out=""
    while n:n,r=divmod(n,58);out=ALPH[r]+out
    z=0
    for x in b:
        if x==0:z+=1
        else:break
    return "1"*z+(out or "")

def on_curve(s):
    if len(s)!=32:return False
    y=int.from_bytes(s,"little")&((1<<255)-1)
    if y>=P:return False
    u=(y*y-1)%P;v=(D*y*y+1)%P
    x2=u*pow(v,P-2,P)%P
    x=pow(x2,(P+3)//8,P)
    if (x*x-x2)%P:x=x*I%P
    return (x*x-x2)%P==0

def pda(seeds,program):
    pb=b58d(program)
    for bump in range(255,-1,-1):
        h=hashlib.sha256(b"".join(seeds)+bytes([bump])+pb+b"ProgramDerivedAddress").digest()
        if not on_curve(h):return b58e(h),bump
    raise RuntimeError("NO_PDA")

def start_index(tick,spacing):
    width=TICK_ARRAY_SIZE*int(spacing)
    return (int(tick)//width)*width

def _read(a):
    try:return c.account(a)
    except Exception:return None,None

def resolve(pool,tick,spacing):
    base=start_index(tick,spacing);width=TICK_ARRAY_SIZE*spacing
    out={}
    for direction,starts in {
        "A_TO_B":[base,base-width,base-2*width],
        "B_TO_A":[base,base+width,base+2*width]}.items():
        seq=[]
        for s in starts:
            addr,bump=pda([b"tick_array",b58d(pool),str(s).encode()],PROGRAM)
            raw,slot=_read(addr)
            seq.append({"start_tick_index":s,"address":addr,"bump":bump,
                        "exists":raw is not None,"bytes":len(raw) if raw is not None else 0,"slot":slot})
        out[direction]=seq
    return out

def build(root):
    root=Path(root);src=root/SRC
    if not src.is_file():raise RuntimeError("QARB_056C_ARTIFACT_MISSING")
    o=json.loads(src.read_text(encoding="utf-8"));rows=[]
    for r0 in o.get("rows") or []:
        st=r0.get("state") or {};pool=r0["pool"]
        seq=resolve(pool,int(st["tick_current"]),int(st["tick_spacing"]))
        rows.append({"pool":pool,"tick":st["tick_current"],"spacing":st["tick_spacing"],"sequences":seq,
                     "a_to_b_live":sum(1 for x in seq["A_TO_B"] if x["exists"]),
                     "b_to_a_live":sum(1 for x in seq["B_TO_A"] if x["exists"])})
    payload={"revision":"QARB_057B","rows":rows,"pools":len(rows),
             "both_direction_sequences_ready":sum(1 for r in rows if r["a_to_b_live"] and r["b_to_a_live"]),
             "full_3x3_ready":sum(1 for r in rows if r["a_to_b_live"]==3 and r["b_to_a_live"]==3),
             "priced_live":False,"next":"ORCA_LOCAL_SWAP_STEP_ENGINE_FROM_RESOLVED_TICK_ARRAYS",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-057B] ORCA TICK ARRAY PDA RESOLVER")
    print("[ORCA] pools=%d both_direction_ready=%d full_3x3_ready=%d priced_live=%s"%(
        p["pools"],p["both_direction_sequences_ready"],p["full_3x3_ready"],p["priced_live"]))
    for r in p["rows"]:
        print("[ORCA_TICKS] %s A_TO_B=%d/3 B_TO_A=%d/3 tick=%s spacing=%s"%(
            r["pool"][:12],r["a_to_b_live"],r["b_to_a_live"],r["tick"],r["spacing"]))
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
