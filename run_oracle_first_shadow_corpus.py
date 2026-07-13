from __future__ import annotations

import argparse
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
    DEFAULT_FIRST_RUN_ITERATIONS,
    DEFAULT_RUNTIME_ROOT,
    run_first_real_shadow_corpus_from_env,
    validate_first_real_launch_environment,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Oracle first bounded real live-shadow "
            "corpus collection"
        )
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Validate launch configuration without "
            "contacting Kalshi or PostgreSQL"
        ),
    )

    parser.add_argument(
        "--launch",
        action="store_true",
        help=(
            "Explicitly launch the bounded first "
            "real shadow corpus run"
        ),
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_FIRST_RUN_ITERATIONS,
    )

    parser.add_argument(
        "--runtime-root",
        default=str(
            DEFAULT_RUNTIME_ROOT
        ),
    )

    parser.add_argument(
        "--env-file",
        default=".env",
    )

    args = parser.parse_args()

    if args.check and args.launch:
        parser.error(
            "use either --check or --launch, not both"
        )

    if not args.check and not args.launch:
        parser.error(
            "explicitly choose --check or --launch"
        )

    runtime_root = Path(
        args.runtime_root
    ).resolve(
        strict=False
    )

    if args.check:
        result = (
            validate_first_real_launch_environment(
                env_file=args.env_file
            )
        )

        print(
            "[READY] Oracle first real shadow "
            "corpus launch configuration"
        )

        print(result)

        print(
            "Runtime root:",
            runtime_root,
        )

        print(
            "Stop command:"
        )

        print(
            'type nul > "'
            + str(
                runtime_root
                / "state"
                / "STOP_ORACLE_SHADOW"
            )
            + '"'
        )

        return

    result = (
        run_first_real_shadow_corpus_from_env(
            runtime_root=runtime_root,
            env_file=args.env_file,
            max_iterations=args.iterations,
        )
    )

    if result.corpus_acquisition_succeeded is True:
        print(
            "[COMPLETE] Oracle first real shadow "
            "corpus run"
        )
    else:
        print(
            "[FAILED] Oracle first real shadow "
            "corpus acquisition"
        )

    print(
        result.to_dict()
    )


if __name__ == "__main__":
    main()
