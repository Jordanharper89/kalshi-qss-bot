from pathlib import Path
import py_compile

ROOT = Path.cwd()

QSB015 = ROOT / "run_qsb_015_first_seconds_launch_impulse.py"
GMGN300 = ROOT / "qseries_v2/oracle_adapters/independent/oad_300_solana_wallet_trader_claim_normalization.py"

for dep in (QSB015, GMGN300):
    if not dep.is_file():
        raise SystemExit("[FAIL] missing dependency: " + str(dep))

PKG = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_money"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch(exist_ok=True)

module_path = PKG / "qsb_018b_unified_first_seconds_champion_runtime.py"
test_path = ROOT / "test_qsb_018b_unified_first_seconds_champion_runtime.py"
run_path = ROOT / "run_qsb_018b_unified_first_seconds_champion_runtime.py"

module = r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping, Any, Iterable

READ_ONLY = True
EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REVISION = "QSB_018B_UNIFIED_FIRST_SECONDS_CHAMPION_RUNTIME_V1"

@dataclass(frozen=True)
class UnifiedDecision:
    admitted: bool
    mint: str
    buy_pressure_score: float
    qualified_wallets: int
    independent_early_buyers: int
    early_buy_ratio: float
    liquidity_usd: float
    reason: str
    read_only: bool = True
    execution_authority: bool = False
    paper_only: bool = True
    def to_dict(self):
        return asdict(self)

def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)

def _wallet(row):
    for k in ("wallet","wallet_address","owner","address","maker","trader"):
        v=row.get(k)
        if isinstance(v,str) and v.strip():
            return v.strip()
    return ""

def _side(row):
    return str(row.get("side") or row.get("action") or row.get("direction") or "").upper()

def _age(row):
    for k in ("age_seconds","seconds_after_launch","launch_age_seconds","buyer_age_seconds"):
        if k in row:
            return _f(row[k], 999999.0)
    return 999999.0

def _win_rate(row):
    for k in ("win_rate","winrate","win_ratio","profitable_rate"):
        if k in row:
            x=_f(row[k])
            return x/100.0 if x > 1.0 else x
    return 0.0

def _pnl(row):
    for k in ("realized_pnl","pnl","total_pnl","profit","realized_profit"):
        if k in row:
            return _f(row[k])
    return 0.0

def _trades(row):
    for k in ("closed_trades","trades","trade_count","total_trades"):
        if k in row:
            return int(_f(row[k]))
    return 0

def evaluate(
    mint: str,
    early_rows: Iterable[Mapping[str, Any]],
    wallet_claims: Iterable[Mapping[str, Any]],
    *,
    buy_pressure_score: float,
    liquidity_usd: float,
    max_age_seconds: float = 8.0,
    min_buy_pressure_score: float = 1.0,
    min_liquidity_usd: float = 1000.0,
    min_wallet_win_rate: float = 0.55,
    min_wallet_trades: int = 10,
    min_qualified_wallets: int = 2,
    min_early_buy_ratio: float = 0.65,
) -> UnifiedDecision:
    if not mint:
        return UnifiedDecision(False,"",_f(buy_pressure_score),0,0,0.0,_f(liquidity_usd),"NO_MINT")

    early=[r for r in early_rows if _age(r) <= max_age_seconds]
    buys=[r for r in early if _side(r) in ("BUY","B","SWAP_BUY","LONG")]
    sells=[r for r in early if _side(r) in ("SELL","S","SWAP_SELL","SHORT")]
    denom=len(buys)+len(sells)
    buy_ratio=(len(buys)/denom) if denom else 0.0
    early_buyers={_wallet(r) for r in buys if _wallet(r)}

    by_wallet={}
    for c in wallet_claims:
        w=_wallet(c)
        if w:
            by_wallet.setdefault(w,[]).append(c)

    qualified=set()
    for w in early_buyers:
        claims=by_wallet.get(w,())
        if any(
            _win_rate(c) >= min_wallet_win_rate
            and _trades(c) >= min_wallet_trades
            and _pnl(c) > 0
            for c in claims
        ):
            qualified.add(w)

    bp=_f(buy_pressure_score)
    liq=_f(liquidity_usd)

    if liq < min_liquidity_usd:
        reason="MIN_EXECUTABLE_LIQUIDITY_FAIL"
        admitted=False
    elif bp < min_buy_pressure_score:
        reason="BUY_PRESSURE_FAIL"
        admitted=False
    elif buy_ratio < min_early_buy_ratio:
        reason="EARLY_BUY_FLOW_FAIL"
        admitted=False
    elif len(qualified) < min_qualified_wallets:
        reason="EARLY_WALLET_QUALITY_FAIL"
        admitted=False
    else:
        reason="UNIFIED_FIRST_SECONDS_PAPER_ADMISSION"
        admitted=True

    return UnifiedDecision(
        admitted,mint,bp,len(qualified),len(early_buyers),
        round(buy_ratio,6),liq,reason
    )
"""

test = r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018b_unified_first_seconds_champion_runtime import (
    evaluate, EXECUTION_AUTHORITY, PAPER_ONLY
)

class T(unittest.TestCase):
    def test_unified_positive_case(self):
        flow=[
            {"wallet":"A","side":"BUY","age_seconds":1.0},
            {"wallet":"B","side":"BUY","age_seconds":2.0},
            {"wallet":"C","side":"BUY","age_seconds":3.0},
            {"wallet":"D","side":"SELL","age_seconds":4.0},
        ]
        claims=[
            {"wallet":"A","win_rate":0.68,"closed_trades":40,"realized_pnl":500},
            {"wallet":"B","win_rate":61,"closed_trades":25,"realized_pnl":300},
            {"wallet":"C","win_rate":0.45,"closed_trades":30,"realized_pnl":-5},
        ]
        r=evaluate("MINT",flow,claims,buy_pressure_score=1.7,liquidity_usd=2500)
        self.assertTrue(r.admitted)
        self.assertEqual(r.qualified_wallets,2)
        self.assertEqual(r.reason,"UNIFIED_FIRST_SECONDS_PAPER_ADMISSION")
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

    def test_buy_pressure_still_required(self):
        flow=[
            {"wallet":"A","side":"BUY","age_seconds":1.0},
            {"wallet":"B","side":"BUY","age_seconds":2.0},
        ]
        claims=[
            {"wallet":"A","win_rate":0.7,"closed_trades":20,"realized_pnl":100},
            {"wallet":"B","win_rate":0.7,"closed_trades":20,"realized_pnl":100},
        ]
        r=evaluate("MINT",flow,claims,buy_pressure_score=0.1,liquidity_usd=2500)
        self.assertFalse(r.admitted)
        self.assertEqual(r.reason,"BUY_PRESSURE_FAIL")

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

runtime = r"""
from __future__ import annotations
import json, time, subprocess, sys
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018b_unified_first_seconds_champion_runtime import evaluate

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"
QSB015=ROOT/"run_qsb_015_first_seconds_launch_impulse.py"
OUT=STATE/"solana_opportunities"/"qsb_018b_unified_first_seconds_champion_runtime.jsonl"

def _read(p):
    out=[]
    try:
        if p.suffix.lower()==".jsonl":
            for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
                try: out.append(json.loads(line))
                except Exception: pass
        else:
            out.append(json.loads(p.read_text(encoding="utf-8",errors="ignore")))
    except Exception:
        pass
    return out

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x,list):
        for v in x:
            yield from _walk(v)

def _mint(r):
    for k in ("mint","token_mint","token_address","address"):
        v=r.get(k)
        if isinstance(v,str) and len(v)>=20:
            return v
    return ""

def _num(r,*keys):
    for k in keys:
        if k in r:
            try: return float(r[k])
            except (TypeError,ValueError): pass
    return 0.0

def _collect():
    launch=[]
    gmgn=[]
    if not STATE.exists():
        return launch,gmgn

    for p in STATE.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):
            continue
        s=str(p).lower()
        target=None
        if "qsb_015" in s or "first_seconds" in s or "buy_pressure" in s:
            target=launch
        elif "gmgn" in s or "wallet" in s or "trader" in s:
            target=gmgn
        if target is None:
            continue
        for obj in _read(p):
            target.extend(list(_walk(obj)))
    return launch,gmgn

def cycle():
    launch,gmgn=_collect()
    by_mint={}
    for r in launch:
        m=_mint(r)
        if m:
            by_mint.setdefault(m,[]).append(r)

    admitted=[]
    for mint,rows in by_mint.items():
        bp=max((_num(r,"buy_pressure_score","pressure_score","buy_pressure","acceleration_score") for r in rows),default=0.0)
        liq=max((_num(r,"liquidity_usd","liquidity","pool_liquidity_usd") for r in rows),default=0.0)

        relevant_claims=[]
        for c in gmgn:
            cm=_mint(c)
            if not cm or cm==mint or c.get("token_mint")==mint:
                relevant_claims.append(c)

        d=evaluate(
            mint,
            rows,
            relevant_claims,
            buy_pressure_score=bp,
            liquidity_usd=liq,
        )

        if d.admitted:
            row=d.to_dict()
            row["strategy"]="FIRST_SECONDS+BUY_PRESSURE_ACCELERATION+GMGN_EARLY_WALLET_QUALITY"
            row["mode"]="PAPER_ONLY"
            admitted.append(row)

    OUT.parent.mkdir(parents=True,exist_ok=True)
    if admitted:
        with OUT.open("a",encoding="utf-8") as f:
            for row in admitted:
                f.write(json.dumps(row,sort_keys=True)+"\n")

    print("[QSB-018B] markets=",len(by_mint)," paper_admissions=",len(admitted))
    for row in admitted[:10]:
        print("[PAPER_ADMISSION]",json.dumps(row,sort_keys=True))
    print("[PASS] execution_authority=FALSE")
    return admitted

def main():
    if not QSB015.is_file():
        raise SystemExit("[FAIL] missing QSB-015 runtime")

    child=subprocess.Popen([sys.executable,str(QSB015)],cwd=str(ROOT))
    print("[QSB-018B] SINGLE SOLANA MONEY RUNTIME")
    print("[QSB-018B] QSB-015 + BUY_PRESSURE + GMGN EARLY WALLET QUALITY")
    print("[QSB-018B] PAPER ONLY / execution_authority=FALSE")

    try:
        while True:
            if child.poll() is not None:
                raise SystemExit("[FAIL] QSB-015 child exited rc="+str(child.returncode))
            cycle()
            time.sleep(1.0)
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

if __name__=="__main__":
    main()
"""

module_path.write_text(module,encoding="utf-8")
test_path.write_text(test,encoding="utf-8")
run_path.write_text(runtime,encoding="utf-8")

for p in (module_path,test_path,run_path):
    py_compile.compile(str(p),doraise=True)

print("[PASS] dependency:",QSB015.relative_to(ROOT))
print("[PASS] dependency:",GMGN300.relative_to(ROOT))
print("[PASS] installed:",module_path.relative_to(ROOT))
print("[PASS] test:",test_path.relative_to(ROOT))
print("[PASS] runtime:",run_path.relative_to(ROOT))
print("[PASS] QSB-018B installed")
print("[PASS] no QSB-017 dependency")
print("[PASS] one user-facing runtime")
print("[PASS] PAPER_ONLY=True execution_authority=FALSE")
