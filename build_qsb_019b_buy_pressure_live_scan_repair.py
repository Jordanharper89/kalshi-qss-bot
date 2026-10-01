from pathlib import Path
import py_compile

ROOT = Path.cwd()
DEP = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_money/qsb_019_buy_pressure_ten_win_forward_trial.py"
if not DEP.is_file():
    raise SystemExit("[FAIL] missing dependency: " + str(DEP))

PKG = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_money"
MODULE = PKG / "qsb_019b_buy_pressure_live_scan_repair.py"
TEST = ROOT / "test_qsb_019b_buy_pressure_live_scan_repair.py"
RUN = ROOT / "run_qsb_019b_buy_pressure_live_scan_repair.py"

module = r"""
from __future__ import annotations
import json, math, time
from pathlib import Path

READ_ONLY=True
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REVISION="QSB_019B_BUY_PRESSURE_LIVE_SCAN_REPAIR_V1"

def fresh_candidate_files(root: Path, max_files=300, max_age_seconds=7200):
    roots=(
        root/"runtime_state/solana_opportunities",
        root/"runtime/solana",
        root/"runtime/strategy_discovery",
    )
    now=time.time()
    found=[]
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):
                continue
            try:
                age=now-p.stat().st_mtime
                if age<=max_age_seconds:
                    found.append((p.stat().st_mtime,p))
            except OSError:
                continue
    found.sort(key=lambda x:x[0],reverse=True)
    return [p for _,p in found[:max_files]]

def load_tail_objects(path: Path, max_lines=400):
    out=[]
    try:
        if path.suffix.lower()==".jsonl":
            lines=path.read_text(encoding="utf-8",errors="ignore").splitlines()
            for ln in lines[-max_lines:]:
                try: out.append(json.loads(ln))
                except Exception: pass
        else:
            out.append(json.loads(path.read_text(encoding="utf-8",errors="ignore")))
    except Exception:
        pass
    return out
"""

test = r"""
import json,tempfile,time,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_019b_buy_pressure_live_scan_repair import (
    fresh_candidate_files,load_tail_objects,EXECUTION_AUTHORITY,PAPER_ONLY
)

class T(unittest.TestCase):
    def test_bounded_recent_scan(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            base=root/"runtime_state/solana_opportunities"
            base.mkdir(parents=True)
            for i in range(5):
                p=base/f"{i}.json"
                p.write_text(json.dumps({"i":i}),encoding="utf-8")
            files=fresh_candidate_files(root,max_files=3,max_age_seconds=7200)
            self.assertEqual(len(files),3)

    def test_tail_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.jsonl"
            p.write_text("\n".join(json.dumps({"i":i}) for i in range(1000)),encoding="utf-8")
            rows=load_tail_objects(p,max_lines=25)
            self.assertEqual(len(rows),25)
            self.assertEqual(rows[-1]["i"],999)

    def test_authority(self):
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

runtime = r"""
from __future__ import annotations
import json,time,math
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_019_buy_pressure_ten_win_forward_trial import (
    Position,qualifies,close_reason,realized_pnl,milestone
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_019b_buy_pressure_live_scan_repair import (
    fresh_candidate_files,load_tail_objects
)

ROOT=Path.cwd()
STATE=ROOT/"runtime_state/qseries/qsb019b_buy_pressure"
POSITIONS=STATE/"positions.json"
TRADES=STATE/"trades.json"
STATUS=STATE/"status.json"

def _load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def _atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x,list):
        for v in x:
            yield from _walk(v)

def _f(v,d=0.0):
    try:
        x=float(v);return x if math.isfinite(x) else float(d)
    except Exception:return float(d)

def _normalize(d):
    mint=str(d.get("token_mint") or d.get("mint") or d.get("token") or "")
    pool=str(d.get("pool") or d.get("pool_address") or d.get("market_address") or "")
    price=_f(d.get("price") or d.get("last_price") or d.get("current_price"))
    ts=_f(d.get("observed_unix") or d.get("timestamp_unix") or d.get("block_time") or d.get("timestamp"))
    if not mint or not pool or price<=0 or ts<=0:return None
    return {
        "token_mint":mint,
        "pool":pool,
        "family":str(d.get("family") or d.get("venue") or d.get("protocol") or "UNKNOWN"),
        "price":price,
        "observed_unix":ts,
        "liquidity_usd":_f(d.get("liquidity_usd") or d.get("liquidity") or d.get("liq")),
        "buy_count":_f(d.get("buy_count") or d.get("buys") or d.get("buyer_count")),
        "sell_count":_f(d.get("sell_count") or d.get("sells") or d.get("seller_count")),
        "volume":_f(d.get("volume") or d.get("volume_usd") or d.get("quote_volume")),
    }

def ingest_bounded():
    files=fresh_candidate_files(ROOT,max_files=300,max_age_seconds=7200)
    rows=[]
    for p in files:
        for obj in load_tail_objects(p,max_lines=400):
            for d in _walk(obj):
                r=_normalize(d)
                if r:rows.append(r)
    rows.sort(key=lambda x:x["observed_unix"])
    prev={}
    out=[]
    for r in rows:
        x=dict(r)
        x["prev_volume"]=prev.get(r["pool"],0.0)
        prev[r["pool"]]=r["volume"]
        out.append(x)
    return files,out

def stats(trades):
    wins=sum(1 for t in trades if _f(t.get("realized_pnl_usdc"))>0)
    losses=sum(1 for t in trades if _f(t.get("realized_pnl_usdc"))<=0)
    net=sum(_f(t.get("realized_pnl_usdc")) for t in trades)
    return {"closed":len(trades),"wins":wins,"losses":losses,"net_pnl_usdc":net}

def main():
    STATE.mkdir(parents=True,exist_ok=True)
    posdb=_load(POSITIONS,{"positions":[]})
    tradedb=_load(TRADES,{"trades":[]})
    seen=set((t.get("pool"),t.get("token_mint")) for t in tradedb["trades"])
    seen.update((p.get("pool"),p.get("token_mint")) for p in posdb["positions"])

    print("[QSB-019B] BUY_PRESSURE-ONLY LIVE SCAN REPAIR",flush=True)
    print("[QSB-019B] bounded fresh-file scan active; no silent recursive full-repo ingest",flush=True)
    print("[QSB-019B] PAPER ONLY / execution_authority=FALSE",flush=True)

    cycle=0
    while True:
        cycle+=1
        t0=time.time()
        files,rows=ingest_bounded()
        latest={}
        for r in rows:
            latest[r["pool"]]=r

        entered=0
        closed=0

        for p in posdb["positions"]:
            if p.get("status")!="OPEN":continue
            r=latest.get(p["pool"])
            if not r:continue
            obj=Position(**{k:p[k] for k in Position.__dataclass_fields__.keys() if k in p})
            reason=close_reason(obj,r["price"],time.time())
            p["high_water_price"]=obj.high_water_price
            if not reason:continue
            pnl,exit_px=realized_pnl(obj,r["price"],0.03)
            p.update(status="CLOSED",closed_unix=time.time(),exit_reason=reason,
                     exit_price=exit_px,reference_exit_price=r["price"],
                     realized_pnl_usdc=pnl,realized_return=pnl/p["notional_usdc"])
            tradedb["trades"].append(dict(p))
            closed+=1
            print("[CLOSE]",json.dumps({
                "pool":p["pool"],"token":p["token_mint"],"family":p["family"],
                "reason":reason,"pnl_usdc":round(pnl,6)
            },sort_keys=True),flush=True)

        if not any(p.get("status")=="OPEN" for p in posdb["positions"]):
            for r in sorted(latest.values(),key=lambda x:x["observed_unix"],reverse=True):
                key=(r["pool"],r["token_mint"])
                if key in seen:continue
                if time.time()-r["observed_unix"]>30:continue
                ok,reason,score=qualifies(r,0.60,1000.0)
                if not ok:continue
                entry=r["price"]*1.015
                p=Position(
                    position_id=f"QSB019B-{int(time.time()*1000)}",
                    pool=r["pool"],token_mint=r["token_mint"],family=r["family"],
                    entry_price=entry,reference_entry_price=r["price"],
                    qty=5.0/entry,notional_usdc=5.0,opened_unix=time.time(),
                    high_water_price=entry
                )
                posdb["positions"].append(p.__dict__)
                seen.add(key)
                entered=1
                print("[ENTRY]",json.dumps({
                    "pool":p.pool,"token":p.token_mint,"family":p.family,
                    "buy_pressure_score":round(score,6),"liq":r["liquidity_usd"]
                },sort_keys=True),flush=True)
                break

        _atomic(POSITIONS,posdb)
        _atomic(TRADES,tradedb)

        s=stats(tradedb["trades"])
        s.update({
            "revision":"QSB_019B_BUY_PRESSURE_LIVE_SCAN_REPAIR_V1",
            "paper_only":True,
            "execution_authority":False,
            "milestone_reached":milestone(s),
            "files_scanned":len(files),
            "rows_scanned":len(rows),
            "markets":len(latest),
            "cycle":cycle,
            "cycle_seconds":round(time.time()-t0,3),
            "entered_this_cycle":entered,
            "closed_this_cycle":closed,
        })
        _atomic(STATUS,s)

        print(
            "[SCAN] cycle={cycle} files={files_scanned} rows={rows_scanned} markets={markets} "
            "entered={entered_this_cycle} closed={closed_this_cycle} elapsed={cycle_seconds}s".format(**s),
            flush=True
        )
        print(
            "[BUY_PRESSURE RESULT] closed={closed} wins={wins} losses={losses} "
            "NET=${net_pnl_usdc:.4f} milestone={milestone_reached}".format(**s),
            flush=True
        )

        if s["milestone_reached"]:
            print("[PASS] BUY_PRESSURE 10-WIN POSITIVE-NET MILESTONE REACHED",flush=True)

        time.sleep(1)

if __name__=="__main__":
    main()
"""

MODULE.write_text(module,encoding="utf-8")
TEST.write_text(test,encoding="utf-8")
RUN.write_text(runtime,encoding="utf-8")

for p in (MODULE,TEST,RUN):
    py_compile.compile(str(p),doraise=True)

print("[PASS] dependency:",DEP.relative_to(ROOT))
print("[PASS] installed:",MODULE.relative_to(ROOT))
print("[PASS] test:",TEST.relative_to(ROOT))
print("[PASS] runtime:",RUN.relative_to(ROOT))
print("[PASS] QSB-019B live scan repair installed")
print("[PASS] immediate scan/result heartbeat every cycle")
print("[PASS] bounded recent files only")
print("[PASS] PAPER_ONLY=True execution_authority=FALSE")
