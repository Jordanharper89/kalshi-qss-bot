
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from qseries_v2.solana_windows_safe_provider import WindowsSafeUniversalProvider
from qseries_v2.solana_qsb013_burst import BurstRadar,expand_hot_mints
from qseries_v2.solana_champion_challenger_arena import ChampionChallengerArena

STATE=Path("runtime_state/qseries/qsb013_universal")
WORKSPACE=STATE/"workspace"
FEED=Path("runtime_state/solana_opportunities/qsb013_feed.jsonl")
OLD=Path("runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/qseries/solana_24_strategy_arena")

def _seed(root,workspace):
    dst=workspace/"runtime_state/qseries/solana_24_strategy_arena";dst.mkdir(parents=True,exist_ok=True)
    for n in ("ledger.json","positions.json"):
        s=root/OLD/n;d=dst/n
        if s.exists() and not d.exists():d.write_text(s.read_text(encoding="utf-8",errors="ignore"),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--once",action="store_true");ap.add_argument("--sleep",type=float,default=1)
    a=ap.parse_args();root=Path(a.root).resolve();workspace=root/WORKSPACE;feed=workspace/FEED;feed.parent.mkdir(parents=True,exist_ok=True)
    _seed(root,workspace)
    stable=WindowsSafeUniversalProvider(root,max_tokens=48,active_tokens=20,timeout=8,refresh_seconds=90)
    stable.cache_path=root/STATE/"universe_cache.json";stable.cache_path.parent.mkdir(parents=True,exist_ok=True)
    burst=BurstRadar(root);arena=ChampionChallengerArena(workspace,physical_root=root,start_worker=not a.once)
    while True:
        try:ss=stable.snapshot();stable_rows=list(ss.get("rows") or [])
        except Exception:stable_rows=[]
        try:bs=burst.scan(4,8);hot_rows=expand_hot_mints(bs.get("hot_mints") or [],8)
        except Exception:bs={"raw_rows":0,"new_signatures":0,"hydrated":0,"hot_mints":[],"family_counts":{}};hot_rows=[]
        merged={}
        for r in stable_rows+hot_rows:
            if r.get("market_address"):merged[r["market_address"]]=r
        rows=list(merged.values())
        with feed.open("a",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")

        s=arena.cycle(False,burst_family_counts=bs.get("family_counts") or {})
        p=s["pump_buy_pressure"];L=p["learning"];C=p["coverage"]

        print("="*132);print(" QSB-022 QSB-013 PUMP ECOSYSTEM END-TO-END PROFITABILITY RUNTIME");print("="*132)
        print(f"[BURST] raw={bs.get('raw_rows')} sigs={bs.get('new_signatures')} hydrated={bs.get('hydrated')} hot_mints={len(bs.get('hot_mints') or [])} hot_rows={len(hot_rows)}")
        print("[BURST FAMILIES]",json.dumps(bs.get("family_counts") or {},sort_keys=True))
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} rows={s['source_rows']}")
        print(f"[PUMP COVERAGE] births={C['birth_rows']} exact={C['fresh_exact_trades']} pumpfun={C['pumpfun_fresh']} pumpswap={C['pumpswap_fresh']} tokens={C['unique_tokens']} traders={C['unique_traders']} context={C['context_sources']} gmgn_module={C['gmgn_module_available']} security_module={C['security_module_available']}")
        if C["source_disconnect"]:
            print(f"[FAIL PUMP SOURCE] burst_events={C['pump_burst_events']} but fresh_exact_trades=0 -- BUY_PRESSURE NOT ALLOWED TO FALL BACK")
        elif not C["source_connected"]:
            print("[PUMP SOURCE] waiting for first fresh exact Pump.fun/PumpSwap trade; NO FALLBACK")
        else:
            print("[PUMP SOURCE] CONNECTED exact Pump.fun/PumpSwap trade tape is feeding BUY_PRESSURE")
        print(f"[PUMP PRESSURE] ready={p['ready']} entered={p['entered']} open={p['open']} closed_now={p['closed_this_cycle']}")
        print(f"[PUMP MONEY] total_closed={p['closed']} wins={p['wins']} losses={p['losses']} win_rate={p['win_rate']} NET=${p['net']:.4f} milestone={p['milestone']}")
        print(f"[BUY_PRESSURE LEARNING] sample={L['sample']} admission={L['admission_score']:.3f} promoted={L['promoted']} demoted={L['demoted']}")
        print(f"[ADAPTIVE EXITS] stop={L['stop_loss']:.3f} tp={L['take_profit']:.3f} trail={L['trailing_stop']:.3f} max_hold={L['max_hold_seconds']:.0f}s")
        print(f"[OTHER STRATEGIES] ready={s['ready_signals']} entered={s['entered_this_cycle']} closed={s['closed_this_cycle']} open={s['open_positions']}")
        print("[MODE] ONE RUNTIME | INTERNAL PUMP PRODUCERS | JOINED PUMPFUN+PUMPSWAP | PAPER_ONLY | REAL_MONEY_MOVED=False")
        if p["milestone"]:print("[PASS] 10 PUMP BUY_PRESSURE WINS + POSITIVE NET")
        if a.once:break
        time.sleep(max(.5,a.sleep))
if __name__=="__main__":main()
