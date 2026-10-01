from pathlib import Path
import py_compile

ROOT = Path.cwd()
DEP1 = ROOT / "run_qsb_015_first_seconds_launch_impulse.py"
DEP2 = ROOT / "qseries_v2/oracle_adapters/independent/oad_300_solana_wallet_trader_claim_normalization.py"
for dep in (DEP1, DEP2):
    if not dep.is_file():
        raise SystemExit("[FAIL] missing dependency: " + str(dep))

PKG = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_money"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch(exist_ok=True)

module = r"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, Mapping, Any

READ_ONLY = True
EXECUTION_AUTHORITY = False
PAPER_ONLY = True
REVISION = "QSB_017_EARLY_BUYER_WALLET_QUALITY_GATE_V1"

@dataclass(frozen=True)
class GateResult:
    admitted: bool
    mint: str
    qualified_wallets: int
    independent_wallets: int
    early_buy_ratio: float
    liquidity_usd: float
    reason: str
    read_only: bool = True
    execution_authority: bool = False
    paper_only: bool = True
    def to_dict(self): return asdict(self)

def _f(v, default=0.0):
    try: return float(v)
    except (TypeError, ValueError): return float(default)

def _wallet_id(row: Mapping[str, Any]) -> str:
    for k in ("wallet","owner","address","wallet_address","maker","trader"):
        v=row.get(k)
        if isinstance(v,str) and v.strip(): return v.strip()
    return ""

def _win_rate(row):
    for k in ("win_rate","winrate","win_ratio","profitable_rate"):
        if k in row:
            x=_f(row[k])
            return x/100.0 if x>1.0 else x
    return 0.0

def _pnl(row):
    for k in ("realized_pnl","pnl","total_pnl","profit","realized_profit"):
        if k in row: return _f(row[k])
    return 0.0

def _trades(row):
    for k in ("closed_trades","trades","trade_count","total_trades"):
        if k in row: return int(_f(row[k]))
    return 0

def _age(row):
    for k in ("age_seconds","seconds_after_launch","launch_age_seconds","buyer_age_seconds"):
        if k in row: return _f(row[k], 999999.0)
    return 999999.0

def _side(row):
    return str(row.get("side") or row.get("action") or row.get("direction") or "").upper()

def evaluate(
    mint: str,
    early_rows: Iterable[Mapping[str, Any]],
    wallet_claims: Iterable[Mapping[str, Any]],
    *,
    liquidity_usd: float,
    max_age_seconds: float = 8.0,
    min_liquidity_usd: float = 1000.0,
    min_qualified_wallets: int = 2,
    min_wallet_win_rate: float = 0.55,
    min_wallet_trades: int = 10,
    min_early_buy_ratio: float = 0.65,
) -> GateResult:
    if not mint:
        return GateResult(False,"",0,0,0.0,_f(liquidity_usd),"NO_MINT")
    early=[r for r in early_rows if _age(r)<=max_age_seconds]
    buys=[r for r in early if _side(r) in ("BUY","B","SWAP_BUY","LONG")]
    sells=[r for r in early if _side(r) in ("SELL","S","SWAP_SELL","SHORT")]
    denom=len(buys)+len(sells)
    buy_ratio=(len(buys)/denom) if denom else 0.0
    buying_wallets={_wallet_id(r) for r in buys if _wallet_id(r)}
    claims_by_wallet={}
    for c in wallet_claims:
        w=_wallet_id(c)
        if w: claims_by_wallet.setdefault(w,[]).append(c)
    qualified=set()
    for w in buying_wallets:
        claims=claims_by_wallet.get(w,())
        if any(_win_rate(c)>=min_wallet_win_rate and _trades(c)>=min_wallet_trades and _pnl(c)>0 for c in claims):
            qualified.add(w)
    liq=_f(liquidity_usd)
    if liq < min_liquidity_usd:
        reason="MIN_EXECUTABLE_LIQUIDITY_FAIL"
        admitted=False
    elif buy_ratio < min_early_buy_ratio:
        reason="EARLY_BUY_FLOW_FAIL"
        admitted=False
    elif len(qualified) < min_qualified_wallets:
        reason="WALLET_QUALITY_FAIL"
        admitted=False
    else:
        reason="EARLY_BUYER_EDGE_PAPER_ADMISSION"
        admitted=True
    return GateResult(admitted,mint,len(qualified),len(buying_wallets),round(buy_ratio,6),liq,reason)
"""

test = r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_017_early_buyer_wallet_quality_gate import evaluate, EXECUTION_AUTHORITY, PAPER_ONLY

class T(unittest.TestCase):
    def test_early_buyer_can_admit_before_mature_volume(self):
        flow=[
            {"wallet":"A","side":"BUY","age_seconds":1.2},
            {"wallet":"B","side":"BUY","age_seconds":2.0},
            {"wallet":"C","side":"BUY","age_seconds":3.1},
            {"wallet":"D","side":"SELL","age_seconds":4.0},
        ]
        claims=[
            {"wallet":"A","win_rate":0.68,"closed_trades":44,"realized_pnl":920},
            {"wallet":"B","win_rate":61,"closed_trades":31,"realized_pnl":410},
            {"wallet":"C","win_rate":0.40,"closed_trades":50,"realized_pnl":-20},
        ]
        r=evaluate("MINT",flow,claims,liquidity_usd=1800)
        self.assertTrue(r.admitted)
        self.assertEqual(r.qualified_wallets,2)
        self.assertEqual(r.reason,"EARLY_BUYER_EDGE_PAPER_ADMISSION")
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

    def test_fail_closed_without_executable_liquidity(self):
        flow=[{"wallet":"A","side":"BUY","age_seconds":1},{"wallet":"B","side":"BUY","age_seconds":2}]
        claims=[
            {"wallet":"A","win_rate":0.7,"closed_trades":20,"realized_pnl":10},
            {"wallet":"B","win_rate":0.7,"closed_trades":20,"realized_pnl":10},
        ]
        r=evaluate("M",flow,claims,liquidity_usd=200)
        self.assertFalse(r.admitted)
        self.assertEqual(r.reason,"MIN_EXECUTABLE_LIQUIDITY_FAIL")

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

runtime = r"""
from __future__ import annotations
import json, time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_017_early_buyer_wallet_quality_gate import evaluate

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"
OUT=STATE/"solana_opportunities"/"qsb_017_early_buyer_wallet_quality_gate.jsonl"

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from _walk(v)
    elif isinstance(x,list):
        for v in x: yield from _walk(v)

def _read(path):
    try:
        if path.suffix.lower()==".jsonl":
            rows=[]
            for ln in path.read_text(encoding="utf-8",errors="ignore").splitlines():
                try: rows.append(json.loads(ln))
                except Exception: pass
            return rows
        return [json.loads(path.read_text(encoding="utf-8",errors="ignore"))]
    except Exception:
        return []

def _mint(r):
    for k in ("mint","token_mint","token_address","address"):
        v=r.get(k)
        if isinstance(v,str) and len(v)>=20: return v
    return ""

def _liq(r):
    for k in ("liquidity_usd","liquidity","pool_liquidity_usd"):
        try: return float(r.get(k))
        except (TypeError,ValueError): pass
    return 0.0

def cycle():
    files=[p for p in STATE.rglob("*") if p.is_file() and p.suffix.lower() in (".json",".jsonl")]
    launch_files=[p for p in files if "qsb_015" in p.name.lower() or "first_seconds" in p.name.lower()]
    gmgn_files=[p for p in files if any(s in str(p).lower() for s in ("gmgn","wallet","trader"))]
    launches=[]; claims=[]
    for p in launch_files:
        for obj in _read(p):
            launches.extend(list(_walk(obj)))
    for p in gmgn_files:
        for obj in _read(p):
            claims.extend(list(_walk(obj)))
    by_mint={}
    for r in launches:
        m=_mint(r)
        if m: by_mint.setdefault(m,[]).append(r)
    emitted=[]
    for mint,rows in by_mint.items():
        liq=max((_liq(r) for r in rows),default=0.0)
        mclaims=[c for c in claims if _mint(c) in ("",mint) or c.get("token_mint")==mint]
        result=evaluate(mint,rows,mclaims,liquidity_usd=liq)
        d=result.to_dict()
        if result.admitted:
            d["strategy"]="FIRST_SECONDS_EARLY_BUYER_WALLET_QUALITY"
            d["mode"]="PAPER_ONLY"
            emitted.append(d)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if emitted:
        with OUT.open("a",encoding="utf-8") as f:
            for row in emitted:
                f.write(json.dumps(row,sort_keys=True)+"\n")
    print("[QSB-017] launch_files=",len(launch_files),"gmgn_files=",len(gmgn_files),"paper_admissions=",len(emitted))
    for row in emitted[:10]: print("[PAPER_ADMISSION]",json.dumps(row,sort_keys=True))
    print("[PASS] execution_authority=FALSE")
    return emitted

if __name__=="__main__":
    while True:
        cycle()
        time.sleep(1.0)
"""

module_path = PKG / "qsb_017_early_buyer_wallet_quality_gate.py"
test_path = ROOT / "test_qsb_017_early_buyer_wallet_quality_gate.py"
run_path = ROOT / "run_qsb_017_early_buyer_wallet_quality_gate.py"

module_path.write_text(module, encoding="utf-8")
test_path.write_text(test, encoding="utf-8")
run_path.write_text(runtime, encoding="utf-8")

for p in (module_path,test_path,run_path):
    py_compile.compile(str(p), doraise=True)

print("[PASS] dependency:", DEP1.relative_to(ROOT))
print("[PASS] dependency:", DEP2.relative_to(ROOT))
print("[PASS] installed:", module_path.relative_to(ROOT))
print("[PASS] test:", test_path.relative_to(ROOT))
print("[PASS] runtime:", run_path.relative_to(ROOT))
print("[PASS] QSB-017 early-buyer wallet-quality gate installed")
print("[PASS] mature chart volume is NOT an entry prerequisite")
print("[PASS] minimum executable liquidity remains fail-closed")
print("[PASS] PAPER_ONLY=True execution_authority=FALSE")
