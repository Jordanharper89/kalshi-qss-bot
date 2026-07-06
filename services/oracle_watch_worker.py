import threading
import time

from services.base_service import BaseService
from services.oracle_watchlist import oracle_watchlist
from services.notification_service import notification_service

from oracle.api.ticker_ingest import ensure_ticker_in_oracle
from oracle_telegram import get_signal_by_ticker
from oracle.engines.trade_decision import decide_trade


class OracleWatchWorker(BaseService):

    def __init__(self):
        super().__init__("oracle_watch_worker")

        self.interval = 60
        self.thread = None
        self.running = False

        self.scan_count = 0
        self.alert_count = 0

        self.last_state = {}

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._loop,
            daemon=True,
        )

        self.thread.start()
        self.mark_started()

    def stop(self):
        self.running = False
        self.mark_stopped()

    def _loop(self):

        while self.running:

            try:
                self.scan_once()
            except Exception as e:
                self.last_error = str(e)

            time.sleep(self.interval)

    def scan_once(self):

        watchlist = oracle_watchlist.all()

        for ticker in watchlist.keys():

            cleaned = ensure_ticker_in_oracle(ticker)

            signal = get_signal_by_ticker(cleaned)

            if not signal:
                continue

            decision = decide_trade(
                signal.get("yes_price"),
                signal.get("no_price"),
                signal.get("oracle_fair_value"),
                signal.get("confidence_score"),
            )

            action = decision["action"]
            edge = decision["selected_edge"]

            previous = self.last_state.get(cleaned)

            changed = (
                previous is None
                or previous["action"] != action
                or abs(previous["edge"] - edge) >= 2
            )

            if changed:

                self.last_state[cleaned] = {
                    "action": action,
                    "edge": edge,
                }

                notification_service.notify(
                    title="Oracle Edge Update",
                    ticker=cleaned,
                    dedupe_key=f"{cleaned}-{action}",
                    message=f"""
Ticker:
{cleaned}

Action:
{action}

Edge:
{edge:.2f}c

Confidence:
{signal.get('confidence_score')}%

Reason:
{decision['reason']}
""".strip(),
                )

                self.alert_count += 1

        self.scan_count += 1

    def diagnostics(self):

        d = super().diagnostics()

        d.update(
            {
                "scan_count": self.scan_count,
                "alert_count": self.alert_count,
                "watching": len(oracle_watchlist.all()),
                "interval": self.interval,
            }
        )

        return d


oracle_watch_worker = OracleWatchWorker()