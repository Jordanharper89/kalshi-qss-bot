from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "oracle_live_trade_tracker.py"
CONTINUOUS = ROOT / "oracle_continuous_intelligence.py"

CODE = r'''
"""
ORACLE-066 Live Trade Tracker

Purpose:
- Track Oracle opportunities after discovery.
- Records paper entry, current price, best/worst price, MFE/MAE, time active.
- Foundation for future self-learning outcome scoring.
- Does NOT place trades.
"""

from datetime import datetime, UTC
from pathlib import Path
import json
import hashlib

STATE_FILE = Path("oracle_live_trade_tracker_state.json")
MAX_TRADES = 1000


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _txt(v):
    return str(v or "").strip()


class OracleLiveTradeTracker:
    def __init__(self):
        self.version = "ORACLE-066"
        self.state = {
            "open_trades": {},
            "closed_trades": [],
            "history": [],
        }
        self._load()

    def track(self, ranked):
        ranked = ranked if isinstance(ranked, list) else []

        updated = []
        opened = []
        ignored = []

        for item in ranked:
            if not isinstance(item, dict):
                continue

            action = _txt(item.get("oracle_final_action")).upper()
            if action not in ("READY_FOR_EXECUTION", "HUMAN_REVIEW", "WATCH"):
                ignored.append({
                    "ticker": item.get("ticker"),
                    "reason": f"Final action {action} is not trackable."
                })
                continue

            trade_id = self._trade_id(item)
            price = self._current_price(item)
            now = datetime.now(UTC).isoformat()

            if trade_id not in self.state["open_trades"]:
                trade = self._new_trade(trade_id, item, price, now)
                self.state["open_trades"][trade_id] = trade
                opened.append(trade)
            else:
                trade = self.state["open_trades"][trade_id]
                self._update_trade(trade, item, price, now)
                updated.append(trade)

        self._save()

        return {
            "module": "oracle_live_trade_tracker",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "opened": len(opened),
            "updated": len(updated),
            "ignored": len(ignored),
            "open_count": len(self.state["open_trades"]),
            "closed_count": len(self.state["closed_trades"]),
            "opened_trades": opened[:10],
            "updated_trades": updated[:10],
            "ignored_items": ignored[:10],
            "open_trades": list(self.state["open_trades"].values())[-25:],
            "state_file": str(STATE_FILE),
        }

    def _trade_id(self, item):
        raw = f"{item.get('ticker')}|{item.get('title')}|{item.get('side') or item.get('consensus_final_recommendation')}"
        return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:18]

    def _current_price(self, item):
        price_metrics = item.get("price_metrics") if isinstance(item.get("price_metrics"), dict) else {}
        avg_mid = _num(price_metrics.get("avg_mid"), None)
        if avg_mid is not None and avg_mid > 0:
            return avg_mid

        obi = item.get("order_book_intelligence") if isinstance(item.get("order_book_intelligence"), dict) else {}
        metrics = obi.get("metrics") if isinstance(obi.get("metrics"), dict) else {}
        raw_edge = _num(metrics.get("raw_edge"), 0)

        market_price = _num(item.get("market_price"), 0)
        if market_price > 0:
            return market_price

        edge = _num(item.get("edge"), raw_edge)
        if edge > 0:
            return max(0.01, min(0.99, 0.50 - edge / 2))

        return 0.50

    def _new_trade(self, trade_id, item, price, now):
        side = _txt(item.get("side") or item.get("consensus_final_recommendation") or "WATCH").upper()

        return {
            "module": "oracle_live_trade_tracker",
            "version": self.version,
            "trade_id": trade_id,
            "status": "OPEN",
            "opened_at": now,
            "updated_at": now,
            "ticker": item.get("ticker"),
            "title": item.get("title"),
            "side": side,
            "entry_price": round(price, 6),
            "current_price": round(price, 6),
            "best_price": round(price, 6),
            "worst_price": round(price, 6),
            "mfe": 0.0,
            "mae": 0.0,
            "paper_pnl": 0.0,
            "updates": 1,
            "oracle_final_action": item.get("oracle_final_action"),
            "oracle_final_score": item.get("oracle_final_score"),
            "ev_decision": item.get("ev_decision"),
            "ev_score": item.get("ev_score"),
            "market_regime": item.get("market_regime"),
            "entry_snapshot": self._snapshot(item),
            "latest_snapshot": self._snapshot(item),
            "compact_card": "",
        }

    def _update_trade(self, trade, item, price, now):
        trade["updated_at"] = now
        trade["current_price"] = round(price, 6)
        trade["best_price"] = round(max(_num(trade.get("best_price"), price), price), 6)
        trade["worst_price"] = round(min(_num(trade.get("worst_price"), price), price), 6)
        trade["updates"] = int(trade.get("updates", 0)) + 1
        trade["latest_snapshot"] = self._snapshot(item)

        entry = _num(trade.get("entry_price"), price)
        side = _txt(trade.get("side")).upper()

        if "BUY NO" in side:
            pnl = entry - price
            mfe = entry - trade["worst_price"]
            mae = entry - trade["best_price"]
        else:
            pnl = price - entry
            mfe = trade["best_price"] - entry
            mae = trade["worst_price"] - entry

        trade["paper_pnl"] = round(pnl, 6)
        trade["mfe"] = round(mfe, 6)
        trade["mae"] = round(mae, 6)
        trade["compact_card"] = self._card(trade)

    def _snapshot(self, item):
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "final_action": item.get("oracle_final_action"),
            "final_score": item.get("oracle_final_score"),
            "consensus": item.get("consensus_final_recommendation"),
            "consensus_confidence": item.get("consensus_confidence"),
            "ev_decision": item.get("ev_decision"),
            "ev_score": item.get("ev_score"),
            "readiness": item.get("trade_readiness_verdict"),
            "readiness_score": item.get("trade_readiness_score"),
            "queue_decision": item.get("queue_decision"),
            "execution_decision": item.get("execution_decision"),
            "tradability": item.get("tradability"),
            "order_book_rating": item.get("order_book_rating"),
            "flow_signal": item.get("flow_signal"),
            "market_regime": item.get("market_regime"),
        }

    def _card(self, trade):
        return "\n".join([
            "📈 ORACLE LIVE TRADE TRACKER",
            f"Trade ID: {trade.get('trade_id')}",
            f"Ticker: {trade.get('ticker')}",
            f"Market: {trade.get('title')}",
            "",
            f"Status: {trade.get('status')}",
            f"Side: {trade.get('side')}",
            f"Entry: {trade.get('entry_price')}",
            f"Current: {trade.get('current_price')}",
            f"Best: {trade.get('best_price')}",
            f"Worst: {trade.get('worst_price')}",
            f"Paper P&L: {trade.get('paper_pnl')}",
            f"MFE: {trade.get('mfe')}",
            f"MAE: {trade.get('mae')}",
            f"Updates: {trade.get('updates')}",
            "",
            f"Final Action: {trade.get('oracle_final_action')}",
            f"EV: {trade.get('ev_decision')} | {trade.get('ev_score')}",
            f"Regime: {trade.get('market_regime')}",
        ])

    def diagnostics(self):
        return {
            "module": "oracle_live_trade_tracker",
            "version": self.version,
            "status": "ok",
            "open_count": len(self.state.get("open_trades", {})),
            "closed_count": len(self.state.get("closed_trades", [])),
            "state_file": str(STATE_FILE),
        }

    def _load(self):
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.state.update(data)
        except Exception:
            pass

    def _save(self):
        try:
            STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception:
            pass


oracle_live_trade_tracker = OracleLiveTradeTracker()


if __name__ == "__main__":
    sample = [{
        "ticker": "TEST",
        "title": "Sample tracked trade",
        "side": "BUY YES",
        "oracle_final_action": "HUMAN_REVIEW",
        "oracle_final_score": 72,
        "ev_decision": "WATCH_EV",
        "ev_score": 8,
        "market_regime": "TRENDING_EDGE",
        "price_metrics": {"avg_mid": 0.42},
    }]

    import pprint
    pprint.pp(oracle_live_trade_tracker.track(sample))
'''

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-066 Live Trade Tracker Integration
# ============================================================

try:
    from oracle_live_trade_tracker import oracle_live_trade_tracker
except Exception:
    oracle_live_trade_tracker = None


def _oracle066_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            ranked = _state.get("last_ranked", [])

            if oracle_live_trade_tracker is None:
                _state["live_trade_tracker_status"] = {"status": "missing"}
                _state["live_trades"] = []
                return

            result = oracle_live_trade_tracker.track(ranked if isinstance(ranked, list) else [])
            _state["live_trade_tracker_status"] = result
            _state["live_trades"] = result.get("open_trades", [])
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["live_trade_tracker_status"] = {"status": "error", "error": str(exc)}
            _state["live_trades"] = []


if "_oracle066_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle066_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle066_original_run_cycle(*args, **kwargs)
        _oracle066_enrich_state()
        return result


if "_oracle066_original_status" not in globals() and "status" in globals():
    _oracle066_original_status = status

    def status(*args, **kwargs):
        result = _oracle066_original_status(*args, **kwargs)
        _oracle066_enrich_state()

        if isinstance(result, dict):
            result["live_trade_tracker_status"] = (
                globals().get("_state", {}).get("live_trade_tracker_status")
                if isinstance(globals().get("_state"), dict)
                else {"status": "unknown"}
            )
            result["live_trades"] = (
                globals().get("_state", {}).get("live_trades")
                if isinstance(globals().get("_state"), dict)
                else []
            )

        return result

# ============================================================
# END ORACLE-066
# ============================================================
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle066_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-066 INSTALLER")
    print(" Live Trade Tracker")
    print("===================================")

    backup(TARGET)
    TARGET.write_text(CODE, encoding="utf-8")
    print("[OK] Created oracle_live_trade_tracker.py")

    if CONTINUOUS.exists():
        text = CONTINUOUS.read_text(encoding="utf-8", errors="ignore")
        if "ORACLE-066 Live Trade Tracker Integration" in text:
            print("[SKIP] Continuous Intelligence already patched")
        else:
            b = backup(CONTINUOUS)
            marker = 'if __name__ == "__main__":'
            if marker in text:
                text = text.replace(marker, PATCH_BLOCK + "\n\n" + marker, 1)
            else:
                text += "\n\n" + PATCH_BLOCK + "\n"
            CONTINUOUS.write_text(text, encoding="utf-8")
            print("[OK] Patched oracle_continuous_intelligence.py")
            print(f"[OK] Backup created: {b}")
    else:
        print("[WARN] oracle_continuous_intelligence.py not found")

    print("")
    print("Tests:")
    print(" python oracle_live_trade_tracker.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); s=o.status(); print(s.get('live_trade_tracker_status')); print(s.get('live_trades')[:3])\"")
    print("")
    print("[DONE] ORACLE-066 Live Trade Tracker installed")


if __name__ == "__main__":
    main()