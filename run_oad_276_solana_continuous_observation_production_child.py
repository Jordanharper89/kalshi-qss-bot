from __future__ import annotations
import argparse,time
from pathlib import Path

from qseries_v2.oracle_adapters.independent.oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy
from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_resilient_solana_continuous_worker

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

def build_parser():
    p=argparse.ArgumentParser(description="Oracle continuous Solana observation production child")
    p.add_argument("--check",action="store_true")
    p.add_argument("--tick-seconds",type=float,default=1.0)
    p.add_argument("--acquisition-seconds",type=float,default=5.0)
    p.add_argument("--history-limit",type=int,default=512)
    p.add_argument("--max-cycles",type=int,default=None)
    p.add_argument("--acquisition-timeout-seconds",type=float,default=20.0)
    p.add_argument("--persistence-timeout-seconds",type=float,default=120.0)
    return p

def main(argv=None):
    a=build_parser().parse_args(argv)
    policy=build_solana_continuous_observation_policy(
        tick_seconds=a.tick_seconds,
        acquisition_seconds=a.acquisition_seconds,
        history_limit=a.history_limit,
        acquisition_timeout_seconds=a.acquisition_timeout_seconds,
        persistence_timeout_seconds=a.persistence_timeout_seconds,
    )
    if a.max_cycles is not None and a.max_cycles<1:
        raise SystemExit("--max-cycles must be >= 1")
    if a.check:
        print(
            "[READY] solana_continuous child "
            f"tick_seconds={policy.tick_seconds} "
            f"acquisition_seconds={policy.acquisition_seconds} "
            f"windows={policy.windows_seconds} "
            "pinned_session=TRUE holder_concentration=DEFERRED "
            "probability_enabled=FALSE direction_enabled=FALSE "
            "publication_allowed=FALSE execution_authority=FALSE",
            flush=True,
        )
        return 0

    print(
        "[START] Oracle continuous Solana observation child "
        f"tick_seconds={policy.tick_seconds} "
        f"acquisition_seconds={policy.acquisition_seconds} "
        "pinned_session=TRUE execution_authority=FALSE",
        flush=True,
    )
    s=run_resilient_solana_continuous_worker(
        root=Path.cwd(),policy=policy,max_cycles=a.max_cycles,
        progress=lambda x:print(x,flush=True),sleep_fn=time.sleep
    )
    if a.max_cycles is not None:
        print("[SUMMARY]",s,flush=True)
        return 0 if s.successful_cycles>0 else 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
