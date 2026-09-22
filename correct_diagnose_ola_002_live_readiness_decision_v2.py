from __future__ import annotations

import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parent

TARGET = (
    ROOT
    / "diagnose_ola_002_live_readiness_decision.py"
)


def replace_exactly_once(
    text: str,
    old: str,
    new: str,
    description: str,
) -> str:
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"{description}: expected exactly one match, "
            f"found {count}"
        )

    return text.replace(
        old,
        new,
        1,
    )


def main() -> int:
    print("========================================")
    print(" OLA-002 DIAGNOSTIC CORRECTION V2")
    print(" DIRECT PROVIDER CALL CONTRACT")
    print(" SINGLE-ATTEMPT RETRY INTERRUPT")
    print("========================================")

    if not TARGET.exists():
        raise RuntimeError(
            f"Diagnostic file not found: {TARGET}"
        )

    source = TARGET.read_text(
        encoding="utf-8"
    )

    old_call = '''            readiness = graph[
                "readiness_provider"
            ].readiness_callable(
                **dict(
                    readiness_kwargs
                )
            )
'''

    new_call = '''            readiness_provider = graph[
                "readiness_provider"
            ]

            class _StopAfterFirstReadinessAttempt(
                RuntimeError
            ):
                pass

            def stop_after_first_attempt(
                delay_seconds,
            ):
                raise _StopAfterFirstReadinessAttempt(
                    "First production readiness attempt "
                    "captured; retry loop intentionally "
                    "stopped by diagnostic"
                )

            original_provider_sleeper = (
                readiness_provider._sleeper
            )

            readiness_provider._sleeper = (
                stop_after_first_attempt
            )

            try:
                readiness = readiness_provider(
                    **dict(
                        readiness_kwargs
                    )
                )
            finally:
                readiness_provider._sleeper = (
                    original_provider_sleeper
                )
'''

    source = replace_exactly_once(
        source,
        old_call,
        new_call,
        (
            "Production readiness-provider "
            "call correction"
        ),
    )

    TARGET.write_text(
        source,
        encoding="utf-8",
    )

    py_compile.compile(
        str(TARGET),
        doraise=True,
    )

    print(
        f"[OK] CORRECTED: {TARGET}"
    )
    print(
        "[OK] Direct callable provider contract installed"
    )
    print(
        "[OK] First-attempt retry interrupt installed"
    )
    print(
        "[OK] Production modules remain unchanged"
    )
    print(
        "[OK] Diagnostic syntax verified"
    )
    print()
    print(
        "[DONE] OLA-002 readiness diagnostic "
        "correction installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )