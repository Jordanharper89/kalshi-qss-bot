from oracle_risk_engine import apply_risk
from oracle_trade_decision_engine import apply_trade_decisions
from oracle_confidence_engine import apply_confidence
from oracle_fair_value_engine import apply_fair_values
from oracle_signal_engine import build_signals
from oracle_opportunity_ranking import rank_markets
from oracle_market_normalizer import normalize_market
from oracle_market_cache import oracle_market_cache
from oracle_provider_registry import oracle_provider_registry

"""
ORACLE-027 — Live Research Engine

Purpose:
- Run a lightweight Oracle research loop in the background.
- Maintain a shared market/opportunity snapshot cache.
- Let Oracle UI screens read cached data instead of rebuilding everything.
"""

import time
import threading


class OracleResearchEngine:
    def __init__(self, refresh_seconds=10):
        self.refresh_seconds = refresh_seconds
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        self.snapshot = {
            "status": "starting",
            "updated_at": None,
            "markets_checked": 0,
            "opportunities": [],
            "errors": [],
        }

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[ORACLE-027] Live research engine started")

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            try:
                self.refresh()
            except Exception as e:
                self._record_error(str(e))

            time.sleep(self.refresh_seconds)

    def refresh(self):
        """
        ORACLE-030:
        Pull data from registered providers and store returned markets
        in the shared Oracle market cache.
        """
        provider_results = oracle_provider_registry.fetch_all()
        markets_checked = 0
        provider_errors = []

        for result in provider_results:
            provider_name = result.get("provider", "unknown")
            markets = result.get("markets", []) or []
            errors = result.get("errors", []) or []

            for error in errors:
                provider_errors.append({
                    "provider": provider_name,
                    "error": str(error),
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                })

            for market in markets:
                ticker = market.get("ticker") or market.get("market_ticker")
                if not ticker:
                    continue

                normalized = normalize_market(market, provider_name)
                normalized["cached_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

                normalized_ticker = normalized.get("ticker")
                if not normalized_ticker:
                    continue

                oracle_market_cache.update_market(normalized_ticker, normalized)
                markets_checked += 1

        ranked = rank_markets(
            oracle_market_cache.get_all()
        )

        cache_count = oracle_market_cache.market_count()

        with self.lock:
            self.snapshot["status"] = "running"
            self.snapshot["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.snapshot["markets_checked"] = cache_count
            self.snapshot["provider_results"] = provider_results
            self.snapshot["errors"] = (self.snapshot.get("errors", []) + provider_errors)[-10:]
            ranked = apply_fair_values(ranked)
            ranked = apply_confidence(ranked)
            ranked = build_signals(ranked)
            ranked = apply_trade_decisions(ranked)
            ranked = apply_risk(ranked)

            self.snapshot["opportunities"] = ranked[:25]

    def _record_error(self, error):
        with self.lock:
            self.snapshot["status"] = "error"
            self.snapshot.setdefault("errors", []).append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": error,
            })
            self.snapshot["errors"] = self.snapshot["errors"][-10:]

    def get_snapshot(self):
        with self.lock:
            return dict(self.snapshot)

    def diagnostics_text(self):
        snap = self.get_snapshot()
        return (
            "ORACLE RESEARCH ENGINE\n\n"
            f"Status: {snap.get('status')}\n"
            f"Updated: {snap.get('updated_at')}\n"
            f"Markets checked: {snap.get('markets_checked')}\n"
            f"Opportunities: {len(snap.get('opportunities', []))}\n"
            f"Errors: {len(snap.get('errors', []))}"
        )


oracle_research_engine = OracleResearchEngine(refresh_seconds=10)


# =====================================================
# ORACLE-033.1 DEBUG
# =====================================================

def oracle_debug_snapshot():

    try:
        snap = oracle_research_engine.get_snapshot()

        print("\n==============================")
        print("ORACLE SNAPSHOT")
        print("==============================")
        print("Status:", snap.get("status"))
        print("Markets:", snap.get("markets_checked"))
        print("Provider Results:", len(snap.get("provider_results", [])))
        print("Ranked Opportunities:", len(snap.get("opportunities", [])))

        for i, opp in enumerate(snap.get("opportunities", [])[:10], start=1):
            print(
                f"{i}. "
                f"{opp.get('ticker')} | "
                f"{opp.get('oracle_score')} | "
                f"{opp.get('grade')}"
            )

        print("==============================\n")

    except Exception as e:
        print("[ORACLE DEBUG]", e)

