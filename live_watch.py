import time
import os

from logger import log_message
from q1_crypto import run_q1_crypto
from q2_series_scanner import run_q2_series
from q3_same_day_runners import run_q3_same_day_runners


Q1_REFRESH_SECONDS = 15
Q2_REFRESH_SECONDS = 90
Q3_REFRESH_SECONDS = 180


def clear_screen():
    os.system("cls")


def run_live_watch():
    last_q2_run = 0
    last_q3_run = 0

    while True:
        now = time.time()
        log_message("HEARTBEAT", "Q1/Q2/Q3 live board refresh")

        clear_screen()

        print("=" * 70)
        print("KALSHI Q-SERIES LIVE BOARD")
        print("Q1 refresh: 15 seconds")
        print("Q2 refresh: 90 seconds")
        print("Q3 refresh: 180 seconds")
        print("=" * 70)

        print("\n[ Q1 - ALL QUALIFIED CRYPTO PLAYS ]")
        print("-" * 70)
        run_q1_crypto()

        print("\n" + "=" * 70)

        print("\n[ Q2 - ALL QUALIFIED FAST TRADES ]")
        print("-" * 70)
        if now - last_q2_run >= Q2_REFRESH_SECONDS:
            last_q2_run = now
            run_q2_series()
        else:
            remaining = int(Q2_REFRESH_SECONDS - (now - last_q2_run))
            print(f"Q2 waiting {remaining} seconds to avoid Kalshi rate limits.")

        print("\n" + "=" * 70)

        print("\n[ Q3 - SAME DAY RUNNERS ]")
        print("-" * 70)
        if now - last_q3_run >= Q3_REFRESH_SECONDS:
            last_q3_run = now
            run_q3_same_day_runners()
        else:
            remaining = int(Q3_REFRESH_SECONDS - (now - last_q3_run))
            print(f"Q3 waiting {remaining} seconds to avoid Kalshi rate limits.")

        print("\n" + "=" * 70)
        print(f"Next Q1 refresh in {Q1_REFRESH_SECONDS} seconds.")
        print("Press CTRL+C to stop.")

        time.sleep(Q1_REFRESH_SECONDS)


if __name__ == "__main__":
    run_live_watch()