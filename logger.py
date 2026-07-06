import csv
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("kalshi_scan_log.csv")


def log_rows(section, rows):
    file_exists = LOG_FILE.exists()

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "section",
                "grade",
                "score",
                "signal",
                "symbol",
                "market",
                "event",
                "ticker",
                "minutes_left",
                "price",
                "yes_bid",
                "yes_ask",
                "spread",
                "volume_24h",
            ])

        now = datetime.now().isoformat(timespec="seconds")

        for row in rows:
            writer.writerow([
                now,
                section,
                row.get("elite_grade") or row.get("grade") or "",
                row.get("elite_score") or row.get("score") or "",
                row.get("signal") or row.get("system2_signal") or "",
                row.get("symbol") or "",
                row.get("title") or "",
                row.get("event") or "",
                row.get("ticker") or "",
                row.get("minutes_left") or "",
                row.get("price") or "",
                row.get("yes_bid") or "",
                row.get("yes_ask") or "",
                row.get("spread") or "",
                row.get("volume_24h") or "",
            ])


def log_message(section, message):
    file_exists = LOG_FILE.exists()

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "section",
                "message",
            ])

        now = datetime.now().isoformat(timespec="seconds")
        writer.writerow([now, section, message])