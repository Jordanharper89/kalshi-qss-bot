from pathlib import Path
from datetime import datetime, timezone
import shutil
import json
import glob

ROOT = Path.cwd()
BOT = ROOT / "telegram_bot.py"
V2 = ROOT / "oracle_v2_live_data_layer.py"
CACHE = ROOT / "oracle_market_cache.py"

V2_CODE = r'''
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
'''

CACHE_PATCH = r'''

# ============================================================
# ORACLE V2.0 Live Data Layer Cache Bridge
# ============================================================

try:
    from oracle_v2_live_data_layer import oracle_v2_live_data_layer
except Exception:
    oracle_v2_live_data_layer = None


def _oracle_v2_cache_snapshot():
    if oracle_v2_live_data_layer is None:
        return {"markets": 0, "last_refresh": None, "status": "missing_v2_layer"}

    snap = oracle_v2_live_data_layer.refresh()
    return {
        "markets": snap.get("markets", 0),
        "last_refresh": snap.get("last_refresh"),
        "status": "ok",
        "source": "oracle_v2_live_data_layer",
    }


def diagnostics():
    try:
        return _oracle_v2_cache_snapshot()
    except Exception as exc:
        return {"markets": 0, "last_refresh": None, "status": "error", "error": str(exc)}


def get_markets():
    try:
        if oracle_v2_live_data_layer is None:
            return []
        return oracle_v2_live_data_layer.get_markets()
    except Exception:
        return []


# If old singleton exists, attach V2 methods to it too.
try:
    if "oracle_market_cache" in globals():
        oracle_market_cache.diagnostics = diagnostics
        oracle_market_cache.get_markets = get_markets
except Exception:
    pass

# ============================================================
# END ORACLE V2.0
# ============================================================
'''


def backup(path, tag):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_{tag}_{stamp}")
    shutil.copy2(path, b)
    return b


def repair_telegram_bot():
    if not BOT.exists():
        print("[WARN] telegram_bot.py not found")
        return

    text = BOT.read_text(encoding="utf-8", errors="ignore")

    # If current bot has syntax error from KQ-020 insertion, restore latest backup.
    bad = "KQ-020 Telegram Text Guard" in text and "SyntaxError" not in text

    backups = sorted(glob.glob(str(BOT) + ".bak_kq020_*"), reverse=True)
    if backups:
        # Restore the pre-KQ020 backup because current file is broken at line 78.
        b = backup(BOT, "before_v2_restore")
        shutil.copy2(backups[0], BOT)
        print(f"[OK] Restored telegram_bot.py from {backups[0]}")
        print(f"[OK] Broken copy backed up: {b}")
    else:
        print("[INFO] No KQ-020 backup found; telegram_bot.py restore skipped")


def patch_cache():
    if not CACHE.exists():
        print("[WARN] oracle_market_cache.py not found")
        return

    text = CACHE.read_text(encoding="utf-8", errors="ignore")
    if "ORACLE V2.0 Live Data Layer Cache Bridge" in text:
        print("[SKIP] oracle_market_cache.py already patched")
        return

    b = backup(CACHE, "oracle_v2_0")
    text += "\n\n" + CACHE_PATCH + "\n"
    CACHE.write_text(text, encoding="utf-8")

    print("[OK] Patched oracle_market_cache.py")
    print(f"[OK] Backup created: {b}")


def main():
    print("===================================")
    print(" ORACLE V2.0 INSTALLER")
    print(" Live Data Layer Rewrite")
    print("===================================")

    V2.write_text(V2_CODE, encoding="utf-8")
    print("[OK] Created oracle_v2_live_data_layer.py")

    repair_telegram_bot()
    patch_cache()

    print("")
    print("Tests:")
    print(" python oracle_v2_live_data_layer.py")
    print(" python -c \"from oracle_market_cache import oracle_market_cache; print(oracle_market_cache.diagnostics())\"")
    print(" python telegram_bot.py")
    print("")
    print("[DONE] ORACLE V2.0 Live Data Layer installed")


if __name__ == "__main__":
    main()