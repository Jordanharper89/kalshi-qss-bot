from __future__ import annotations
import json,struct,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
SRC=Path("runtime_state/qseries/qarb_clean_bot/qarb_056b_clmm_tick_fee_state.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/qarb_057a_clmm_initialized_tick_decoder.json")
TICK_LEN=168
TICKS_PER_ARRAY=60

def _read(a,tries=3):
    last=None
    for i in range(tries):
        try:return c.account(a)
        except Exception as e:
            last=e;time.sleep(.25*(i+1))
    raise last

def decode_tick_array(raw,pool_bytes):
    if len(raw)<44+TICKS_PER_ARRAY*TICK_LEN+116: raise RuntimeError("TICK_ARRAY_SHORT")
    if raw[8:40]!=pool_bytes: raise RuntimeError("POOL_ID_MISMATCH")
    start=struct.unpack_from("<i",raw,40)[0]
    ticks=[];off=44
    for _ in range(TICKS_PER_ARRAY):
        tick=struct.unpack_from("<i",raw,off)[0]
        liq_net=int.from_bytes(raw[off+4:off+20],"little",signed=True)
        liq_gross=int.from_bytes(raw[off+20:off+36],"little")
        if liq_gross:
            ticks.append({"tick":tick,"liquidity_net":liq_net,"liquidity_gross":liq_gross})
        off+=TICK_LEN
    initialized_count=raw[off]
    return {"start_tick_index":start,"initialized_count_header":initialized_count,
            "initialized_ticks":ticks,"decoded_initialized":len(ticks),"bytes":len(raw)}

ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def b58d(s):
    n=0
    for ch in s:n=n*58+ALPH.index(ch)
    h=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
    z=0
    for ch in s:
        if ch=="1":z+=1
        else:break
    return b"\0"*z+h

def build(root):
    root=Path(root)
    src=root/SRC
    if not src.is_file(): raise RuntimeError("QARB_056B_ARTIFACT_MISSING")
    o=json.loads(src.read_text(encoding="utf-8"));rows=[]
    for r0 in o.get("rows") or []:
        pool=r0["pool"];pb=b58d(pool);arrays=[]
        for ta in r0.get("tick_arrays") or []:
            a=ta.get("address")
            if not a:continue
            try:
                raw,slot=_read(a);x=decode_tick_array(raw,pb);x.update({"address":a,"slot":slot});arrays.append(x)
            except Exception as e:
                arrays.append({"address":a,"error":type(e).__name__+":"+str(e)})
        good=[x for x in arrays if "initialized_ticks" in x]
        current=(r0.get("state") or {}).get("tick_current")
        below=[];above=[]
        for x in good:
            for t in x["initialized_ticks"]:
                if current is not None and t["tick"]<=current: below.append(t["tick"])
                if current is not None and t["tick"]>current: above.append(t["tick"])
        rows.append({"pool":pool,"current_tick":current,"arrays":arrays,
                     "initialized_ticks":sum(len(x["initialized_ticks"]) for x in good),
                     "nearest_below":max(below) if below else None,
                     "nearest_above":min(above) if above else None,
                     "directional_boundary_ready":bool(below and above)})
    payload={"revision":"QARB_057A","rows":rows,"pools":len(rows),
             "decoded_pools":sum(1 for r in rows if any("initialized_ticks" in a for a in r["arrays"])),
             "directional_boundary_ready":sum(1 for r in rows if r["directional_boundary_ready"]),
             "priced_live":False,
             "next":"RAYDIUM_CLMM_EXACT_SWAP_STEP_ENGINE",
             "execution_authority":False,"paper_only":True}
    p=root/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main():
    p=build(Path.cwd())
    print("[QARB-057A] CLMM INITIALIZED TICK DECODER")
    print("[CLMM] pools=%d decoded=%d directional_boundary_ready=%d priced_live=%s"%(
        p["pools"],p["decoded_pools"],p["directional_boundary_ready"],p["priced_live"]))
    for r in p["rows"]:
        print("[CLMM_TICKS] %s initialized=%d below=%s above=%s ready=%s"%(
            r["pool"][:12],r["initialized_ticks"],r["nearest_below"],r["nearest_above"],r["directional_boundary_ready"]))
    print("[NEXT]",p["next"]);print("[REPORT]",OUT);print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__":main()
