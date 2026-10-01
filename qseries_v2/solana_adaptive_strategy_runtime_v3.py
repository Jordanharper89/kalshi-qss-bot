from __future__ import annotations
import argparse,json,time,traceback
from pathlib import Path
from qseries_v2.solana_adaptive_strategy_selector import AdaptiveArena
from qseries_v2.solana_windows_safe_provider import WindowsSafeUniversalProvider

STATE=Path("runtime_state/qseries/solana_adaptive_runtime_v3")
WORKSPACE=STATE/"workspace"
FEED=Path("runtime_state/solana_opportunities/qsb011c_adaptive_feed.jsonl")
QSB009_FEED=Path("runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/solana_opportunities/qsb009_24_strategy_feed.jsonl")
QSB006_FEED=Path("runtime_state/qseries/solana_universal_money_runner_v2/workspace/runtime_state/solana_opportunities/qsb006_universal_live_price_feed.jsonl")

def _warm(root,feed):
    if feed.exists(): return
    feed.parent.mkdir(parents=True,exist_ok=True)
    src=root/QSB009_FEED
    if not src.exists(): src=root/QSB006_FEED
    feed.write_text(src.read_text(encoding="utf-8",errors="ignore") if src.exists() else "",encoding="utf-8")

def _seed_evidence(root,workspace):
    old=root/"runtime_state/qseries/solana_24_strategy_arena"
    new=workspace/"runtime_state/qseries/solana_24_strategy_arena"
    new.mkdir(parents=True,exist_ok=True)
    for n in ("ledger.json","positions.json"):
        src=old/n;dst=new/n
        if not dst.exists() and src.exists():
            dst.write_text(src.read_text(encoding="utf-8",errors="ignore"),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--sleep",type=float,default=5)
    a=ap.parse_args()
    root=Path(a.root).resolve();workspace=root/WORKSPACE;feed=workspace/FEED
    _warm(root,feed);_seed_evidence(root,workspace)
    provider=WindowsSafeUniversalProvider(root,max_tokens=48,active_tokens=24,timeout=10,refresh_seconds=90)
    arena=AdaptiveArena(workspace)
    last_rows=[]
    while True:
        acquisition_error=None
        try:
            snap=provider.snapshot()
            rows=list(snap.get("rows") or [])
            if rows:last_rows=rows
        except Exception as e:
            acquisition_error=f"{type(e).__name__}: {e}"
            rows=list(last_rows)

        if rows:
            feed.parent.mkdir(parents=True,exist_ok=True)
            with feed.open("a",encoding="utf-8") as f:
                for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")

        try:
            s=arena.cycle(False)
        except Exception as e:
            print("="*124)
            print(" QSB-011C SOLANA ADAPTIVE STRATEGY SELECTOR")
            print("="*124)
            print("[ARENA ERROR]",type(e).__name__,str(e))
            if a.once:raise
            time.sleep(max(1,a.sleep));continue

        print("="*124);print(" QSB-011C SOLANA ADAPTIVE STRATEGY SELECTOR");print("="*124)
        print(f"[FEED] rows_now={len(rows)} acquisition_error={acquisition_error}")
        print(f"[CACHE] persist_errors={provider.cache_persist_errors} path={provider.cache_path}")
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} rows={s['source_rows']}")
        print(f"[PROMOTED] {s['promoted']}")
        print(f"[ARENA] ready={s['ready_signals']} entered={s['entered_this_cycle']} closed={s['closed_this_cycle']} open={s['open_positions']} total_closed={s['closed_trades']} NET=${s['arena_net_pnl_usdc']:.4f}")
        print("[LEADERS]",json.dumps(s["leaderboard"][:8],sort_keys=True))
        print("[MODE] PAPER_ONLY | REAL_MONEY_MOVED=False")
        if a.once:break
        time.sleep(max(1,a.sleep))

if __name__=="__main__":main()
