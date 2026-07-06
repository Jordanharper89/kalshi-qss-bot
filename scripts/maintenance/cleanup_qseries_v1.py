
from pathlib import Path
import shutil

ROOT = Path(".")
ARCHIVE = ROOT / "archive"

OLD_SCANNERS = [
    "q1.py",
    "q1_crypto.py",
    "q2_debug.py",
    "q2_near_miss.py",
    "q2_scanner.py",
    "q2_series_scanner.py",
    "q2_universe.py",
    "q3_same_day_runners.py",
    "q4_debug.py",
    "q4_edge_engine.py",
    "q4_rejections.py",
    "q4_series_edge.py",
    "q5_volume_scalp.py",
    "q6_trend_filter.py",
    "qss_crypto.py",
    "qss_elite.py",
    "qss_full_crypto.py",
    "crypto_15m_scan.py",
    "crypto_finder.py",
    "current_crypto_events.py",
    "top_scanner.py",
    "category_scan.py",
    "trade_scan.py",
]

DEBUG_TOOLS = [
    "debug_q1_crypto.py",
    "debug_qss_crypto.py",
    "debug_scan.py",
    "direct_crypto_test.py",
    "direct_market_test.py",
    "events_test.py",
    "event_markets_test.py",
    "inspect_event.py",
    "inspect_market.py",
    "inspect_markets.py",
    "series_probe.py",
    "ticker_diagnoser.py",
    "test_bot.py",
]

OLD_BACKUPS = [
    "telegram_bot_backup.py",
    "trade_settings_backup.py",
]

def move_files(files, folder):
    target = ARCHIVE / folder
    target.mkdir(parents=True, exist_ok=True)

    moved = 0

    for name in files:
        src = ROOT / name
        dst = target / name

        if src.exists():
            if dst.exists():
                print(f"Already archived: {name}")
                continue

            shutil.move(str(src), str(dst))
            print(f"Moved: {name} -> {dst}")
            moved += 1

    return moved

def main():
    print("Q SERIES CLEANUP-001")
    print("Archiving old scanner/debug files. Nothing will be deleted.")
    print("")

    moved = 0
    moved += move_files(OLD_SCANNERS, "old_scanners")
    moved += move_files(DEBUG_TOOLS, "debug_tools")
    moved += move_files(OLD_BACKUPS, "old_backups")

    print("")
    print(f"Cleanup complete. Files moved: {moved}")

if __name__ == "__main__":
    main()