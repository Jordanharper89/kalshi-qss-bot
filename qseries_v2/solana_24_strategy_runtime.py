from __future__ import annotations
import argparse,json,time
from pathlib import Path
from qseries_v2.solana_universal_money_runner_v2 import StableUniversalProvider
from qseries_v2.solana_24_strategy_arena import Arena

STATE=Path("runtime_state/qseries/solana_24_strategy_runtime")
WORKSPACE=STATE/"workspace"
FEED=Path("runtime_state/solana_opportunities/qsb009_24_strategy_feed.jsonl")
QSB006=Path("runtime_state/qseries/solana_universal_money_runner_v2/workspace/runtime_state/solana_opportunities/qsb006_universal_live_price_feed.jsonl")

def warm(root,feed,state):
    marker=state/"warm_start.json"
    if marker.exists():return json.loads(marker.read_text())
    rows=[];seen=set();src=root/QSB006
    if src.exists():
        for ln in src.read_text(encoding="utf-8",errors="ignore").splitlines():
            try:r=json.loads(ln)
            except Exception:continue
            if not isinstance(r,dict):continue
            k=(r.get("market_address"),r.get("token_mint"),r.get("observed_unix"),r.get("last_price"))
            if k not in seen:seen.add(k);rows.append(r)
    feed.parent.mkdir(parents=True,exist_ok=True)
    with feed.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")
    d={"seed_rows":len(rows),"activation_unix":time.time(),"historical_rows_trading_authority":False}
    marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text(json.dumps(d,indent=2),encoding="utf-8");return d

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--once",action="store_true");ap.add_argument("--sleep",type=float,default=5)
    a=ap.parse_args();root=Path(a.root).resolve();state=root/STATE;workspace=root/WORKSPACE;feed=workspace/FEED
    seed=warm(root,feed,state);provider=StableUniversalProvider(root,max_tokens=48,active_tokens=24,timeout=10,refresh_seconds=90)
    arena=Arena(workspace)
    while True:
        snap=provider.snapshot();rows=list(snap.get("rows") or [])
        with feed.open("a",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")
        s=arena.cycle(progress=False)
        print("="*122);print(" QSB-009 SOLANA UNIVERSAL 24-STRATEGY ARENA");print("="*122)
        print(f"[WARM START] seed_rows={seed['seed_rows']} | [UNIVERSE] cached={snap.get('tokens_cached')} polled={snap.get('tokens_polled')} rows_now={len(rows)} errors={len(snap.get('errors') or [])}")
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} source_rows={s['source_rows']} strategies={s['strategy_count']}")
        print(f"[ARENA] ready={s['ready_signals']} entered={s['entered_this_cycle']} closed={s['closed_this_cycle']} open={s['open_positions']} total_closed={s['closed_trades']} arena_NET=${s['arena_net_pnl_usdc']:.4f}")
        leaders=[x for x in s["leaderboard"] if x["closed"]>0][:8]
        print("[LEADERBOARD]",json.dumps(leaders,sort_keys=True))
        print("[MODE] PAPER_ONLY | 24 independent shadow strategy lanes | REAL_MONEY_MOVED=False")
        if a.once:break
        time.sleep(max(1.0,a.sleep))
if __name__=="__main__":main()
