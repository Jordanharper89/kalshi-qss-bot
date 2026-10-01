from __future__ import annotations
import argparse,json,time
from pathlib import Path
from qseries_v2.solana_universal_money_runner_v2 import StableUniversalProvider
from qseries_v2.solana_24_strategy_arena import Arena
from qseries_v2.solana_onchain_burst_radar import BurstRadar,expand_hot_mints

STATE=Path("runtime_state/qseries/solana_24_strategy_burst_runtime")
WORKSPACE=STATE/"workspace"
FEED=Path("runtime_state/solana_opportunities/qsb010_burst_feed.jsonl")
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
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--once",action="store_true");ap.add_argument("--sleep",type=float,default=2)
    a=ap.parse_args();root=Path(a.root).resolve();state=root/STATE;workspace=root/WORKSPACE;feed=workspace/FEED
    seed=warm(root,feed,state);provider=StableUniversalProvider(root,max_tokens=48,active_tokens=20,timeout=8,refresh_seconds=90)
    radar=BurstRadar(root);arena=Arena(workspace)
    while True:
        stable=provider.snapshot()
        burst=radar.scan(seconds=4,max_hydrate=8)
        hot_rows,hot_errors=expand_hot_mints(burst["hot_mints"],timeout=8)
        merged={r.get("market_address"):r for r in list(stable.get("rows") or [])+hot_rows if r.get("market_address")}
        rows=list(merged.values())
        with feed.open("a",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")
        s=arena.cycle(False)
        print("="*124);print(" QSB-010 SOLANA UNIVERSAL ON-CHAIN BURST + 24-STRATEGY ARENA");print("="*124)
        print(f"[WARM] seed_rows={seed['seed_rows']} | [STABLE] rows={len(stable.get('rows') or [])} | [BURST] raw={burst['raw_rows']} new_sigs={burst['new_signatures']} hydrated={burst['hydrated']} hot_mints={len(burst['hot_mints'])} hot_rows={len(hot_rows)}")
        print("[BURST FAMILIES]",json.dumps(burst["family_counts"],sort_keys=True))
        print("[HOT MINTS]",json.dumps(burst["hot_mints"][:8]))
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} source_rows={s['source_rows']} strategies={s['strategy_count']}")
        print(f"[ARENA] ready={s['ready_signals']} entered={s['entered_this_cycle']} closed={s['closed_this_cycle']} open={s['open_positions']} total_closed={s['closed_trades']} NET=${s['arena_net_pnl_usdc']:.4f}")
        print("[LEADERBOARD]",json.dumps([x for x in s["leaderboard"] if x["closed"]>0][:8],sort_keys=True))
        print("[MODE] PAPER_ONLY | EVENT-DRIVEN 14-PROGRAM RADAR | REAL_MONEY_MOVED=False")
        if a.once:break
        time.sleep(max(1,a.sleep))
if __name__=="__main__":main()
