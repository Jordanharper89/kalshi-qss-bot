from __future__ import annotations
import argparse,json,time
from pathlib import Path
from qseries_v2.solana_windows_safe_provider import WindowsSafeUniversalProvider
from qseries_v2.solana_qsb013_burst import BurstRadar,expand_hot_mints
from qseries_v2.solana_qsb015_first_seconds import FirstSecondsLane

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--once",action="store_true")
    ap.add_argument("--sleep",type=float,default=1);a=ap.parse_args()
    root=Path(a.root).resolve()
    stable=WindowsSafeUniversalProvider(root,max_tokens=48,active_tokens=12,timeout=6,refresh_seconds=90)
    stable.cache_path=root/"runtime_state/qseries/qsb015_first_seconds/universe_cache.json"
    stable.cache_path.parent.mkdir(parents=True,exist_ok=True)
    burst=BurstRadar(root,state_rel=Path("runtime_state/qseries/qsb015_first_seconds/burst"))
    lane=FirstSecondsLane(root)
    while True:
        try:bs=burst.scan(seconds=1,max_hydrate=12);hot_rows=expand_hot_mints(bs.get("hot_mints") or [],6)
        except Exception:bs={"raw_rows":0,"new_signatures":0,"hydrated":0,"hot_mints":[],"family_counts":{}};hot_rows=[]
        try:ss=stable.snapshot();stable_rows=list(ss.get("rows") or [])
        except Exception:stable_rows=[]
        merged={}
        for r in hot_rows+stable_rows:
            if r.get("market_address"):merged[r["market_address"]]=r
        rows=list(merged.values())
        price_by_market={r["market_address"]:float(r["last_price"]) for r in rows if r.get("market_address") and r.get("last_price") is not None}
        closed=lane.manage(price_by_market);entered=lane.evaluate(bs,rows);s=lane.status()
        print("="*124);print(" QSB-015 FIRST-SECONDS SOLANA LAUNCH IMPULSE");print("="*124)
        print(f"[BURST] raw={bs.get('raw_rows')} sigs={bs.get('new_signatures')} hydrated={bs.get('hydrated')} hot_mints={len(bs.get('hot_mints') or [])} hot_rows={len(hot_rows)}")
        print("[FAMILIES]",json.dumps(bs.get("family_counts") or {},sort_keys=True))
        print(f"[FLOW] entered={len(entered)} closed={len(closed)} open={s['open']}")
        print(f"[FRESH MONEY] closed={s['closed']} wins={s['wins']} losses={s['losses']} win_rate={s['win_rate']} NET=${s['net']:.4f}")
        if entered:print("[FAST ENTRIES]",json.dumps([{"family":x["family"],"token":x["token"],"score":x["signal_score"],"liq":x["liquidity_usd"]} for x in entered]))
        print("[MODE] PAPER_ONLY | 1-second burst scan | no 8-bar wait | REAL_MONEY_MOVED=False")
        if a.once:break
        time.sleep(max(.25,a.sleep))
if __name__=="__main__":main()
