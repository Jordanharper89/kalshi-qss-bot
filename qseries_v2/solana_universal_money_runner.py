from __future__ import annotations
import argparse, concurrent.futures, json, os, time
from pathlib import Path
from typing import Callable
from qseries_v2.solana_money_runner import MoneyRunner

REVISION="QSB-005-SOLANA-UNIVERSAL-MONEY-RUNNER-V1"
STATE_REL=Path("runtime_state/qseries/solana_universal_money_runner")
WORKSPACE_REL=STATE_REL/"workspace"
FEED_REL=Path("runtime_state/solana_opportunities/qsb005_universal_live_price_feed.jsonl")

def _n(v):
    try:
        x=float(v); return x if x==x else None
    except Exception:return None

def _write_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str),encoding="utf-8")
    t.replace(p)

def _discover(max_tokens,timeout):
    from qseries_v2.oracle_adapters.independent.oad_262_solana_live_token_discovery import discover_live_solana_tokens
    d=discover_live_solana_tokens(timeout_seconds=timeout)
    return [str(x.get("token_address")) for x in (d.payload or {}).get("tokens",()) if x.get("token_address")][:max_tokens]

def _expand_one(token,timeout):
    from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
    try:
        x=expand_live_solana_token_pools(token_address=token,timeout_seconds=timeout)
        return token,list((x.payload or {}).get("pools") or []),None
    except Exception as e:
        return token,[],type(e).__name__

def default_provider(max_tokens=60,timeout=12.0,max_markets=120):
    tokens=_discover(max_tokens,timeout)
    workers=min(12,max(1,len(tokens)))
    expanded=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs=[ex.submit(_expand_one,t,timeout) for t in tokens]
        for f in concurrent.futures.as_completed(futs):
            expanded.append(f.result())
    min_liq=float(os.getenv("QSB005_MIN_LIQUIDITY_USD","5000"))
    min_vol=float(os.getenv("QSB005_MIN_VOLUME_H24_USD","5000"))
    rows=[];errors=[];now=time.time()
    for token,pools,err in expanded:
        if err: errors.append({"token":token,"error":err}); continue
        ranked=[]
        for p in pools:
            px=_n(p.get("price_usd"));liq=_n(p.get("liquidity_usd"));vol=_n(p.get("volume_h24"))
            if not px or px<=0:continue
            if liq is None or liq<min_liq:continue
            if vol is None or vol<min_vol:continue
            ranked.append((liq,vol,p))
        ranked.sort(key=lambda z:(z[0],z[1]),reverse=True)
        for _,__,p in ranked[:3]:
            rows.append({
                "market_address":str(p.get("pair_address") or ""),
                "token_mint":token,
                "family":str(p.get("dex_id") or "UNKNOWN").upper(),
                "last_price":float(p["price_usd"]),
                "observed_unix":now,
                "liquidity_usd":_n(p.get("liquidity_usd")),
                "volume_usd":_n(p.get("volume_h24")),
                "buy_count":_n(p.get("buys_h24")),
                "sell_count":_n(p.get("sells_h24")),
                "price_basis":"DEXSCREENER_PRICE_USD",
                "source":"QSB005_SOLANA_UNIVERSAL"
            })
    rows.sort(key=lambda r:(r.get("liquidity_usd") or 0,r.get("volume_usd") or 0),reverse=True)
    return {"rows":rows[:max_markets],"errors":errors,"tokens_discovered":len(tokens),"markets_eligible":len(rows)}

class UniversalMoneyRunner:
    def __init__(self,root:Path,provider:Callable|None=None,max_tokens=60,max_markets=120,timeout=12.0):
        self.root=Path(root).resolve();self.state=self.root/STATE_REL;self.workspace=self.root/WORKSPACE_REL
        self.feed=self.workspace/FEED_REL;self.provider=provider or default_provider
        self.max_tokens=int(max_tokens);self.max_markets=int(max_markets);self.timeout=float(timeout)
        try:self.cycle_no=int(json.loads((self.state/"runtime.json").read_text()).get("cycle_number") or 0)
        except Exception:self.cycle_no=0
        os.environ.setdefault("QSB_ROUNDTRIP_FRICTION","0.03")
    def _append(self,rows):
        self.feed.parent.mkdir(parents=True,exist_ok=True)
        with self.feed.open("a",encoding="utf-8") as f:
            for r in rows:
                if r.get("market_address") and r.get("token_mint") and _n(r.get("last_price")):
                    f.write(json.dumps(r,sort_keys=True)+"\n")
    def _publish(self):
        src=self.workspace/"runtime_state/qseries/solana_money_runner";self.state.mkdir(parents=True,exist_ok=True)
        for n in ("status.json","ledger.json","positions.json"):
            p=src/n
            if p.exists():(self.state/n).write_text(p.read_text(encoding="utf-8"),encoding="utf-8")
    def cycle(self):
        self.cycle_no+=1
        try:
            snap=self.provider(self.max_tokens,self.timeout,self.max_markets)
            rows=list(snap.get("rows") or []);err=None
        except Exception as e:
            snap={"rows":[],"errors":[],"tokens_discovered":0,"markets_eligible":0};rows=[];err=f"{type(e).__name__}: {e}"
        self._append(rows)
        money=MoneyRunner(self.workspace).cycle(progress=False)
        self._publish()
        why=None
        if err:why="LIVE_ACQUISITION_ERROR"
        elif not rows:why="NO_REAL_SOLANA_ROWS_THIS_CYCLE"
        elif money["source_rows"]==0:why="NO_USABLE_PRICE_HISTORY"
        elif money["ready_setups"]==0:why="NO_READY_SETUP"
        report={
            "revision":REVISION,"cycle_number":self.cycle_no,"paper_only":True,"real_money_moved":False,
            "tokens_discovered_this_cycle":int(snap.get("tokens_discovered") or 0),
            "markets_eligible_this_cycle":int(snap.get("markets_eligible") or 0),
            "real_rows_this_cycle":len(rows),"token_errors":list(snap.get("errors") or []),
            "acquisition_error":err,"money":money,"why_no_money_action":why
        }
        _write_json(self.state/"runtime.json",report);return report

def show(r):
    m=r["money"]
    print("="*118);print(" QSB-005 SOLANA UNIVERSAL MONEY RUNNER");print("="*118)
    print(f"[UNIVERSE] tokens_discovered={r['tokens_discovered_this_cycle']} eligible_markets={r['markets_eligible_this_cycle']} rows_now={r['real_rows_this_cycle']} errors={len(r['token_errors'])}")
    print(f"[WATCHING] markets={m['markets_watched']} tokens={m['tokens_watched']} source_rows={m['source_rows']}")
    print(f"[TRADES] setups={m['setups_found']} ready={m['ready_setups']} entered={m['trades_entered_this_cycle']} closed={m['trades_closed_this_cycle']} open={m['open_positions']}")
    print(f"[MONEY $] closed={m['closed_trades']} wins={m['wins']} losses={m['losses']} win_rate={m['win_rate']} gross=${m['gross_pnl_usdc']:.4f} friction=${m['modeled_friction_usdc']:.4f} NET=${m['net_pnl_usdc']:.4f}")
    print(f"[PROFITABILITY_PROVEN] {m['profitability_proven']} [PAPER_ONLY] True [REAL_MONEY_MOVED] False")
    if r["why_no_money_action"]:print("[WHY NO MONEY ACTION]",r["why_no_money_action"])
    if m.get("why_no_trade"):print("[WHY NO TRADE]",json.dumps(m["why_no_trade"],sort_keys=True))
    print("[LEDGER] runtime_state/qseries/solana_universal_money_runner/ledger.json");print("="*118)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--sleep",type=float,default=float(os.getenv("QSB005_SLEEP_SECONDS","5")))
    ap.add_argument("--max-tokens",type=int,default=int(os.getenv("QSB005_MAX_TOKENS","60")))
    ap.add_argument("--max-markets",type=int,default=int(os.getenv("QSB005_MAX_MARKETS","120")))
    ap.add_argument("--timeout",type=float,default=float(os.getenv("QSB005_HTTP_TIMEOUT","12")))
    a=ap.parse_args();r=UniversalMoneyRunner(Path(a.root),max_tokens=a.max_tokens,max_markets=a.max_markets,timeout=a.timeout)
    while True:
        show(r.cycle())
        if a.once:break
        time.sleep(max(1.0,a.sleep))
if __name__=="__main__":main()
