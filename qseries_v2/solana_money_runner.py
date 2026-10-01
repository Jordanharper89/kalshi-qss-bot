from __future__ import annotations

import argparse
import json
import math
import os
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

REVISION = "QSB-003-MONEY-RUNNER-V1"

SOURCE_ROOTS = (
    Path("runtime_state/solana_opportunities"),
    Path("runtime_state/oracle"),
    Path("runtime/solana"),
    Path("runtime/strategy_discovery"),
)

STATE_DIR = Path("runtime_state/qseries/solana_money_runner")
LEDGER_FILE = "ledger.json"
POSITIONS_FILE = "positions.json"
STATUS_FILE = "status.json"

PRICE_KEYS = (
    "effective_price", "last_price", "price", "first_price",
    "directed_effective_price", "entry_reference_price",
    "mid_price", "spot_price", "quote_price",
)
TIME_KEYS = (
    "observed_unix", "timestamp_unix", "freeze_unix", "block_time",
    "blockTime", "timestamp", "t", "unix",
)
POOL_KEYS = (
    "market_address", "pool_address", "pool", "market", "pair_address",
    "amm", "pool_id", "poolAddress",
)
TOKEN_KEYS = (
    "token_mint", "mint", "base_mint", "output_asset",
    "token_address", "baseMint", "mint_address",
)
FAMILY_KEYS = ("family", "venue", "protocol", "source_family", "dex")
LIQ_KEYS = ("liquidity_usd", "liquidity", "tvl_usd", "tvl")
VOL_KEYS = ("volume_usd", "volume", "quote_volume", "volume_5m")
BUY_KEYS = ("buy_count", "buys", "buyer_count", "buy_tx_count")
SELL_KEYS = ("sell_count", "sells", "seller_count", "sell_tx_count")

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_MINT = "So11111111111111111111111111111111111111112"

def _now() -> float:
    return time.time()

def _finite(v: Any) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def _pick(d: dict, keys) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None

def _atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")
    tmp.replace(path)

def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def _walk_dicts(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            if isinstance(v, (dict, list)):
                yield from _walk_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, list)):
                yield from _walk_dicts(v)

@dataclass
class Row:
    market: str
    token: str
    family: str
    t: float
    price: float
    liquidity: float | None = None
    volume: float | None = None
    buys: float | None = None
    sells: float | None = None
    source_file: str = ""

def _normalize(d: dict, source_file: str = "") -> Row | None:
    market = _pick(d, POOL_KEYS)
    price = _finite(_pick(d, PRICE_KEYS))
    ts = _finite(_pick(d, TIME_KEYS))
    if market is None or price is None or price <= 0 or ts is None:
        return None
    token = _pick(d, TOKEN_KEYS)
    if not token:
        a = _pick(d, ("input_asset", "input_mint", "quote_mint"))
        b = _pick(d, ("output_asset", "output_mint", "base_mint"))
        assets = [str(x) for x in (a, b) if x]
        non_quote = [x for x in assets if x not in (USDC_MINT, SOL_MINT)]
        token = non_quote[0] if non_quote else (assets[-1] if assets else "")
    return Row(
        market=str(market),
        token=str(token or ""),
        family=str(_pick(d, FAMILY_KEYS) or "UNKNOWN"),
        t=ts,
        price=price,
        liquidity=_finite(_pick(d, LIQ_KEYS)),
        volume=_finite(_pick(d, VOL_KEYS)),
        buys=_finite(_pick(d, BUY_KEYS)),
        sells=_finite(_pick(d, SELL_KEYS)),
        source_file=source_file,
    )

@dataclass
class Config:
    paper_notional_usdc: float = 5.0
    min_history: int = 8
    max_open_positions: int = 3
    max_signal_age_seconds: int = 300
    max_hold_seconds: int = 900
    stop_loss: float = 0.12
    take_profit: float = 0.25
    trailing_stop: float = 0.10
    roundtrip_friction: float = 0.02584132405858526
    min_score: float = 0.55
    max_files: int = 300
    max_json_bytes: int = 8 * 1024 * 1024
    max_jsonl_tail_bytes: int = 2 * 1024 * 1024
    max_file_bytes: int = 64 * 1024 * 1024

    @classmethod
    def from_env(cls):
        def f(name, default): return float(os.getenv(name, str(default)))
        def i(name, default): return int(os.getenv(name, str(default)))
        return cls(
            paper_notional_usdc=f("QSB_NOTIONAL_USDC", 5.0),
            min_history=i("QSB_MIN_HISTORY", 8),
            max_open_positions=i("QSB_MAX_OPEN_POSITIONS", 3),
            max_signal_age_seconds=i("QSB_MAX_SIGNAL_AGE_SECONDS", 300),
            max_hold_seconds=i("QSB_MAX_HOLD_SECONDS", 900),
            stop_loss=f("QSB_STOP_LOSS", 0.12),
            take_profit=f("QSB_TAKE_PROFIT", 0.25),
            trailing_stop=f("QSB_TRAILING_STOP", 0.10),
            roundtrip_friction=f("QSB_ROUNDTRIP_FRICTION", 0.02584132405858526),
            min_score=f("QSB_MIN_SCORE", 0.55),
            max_files=i("QSB_MAX_FILES", 300),
            max_json_bytes=i("QSB_MAX_JSON_BYTES", 8 * 1024 * 1024),
            max_jsonl_tail_bytes=i("QSB_MAX_JSONL_TAIL_BYTES", 2 * 1024 * 1024),
            max_file_bytes=i("QSB_MAX_FILE_BYTES", 64 * 1024 * 1024),
        )

def _candidate_files(root: Path, cfg: Config):
    out = []
    for rel in SOURCE_ROOTS:
        base = root / rel
        if not base.exists():
            continue
        try:
            for p in base.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in (".json", ".jsonl"):
                    continue
                try:
                    st = p.stat()
                except OSError:
                    continue
                if st.st_size > cfg.max_file_bytes:
                    continue
                out.append((st.st_mtime, p, st.st_size))
        except OSError:
            continue
    out.sort(key=lambda x: x[0], reverse=True)
    return out[: cfg.max_files]

def _read_jsonl_tail(path: Path, max_bytes: int):
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                f.readline()
            raw = f.read(max_bytes)
        arr = []
        for line in raw.decode("utf-8", errors="replace").splitlines():
            try:
                arr.append(json.loads(line))
            except Exception:
                pass
        return arr
    except Exception:
        return []

def ingest(root: Path, cfg: Config, progress=True):
    rows: list[Row] = []
    seen = set()
    files = _candidate_files(root, cfg)
    if progress:
        print(f"[INGEST] files_selected={len(files)}", flush=True)
    for n, (_, p, size) in enumerate(files, 1):
        objs = []
        try:
            if p.suffix.lower() == ".jsonl":
                objs = _read_jsonl_tail(p, cfg.max_jsonl_tail_bytes)
            elif size <= cfg.max_json_bytes:
                objs = [json.loads(p.read_text(encoding="utf-8", errors="replace"))]
        except Exception:
            objs = []
        for obj in objs:
            for d in _walk_dicts(obj):
                r = _normalize(d, str(p.relative_to(root)))
                if r is None:
                    continue
                key = (r.market, r.t, r.price, r.token)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(r)
        if progress and (n == 1 or n % 25 == 0 or n == len(files)):
            print(f"[INGEST] scanned={n}/{len(files)} rows={len(rows)} last={p.name}", flush=True)
    rows.sort(key=lambda r: r.t)
    return rows, files

def _histories(rows: list[Row], horizon_seconds=7200):
    cutoff = _now() - horizon_seconds
    by = defaultdict(list)
    for r in rows:
        if r.t >= cutoff:
            by[r.market].append(r)
    for h in by.values():
        h.sort(key=lambda r: r.t)
    return dict(by)

def _second_leg(hist: list[Row], cfg: Config):
    if len(hist) < cfg.min_history:
        return None, "TOO_FEW_POINTS"
    p = [x.price for x in hist[-80:]]
    rows = hist[-80:]
    first = p[0]
    hi_i = max(range(len(p)), key=p.__getitem__)
    hi = p[hi_i]
    pump = hi / first - 1
    if hi_i < 1 or pump < 0.25:
        return None, "NO_INITIAL_PUMP"
    tail = p[hi_i + 1 :]
    if len(tail) < 4:
        return None, "NO_POST_HIGH_PATH"
    lo_rel = min(range(len(tail)), key=tail.__getitem__)
    lo_i = hi_i + 1 + lo_rel
    lo = p[lo_i]
    dd = 1 - lo / hi
    if not 0.20 <= dd <= 0.75:
        return None, "DRAWDOWN_OUTSIDE_GATE"
    if len(p[lo_i:]) < 3:
        return None, "NO_REBOUND_PATH"
    current = p[-1]
    rebound = current / lo - 1
    if rebound < 0.08:
        return None, "NO_REBOUND"
    base = p[max(lo_i, len(p) - 7):-2]
    if len(base) < 3:
        return None, "NO_BASE"
    base_range = max(base) / min(base) - 1
    if base_range > 0.12:
        return None, "BASE_TOO_WIDE"
    if current <= max(base):
        return None, "NO_RECLAIM"

    reclaim = (current - lo) / max(hi - lo, 1e-18)
    momentum = max(0.0, current / p[-2] - 1)
    last = rows[-1]
    flow = 0.0
    if last.buys is not None and last.sells is not None and last.buys + last.sells > 0:
        flow = max(0.0, (last.buys / (last.buys + last.sells) - 0.5) * 2)
    volume_boost = 0.0
    vols = [r.volume for r in rows if r.volume is not None]
    if len(vols) >= 4 and sum(vols[-4:-2]) > 0:
        volume_boost = max(0.0, min(1.0, sum(vols[-2:]) / sum(vols[-4:-2]) - 1))

    score = (
        0.24 * min(1, pump / 0.8)
        + 0.18 * min(1, dd / 0.5)
        + 0.22 * min(1, rebound / 0.3)
        + 0.18 * min(1, max(0.0, reclaim))
        + 0.08 * min(1, momentum / 0.08)
        + 0.06 * volume_boost
        + 0.04 * flow
    )
    s = {
        "strategy": "SECOND_LEG",
        "market": last.market,
        "token": last.token,
        "family": last.family,
        "signal_unix": last.t,
        "price": current,
        "score": score,
        "pump": pump,
        "drawdown": dd,
        "rebound": rebound,
        "base_range": base_range,
        "reclaim": reclaim,
        "momentum": momentum,
        "liquidity": last.liquidity,
        "source_file": last.source_file,
    }
    if not last.token:
        return s, "NO_TOKEN_IDENTITY"
    if _now() - last.t > cfg.max_signal_age_seconds:
        return s, "STALE"
    if score < cfg.min_score:
        return s, "SCORE_BELOW_GATE"
    return s, "READY"

class MoneyRunner:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.cfg = Config.from_env()
        self.state = self.root / STATE_DIR
        self.ledger_path = self.state / LEDGER_FILE
        self.positions_path = self.state / POSITIONS_FILE
        self.status_path = self.state / STATUS_FILE
        self.ledger = _load_json(self.ledger_path, {"trades": []})
        self.positions = _load_json(self.positions_path, {"positions": []})

    def _open_positions(self):
        return [p for p in self.positions["positions"] if p.get("status") == "OPEN"]

    def _already_traded(self, signal):
        key = f'{signal["strategy"]}:{signal["market"]}:{int(signal["signal_unix"])}'
        for p in self.positions["positions"]:
            if p.get("signal_key") == key:
                return True
        for t in self.ledger["trades"]:
            if t.get("signal_key") == key:
                return True
        return False

    def _enter(self, signal):
        friction_half = self.cfg.roundtrip_friction / 2
        ref = signal["price"]
        entry = ref * (1 + friction_half)
        n = self.cfg.paper_notional_usdc
        pos = {
            "position_id": f"PAPER-{int(_now()*1000)}",
            "mode": "PAPER",
            "status": "OPEN",
            "strategy": signal["strategy"],
            "market": signal["market"],
            "token": signal["token"],
            "family": signal["family"],
            "signal_key": f'{signal["strategy"]}:{signal["market"]}:{int(signal["signal_unix"])}',
            "opened_unix": _now(),
            "reference_entry_price": ref,
            "entry_price": entry,
            "high_water_price": entry,
            "notional_usdc": n,
            "qty": n / entry,
            "modeled_entry_friction_usdc": n * friction_half,
            "signal": signal,
        }
        self.positions["positions"].append(pos)
        _atomic_json(self.positions_path, self.positions)
        return pos

    def _manage(self, latest: dict[str, Row]):
        closed = []
        half = self.cfg.roundtrip_friction / 2
        for p in self.positions["positions"]:
            if p.get("status") != "OPEN":
                continue
            r = latest.get(p["market"])
            if r is None:
                continue
            px = r.price
            entry = float(p["entry_price"])
            p["high_water_price"] = max(float(p.get("high_water_price", entry)), px)
            ret = px / entry - 1
            trail = px / p["high_water_price"] - 1
            age = _now() - float(p["opened_unix"])
            reason = None
            if ret <= -self.cfg.stop_loss:
                reason = "STOP_LOSS"
            elif ret >= self.cfg.take_profit:
                reason = "TAKE_PROFIT"
            elif p["high_water_price"] >= entry * 1.08 and trail <= -self.cfg.trailing_stop:
                reason = "TRAILING_STOP"
            elif age >= self.cfg.max_hold_seconds:
                reason = "MAX_HOLD"
            if reason is None:
                continue
            exit_px = px * (1 - half)
            gross_proceeds = p["qty"] * px
            net_proceeds = p["qty"] * exit_px
            gross_pnl = gross_proceeds - p["notional_usdc"]
            net_pnl = net_proceeds - p["notional_usdc"]
            friction = gross_pnl - net_pnl + float(p.get("modeled_entry_friction_usdc") or 0)
            p.update({
                "status": "CLOSED",
                "closed_unix": _now(),
                "reference_exit_price": px,
                "exit_price": exit_px,
                "exit_reason": reason,
                "gross_pnl_usdc": gross_pnl,
                "modeled_friction_usdc": friction,
                "net_pnl_usdc": net_pnl,
                "net_return": net_pnl / p["notional_usdc"],
            })
            self.ledger["trades"].append(dict(p))
            closed.append(dict(p))
        _atomic_json(self.positions_path, self.positions)
        _atomic_json(self.ledger_path, self.ledger)
        return closed

    def cycle(self, progress=True):
        rows, files = ingest(self.root, self.cfg, progress=progress)
        hist = _histories(rows)
        latest = {m: h[-1] for m, h in hist.items() if h}

        closed = self._manage(latest)
        reasons = Counter()
        setups = []
        for market, h in hist.items():
            sig, reason = _second_leg(h, self.cfg)
            reasons[reason] += 1
            if sig:
                sig = dict(sig)
                sig["gate_reason"] = reason
                setups.append(sig)
        setups.sort(key=lambda s: s["score"], reverse=True)

        entered = []
        open_now = len(self._open_positions())
        capacity = max(0, self.cfg.max_open_positions - open_now)
        for s in setups:
            if capacity <= 0:
                break
            if s["gate_reason"] != "READY":
                continue
            if self._already_traded(s):
                reasons["DUPLICATE_SIGNAL"] += 1
                continue
            entered.append(self._enter(s))
            capacity -= 1

        trades = self.ledger["trades"]
        wins = sum(1 for t in trades if float(t.get("net_pnl_usdc") or 0) > 0)
        losses = sum(1 for t in trades if float(t.get("net_pnl_usdc") or 0) < 0)
        gross = sum(float(t.get("gross_pnl_usdc") or 0) for t in trades)
        friction = sum(float(t.get("modeled_friction_usdc") or 0) for t in trades)
        net = sum(float(t.get("net_pnl_usdc") or 0) for t in trades)

        status = {
            "revision": REVISION,
            "unix": _now(),
            "source_files": len(files),
            "source_rows": len(rows),
            "tokens_watched": len({r.token for r in rows if r.token}),
            "markets_watched": len(hist),
            "setups_found": len(setups),
            "ready_setups": sum(s["gate_reason"] == "READY" for s in setups),
            "trades_entered_this_cycle": len(entered),
            "trades_closed_this_cycle": len(closed),
            "closed_trades": len(trades),
            "wins": wins,
            "losses": losses,
            "win_rate": wins / len(trades) if trades else None,
            "gross_pnl_usdc": gross,
            "modeled_friction_usdc": friction,
            "net_pnl_usdc": net,
            "open_positions": len(self._open_positions()),
            "top_setups": setups[:10],
            "why_no_trade": dict(reasons.most_common(12)),
            "profitability_proven": bool(len(trades) >= 20 and net > 0 and wins / len(trades) > 0.5),
            "execution_mode": "PAPER_ONLY",
        }
        _atomic_json(self.status_path, status)
        return status

def print_status(s):
    print("=" * 118)
    print(" Q SERIES SOLANA MONEY RUNNER")
    print("=" * 118)
    print(f"[FEED] files={s['source_files']} rows={s['source_rows']} markets={s['markets_watched']} tokens={s['tokens_watched']}")
    print(f"[SETUPS] found={s['setups_found']} ready={s['ready_setups']} entered={s['trades_entered_this_cycle']} closed={s['trades_closed_this_cycle']}")
    print(f"[LEDGER] closed={s['closed_trades']} wins={s['wins']} losses={s['losses']} win_rate={s['win_rate']}")
    print(f"[MONEY] gross=${s['gross_pnl_usdc']:.4f} friction=${s['modeled_friction_usdc']:.4f} NET=${s['net_pnl_usdc']:.4f}")
    print(f"[OPEN] {s['open_positions']} | [PROFITABILITY_PROVEN] {s['profitability_proven']} | [MODE] {s['execution_mode']}")
    if s["top_setups"]:
        x = s["top_setups"][0]
        print(f"[TOP] {x['gate_reason']} score={x['score']:.3f} family={x['family']} market={x['market']} token={x['token']} price={x['price']}")
    if s["why_no_trade"]:
        print("[WHY_NO_TRADE]", json.dumps(s["why_no_trade"], sort_keys=True))
    print("=" * 118)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--sleep", type=int, default=5)
    args = ap.parse_args()
    bot = MoneyRunner(Path(args.root))
    while True:
        print_status(bot.cycle(progress=True))
        if args.once:
            break
        time.sleep(max(1, args.sleep))

if __name__ == "__main__":
    main()
