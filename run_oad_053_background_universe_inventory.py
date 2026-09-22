from pathlib import Path
import argparse,time
from qseries_v2.oracle_adapters.kalshi.oad_053_background_universe_inventory import run_inventory_slice

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pages-per-slice",type=int,default=5)
    p.add_argument("--sleep-seconds",type=float,default=5.0)
    p.add_argument("--timeout-seconds",type=float,default=8.0)
    p.add_argument("--max-retries",type=int,default=4)
    p.add_argument("--retry-backoff-seconds",type=float,default=1.0)
    p.add_argument("--once",action="store_true")
    a=p.parse_args()

    if a.pages_per_slice<1:
        raise SystemExit("--pages-per-slice must be >= 1")
    if a.sleep_seconds<0 or a.timeout_seconds<=0 or a.max_retries<0 or a.retry_backoff_seconds<0:
        raise SystemExit("invalid runtime arguments")

    root=Path.cwd()
    print("="*72,flush=True)
    print(" OAD-053 BACKGROUND KALSHI UNIVERSE INVENTORY - RESILIENT 24/7 V2",flush=True)
    print("="*72,flush=True)

    outer_failures=0

    try:
        while True:
            try:
                result=run_inventory_slice(
                    root,
                    pages_per_slice=a.pages_per_slice,
                    timeout_seconds=a.timeout_seconds,
                    progress=lambda x:print(x,flush=True),
                    max_retries=a.max_retries,
                    base_backoff_seconds=a.retry_backoff_seconds,
                )
                outer_failures=0
                print("[CHECKPOINT]",result.checkpoint,flush=True)
                print(
                    f"[INVENTORY] slice_complete terminal={result.terminal_cursor_reached} "
                    f"transient_failures={result.transient_failures} "
                    f"retries_used={result.retries_used}",
                    flush=True,
                )

                if a.once:
                    return 0

                time.sleep(a.sleep_seconds)

            except KeyboardInterrupt:
                raise

            except Exception as exc:
                outer_failures+=1
                delay=min(
                    60.0,
                    max(1.0,a.retry_backoff_seconds)*(2.0**min(outer_failures-1,5)),
                )
                print(
                    f"[INVENTORY] recoverable_cycle_failure={type(exc).__name__} "
                    f"consecutive_failures={outer_failures} "
                    f"resume_from_checkpoint_in={delay:.1f}s",
                    flush=True,
                )
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n[STOP] Background universe inventory stopped by operator.",flush=True)
        return 0

if __name__=="__main__":
    raise SystemExit(main())
