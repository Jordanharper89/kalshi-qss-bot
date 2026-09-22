from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_ola_068_oracle_postgresql_canonical_advancement_correction_v3.py"
)


OLD_BLOCK = """        snapshot_hash="c" * 64,
    )
"""


NEW_BLOCK = """        snapshot_hash="c" * 64,
        read_only=True,
        execution_allowed=False,
        alerts_allowed=False,
        qseries_handoff_allowed=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
    )
"""


def main() -> int:
    print(
        "========================================"
    )
    print(
        " OLA-068 TEST CORRECTION V2"
    )
    print(
        " COMPLETE SNAPSHOT SAFETY CONTRACT"
    )
    print(
        " PRODUCTION FILES UNCHANGED"
    )
    print(
        "========================================"
    )

    if not TEST_PATH.is_file():
        raise RuntimeError(
            f"Test file not found: {TEST_PATH}"
        )

    source = TEST_PATH.read_text(
        encoding="utf-8"
    )

    old_count = source.count(
        OLD_BLOCK
    )

    new_count = source.count(
        NEW_BLOCK
    )

    if old_count == 1:
        source = source.replace(
            OLD_BLOCK,
            NEW_BLOCK,
            1,
        )
    elif (
        old_count == 0
        and new_count == 1
    ):
        print(
            "[INFO] Complete safety fixture "
            "already installed"
        )
    else:
        raise RuntimeError(
            "Snapshot fixture did not match expected state. "
            f"old_count={old_count}, "
            f"new_count={new_count}"
        )

    TEST_PATH.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] FULL REPLACEMENT: {TEST_PATH}"
    )
    print(
        "[OK] read_only explicitly supplied"
    )
    print(
        "[OK] execution_allowed explicitly supplied"
    )
    print(
        "[OK] alerts_allowed explicitly supplied"
    )
    print(
        "[OK] qseries_handoff_allowed explicitly supplied"
    )
    print(
        "[OK] trade_authorization_allowed explicitly supplied"
    )
    print(
        "[OK] order_placement_allowed explicitly supplied"
    )
    print(
        "[OK] funds_moved explicitly supplied"
    )
    print(
        "[OK] portfolio_mutated explicitly supplied"
    )
    print(
        "[OK] Production files unchanged"
    )
    print(
        "[DONE] OLA-068 test correction V2 installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )