from pathlib import Path
import py_compile
import re

ROOT=Path.cwd()

ENGINE=ROOT/(
    "qseries_v2/oracle_execution/"
    "oracle_003_unified_physical_execution_engine.py"
)

TEST=ROOT/(
    "test_oracle_007_continuous_discovery_execution_hunt.py"
)

if not ENGINE.is_file():
    raise SystemExit(
        "[FAIL] Oracle unified physical engine missing"
    )

src=ENGINE.read_text(
    encoding="utf-8"
)

# ============================================================
# ORACLE-007
#
# Permanent runtime model:
#
# MRIYA
#   -> continuously replenishes
#
# CURRENT HOT EXACT BINDINGS
#   -> continuously admitted
#
# ACTIVE HOT CANDIDATES
#   -> continuously repriced
#
# PHYSICAL POSITIVE PACKET
#   -> signed simulation
#
# PAPER
#   -> report only
#
# LIVE
#   -> one 0.001 SOL canary
#
# Historical memory NEVER resurrects stale execution rows.
# ============================================================

pat=re.compile(
    r'def live_universe_rows\(root\):'
    r'[\s\S]*?'
    r'(?=\n\ndef run\()'
)

replacement=r'''
_DISCOVERY_CHILD=None


def _stop_oracle_discovery():
    global _DISCOVERY_CHILD

    child=_DISCOVERY_CHILD

    _DISCOVERY_CHILD=None

    if child is None:
        return

    try:
        if child.poll() is None:
            child.terminate()

            child.wait(
                timeout=5
            )

    except Exception:
        try:
            child.kill()
        except Exception:
            pass


def _ensure_oracle_discovery(
    root,
    seconds=150.0
):
    import subprocess
    import sys

    global _DISCOVERY_CHILD

    if (
        _DISCOVERY_CHILD is not None
        and _DISCOVERY_CHILD.poll() is None
    ):
        return _DISCOVERY_CHILD

    _DISCOVERY_CHILD=subprocess.Popen(
        [
            sys.executable,
            "run_qarb_043b_paced_mriya_token_discovery.py",
            "--seconds",
            str(
                max(
                    30.0,
                    float(seconds)
                )
            )
        ],
        cwd=str(
            Path(root)
        ),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return _DISCOVERY_CHILD


def _recent_mriya_count(
    hot_seconds
):
    registry=(
        q80.q45.d.load()
    )

    tokens=(
        registry.get(
            "tokens"
        )
        or {}
    )

    now=time.time()

    recent=[]

    for token,info in tokens.items():

        age=max(
            0.0,
            now-float(
                info.get(
                    "last_seen_epoch",
                    0.0
                )
                or 0.0
            )
        )

        if age<=hot_seconds:
            recent.append(
                (
                    token,
                    age
                )
            )

    recent.sort(
        key=lambda x:x[1]
    )

    return recent


def refresh_live_universe_rows(
    root
):
    root=Path(root)

    hot_seconds=min(
        90.0,
        float(
            q80.q45.HOT
        )
    )

    recent=_recent_mriya_count(
        hot_seconds
    )

    if not recent:
        return []

    payload,active=(
        q80.q45.classify()
    )

    now=time.time()

    rows=[]

    for row in active:

        life=(
            row.get(
                "lifecycle"
            )
            or {}
        )

        age=float(
            life.get(
                "seconds_since_last_seen",
                1e18
            )
        )

        # LIVE-MONEY INTAKE:
        # HOT only.
        if age>hot_seconds:
            continue

        token=row.get(
            "token"
        )

        pump=row.get(
            "pump_pool"
        )

        meta=(
            row.get(
                "meteora_meta"
            )
            or {}
        )

        meteora=meta.get(
            "address"
        )

        if not (
            token
            and pump
            and meteora
            and meta.get(
                "token_x"
            )
            and meta.get(
                "token_y"
            )
        ):
            continue

        x=dict(
            row
        )

        x[
            "size_sol"
        ]=MICRO_SOL

        x[
            "micro_lamports"
        ]=MICRO_LAMPORTS

        x[
            "_oracle_hot_valid_until"
        ]=(
            now
            +max(
                0.0,
                hot_seconds-age
            )
        )

        rows.append(
            x
        )

    rows.sort(
        key=lambda x:
            float(
                (
                    x.get(
                        "lifecycle"
                    )
                    or {}
                ).get(
                    "seconds_since_last_seen",
                    1e18
                )
            )
    )

    return rows


def live_universe_rows(root):

    root=Path(root)

    watch_seconds=float(
        os.getenv(
            "ORACLE_INITIAL_DISCOVERY_SECONDS",
            "120"
        )
    )

    poll_seconds=float(
        os.getenv(
            "ORACLE_DISCOVERY_POLL_SECONDS",
            "2"
        )
    )

    hot_seconds=min(
        90.0,
        float(
            q80.q45.HOT
        )
    )

    _ensure_oracle_discovery(
        root,
        max(
            150.0,
            watch_seconds+30.0
        )
    )

    print(
        "[CONTINUOUS_DISCOVERY] "
        "source=MRIYA "
        "initial_window=%.1fs "
        "hot_max_age=%.1fs "
        "replenishment=CONTINUOUS"%(
            watch_seconds,
            hot_seconds
        ),
        flush=True
    )

    deadline=(
        time.monotonic()
        +watch_seconds
    )

    last_status=0.0

    while (
        time.monotonic()
        <deadline
    ):

        recent=_recent_mriya_count(
            hot_seconds
        )

        if recent:

            rows=refresh_live_universe_rows(
                root
            )

            if rows:

                print(
                    "[INITIAL_FRESH_UNIVERSE] "
                    "recent_mriya=%d "
                    "hot_exact_bound=%d "
                    "youngest_age=%.3fs"%(
                        len(recent),
                        len(rows),
                        recent[0][1]
                    ),
                    flush=True
                )

                for row in rows:

                    life=(
                        row.get(
                            "lifecycle"
                        )
                        or {}
                    )

                    print(
                        "[FRESH_ROW] "
                        "token=%s "
                        "age=%.3fs "
                        "pump=%s "
                        "meteora=%s"%(
                            row[
                                "token"
                            ][:10],

                            float(
                                life.get(
                                    "seconds_since_last_seen",
                                    0.0
                                )
                            ),

                            row[
                                "pump_pool"
                            ][:12],

                            row[
                                "meteora_meta"
                            ][
                                "address"
                            ][:12],
                        ),
                        flush=True
                    )

                return rows

        elapsed=(
            watch_seconds
            -max(
                0.0,
                deadline
                -time.monotonic()
            )
        )

        if (
            elapsed-last_status
            >=10.0
        ):

            print(
                "[FRESH_WAIT] "
                "elapsed=%.1fs "
                "recent_mriya_tokens=%d"%(
                    elapsed,
                    len(recent)
                ),
                flush=True
            )

            last_status=elapsed

        time.sleep(
            min(
                poll_seconds,
                max(
                    0.0,
                    deadline
                    -time.monotonic()
                )
            )
        )

    print(
        "[DISCOVERY_HOLD] "
        "no fresh exact-bound "
        "PumpSwap->Meteora candidate",
        flush=True
    )

    return []
'''

if not pat.search(src):
    raise SystemExit(
        "[FAIL] ORACLE-006 universe seam missing"
    )

src=pat.sub(
    replacement.rstrip(),
    src,
    count=1
)

# ============================================================
# Add atexit cleanup.
# Discovery lives for the whole Oracle execution process,
# but never survives the launcher exiting.
# ============================================================

if "import atexit" not in src:

    src=src.replace(
        "import base64",
        "import atexit\nimport base64",
        1
    )


registration='''
atexit.register(
    _stop_oracle_discovery
)
'''

needle="\ndef run(\n"

pos=src.find(
    needle
)

if pos<0:
    raise SystemExit(
        "[FAIL] run seam missing"
    )

if "atexit.register(" not in src:

    src=(
        src[:pos]
        +"\n"
        +registration.strip()
        +"\n\n"
        +src[pos+1:]
    )

# ============================================================
# Rolling admission inside hunt loop.
# Existing candidates continue repricing.
# New HOT candidates join while hunt remains alive.
# ============================================================

old='''    sends=0
    confirmed=0
    rejects=0
    hunt_round=0

    while (
        time.monotonic()
        <deadline
    ):
        hunt_round+=1

        now_epoch=time.time()

        rows=[
            row
            for row in rows
            if float(
                row.get(
                    "_oracle_hot_valid_until",
                    now_epoch
                )
            ) > now_epoch
        ]

        if not rows:
            print(
                "[ORACLE-006 HOLD] "
                "fresh candidate set expired "
                "without executable profit",
                flush=True
            )

            save({
                "revision":
                    "ORACLE_006",

                "status":
                    "HOT_SET_EXPIRED_NO_EXECUTABLE_PROFIT",

                "execution_owner":
                    "ORACLE",

                "sends":
                    sends,

                "confirmed":
                    confirmed,

                "rejects":
                    rejects,

                "hunt_rounds":
                    hunt_round-1,
            })

            return 2

        print(
            "[HUNT_ROUND] "
            "round=%d active=%d"%(
                hunt_round,
                len(rows)
            ),
            flush=True
        )'''

new='''    sends=0
    confirmed=0
    rejects=0
    hunt_round=0

    admission_refresh_seconds=float(
        os.getenv(
            "ORACLE_ADMISSION_REFRESH_SECONDS",
            "10"
        )
    )

    next_admission_refresh=0.0

    row_map={
        row["token"]:
            row
        for row in rows
    }

    while (
        time.monotonic()
        <deadline
    ):
        hunt_round+=1

        now_mono=time.monotonic()
        now_epoch=time.time()

        # ----------------------------------------------------
        # CONTINUOUS REPLENISHMENT
        # ----------------------------------------------------

        if (
            now_mono
            >=next_admission_refresh
        ):

            incoming=(
                refresh_live_universe_rows(
                    root
                )
            )

            admitted=0
            refreshed=0

            for row in incoming:

                token=row[
                    "token"
                ]

                if token in row_map:
                    refreshed+=1
                else:
                    admitted+=1

                # Replace with newest current binding/freshness
                # data for that token.
                row_map[
                    token
                ]=row

            next_admission_refresh=(
                now_mono
                +max(
                    5.0,
                    admission_refresh_seconds
                )
            )

            print(
                "[ROLLING_ADMISSION] "
                "incoming=%d "
                "new=%d "
                "refreshed=%d "
                "tracked=%d"%(
                    len(incoming),
                    admitted,
                    refreshed,
                    len(row_map)
                ),
                flush=True
            )

        # ----------------------------------------------------
        # AGE OUT ONLY TOKENS WHOSE CURRENT OBSERVATION EXPIRED
        # ----------------------------------------------------

        expired=[]

        for token,row in list(
            row_map.items()
        ):

            if float(
                row.get(
                    "_oracle_hot_valid_until",
                    0.0
                )
            ) <=now_epoch:

                expired.append(
                    token
                )

                row_map.pop(
                    token,
                    None
                )

        for token in expired:

            print(
                "[HOT_EXPIRE] "
                "token=%s"%(
                    token[:10]
                ),
                flush=True
            )

        rows=list(
            row_map.values()
        )

        # New Mriya candidates may arrive after every prior
        # candidate expires. Do NOT terminate the hunt merely
        # because the current active set is temporarily empty.
        if not rows:

            print(
                "[HUNT_EMPTY] "
                "round=%d "
                "waiting_for_replenishment=True"%(
                    hunt_round
                ),
                flush=True
            )

            time.sleep(
                min(
                    3.0,
                    max(
                        0.0,
                        deadline
                        -time.monotonic()
                    )
                )
            )

            continue

        print(
            "[HUNT_ROUND] "
            "round=%d "
            "active=%d "
            "tracked=%d"%(
                hunt_round,
                len(rows),
                len(row_map)
            ),
            flush=True
        )'''

if old not in src:
    if "[ROLLING_ADMISSION]" not in src:
        raise SystemExit(
            "[FAIL] ORACLE-006 hunt-loop seam missing"
        )
else:
    src=src.replace(
        old,
        new,
        1
    )


# ============================================================
# HUNT_HOLD remaining_hot calculation:
# keep waiting for NEW discovery even if current cohort expires.
# ============================================================

old_hold='''            sleep_for=min(
                max(
                    3.0,
                    float(
                        scan_seconds
                    )
                ),
                remaining_hot,
                max(
                    0.0,
                    deadline
                    -time.monotonic()
                )
            )

            if sleep_for<=0:
                continue

            time.sleep(
                sleep_for
            )

            continue'''

new_hold='''            sleep_for=min(
                max(
                    3.0,
                    float(
                        scan_seconds
                    )
                ),
                max(
                    0.0,
                    deadline
                    -time.monotonic()
                )
            )

            if sleep_for<=0:
                continue

            time.sleep(
                sleep_for
            )

            continue'''

if old_hold in src:
    src=src.replace(
        old_hold,
        new_hold,
        1
    )


# Runtime label.
src=src.replace(
    "[ORACLE-006]",
    "[ORACLE-007]"
)

ENGINE.write_text(
    src,
    encoding="utf-8"
)

py_compile.compile(
    str(ENGINE),
    doraise=True
)


TEST.write_text(
r'''import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )


    def test_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_continuous_discovery(self):
        self.assertTrue(
            callable(
                q._ensure_oracle_discovery
            )
        )

        self.assertTrue(
            callable(
                q.refresh_live_universe_rows
            )
        )


    def test_discovery_cleanup(self):
        self.assertTrue(
            callable(
                q._stop_oracle_discovery
            )
        )


    def test_stale_memory_not_execution(self):
        s=inspect.getsource(
            q.refresh_live_universe_rows
        )

        self.assertNotIn(
            "q80.select_rows",
            s
        )

        self.assertNotIn(
            "q80.MEMORY",
            s
        )


    def test_hot_only(self):
        s=inspect.getsource(
            q.refresh_live_universe_rows
        )

        self.assertIn(
            "age>hot_seconds",
            s
        )

        self.assertIn(
            "_oracle_hot_valid_until",
            s
        )


    def test_rolling_admission(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[ROLLING_ADMISSION]",
            s
        )

        self.assertIn(
            "refresh_live_universe_rows",
            s
        )

        self.assertIn(
            "row_map",
            s
        )


    def test_empty_set_does_not_end_hunt(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[HUNT_EMPTY]",
            s
        )


    def test_strategy_unchanged(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )

        self.assertIn(
            "meteora_swap",
            s
        )


    def test_signed_sim_required(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
''',
    encoding="utf-8"
)

py_compile.compile(
    str(TEST),
    doraise=True
)

print(
    "[PASS] ORACLE-007 continuous discovery execution hunt installed"
)

print(
    "[MRIYA] continuous replenishment remains alive during hunt"
)

print(
    "[ADMISSION] fresh exact-bound universe refresh every 10 seconds"
)

print(
    "[REPRICE] active candidates continue physical repricing"
)

print(
    "[EXPIRY] each token ages out independently at HOT 90s"
)

print(
    "[EMPTY_SET] Oracle waits for new opportunities instead of stopping"
)

print(
    "[STALE_MEMORY] prohibited from execution intake"
)

print(
    "[PROFIT] guaranteed physical net must be positive"
)

print(
    "[SIM] signed simulation mandatory before PASS"
)

print(
    "[PAPER] no broadcast"
)

print(
    "[CAP] exact 0.001 SOL principal"
)

print(
    "[OWNER] ORACLE"
)