"""
Oracle Logger

ORACLE-021.9

Purpose:
- Central logging for Oracle.
- Console + file logging.
- Timestamp every event.
"""

import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "oracle.log"


def get_oracle_logger(name: str = "oracle") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


oracle_logger = get_oracle_logger()


def log_cycle_started():
    oracle_logger.info("Research cycle started.")


def log_cycle_finished(summary):
    oracle_logger.info(
        "Research cycle complete | "
        f"Scanned={summary.get('raw_markets_scanned',0)} "
        f"Discovered={summary.get('markets_discovered',0)} "
        f"Added={summary.get('markets_added_to_watchlist',0)} "
        f"Researched={summary.get('markets_researched',0)} "
        f"Signals={summary.get('signal_change_events',0)}"
    )


def log_error(error: Exception):
    oracle_logger.exception(error)


def log_discovery(ticker: str):
    oracle_logger.info(f"Discovered market: {ticker}")


def log_signal_change(ticker: str):
    oracle_logger.info(f"Signal changed: {ticker}")