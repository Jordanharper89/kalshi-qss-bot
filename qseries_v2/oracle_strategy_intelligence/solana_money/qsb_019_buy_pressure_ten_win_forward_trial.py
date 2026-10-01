
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
