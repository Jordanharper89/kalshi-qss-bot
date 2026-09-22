from pathlib import Path
import argparse

from qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import (
    run_persistent_kalshi_loop,
)

def main():
    parser = argparse.ArgumentParser(
        description="Persistent Kalshi live stream"
    )
    parser.add_argument(
        "--max-market-messages",
        type=int,
        default=None,
        help="Diagnostic only. Production default is unbounded.",
    )
    parser.add_argument(
        "--connect-timeout-seconds",
        type=float,
        default=15.0,
    )
    args = parser.parse_args()

    print("=" * 72, flush=True)
    print(
        " OAD-032 PERSISTENT KALSHI LIVE STREAM — "
        "LIVENESS CORRECTION V3",
        flush=True,
    )
    print("=" * 72, flush=True)

    if args.max_market_messages is None:
        print(
            "[MODE] PRODUCTION 24/7 — UNBOUNDED — "
            "PING/PONG LIVENESS",
            flush=True,
        )
    else:
        print(
            f"[MODE] DIAGNOSTIC — "
            f"max_market_messages={args.max_market_messages}",
            flush=True,
        )

    try:
        result = run_persistent_kalshi_loop(
            Path.cwd(),
            max_market_messages=args.max_market_messages,
            connect_timeout_seconds=args.connect_timeout_seconds,
            progress=lambda x: print(x, flush=True),
        )
        print("[SUMMARY]", result, flush=True)
        return 0

    except KeyboardInterrupt:
        print(
            "\n[STOP] Kalshi persistent stream stopped by operator.",
            flush=True,
        )
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
