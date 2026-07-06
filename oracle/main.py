"""
Oracle Main Entry Point

ORACLE-010:
Run Oracle Phase 1 pipeline with time-series engine.

Oracle is research-only.
It does not place trades.
"""

from oracle.collectors.kalshi.market_collector import collect_kalshi_markets
from oracle.collectors.kalshi.orderbook_collector import collect_orderbook_snapshots
from oracle.engines.market_normalizer import normalize_markets, preview_normalized_markets
from oracle.engines.features import build_features
from oracle.engines.signal_engine import build_signals, preview_signals
from oracle.engines.time_series.market_timeseries import build_market_timeseries, preview_market_timeseries
from oracle.monitoring.run_manager import OracleRunManager
from oracle.monitoring.data_quality import build_data_quality_report
from oracle.warehouse.market_history import capture_market_history


def main():
    print("Starting Oracle Phase 1 pipeline...")

    run = OracleRunManager()
    run.start_run()

    try:
        with run.step("kalshi_market_collection") as step:
            step["records_processed"] = collect_kalshi_markets()

        with run.step("market_normalization") as step:
            step["records_processed"] = normalize_markets(limit=500)

        with run.step("market_history_capture") as step:
            step["records_processed"] = capture_market_history(limit=1000)

        with run.step("market_timeseries_engine") as step:
            step["records_processed"] = build_market_timeseries(limit=500)

        preview_normalized_markets(limit=10)
        preview_market_timeseries(limit=10)

        with run.step("orderbook_snapshots") as step:
            step["records_processed"] = collect_orderbook_snapshots(limit=25)

        with run.step("feature_engine") as step:
            step["records_processed"] = build_features(limit=25)

        with run.step("signal_engine") as step:
            step["records_processed"] = build_signals(limit=25)

        preview_signals(limit=10)

        with run.step("data_quality_report") as step:
            build_data_quality_report(run.run_id)
            step["records_processed"] = 1

        run.finish_run(status="success")

    except Exception as e:
        run.finish_run(status="failed", notes=str(e))
        raise


if __name__ == "__main__":
    main()