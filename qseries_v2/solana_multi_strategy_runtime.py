from __future__ import annotations
import argparse,json,os,time
from pathlib import Path
from qseries_v2.solana_universal_money_runner_v2 import StableUniversalProvider
from qseries_v2.solana_multi_strategy_money import EnsembleMoneyRunner

STATE_REL=Path("runtime_state/qseries/solana_universal_multi_strategy")
WORKSPACE_REL=STATE_REL/"workspace"
FEED_REL=Path("runtime_state/solana_opportunities/qsb007_universal_feed.jsonl")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--once",action="store_true")
    ap.add_argument("--sleep",type=float,default=5.0);a=ap.parse_args();root=Path(a.root).resolve()
    provider=StableUniversalProvider(root,max_tokens=48,active_tokens=24,timeout=10.0,refresh_seconds=90.0)
    workspace=root/WORKSPACE_REL;feed=workspace/FEED_REL;feed.parent.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault("QSB_MAX_HOLD_SECONDS","300");os.environ.setdefault("QSB_STOP_LOSS","0.08")
    os.environ.setdefault("QSB_TAKE_PROFIT","0.15");os.environ.setdefault("QSB_TRAILING_STOP","0.07")
    while True:
        snap=provider.snapshot();rows=list(snap.get("rows") or [])
        with feed.open("a",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")
        s=EnsembleMoneyRunner(workspace).cycle(progress=False)
        print("="*118);print(" QSB-007 SOLANA UNIVERSAL MULTI-STRATEGY MONEY RUNNER");print("="*118)
        print(f"[UNIVERSE] cached={snap.get('tokens_cached')} polled={snap.get('tokens_polled')} rows_now={len(rows)} errors={len(snap.get('errors') or [])}")
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} source_rows={s['source_rows']}")
        print(f"[TRADES] setups={s['setups_found']} ready={s['ready_setups']} entered={s['trades_entered_this_cycle']} closed={s['trades_closed_this_cycle']} open={s['open_positions']}")
        print(f"[MONEY $] closed={s['closed_trades']} wins={s['wins']} losses={s['losses']} win_rate={s['win_rate']} gross=${s['gross_pnl_usdc']:.4f} friction=${s['modeled_friction_usdc']:.4f} NET=${s['net_pnl_usdc']:.4f}")
        print("[STRATEGIES]",json.dumps(s["strategy_results"],sort_keys=True))
        print("[WHY NO TRADE]",json.dumps(s["why_no_trade"],sort_keys=True))
        print(f"[PROFITABILITY_PROVEN] {s['profitability_proven']} [PAPER_ONLY] True [REAL_MONEY_MOVED] False")
        if a.once:break
        time.sleep(max(1.0,a.sleep))
if __name__=="__main__":main()
