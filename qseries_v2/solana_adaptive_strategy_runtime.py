from __future__ import annotations
import argparse,json,time
from pathlib import Path
from qseries_v2.solana_universal_money_runner_v2 import StableUniversalProvider
from qseries_v2.solana_adaptive_strategy_selector import AdaptiveArena

STATE=Path("runtime_state/qseries/solana_adaptive_runtime")
WORKSPACE=STATE/"workspace"
FEED=Path("runtime_state/solana_opportunities/qsb011_adaptive_feed.jsonl")
QSB009_FEED=Path("runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/solana_opportunities/qsb009_24_strategy_feed.jsonl")
QSB006_FEED=Path("runtime_state/qseries/solana_universal_money_runner_v2/workspace/runtime_state/solana_opportunities/qsb006_universal_live_price_feed.jsonl")

def _warm(root,feed):
    if feed.exists(): return
    feed.parent.mkdir(parents=True,exist_ok=True)
    src=root/QSB009_FEED
    if not src.exists():src=root/QSB006_FEED
    if src.exists():feed.write_text(src.read_text(encoding="utf-8",errors="ignore"),encoding="utf-8")
    else:feed.write_text("",encoding="utf-8")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--once",action="store_true")
    ap.add_argument("--sleep",type=float,default=5);a=ap.parse_args()
    root=Path(a.root).resolve();workspace=root/WORKSPACE;feed=workspace/FEED;_warm(root,feed)
    provider=StableUniversalProvider(root,max_tokens=48,active_tokens=24,timeout=10,refresh_seconds=90)
    arena=AdaptiveArena(workspace)
    # import QSB-009 accumulated evidence once
    old_state=root/"runtime_state/qseries/solana_24_strategy_arena"
    new_state=workspace/"runtime_state/qseries/solana_24_strategy_arena"
    new_state.mkdir(parents=True,exist_ok=True)
    for n in ("ledger.json","positions.json"):
        dst=new_state/n;src=old_state/n
        if not dst.exists() and src.exists():dst.write_text(src.read_text(encoding="utf-8"),encoding="utf-8")
    arena=AdaptiveArena(workspace)
    while True:
        snap=provider.snapshot();rows=list(snap.get("rows") or [])
        with feed.open("a",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")
        s=arena.cycle(False)
        print("="*124);print(" QSB-011 SOLANA ADAPTIVE STRATEGY SELECTOR");print("="*124)
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} rows={s['source_rows']}")
        print(f"[PROMOTED] {s['promoted']}")
        print(f"[ARENA] ready={s['ready_signals']} entered={s['entered_this_cycle']} closed={s['closed_this_cycle']} open={s['open_positions']} total_closed={s['closed_trades']} NET=${s['arena_net_pnl_usdc']:.4f}")
        print("[LEADERS]",json.dumps(s["leaderboard"][:8],sort_keys=True))
        print("[RULE] only strategies with >=4 closed, positive net, >=55% win rate; max 1 open position per token")
        print("[MODE] PAPER_ONLY | REAL_MONEY_MOVED=False")
        if a.once:break
        time.sleep(max(1,a.sleep))
if __name__=="__main__":main()
