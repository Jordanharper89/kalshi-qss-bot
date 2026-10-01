from pathlib import Path
import py_compile

ROOT = Path.cwd()
DEP = ROOT / "build_qsb_001_unified_solana_money_bot.py"

if not DEP.is_file():
    raise SystemExit("[FAIL] missing dependency: " + str(DEP))

PKG = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_money"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch(exist_ok=True)

MODULE = PKG / "qsb_019_buy_pressure_ten_win_forward_trial.py"
TEST = ROOT / "test_qsb_019_buy_pressure_ten_win_forward_trial.py"
RUN = ROOT / "run_qsb_019_buy_pressure_ten_win_forward_trial.py"

module = r"""
from __future__ import annotations
import json, math, time
from dataclasses import dataclass, asdict
from pathlib import Path

READ_ONLY=True
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REVISION="QSB_019_BUY_PRESSURE_TEN_WIN_FORWARD_TRIAL_V1"

@dataclass
class Position:
    position_id: str
    pool: str
    token_mint: str
    family: str
    entry_price: float
    reference_entry_price: float
    qty: float
    notional_usdc: float
    opened_unix: float
    high_water_price: float
    status: str="OPEN"

def _f(v, d=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else float(d)
    except Exception:
        return float(d)

def now():
    return time.time()

def buy_pressure_score(row):
    # Reuse the existing BUY_PRESSURE idea directly: buy dominance + acceleration.
    buys=_f(row.get("buy_count") or row.get("buys") or row.get("buyer_count"))
    sells=_f(row.get("sell_count") or row.get("sells") or row.get("seller_count"))
    vol=_f(row.get("volume") or row.get("volume_usd") or row.get("quote_volume"))
    prev=_f(row.get("prev_volume") or row.get("previous_volume") or row.get("volume_prev"))
    total=buys+sells
    ratio=(buys/total) if total>0 else 0.0
    accel=((vol/prev)-1.0) if prev>0 else 0.0
    return max(0.0, (ratio-0.5)*2.0) + max(0.0, accel)

def qualifies(row, min_score=0.60, min_liquidity=1000.0):
    mint=str(row.get("token_mint") or row.get("mint") or row.get("token") or "")
    pool=str(row.get("pool") or row.get("pool_address") or row.get("market_address") or "")
    price=_f(row.get("price") or row.get("last_price") or row.get("current_price"))
    liq=_f(row.get("liquidity_usd") or row.get("liquidity") or row.get("liq"))
    score=_f(row.get("buy_pressure_score"), buy_pressure_score(row))
    if not mint or not pool or price<=0:
        return False,"MISSING_IDENTITY_OR_PRICE",score
    if liq<min_liquidity:
        return False,"MIN_EXECUTABLE_LIQUIDITY_FAIL",score
    if score<min_score:
        return False,"BUY_PRESSURE_FAIL",score
    return True,"READY",score

def close_reason(position, current_price, now_unix, stop_loss=0.10, take_profit=0.30, trailing_stop=0.12, max_hold_seconds=120):
    px=_f(current_price)
    if px<=0:
        return None
    position.high_water_price=max(position.high_water_price,px)
    ret=px/position.entry_price-1.0
    trail=px/position.high_water_price-1.0
    age=now_unix-position.opened_unix
    if ret<=-stop_loss:
        return "STOP_LOSS"
    if ret>=take_profit:
        return "TAKE_PROFIT"
    if position.high_water_price>position.entry_price*1.10 and trail<=-trailing_stop:
        return "TRAILING_STOP"
    if age>=max_hold_seconds:
        return "MAX_HOLD"
    return None

def realized_pnl(position, current_price, friction=0.03):
    # half friction on entry + half on exit
    exit_px=_f(current_price)*(1.0-friction/2.0)
    proceeds=position.qty*exit_px
    return proceeds-position.notional_usdc, exit_px

def milestone(stats):
    return bool(stats.get("wins",0)>=10 and _f(stats.get("net_pnl_usdc"))>0)
"""

test = r"""
import unittest,time
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_019_buy_pressure_ten_win_forward_trial import (
    Position,qualifies,close_reason,realized_pnl,milestone,EXECUTION_AUTHORITY,PAPER_ONLY
)

class T(unittest.TestCase):
    def test_buy_pressure_ready(self):
        row={
            "token_mint":"MINT1","pool":"POOL1","price":1.0,"liquidity_usd":5000,
            "buy_count":18,"sell_count":4,"volume":2200,"prev_volume":1000
        }
        ok,reason,score=qualifies(row)
        self.assertTrue(ok)
        self.assertEqual(reason,"READY")
        self.assertGreater(score,0.60)

    def test_positive_close_after_friction(self):
        p=Position("P1","POOL1","MINT1","PUMP_SWAP",1.015,1.0,5/1.015,5.0,time.time()-20,1.015)
        reason=close_reason(p,1.40,time.time())
        self.assertEqual(reason,"TAKE_PROFIT")
        pnl,exit_px=realized_pnl(p,1.40,0.03)
        self.assertGreater(pnl,0)

    def test_milestone_requires_ten_wins_and_positive_net(self):
        self.assertFalse(milestone({"wins":9,"net_pnl_usdc":100}))
        self.assertFalse(milestone({"wins":10,"net_pnl_usdc":0}))
        self.assertTrue(milestone({"wins":10,"net_pnl_usdc":0.01}))
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

ROOT=Path.cwd()
SOURCES=(
    ROOT/"runtime_state/solana_opportunities",
    ROOT/"runtime/solana",
    ROOT/"runtime/strategy_discovery",
)
STATE=ROOT/"runtime_state/qseries/qsb019_buy_pressure"
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

def ingest():
    rows=[]
    for base in SOURCES:
        if not base.exists():continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):continue
            try:
                if p.suffix.lower()==".jsonl":
                    objs=[]
                    for ln in p.read_text(encoding="utf-8",errors="ignore").splitlines():
                        try:objs.append(json.loads(ln))
                        except Exception:pass
                else:
                    objs=[json.loads(p.read_text(encoding="utf-8",errors="ignore"))]
            except Exception:
                continue
            for obj in objs:
                for d in _walk(obj):
                    r=_normalize(d)
                    if r:rows.append(r)
    rows.sort(key=lambda x:x["observed_unix"])
    # derive previous volume per pool so acceleration is forward-only
    prev={}
    out=[]
    for r in rows:
        x=dict(r)
        x["prev_volume"]=prev.get(r["pool"],0.0)
        prev[r["pool"]]=r["volume"]
        out.append(x)
    return out

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

    print("[QSB-019] BUY_PRESSURE-ONLY 10-WIN FORWARD TRIAL",flush=True)
    print("[QSB-019] ALL SOLANA SOURCE ROOTS | PAPER ONLY | execution_authority=FALSE",flush=True)

    while True:
        rows=ingest()
        latest={}
        for r in rows:
            latest[r["pool"]]=r

        # manage open positions first
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
            print("[CLOSE]",json.dumps({
                "pool":p["pool"],"token":p["token_mint"],"family":p["family"],
                "reason":reason,"pnl_usdc":round(pnl,6)
            },sort_keys=True),flush=True)

        # one active position at a time for clean forward evidence
        if not any(p.get("status")=="OPEN" for p in posdb["positions"]):
            for r in sorted(latest.values(),key=lambda x:x["observed_unix"],reverse=True):
                key=(r["pool"],r["token_mint"])
                if key in seen:continue
                if time.time()-r["observed_unix"]>30:continue
                ok,reason,score=qualifies(r,0.60,1000.0)
                if not ok:continue
                entry=r["price"]*1.015
                p=Position(
                    position_id=f"QSB019-{int(time.time()*1000)}",
                    pool=r["pool"],token_mint=r["token_mint"],family=r["family"],
                    entry_price=entry,reference_entry_price=r["price"],
                    qty=5.0/entry,notional_usdc=5.0,opened_unix=time.time(),
                    high_water_price=entry
                )
                posdb["positions"].append(p.__dict__)
                seen.add(key)
                print("[ENTRY]",json.dumps({
                    "pool":p.pool,"token":p.token_mint,"family":p.family,
                    "buy_pressure_score":round(score,6),"liq":r["liquidity_usd"]
                },sort_keys=True),flush=True)
                break

        _atomic(POSITIONS,posdb)
        _atomic(TRADES,tradedb)

        s=stats(tradedb["trades"])
        s.update({
            "revision":"QSB_019_BUY_PRESSURE_TEN_WIN_FORWARD_TRIAL_V1",
            "paper_only":True,
            "execution_authority":False,
            "milestone_reached":milestone(s),
        })
        _atomic(STATUS,s)
        print("[BUY_PRESSURE RESULT] closed={closed} wins={wins} losses={losses} NET=${net_pnl_usdc:.4f} milestone={milestone_reached}".format(**s),flush=True)

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
print("[PASS] QSB-019 BUY_PRESSURE-only 10-win forward trial installed")
print("[PASS] milestone requires wins>=10 AND net_pnl_usdc>0")
print("[PASS] PAPER_ONLY=True execution_authority=FALSE")
