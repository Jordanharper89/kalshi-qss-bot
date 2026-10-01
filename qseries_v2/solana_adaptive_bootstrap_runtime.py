from __future__ import annotations
import argparse,json,time
from pathlib import Path

from qseries_v2.solana_windows_safe_provider import WindowsSafeUniversalProvider
from qseries_v2.solana_adaptive_bootstrap_arena import AdaptiveBootstrapArena

STATE=Path("runtime_state/qseries/solana_adaptive_runtime_v4")
WORKSPACE=STATE/"workspace"
FEED=Path("runtime_state/solana_opportunities/qsb012b_feed.jsonl")

LEDGER_CANDIDATES=(
 Path("runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/qseries/solana_24_strategy_arena/ledger.json"),
 Path("runtime_state/qseries/solana_24_strategy_arena/ledger.json"),
)
POSITIONS_CANDIDATES=(
 Path("runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/qseries/solana_24_strategy_arena/positions.json"),
 Path("runtime_state/qseries/solana_24_strategy_arena/positions.json"),
)
FEED_CANDIDATES=(
 Path("runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/solana_opportunities/qsb009_24_strategy_feed.jsonl"),
 Path("runtime_state/qseries/solana_universal_money_runner_v2/workspace/runtime_state/solana_opportunities/qsb006_universal_live_price_feed.jsonl"),
)

def _first_existing(root,cands):
    for rel in cands:
        p=root/rel
        if p.exists():return p
    return None

def _seed(root,workspace,feed):
    feed.parent.mkdir(parents=True,exist_ok=True)
    if not feed.exists():
        src=_first_existing(root,FEED_CANDIDATES)
        feed.write_text(src.read_text(encoding="utf-8",errors="ignore") if src else "",encoding="utf-8")

    dst=workspace/"runtime_state/qseries/solana_24_strategy_arena"
    dst.mkdir(parents=True,exist_ok=True)
    ledger_src=_first_existing(root,LEDGER_CANDIDATES)
    pos_src=_first_existing(root,POSITIONS_CANDIDATES)
    if ledger_src and not (dst/"ledger.json").exists():
        (dst/"ledger.json").write_text(ledger_src.read_text(encoding="utf-8",errors="ignore"),encoding="utf-8")
    if pos_src and not (dst/"positions.json").exists():
        (dst/"positions.json").write_text(pos_src.read_text(encoding="utf-8",errors="ignore"),encoding="utf-8")
    imported=0
    try: imported=len(json.loads((dst/"ledger.json").read_text())["trades"])
    except Exception: imported=0
    return {"ledger_source":str(ledger_src) if ledger_src else None,
            "positions_source":str(pos_src) if pos_src else None,
            "imported_closed_trades":imported}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".")
    ap.add_argument("--once",action="store_true");ap.add_argument("--sleep",type=float,default=5)
    a=ap.parse_args();root=Path(a.root).resolve();workspace=root/WORKSPACE;feed=workspace/FEED
    seed=_seed(root,workspace,feed)

    provider=WindowsSafeUniversalProvider(root,max_tokens=48,active_tokens=24,timeout=10,refresh_seconds=60)
    provider.cache_path=root/STATE/"universe_cache.json"
    provider.cache_path.parent.mkdir(parents=True,exist_ok=True)

    arena=AdaptiveBootstrapArena(workspace)
    while True:
        acquisition_error=None
        try:
            snap=provider.snapshot();rows=list(snap.get("rows") or [])
        except Exception as e:
            rows=[];acquisition_error=f"{type(e).__name__}: {e}"

        if rows:
            with feed.open("a",encoding="utf-8") as f:
                for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")

        s=arena.cycle(False)
        print("="*126);print(" QSB-012B SOLANA ADAPTIVE BOOTSTRAP MONEY RUNNER");print("="*126)
        print(f"[EVIDENCE] imported_closed={seed['imported_closed_trades']} source={seed['ledger_source']}")
        print(f"[FEED] rows_now={len(rows)} acquisition_error={acquisition_error}")
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} rows={s['source_rows']}")
        print(f"[BOOTSTRAP] {s['bootstrap_mode']} [PROMOTED] {s['promoted']}")
        print(f"[ARENA] ready={s['ready_signals']} entered={s['entered_this_cycle']} closed={s['closed_this_cycle']} open={s['open_positions']} total_closed={s['closed_trades']} NET=${s['arena_net_pnl_usdc']:.4f}")
        print("[LEADERS]",json.dumps(s["leaderboard"][:8],sort_keys=True))
        print("[MODE] PAPER_ONLY | bootstrap exploration prevents PROMOTED=[] deadlock | REAL_MONEY_MOVED=False")
        if a.once:break
        time.sleep(max(1,a.sleep))
if __name__=="__main__":main()
