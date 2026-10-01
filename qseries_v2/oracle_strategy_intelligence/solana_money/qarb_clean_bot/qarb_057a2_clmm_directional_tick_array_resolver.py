from __future__ import annotations
import hashlib,json,struct,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
PROGRAM="CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_056b_clmm_tick_fee_state.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_057a2_clmm_directional_tick_array_resolver.json")
TICKS_PER_ARRAY=60
TICK_LEN=168
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
    u=(y*y-1)%P;v=(D*y*y+1)%P;x2=u*pow(v,P-2,P)%P
    x=pow(x2,(P+3)//8,P)
    if (x*x-x2)%P:x=x*I%P
    return (x*x-x2)%P==0

def pda(seeds,program):
    pb=b58d(program)
    for bump in range(255,-1,-1):
        h=hashlib.sha256(b"".join(seeds)+bytes([bump])+pb+b"ProgramDerivedAddress").digest()
        if not on_curve(h):return b58e(h),bump
    raise RuntimeError("NO_PDA")

def array_start(tick,spacing):
    width=TICKS_PER_ARRAY*int(spacing)
    q=int(tick)//width
    return q*width

def signed_be_i32(x):
    return int(x).to_bytes(4,"big",signed=True)

def tick_array_pda(pool,start):
    return pda([b"tick_array",b58d(pool),signed_be_i32(start)],PROGRAM)

def _read(a,tries=3):
    last=None
    for i in range(tries):
        try:return c.account(a)
        except Exception as e:
            last=e;time.sleep(.25*(i+1))
    return None,None

def decode(raw,pool):
    if raw is None:return None
    pb=b58d(pool)
    if len(raw)<44 or raw[8:40]!=pb:return None
    start=struct.unpack_from("<i",raw,40)[0]
    ticks=[];off=44
    for _ in range(TICKS_PER_ARRAY):
        if off+TICK_LEN>len(raw):break
        ti=struct.unpack_from("<i",raw,off)[0]
        gross=int.from_bytes(raw[off+20:off+36],"little")
        if gross:ticks.append(ti)
        off+=TICK_LEN
    return {"start_tick_index":start,"initialized_ticks":ticks,"initialized_count":len(ticks),"bytes":len(raw)}

def build(root):
    root=Path(root);src=root/SRC
    if not src.is_file():raise RuntimeError("QARB_056B_ARTIFACT_MISSING")
    o=json.loads(src.read_text(encoding="utf-8"));rows=[]
    for r0 in o.get("rows") or []:
        pool=r0["pool"];st=r0.get("state") or {};tick=int(st["tick_current"]);spacing=int(st["tick_spacing"])
        base=array_start(tick,spacing);width=TICKS_PER_ARRAY*spacing
        seqs={}
        for direction,starts in {
            "ZERO_FOR_ONE":[base,base-width,base-2*width,base-3*width],
            "ONE_FOR_ZERO":[base,base+width,base+2*width,base+3*width]}.items():
            seq=[]
            for s in starts:
                addr,bump=tick_array_pda(pool,s);raw,slot=_read(addr);dec=decode(raw,pool)
                seq.append({"start_tick_index":s,"address":addr,"bump":bump,"exists":dec is not None,
                            "slot":slot,"decoded":dec})
            seqs[direction]=seq
        below=[];above=[]
        for seq in seqs.values():
            for x in seq:
                d=x.get("decoded") or {}
                for t in d.get("initialized_ticks") or []:
                    if t<=tick:below.append(t)
                    if t>tick:above.append(t)
        rows.append({"pool":pool,"tick":tick,"spacing":spacing,"base_start":base,"sequences":seqs,
                     "zero_for_one_live":sum(1 for x in seqs["ZERO_FOR_ONE"] if x["exists"]),
                     "one_for_zero_live":sum(1 for x in seqs["ONE_FOR_ZERO"] if x["exists"]),
                     "nearest_below":max(below) if below else None,
                     "nearest_above":min(above) if above else None,
                     "directional_boundary_ready":bool(below and above)})
    payload={"revision":"QARB_057A2","rows":rows,"pools":len(rows),
             "directional_boundary_ready":sum(1 for r in rows if r["directional_boundary_ready"]),
             "both_direction_array_sequences":sum(1 for r in rows if r["zero_for_one_live"] and r["one_for_zero_live"]),
             "priced_live":False,"next":"RAYDIUM_CLMM_EXACT_SWAP_STEP_ENGINE",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-057A2] CLMM DIRECTIONAL TICK-ARRAY RESOLVER")
    print("[CLMM] pools=%d boundary_ready=%d both_direction_sequences=%d priced_live=%s"%(
        p["pools"],p["directional_boundary_ready"],p["both_direction_array_sequences"],p["priced_live"]))
    for r in p["rows"]:
        print("[CLMM_DIRECTION] %s ZFO=%d/4 OFZ=%d/4 below=%s above=%s ready=%s"%(
            r["pool"][:12],r["zero_for_one_live"],r["one_for_zero_live"],r["nearest_below"],r["nearest_above"],r["directional_boundary_ready"]))
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
