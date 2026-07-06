
"""
ORACLE V2.0 Live Data Layer

Purpose:
- Create one unified market data layer.
- Populate Oracle market cache from the working arbitrage engine when live cache is empty.
- Normalize every market/opportunity into one structure.
- Does NOT place trades.
"""

from datetime import datetime, timezone
import json
from pathlib import Path

STATE_FILE = Path("oracle_v2_market_cache_state.json")


def _num(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _txt(v):
    return str(v or "").strip()


class OracleV2LiveDataLayer:
    def __init__(self):
        self.version = "ORACLE-V2.0"
        self.markets = {}
        self.last_refresh = None

    def refresh(self):
        rows = []

        try:
            import oracle_cross_market_arbitrage as arb

            if hasattr(arb, "scan"):
                data = arb.scan()
            elif hasattr(arb, "run"):
                data = arb.run()
            elif hasattr(arb, "diagnostics"):
                data = arb.diagnostics()
            else:
                data = {}

            alerts = []
            if isinstance(data, dict):
                alerts = data.get("alerts_list") or data.get("opportunities") or data.get("top") or []
            elif isinstance(data, list):
                alerts = data

            for i, a in enumerate(alerts):
                if isinstance(a, dict):
                    rows.append(self._normalize_alert(a, i))

        except Exception as exc:
            rows.append({
                "ticker": "V2-DATA-ERROR",
                "title": "V2 data layer error",
                "error": str(exc),
                "source": "oracle_v2_live_data_layer",
            })

        self.markets = {r["ticker"]: r for r in rows if isinstance(r, dict) and r.get("ticker")}
        self.last_refresh = datetime.now(timezone.utc).isoformat()
        self._save()

        return self.snapshot()

    def _normalize_alert(self, a, i):
        kind = _txt(a.get("kind") or a.get("type") or "opportunity")
        ticker = _txt(a.get("ticker") or f"ARBITRAGE-{kind.upper()}-{i}")

        edge_pct = _num(a.get("edge_pct") or a.get("edge") or a.get("edge_percent"), 0)
        edge = edge_pct / 100 if edge_pct > 1 else edge_pct
        confidence = _num(a.get("confidence"), 50)

        title = _txt(a.get("title") or a.get("market") or kind.replace("_", " ").title())

        # Unified minimal object. Real bid/ask/depth can be added later.
        return {
            "ticker": ticker,
            "title": title,
            "source": "oracle_cross_market_arbitrage",
            "kind": kind,
            "edge": edge,
            "edge_pct": edge_pct,
            "confidence": confidence,
            "recommendation": a.get("recommendation"),
            "yes_bid": a.get("yes_bid"),
            "yes_ask": a.get("yes_ask"),
            "no_bid": a.get("no_bid"),
            "no_ask": a.get("no_ask"),
            "yes_mid": a.get("yes_mid"),
            "spread": a.get("spread"),
            "bid_depth": a.get("bid_depth") or a.get("yes_bid_depth") or a.get("bid_size"),
            "ask_depth": a.get("ask_depth") or a.get("yes_ask_depth") or a.get("ask_size"),
            "volume": a.get("volume") or a.get("volume_24h") or 0,
            "open_interest": a.get("open_interest") or 0,
            "raw": a,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def snapshot(self):
        return {
            "module": "oracle_v2_live_data_layer",
            "version": self.version,
            "status": "ok",
            "markets": len(self.markets),
            "last_refresh": self.last_refresh,
            "items": list(self.markets.values()),
        }

    def get_markets(self):
        if not self.markets:
            self.refresh()
        return list(self.markets.values())

    def diagnostics(self):
        return {
            "module": "oracle_v2_live_data_layer",
            "version": self.version,
            "status": "ok",
            "markets": len(self.markets),
            "last_refresh": self.last_refresh,
        }

    def _save(self):
        try:
            STATE_FILE.write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")
        except Exception:
            pass


oracle_v2_live_data_layer = OracleV2LiveDataLayer()


if __name__ == "__main__":
    import pprint
    pprint.pp(oracle_v2_live_data_layer.refresh())
