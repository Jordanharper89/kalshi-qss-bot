
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
