from __future__ import annotations
import argparse, concurrent.futures, json, os, time
from pathlib import Path

from qseries_v2.solana_money_runner import MoneyRunner

REVISION="QSB-006-SOLANA-UNIVERSAL-STABLE-SURVEILLANCE-V1"
STATE_REL=Path("runtime_state/qseries/solana_universal_money_runner_v2")
WORKSPACE_REL=STATE_REL/"workspace"
FEED_REL=Path("runtime_state/solana_opportunities/qsb006_universal_live_price_feed.jsonl")

def _num(v):
    try:
        x=float(v)
        return x if x==x else None
    except Exception:
        return None

def _load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def _save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str),encoding="utf-8")
    tmp.replace(path)

class StableUniversalProvider:
    def __init__(self,root:Path,max_tokens=48,active_tokens=24,timeout=10.0,refresh_seconds=90.0):
        self.root=Path(root).resolve()
        self.max_tokens=int(max_tokens)
        self.active_tokens=int(active_tokens)
        self.timeout=float(timeout)
        self.refresh_seconds=float(refresh_seconds)
        self.cache_path=self.root/STATE_REL/"universe_cache.json"
        c=_load(self.cache_path,{})
        self.tokens=list(c.get("tokens") or [])
        self.last_refresh=float(c.get("last_refresh") or 0)
        self.cursor=int(c.get("cursor") or 0)

    def _discover(self):
        from qseries_v2.oracle_adapters.independent.oad_262_solana_live_token_discovery import discover_live_solana_tokens
        d=discover_live_solana_tokens(timeout_seconds=self.timeout)
        found=[str(x.get("token_address")) for x in (d.payload or {}).get("tokens",()) if x.get("token_address")]
        merged=[]
        for t in found+self.tokens:
            if t not in merged:merged.append(t)
        self.tokens=merged[:self.max_tokens]
        self.last_refresh=time.time()
        self._persist()
        return len(found)

    def _persist(self):
        _save(self.cache_path,{"tokens":self.tokens,"last_refresh":self.last_refresh,"cursor":self.cursor})

    def _expand(self,token):
        from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
        try:
            x=expand_live_solana_token_pools(token_address=token,timeout_seconds=self.timeout)
            return token,list((x.payload or {}).get("pools") or []),None
        except Exception as e:
            return token,[],type(e).__name__

    def snapshot(self):
        discovery_error=None
        discovered_now=0
        if not self.tokens or time.time()-self.last_refresh>=self.refresh_seconds:
            try:discovered_now=self._discover()
            except Exception as e:discovery_error=f"{type(e).__name__}: {e}"

        if not self.tokens:
            return {"rows":[],"errors":[],"tokens_cached":0,"tokens_polled":0,
                    "markets_eligible":0,"discovered_now":discovered_now,
                    "discovery_error":discovery_error}

        n=min(self.active_tokens,len(self.tokens))
        chosen=[self.tokens[(self.cursor+i)%len(self.tokens)] for i in range(n)]
        self.cursor=(self.cursor+n)%len(self.tokens)
        self._persist()

        expanded=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4,max(1,n))) as ex:
            futures=[ex.submit(self._expand,t) for t in chosen]
            for f in concurrent.futures.as_completed(futures):expanded.append(f.result())

        min_liq=float(os.getenv("QSB006_MIN_LIQUIDITY_USD","3000"))
        min_vol=float(os.getenv("QSB006_MIN_VOLUME_H24_USD","3000"))
        now=time.time();rows=[];errors=[]
        for token,pools,err in expanded:
            if err:
                errors.append({"token":token,"error":err})
                continue
            ranked=[]
            for p in pools:
                px=_num(p.get("price_usd"));liq=_num(p.get("liquidity_usd"));vol=_num(p.get("volume_h24"))
                if px is None or px<=0:continue
                if liq is None or liq<min_liq:continue
                if vol is None or vol<min_vol:continue
                ranked.append((liq,vol,p))
            ranked.sort(key=lambda x:(x[0],x[1]),reverse=True)
            for _,__,p in ranked[:3]:
                rows.append({
                    "market_address":str(p.get("pair_address") or ""),
                    "token_mint":token,
                    "family":str(p.get("dex_id") or "UNKNOWN").upper(),
                    "last_price":float(p["price_usd"]),
                    "observed_unix":now,
                    "liquidity_usd":_num(p.get("liquidity_usd")),
                    "volume_usd":_num(p.get("volume_h24")),
                    "buy_count":_num(p.get("buys_h24")),
                    "sell_count":_num(p.get("sells_h24")),
                    "price_basis":"DEXSCREENER_PRICE_USD",
                    "source":"QSB006_STABLE_UNIVERSAL"
                })
        return {"rows":rows,"errors":errors,"tokens_cached":len(self.tokens),
                "tokens_polled":len(chosen),"markets_eligible":len(rows),
                "discovered_now":discovered_now,"discovery_error":discovery_error}

class UniversalMoneyRunnerV2:
    def __init__(self,root:Path,provider=None,max_tokens=48,active_tokens=24,timeout=10.0):
        self.root=Path(root).resolve()
        self.state=self.root/STATE_REL
        self.workspace=self.root/WORKSPACE_REL
        self.feed=self.workspace/FEED_REL
        self.provider=provider or StableUniversalProvider(self.root,max_tokens,active_tokens,timeout)
        self.cycle_no=int(_load(self.state/"runtime.json",{}).get("cycle_number") or 0)
        os.environ.setdefault("QSB_ROUNDTRIP_FRICTION","0.03")

    def _append(self,rows):
        self.feed.parent.mkdir(parents=True,exist_ok=True)
        with self.feed.open("a",encoding="utf-8") as f:
            for r in rows:
                if r.get("market_address") and r.get("token_mint") and _num(r.get("last_price")):
                    f.write(json.dumps(r,sort_keys=True)+"\n")

    def _publish(self):
        src=self.workspace/"runtime_state/qseries/solana_money_runner"
        self.state.mkdir(parents=True,exist_ok=True)
        for name in ("status.json","ledger.json","positions.json"):
            p=src/name
            if p.exists():(self.state/name).write_text(p.read_text(encoding="utf-8"),encoding="utf-8")

    def cycle(self):
        self.cycle_no+=1
        try:
            snap=self.provider.snapshot()
            rows=list(snap.get("rows") or [])
            acquisition_error=None
        except Exception as e:
            snap={"rows":[],"errors":[],"tokens_cached":0,"tokens_polled":0,
                  "markets_eligible":0,"discovered_now":0,"discovery_error":None}
            rows=[];acquisition_error=f"{type(e).__name__}: {e}"

        self._append(rows)
        money=MoneyRunner(self.workspace).cycle(progress=False)
        self._publish()

        why=None
        if acquisition_error:why="LIVE_ACQUISITION_ERROR"
        elif not rows:why="NO_REAL_SOLANA_ROWS_THIS_CYCLE"
        elif money["source_rows"]==0:why="NO_USABLE_PRICE_HISTORY"
        elif money["ready_setups"]==0:why="NO_READY_SETUP"

        report={"revision":REVISION,"cycle_number":self.cycle_no,"paper_only":True,
                "real_money_moved":False,"tokens_cached":int(snap.get("tokens_cached") or 0),
                "tokens_polled":int(snap.get("tokens_polled") or 0),
                "markets_eligible_this_cycle":int(snap.get("markets_eligible") or 0),
                "real_rows_this_cycle":len(rows),"token_errors":list(snap.get("errors") or []),
                "discovery_error":snap.get("discovery_error"),"acquisition_error":acquisition_error,
                "money":money,"why_no_money_action":why}
        _save(self.state/"runtime.json",report)
        return report

def show(r):
    m=r["money"]
    print("="*118);print(" QSB-006 SOLANA UNIVERSAL STABLE MONEY RUNNER");print("="*118)
    print(f"[UNIVERSE] cached_tokens={r['tokens_cached']} polled={r['tokens_polled']} eligible_markets={r['markets_eligible_this_cycle']} rows_now={r['real_rows_this_cycle']} token_errors={len(r['token_errors'])}")
    if r["discovery_error"]:print("[DISCOVERY DEGRADED - CACHE STILL ACTIVE]",r["discovery_error"])
    print(f"[WATCHING] markets={m['markets_watched']} tokens={m['tokens_watched']} source_rows={m['source_rows']}")
    print(f"[TRADES] setups={m['setups_found']} ready={m['ready_setups']} entered={m['trades_entered_this_cycle']} closed={m['trades_closed_this_cycle']} open={m['open_positions']}")
    print(f"[MONEY $] closed={m['closed_trades']} wins={m['wins']} losses={m['losses']} win_rate={m['win_rate']} gross=${m['gross_pnl_usdc']:.4f} friction=${m['modeled_friction_usdc']:.4f} NET=${m['net_pnl_usdc']:.4f}")
    print(f"[PROFITABILITY_PROVEN] {m['profitability_proven']} [PAPER_ONLY] True [REAL_MONEY_MOVED] False")
    if r["why_no_money_action"]:print("[WHY NO MONEY ACTION]",r["why_no_money_action"])
    if m.get("why_no_trade"):print("[WHY NO TRADE]",json.dumps(m["why_no_trade"],sort_keys=True))
    print("[LEDGER] runtime_state/qseries/solana_universal_money_runner_v2/ledger.json");print("="*118)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--sleep",type=float,default=float(os.getenv("QSB006_SLEEP_SECONDS","5")))
    ap.add_argument("--max-tokens",type=int,default=int(os.getenv("QSB006_MAX_TOKENS","48")))
    ap.add_argument("--active-tokens",type=int,default=int(os.getenv("QSB006_ACTIVE_TOKENS","24")))
    ap.add_argument("--timeout",type=float,default=float(os.getenv("QSB006_HTTP_TIMEOUT","10")))
    a=ap.parse_args()
    r=UniversalMoneyRunnerV2(Path(a.root),max_tokens=a.max_tokens,active_tokens=a.active_tokens,timeout=a.timeout)
    while True:
        show(r.cycle())
        if a.once:break
        time.sleep(max(1.0,a.sleep))
if __name__=="__main__":main()
