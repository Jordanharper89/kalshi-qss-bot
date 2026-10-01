from __future__ import annotations
import hashlib,json,struct,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
SRC_STATE=Path("runtime_state/qseries/qarb_clean_bot/qarb_056c_orca_tick_fee_state.json")
SRC_ARRAYS=Path("runtime_state/qseries/qarb_clean_bot/qarb_057b_orca_tick_array_pda_resolver.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_058b_orca_local_swap_math.json")

Q64=1<<64
FEE_DEN=1_000_000
FACTORS=[
0xfffcb933bd6fb800,0xfff97272373d4000,0xfff2e50f5f657000,0xffe5caca7e10f000,
0xffcb9843d60f7000,0xff973b41fa98e800,0xff2ea16466c9b000,0xfe5dee046a9a3800,
0xfcbe86c7900bb000,0xf987a7253ac65800,0xf3392b0822bb6000,0xe7159475a2caf000,
0xd097f3bdfd2f2000,0xa9f746462d9f8000,0x70d869a156f31c00,0x31be135f97ed3200,
0x9aa508b5b85a500,0x5d6af8dedc582c,0x2216e584f5fa]
def ceildiv(a,b): return (a+b-1)//b
def sqrt_at_tick(tick):
    a=abs(int(tick))
    ratio=FACTORS[0] if a&1 else Q64
    for i in range(1,len(FACTORS)):
        if a&(1<<i): ratio=(ratio*FACTORS[i])>>64
    if tick>0: ratio=((1<<128)-1)//ratio
    return ratio
def amt0_delta(pa,pb,L,round_up):
    lo=min(pa,pb);hi=max(pa,pb)
    n=L*(hi-lo)*Q64
    d=hi*lo
    return ceildiv(n,d) if round_up else n//d
def amt1_delta(pa,pb,L,round_up):
    n=L*abs(pb-pa)
    return ceildiv(n,Q64) if round_up else n//Q64
def next_sqrt_from_input(p,L,amount,zero_for_one):
    if amount<=0:return p
    if zero_for_one:
        n=L*Q64
        return ceildiv(n*p,n+amount*p)
    return p+(amount*Q64)//L
def gross_for_net(net,fee):
    return ceildiv(net*FEE_DEN,FEE_DEN-fee)
def quote_steps(sqrt_p,liq,fee,amount,ticks,zero_for_one):
    rem=int(amount);out=0;crossed=0;P=int(sqrt_p);L=int(liq)
    ordered=sorted(ticks,key=lambda x:x["tick"],reverse=zero_for_one)
    for t in ordered:
        if rem<=0:break
        T=sqrt_at_tick(t["tick"])
        if zero_for_one and T>=P:continue
        if (not zero_for_one) and T<=P:continue
        need=amt0_delta(P,T,L,True) if zero_for_one else amt1_delta(P,T,L,True)
        gross_need=gross_for_net(need,fee)
        if gross_need<=rem:
            out += amt1_delta(P,T,L,False) if zero_for_one else amt0_delta(P,T,L,False)
            rem -= gross_need; P=T; crossed+=1
            ln=int(t["liquidity_net"])
            L = L-ln if zero_for_one else L+ln
            if L<=0: raise RuntimeError("LIQUIDITY_EXHAUSTED")
        else:
            net=(rem*(FEE_DEN-fee))//FEE_DEN
            N=next_sqrt_from_input(P,L,net,zero_for_one)
            out += amt1_delta(P,N,L,False) if zero_for_one else amt0_delta(P,N,L,False)
            P=N; rem=0
    if rem>0:
        net=(rem*(FEE_DEN-fee))//FEE_DEN
        N=next_sqrt_from_input(P,L,net,zero_for_one)
        out += amt1_delta(P,N,L,False) if zero_for_one else amt0_delta(P,N,L,False)
        P=N; rem=0
    return {"amount_out":int(out),"sqrt_price_after":int(P),"liquidity_after":int(L),"ticks_crossed":crossed}

def _read(a):
    raw,slot=c.account(a);return raw,slot
def tick_disc():return hashlib.sha256(b"account:TickArray").digest()[:8]
def decode_fixed(raw,start,spacing):
    # Anchor discriminator + start_tick_index + 88 Tick values + Whirlpool pubkey.
    # Tick layout: initialized(u8), liquidity_net(i128), liquidity_gross(u128), then fee/reward fields.
    if len(raw)<12:return []
    off=12;out=[];tick_size=113
    for i in range(88):
        if off+tick_size>len(raw):break
        initialized=raw[off]
        liq_net=int.from_bytes(raw[off+1:off+17],"little",signed=True)
        liq_gross=int.from_bytes(raw[off+17:off+33],"little")
        if initialized:
            out.append({"tick":int(start)+i*int(spacing),"liquidity_net":liq_net,"liquidity_gross":liq_gross})
        off+=tick_size
    return out
def build(root):
    root=Path(root)
    st=json.loads((root/SRC_STATE).read_text(encoding="utf-8"))
    ar=json.loads((root/SRC_ARRAYS).read_text(encoding="utf-8"))
    by_pool={r["pool"]:r for r in ar["rows"]};rows=[]
    for r in st["rows"]:
        pool=r["pool"];state=r.get("state") or {};ticks={}
        seqs=by_pool.get(pool,{}).get("sequences") or {}
        for seq in seqs.values():
            for x in seq:
                if not x.get("exists"):continue
                try:
                    raw,_=_read(x["address"])
                    if raw[:8]==tick_disc():
                        for t in decode_fixed(raw,x["start_tick_index"],int(state["tick_spacing"])):ticks[t["tick"]]=t
                except Exception:pass
        fee=int(state.get("fee_rate") or 0)
        safe=bool(r.get("decoded") and r.get("mint_match") and r.get("role_match") and ticks)
        probes=[]
        if safe:
            for a_to_b in (True,False):
                for amount in (1000,100000,1000000):
                    try:
                        q=quote_steps(int(state["sqrt_price_x64"]),int(state["liquidity"]),fee,amount,list(ticks.values()),a_to_b)
                        probes.append({"a_to_b":a_to_b,"amount_in":amount,**q,"ok":q["amount_out"]>=0})
                    except Exception as e:probes.append({"a_to_b":a_to_b,"amount_in":amount,"ok":False,"error":type(e).__name__+":"+str(e)})
        rows.append({"pool":pool,"fee_rate":fee,"tick_count":len(ticks),"math_bound":safe,
                     "probe_passes":sum(1 for x in probes if x.get("ok")),"probes":probes})
    payload={"revision":"QARB_058B","rows":rows,"pools":len(rows),
             "math_bound_pools":sum(1 for r in rows if r["math_bound"]),
             "probe_complete_pools":sum(1 for r in rows if r["math_bound"] and r["probe_passes"]==6),
             "priced_live":False,
             "next":"REPLAY_VALIDATE_ORCA_LOCAL_QUOTES_THEN_BIND_PROVIDER",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload
def main():
    p=build(Path.cwd())
    print("[QARB-058B] ORCA WHIRLPOOL LOCAL SWAP MATH")
    print("[ORCA] pools=%d math_bound=%d probe_complete=%d priced_live=%s"%(p["pools"],p["math_bound_pools"],p["probe_complete_pools"],p["priced_live"]))
    for r in p["rows"]:print("[ORCA_MATH] %s bound=%s fee=%s ticks=%d probes=%d/6"%(r["pool"][:12],r["math_bound"],r["fee_rate"],r["tick_count"],r["probe_passes"]))
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
