from __future__ import annotations
import asyncio,json,math,time
from collections import defaultdict
from pathlib import Path

TARGET_VENUES={
    "PUMP_SWAP","METEORA_DLMM","METEORA_DAMM_V2",
    "RAYDIUM_CLMM","RAYDIUM_CPMM","ORCA"
}
ANCHORS={
    "So11111111111111111111111111111111111111112":"WSOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":"USDC",
    "Es9vMFrzaCERmJfrF4H2FYD9zX6Y2pZPbBZ5w4M7ZC9":"USDT",
}
MIN_OBSERVED_SPREAD_BPS=20.0
MAX_SLOT_SPREAD=2

def _pick(d,*keys):
    for k in keys:
        v=d.get(k) if isinstance(d,dict) else None
        if v is not None:
            return v
    return None

def normalize_row(row):
    if not isinstance(row,dict):
        return None
    ev=row.get("event") if isinstance(row.get("event"),dict) else {}
    d={**row,**ev}
    venue=str(_pick(d,"venue","program_name","dex") or "")
    if venue=="METEORA_DAMM":
        venue="METEORA_DAMM_V2"
    if venue not in TARGET_VENUES:
        return None
    im=_pick(d,"input_mint","in_mint","mint_in")
    om=_pick(d,"output_mint","out_mint","mint_out")
    ia=_pick(d,"input_amount","in_amount","amount_in","ui_input_amount")
    oa=_pick(d,"output_amount","out_amount","amount_out","ui_output_amount")
    if not im or not om or ia is None or oa is None:
        return None
    try:
        ia=float(ia);oa=float(oa)
    except Exception:
        return None
    if ia<=0 or oa<=0:
        return None
    if im in ANCHORS and om not in ANCHORS:
        base=om;quote=im;price=ia/oa
    elif om in ANCHORS and im not in ANCHORS:
        base=im;quote=om;price=oa/ia
    else:
        return None
    try:
        slot=int(_pick(d,"slot","block_slot","context_slot"))
    except Exception:
        slot=None
    return {
        "venue":venue,"base_mint":base,"quote_mint":quote,
        "quote_symbol":ANCHORS[quote],"price":price,"slot":slot,
        "pool":_pick(d,"pool","pool_address","amm","market"),
        "signature":_pick(d,"signature","tx_signature"),
    }

def latest_books(rows):
    books={}
    for raw in rows:
        r=normalize_row(raw)
        if not r:
            continue
        key=(r["base_mint"],r["quote_mint"],r["venue"])
        old=books.get(key)
        old_slot=old.get("slot") if old else None
        new_slot=r.get("slot")
        if old is None or (new_slot is not None and (old_slot is None or new_slot>=old_slot)):
            books[key]=r
    return books

def find_spreads(rows):
    books=latest_books(rows)
    grouped=defaultdict(list)
    for r in books.values():
        grouped[(r["base_mint"],r["quote_mint"])].append(r)
    out=[]
    for (base,quote),rs in grouped.items():
        if len({r["venue"] for r in rs})<2:
            continue
        lo=min(rs,key=lambda x:x["price"]);hi=max(rs,key=lambda x:x["price"])
        spread=(hi["price"]/lo["price"]-1.0)*10000.0 if lo["price"]>0 else 0.0
        slots=[r["slot"] for r in rs if r["slot"] is not None]
        slot_spread=(max(slots)-min(slots)) if len(slots)>=2 else None
        out.append({
            "base_mint":base,"quote_mint":quote,"quote_symbol":lo["quote_symbol"],
            "buy_venue":lo["venue"],"sell_venue":hi["venue"],
            "buy_price":lo["price"],"sell_price":hi["price"],
            "observed_spread_bps":spread,"slot_spread":slot_spread,
            "fresh":slot_spread is not None and slot_spread<=MAX_SLOT_SPREAD,
            "buy_pool":lo.get("pool"),"sell_pool":hi.get("pool"),
            "venues":sorted({r["venue"] for r in rs}),
        })
    return sorted(out,key=lambda x:x["observed_spread_bps"],reverse=True)

async def capture_once(seconds=2.5,max_rows=2200):
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape import usls_046b_shared_multidex_live_event_router as router
    d=await router.capture(seconds=seconds,max_rows=max_rows)
    rows=list((d or {}).get("rows") or [])
    return d,rows

def cycle(root,capture_fn=None):
    if capture_fn is None:
        d,rows=asyncio.run(capture_once())
    else:
        d,rows=capture_fn()
    spreads=find_spreads(rows)
    top=spreads[:12]
    counts=defaultdict(int)
    for r in rows:
        n=normalize_row(r)
        if n: counts[n["venue"]]+=1
    print("[VENUES] "+json.dumps(dict(sorted(counts.items())),sort_keys=True),flush=True)
    print(f"[ROWS] captured={len(rows)} exact_anchor_trades={sum(counts.values())} crossvenue_spreads={len(spreads)}",flush=True)
    actionable=[]
    for s in top:
        flag=s["fresh"] and s["observed_spread_bps"]>=MIN_OBSERVED_SPREAD_BPS
        print("[SPREAD] token=%s quote=%s buy=%s sell=%s bps=%+.2f slots=%s fresh=%s SIGNAL=%s"%(
            s["base_mint"],s["quote_symbol"],s["buy_venue"],s["sell_venue"],
            s["observed_spread_bps"],s["slot_spread"],s["fresh"],"YES" if flag else "NO"),flush=True)
        if flag: actionable.append(s)
    out={
        "revision":"QSB_039","captured_rows":len(rows),"venue_counts":dict(counts),
        "spreads":spreads,"signals":actionable,"execution_authority":False,
        "truth":"OBSERVED_EXACT_TRADE_SPREAD_TRIGGER_NOT_EXECUTABLE_QUOTE"
    }
    p=Path(root)/"runtime_state/qseries/qsb039_multidex_hotgraph/report.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out

def run(root,interval=1.0,max_cycles=0,capture_fn=None):
    i=0
    while True:
        i+=1
        t=time.time()
        print(f"[CYCLE {i}] live multi-DEX event window",flush=True)
        try:
            r=cycle(root,capture_fn)
            if r["signals"]:
                s=r["signals"][0]
                print("[HOT_SIGNAL] token=%s %s->%s observed_bps=%+.2f fresh=%s"%(
                    s["base_mint"],s["buy_venue"],s["sell_venue"],
                    s["observed_spread_bps"],s["fresh"]),flush=True)
                print("[NEXT] exact executable quote/simulation required before any order",flush=True)
            else:
                print("[NO_SIGNAL]",flush=True)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[CYCLE_ERROR] {type(e).__name__}: {e}",flush=True)
        if max_cycles and i>=max_cycles:
            return
        time.sleep(max(0.0,interval-(time.time()-t)))
