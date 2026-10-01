from __future__ import annotations

import argparse
import base64
import json
import math
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REVISION = "QSB-001C-UNIFIED-SOLANA-MONEY-BOT-PHYSICAL-REPAIR"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_MINT = "So11111111111111111111111111111111111111112"
JUPITER_ULTRA = os.getenv("QSB_JUPITER_ULTRA_URL", "https://lite-api.jup.ag/ultra/v1")
STATE_REL = Path("runtime_state/qseries/solana_money_bot")
SOURCE_ROOTS = (
    Path("runtime_state/solana_opportunities"),
    Path("runtime/solana"),
    Path("runtime/strategy_discovery"),
)

def now():
    return time.time()

def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8")
    tmp.replace(path)

def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def finite(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def pick(d, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None

def candidate_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            if isinstance(v, (dict, list)):
                yield from candidate_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, list)):
                yield from candidate_dicts(v)

def normalize_row(d):
    pool = pick(d, "market_address", "pool_address", "pool", "market", "pair_address")
    price = finite(pick(d, "effective_price", "last_price", "price", "first_price",
                        "directed_effective_price", "entry_reference_price"))
    ts = finite(pick(d, "observed_unix", "timestamp_unix", "freeze_unix", "block_time",
                     "blockTime", "timestamp", "t"))
    family = pick(d, "family", "venue", "protocol", "source_family")
    mint = pick(d, "token_mint", "mint", "base_mint", "output_asset", "token_address")
    input_asset = pick(d, "input_asset", "quote_mint")
    output_asset = pick(d, "output_asset", "base_mint")
    if not mint:
        assets = [x for x in (input_asset, output_asset) if isinstance(x, str)]
        non_quote = [x for x in assets if x not in (USDC_MINT, SOL_MINT)]
        mint = non_quote[0] if non_quote else (assets[-1] if assets else None)
    if not pool or price is None or price <= 0 or ts is None:
        return None
    return {
        "pool": str(pool),
        "family": str(family or "UNKNOWN"),
        "token_mint": str(mint or ""),
        "price": price,
        "t": ts,
        "liquidity": finite(pick(d, "liquidity_usd", "quote_reserve_liquidity", "liquidity")),
        "volume": finite(pick(d, "volume_usd", "volume", "quote_volume")),
        "trade_count": finite(pick(d, "trade_count", "trades", "tx_count")),
        "buy_count": finite(pick(d, "buy_count", "buys", "buyer_count")),
        "sell_count": finite(pick(d, "sell_count", "sells", "seller_count")),
    }

def ingest(root: Path):
    rows, seen = [], set()
    for rel in SOURCE_ROOTS:
        base = root / rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".json", ".jsonl"):
                continue
            try:
                if p.suffix.lower() == ".jsonl":
                    objs = []
                    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                        try:
                            objs.append(json.loads(line))
                        except Exception:
                            pass
                else:
                    objs = [json.loads(p.read_text(encoding="utf-8", errors="replace"))]
            except Exception:
                continue
            for obj in objs:
                for d in candidate_dicts(obj):
                    r = normalize_row(d)
                    if not r:
                        continue
                    key = (r["pool"], r["t"], r["price"], r["token_mint"])
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(r)
    rows.sort(key=lambda x: x["t"])
    return rows

@dataclass
class Config:
    mode: str = field(default_factory=lambda: os.getenv("QSB_MODE", "PAPER").upper())
    paper_notional_usdc: float = field(default_factory=lambda: float(os.getenv("QSB_PAPER_NOTIONAL_USDC", "5")))
    live_notional_usdc: float = field(default_factory=lambda: float(os.getenv("QSB_LIVE_NOTIONAL_USDC", "1")))
    max_live_trade_usdc: float = field(default_factory=lambda: float(os.getenv("QSB_MAX_LIVE_TRADE_USDC", "5")))
    max_open_positions: int = field(default_factory=lambda: int(os.getenv("QSB_MAX_OPEN_POSITIONS", "1")))
    max_daily_loss_usdc: float = field(default_factory=lambda: float(os.getenv("QSB_MAX_DAILY_LOSS_USDC", "10")))
    slippage_bps: int = field(default_factory=lambda: int(os.getenv("QSB_MAX_SLIPPAGE_BPS", "300")))
    min_history_points: int = field(default_factory=lambda: int(os.getenv("QSB_MIN_HISTORY_POINTS", "8")))
    min_initial_pump: float = field(default_factory=lambda: float(os.getenv("QSB_MIN_INITIAL_PUMP", "0.25")))
    min_drawdown: float = field(default_factory=lambda: float(os.getenv("QSB_MIN_DRAWDOWN", "0.20")))
    max_drawdown: float = field(default_factory=lambda: float(os.getenv("QSB_MAX_DRAWDOWN", "0.70")))
    min_rebound: float = field(default_factory=lambda: float(os.getenv("QSB_MIN_REBOUND", "0.08")))
    max_base_range: float = field(default_factory=lambda: float(os.getenv("QSB_MAX_BASE_RANGE", "0.10")))
    stop_loss: float = field(default_factory=lambda: float(os.getenv("QSB_STOP_LOSS", "0.12")))
    take_profit: float = field(default_factory=lambda: float(os.getenv("QSB_TAKE_PROFIT", "0.25")))
    trailing_stop: float = field(default_factory=lambda: float(os.getenv("QSB_TRAILING_STOP", "0.10")))
    max_hold_seconds: int = field(default_factory=lambda: int(os.getenv("QSB_MAX_HOLD_SECONDS", "900")))
    modeled_roundtrip_friction: float = field(default_factory=lambda: float(os.getenv("QSB_MODELED_ROUNDTRIP_FRICTION", "0.02584132405858526")))
    max_signal_age_seconds: int = field(default_factory=lambda: int(os.getenv("QSB_MAX_SIGNAL_AGE_SECONDS", "180")))
    min_score: float = field(default_factory=lambda: float(os.getenv("QSB_MIN_SCORE", "0.70")))

class UnifiedSolanaMoneyBot:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.cfg = Config()
        self.state_dir = self.root / STATE_REL
        self.positions_path = self.state_dir / "positions.json"
        self.trades_path = self.state_dir / "trades.json"
        self.signals_path = self.state_dir / "signals.json"
        self.runtime_path = self.state_dir / "runtime.json"
        self.positions = load_json(self.positions_path, {"positions": []})
        self.trades = load_json(self.trades_path, {"trades": []})
        self.signals = load_json(self.signals_path, {"seen": {}})

    def histories(self, rows):
        out = {}
        cutoff = now() - 7200
        for r in rows:
            if r["t"] < cutoff:
                continue
            out.setdefault(r["pool"], []).append(r)
        for pool in out:
            out[pool].sort(key=lambda x: x["t"])
        return out

    def detect_second_leg(self, hist):
        c = self.cfg
        if len(hist) < c.min_history_points:
            return None
        recent = hist[-80:]
        prices = [x["price"] for x in recent]
        first = prices[0]
        high_i = max(range(len(prices)), key=prices.__getitem__)
        high = prices[high_i]
        if high_i < 1 or high / first - 1 < c.min_initial_pump:
            return None
        tail = prices[high_i + 1:]
        if len(tail) < 4:
            return None
        low_rel = min(range(len(tail)), key=tail.__getitem__)
        low_i = high_i + 1 + low_rel
        low = prices[low_i]
        drawdown = 1 - low / high
        if not (c.min_drawdown <= drawdown <= c.max_drawdown):
            return None
        after_low = prices[low_i:]
        if len(after_low) < 3:
            return None
        current = prices[-1]
        rebound = current / low - 1
        if rebound < c.min_rebound:
            return None
        # Measure the base BEFORE the final two reclaim/breakout bars.
        # The original QSB-001 incorrectly included the breakout itself in
        # the compression window, causing valid second-leg structures to fail.
        pre_breakout = prices[low_i:-2]
        if len(pre_breakout) < 3:
            return None
        base = pre_breakout[-5:]
        base_range = max(base) / min(base) - 1
        if base_range > c.max_base_range:
            return None
        if current <= max(base):
            return None
        reclaim_fraction = (current - low) / max(high - low, 1e-18)
        momentum = (current / prices[-2] - 1) if len(prices) >= 2 else 0
        vol = [x["volume"] for x in recent if x["volume"] is not None]
        volume_accel = 0.0
        if len(vol) >= 4 and sum(vol[-4:-2]) > 0:
            volume_accel = max(0.0, min(1.0, (sum(vol[-2:]) / sum(vol[-4:-2]) - 1) / 2))
        flow = 0.0
        last = recent[-1]
        if last["buy_count"] is not None and last["sell_count"] is not None:
            total = last["buy_count"] + last["sell_count"]
            if total > 0:
                flow = max(0.0, (last["buy_count"] / total - 0.5) * 2)
        score = (
            0.22 * min(1.0, (high / first - 1) / 1.0) +
            0.18 * min(1.0, drawdown / 0.50) +
            0.22 * min(1.0, rebound / 0.30) +
            0.18 * min(1.0, max(0.0, reclaim_fraction)) +
            0.08 * min(1.0, max(0.0, momentum) / 0.10) +
            0.07 * volume_accel +
            0.05 * flow
        )
        return {
            "pattern": "PUMP_DIP_BASE_RECLAIM_SECOND_LEG",
            "pool": recent[-1]["pool"],
            "family": recent[-1]["family"],
            "token_mint": recent[-1]["token_mint"],
            "signal_unix": recent[-1]["t"],
            "current_price": current,
            "initial_price": first,
            "initial_high": high,
            "post_high_low": low,
            "initial_pump": high / first - 1,
            "drawdown": drawdown,
            "rebound": rebound,
            "base_range": base_range,
            "reclaim_fraction": reclaim_fraction,
            "momentum": momentum,
            "score": score,
            "liquidity": recent[-1]["liquidity"],
            "volume": recent[-1]["volume"],
        }

    def eligible(self, s):
        if not s:
            return False, "NO_PATTERN"
        if not s.get("token_mint"):
            return False, "NO_TOKEN_MINT"
        if now() - s["signal_unix"] > self.cfg.max_signal_age_seconds:
            return False, "STALE_SIGNAL"
        if s["score"] < self.cfg.min_score:
            return False, "SCORE_BELOW_GATE"
        if any(p.get("status") == "OPEN" for p in self.positions["positions"]):
            return False, "POSITION_ALREADY_OPEN"
        seen = self.signals["seen"]
        key = f'{s["pool"]}:{int(s["signal_unix"])}'
        if key in seen:
            return False, "DUPLICATE_SIGNAL"
        daily = self.daily_realized_pnl()
        if daily <= -self.cfg.max_daily_loss_usdc:
            return False, "DAILY_LOSS_LIMIT"
        return True, "READY"

    def daily_realized_pnl(self):
        cutoff = now() - 86400
        return sum(float(t.get("realized_pnl_usdc") or 0) for t in self.trades["trades"]
                   if float(t.get("closed_unix") or 0) >= cutoff)

    def mark_seen(self, s, action):
        key = f'{s["pool"]}:{int(s["signal_unix"])}'
        self.signals["seen"][key] = {"action": action, "seen_unix": now()}
        atomic_json(self.signals_path, self.signals)

    def paper_enter(self, s):
        n = self.cfg.paper_notional_usdc
        friction_half = self.cfg.modeled_roundtrip_friction / 2
        entry = s["current_price"] * (1 + friction_half)
        qty = n / entry
        p = {
            "position_id": f'PAPER-{int(now()*1000)}',
            "mode": "PAPER", "status": "OPEN", "pattern": s["pattern"],
            "pool": s["pool"], "token_mint": s["token_mint"], "family": s["family"],
            "entry_price": entry, "reference_entry_price": s["current_price"],
            "qty": qty, "notional_usdc": n, "opened_unix": now(), "signal": s,
            "high_water_price": entry, "real_money_moved": False,
        }
        self.positions["positions"].append(p)
        atomic_json(self.positions_path, self.positions)
        self.mark_seen(s, "PAPER_ENTER")
        return p

    def paper_manage(self, latest_by_pool):
        closed = []
        for p in self.positions["positions"]:
            if p.get("status") != "OPEN" or p.get("mode") != "PAPER":
                continue
            r = latest_by_pool.get(p["pool"])
            if not r:
                continue
            px = r["price"]
            p["high_water_price"] = max(float(p.get("high_water_price") or p["entry_price"]), px)
            ret = px / p["entry_price"] - 1
            trail = px / p["high_water_price"] - 1
            age = now() - p["opened_unix"]
            reason = None
            if ret <= -self.cfg.stop_loss:
                reason = "STOP_LOSS"
            elif ret >= self.cfg.take_profit:
                reason = "TAKE_PROFIT"
            elif p["high_water_price"] > p["entry_price"] * 1.08 and trail <= -self.cfg.trailing_stop:
                reason = "TRAILING_STOP"
            elif age >= self.cfg.max_hold_seconds:
                reason = "MAX_HOLD"
            if not reason:
                continue
            friction_half = self.cfg.modeled_roundtrip_friction / 2
            exit_px = px * (1 - friction_half)
            proceeds = p["qty"] * exit_px
            pnl = proceeds - p["notional_usdc"]
            p.update(status="CLOSED", exit_price=exit_px, reference_exit_price=px,
                     closed_unix=now(), exit_reason=reason, realized_pnl_usdc=pnl,
                     realized_return=pnl / p["notional_usdc"])
            self.trades["trades"].append(dict(p))
            closed.append(dict(p))
        atomic_json(self.positions_path, self.positions)
        atomic_json(self.trades_path, self.trades)
        return closed

    def _live_armed(self):
        return (
            self.cfg.mode == "LIVE" and
            os.getenv("QSB_LIVE_ARM", "") == "I_ACCEPT_REAL_MONEY_RISK" and
            0 < self.cfg.live_notional_usdc <= self.cfg.max_live_trade_usdc
        )

    def _keypair(self):
        try:
            from solders.keypair import Keypair
        except Exception as e:
            raise RuntimeError("LIVE_REQUIRES_SOLDERS") from e
        secret = os.getenv("QSB_SOLANA_PRIVATE_KEY", "").strip()
        if not secret:
            raise RuntimeError("QSB_SOLANA_PRIVATE_KEY_MISSING")
        if secret.startswith("["):
            return Keypair.from_bytes(bytes(json.loads(secret)))
        return Keypair.from_base58_string(secret)

    def _http_json(self, url, method="GET", payload=None, timeout=20):
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def _jupiter_order(self, input_mint, output_mint, amount, taker):
        q = urllib.parse.urlencode({
            "inputMint": input_mint, "outputMint": output_mint,
            "amount": str(int(amount)), "taker": taker,
            "slippageBps": str(self.cfg.slippage_bps),
        })
        return self._http_json(f"{JUPITER_ULTRA}/order?{q}")

    def _sign_jupiter_transaction(self, tx_b64, kp):
        try:
            from solders.transaction import VersionedTransaction
            from solders.message import to_bytes_versioned
        except Exception as e:
            raise RuntimeError("LIVE_REQUIRES_SOLDERS") from e
        tx = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
        sig = kp.sign_message(to_bytes_versioned(tx.message))
        signed = VersionedTransaction.populate(tx.message, [sig])
        return base64.b64encode(bytes(signed)).decode()

    def _jupiter_execute(self, signed_tx_b64, request_id):
        return self._http_json(f"{JUPITER_ULTRA}/execute", "POST",
                               {"signedTransaction": signed_tx_b64, "requestId": request_id})

    def live_swap(self, input_mint, output_mint, amount):
        if not self._live_armed():
            raise RuntimeError("LIVE_NOT_ARMED")
        kp = self._keypair()
        order = self._jupiter_order(input_mint, output_mint, amount, str(kp.pubkey()))
        if not order.get("transaction") or not order.get("requestId"):
            raise RuntimeError("JUPITER_ORDER_NOT_EXECUTABLE:" + json.dumps(order)[:500])
        impact = finite(order.get("priceImpactPct"))
        if impact is not None and abs(impact) > self.cfg.slippage_bps / 10000:
            raise RuntimeError("PRICE_IMPACT_LIMIT")
        signed = self._sign_jupiter_transaction(order["transaction"], kp)
        result = self._jupiter_execute(signed, order["requestId"])
        return {"order": order, "execute": result}

    def live_enter(self, s):
        if not self._live_armed():
            return {"submitted": False, "reason": "LIVE_NOT_ARMED"}
        raw_usdc = int(round(self.cfg.live_notional_usdc * 1_000_000))
        result = self.live_swap(USDC_MINT, s["token_mint"], raw_usdc)
        exe, order = result["execute"], result["order"]
        status = str(exe.get("status", "")).lower()
        if status not in ("success", "confirmed", "finalized"):
            return {"submitted": True, "filled": False, "result": result}
        out_raw = int(exe.get("outputAmount") or order.get("outAmount") or 0)
        if out_raw <= 0:
            raise RuntimeError("LIVE_ENTRY_OUTPUT_AMOUNT_MISSING")
        p = {
            "position_id": f'LIVE-{int(now()*1000)}', "mode": "LIVE", "status": "OPEN",
            "pattern": s["pattern"], "pool": s["pool"], "family": s["family"],
            "token_mint": s["token_mint"], "opened_unix": now(), "signal": s,
            "input_usdc_raw": raw_usdc, "token_raw_amount": out_raw,
            "entry_signature": exe.get("signature"), "real_money_moved": True,
            "reference_entry_price": s["current_price"], "high_water_price": s["current_price"],
        }
        self.positions["positions"].append(p)
        atomic_json(self.positions_path, self.positions)
        self.mark_seen(s, "LIVE_ENTER")
        return {"submitted": True, "filled": True, "position": p, "result": result}

    def live_manage(self, latest_by_pool):
        closed = []
        if not self._live_armed():
            return closed
        for p in self.positions["positions"]:
            if p.get("status") != "OPEN" or p.get("mode") != "LIVE":
                continue
            r = latest_by_pool.get(p["pool"])
            if not r:
                continue
            px = r["price"]
            ref = float(p["reference_entry_price"])
            p["high_water_price"] = max(float(p.get("high_water_price") or ref), px)
            ret = px / ref - 1
            trail = px / p["high_water_price"] - 1
            age = now() - p["opened_unix"]
            reason = None
            if ret <= -self.cfg.stop_loss:
                reason = "STOP_LOSS"
            elif ret >= self.cfg.take_profit:
                reason = "TAKE_PROFIT"
            elif p["high_water_price"] > ref * 1.08 and trail <= -self.cfg.trailing_stop:
                reason = "TRAILING_STOP"
            elif age >= self.cfg.max_hold_seconds:
                reason = "MAX_HOLD"
            if not reason:
                continue
            amount = int(p["token_raw_amount"] * 0.995)
            result = self.live_swap(p["token_mint"], USDC_MINT, amount)
            exe, order = result["execute"], result["order"]
            status = str(exe.get("status", "")).lower()
            if status not in ("success", "confirmed", "finalized"):
                continue
            out_raw = int(exe.get("outputAmount") or order.get("outAmount") or 0)
            proceeds = out_raw / 1_000_000
            cost = p["input_usdc_raw"] / 1_000_000
            pnl = proceeds - cost
            p.update(status="CLOSED", closed_unix=now(), exit_reason=reason,
                     exit_signature=exe.get("signature"), output_usdc_raw=out_raw,
                     realized_pnl_usdc=pnl, realized_return=pnl / cost if cost else None)
            self.trades["trades"].append(dict(p))
            closed.append(dict(p))
        atomic_json(self.positions_path, self.positions)
        atomic_json(self.trades_path, self.trades)
        return closed

    def cycle(self):
        rows = ingest(self.root)
        histories = self.histories(rows)
        latest = {pool: hist[-1] for pool, hist in histories.items() if hist}
        paper_closed = self.paper_manage(latest)
        live_closed = self.live_manage(latest)
        candidates = []
        for pool, hist in histories.items():
            s = self.detect_second_leg(hist)
            ok, reason = self.eligible(s)
            if s:
                candidates.append({**s, "eligible": ok, "gate_reason": reason})
        candidates.sort(key=lambda x: x["score"], reverse=True)
        action = {"action": "NONE"}
        for s in candidates:
            if not s["eligible"]:
                continue
            if self.cfg.mode == "PAPER":
                action = {"action": "PAPER_ENTER", "position": self.paper_enter(s)}
            elif self.cfg.mode == "LIVE":
                action = {"action": "LIVE_ENTER", "result": self.live_enter(s)}
            else:
                action = {"action": "ABSTAIN", "reason": "UNKNOWN_MODE"}
            break
        runtime = {
            "revision": REVISION, "unix": now(), "mode": self.cfg.mode,
            "source_rows": len(rows), "markets": len(histories),
            "candidates": candidates[:20], "action": action,
            "open_positions": sum(p.get("status") == "OPEN" for p in self.positions["positions"]),
            "paper_closed_this_cycle": len(paper_closed),
            "live_closed_this_cycle": len(live_closed),
            "realized_pnl_usdc_all": sum(float(t.get("realized_pnl_usdc") or 0) for t in self.trades["trades"]),
            "daily_realized_pnl_usdc": self.daily_realized_pnl(),
            "live_armed": self._live_armed(), "execution_owner": "Q_SERIES",
            "oracle_required_for_decision": False,
        }
        atomic_json(self.runtime_path, runtime)
        return runtime

def format_status(d):
    lines = [
        "=" * 122,
        " Q SERIES UNIFIED SOLANA MONEY BOT",
        "=" * 122,
        f" mode={d['mode']} | live_armed={d['live_armed']} | source_rows={d['source_rows']} | markets={d['markets']}",
        f" open_positions={d['open_positions']} | realized_pnl_usdc={d['realized_pnl_usdc_all']:.4f} | daily_pnl={d['daily_realized_pnl_usdc']:.4f}",
        f" candidates={len(d['candidates'])} | action={d['action'].get('action')}",
    ]
    for s in d["candidates"][:5]:
        lines.append(
            f" {s['gate_reason']:>24} | score={s['score']:.3f} | {s['family']} | "
            f"pool={s['pool']} | pump={s['initial_pump']:.1%} | dd={s['drawdown']:.1%} | "
            f"rebound={s['rebound']:.1%}"
        )
    lines.append("=" * 122)
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--sleep", type=int, default=5)
    args = ap.parse_args()
    bot = UnifiedSolanaMoneyBot(args.root)
    while True:
        try:
            print(format_status(bot.cycle()), flush=True)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("[ERROR]", repr(e), flush=True)
        if args.once:
            break
        time.sleep(max(1, args.sleep))

if __name__ == "__main__":
    main()
