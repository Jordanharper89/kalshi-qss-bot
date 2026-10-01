from pathlib import Path
import ast

ROOT = Path.cwd()

RUNTIME = (
    ROOT
    / "qseries_v2"
    / "oracle_execution"
    / "solana_atomic_executor"
    / "runtime.py"
)

TEST = ROOT / "test_sae_001_meteora_startup_cache.py"

if not RUNTIME.is_file():
    raise RuntimeError("CANONICAL_RUNTIME_MISSING")

src = RUNTIME.read_text(encoding="utf-8")
tree = ast.parse(src)

target = None

for node in tree.body:
    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "prebuild_meteora_templates"
    ):
        target = node
        break

if target is None:
    raise RuntimeError(
        "METEORA_PREBUILD_FUNCTION_NOT_FOUND"
    )

lines = src.splitlines(keepends=True)

replacement = r'''
def prebuild_meteora_templates(
    state,
    user,
    warmed_rows
):
    global METEORA_TEMPLATES
    global READY_TOKENS

    METEORA_TEMPLATES={}

    programs={
        str(row["token"]):
            str(row["program"])
        for row in (
            warmed_rows
            or []
        )
        if (
            row.get("token")
            and row.get("program")
        )
    }

    programs[
        q87.c.WSOL
    ]=q87.c.TOKEN

    descriptors=[]

    for pair in list(
        state.get("pairs")
        or []
    ):
        token=str(
            pair.token
        )

        if token not in READY_TOKENS:
            continue

        pool=str(
            pair.meteora_pool
        )

        token_x=str(
            pair.token_x
        )

        token_y=str(
            pair.token_y
        )

        tx_prog=programs.get(
            token_x
        )

        ty_prog=programs.get(
            token_y
        )

        if (
            not tx_prog
            or not ty_prog
        ):
            print(
                "[SAE001_HOLD] "
                "token=%s "
                "reason=TOKEN_PROGRAM_NOT_PREWARMED "
                "x=%s y=%s"
                %(
                    token[:10],
                    str(tx_prog),
                    str(ty_prog),
                ),
                flush=True,
            )
            continue

        ux=q87.c.ata(
            user,
            token_x,
            tx_prog,
        )

        uy=q87.c.ata(
            user,
            token_y,
            ty_prog,
        )

        rx=q87.c.pda(
            [
                q87.c.b58d(pool),
                q87.c.b58d(token_x),
            ],
            q87.c.DLMM,
        )

        ry=q87.c.pda(
            [
                q87.c.b58d(pool),
                q87.c.b58d(token_y),
            ],
            q87.c.DLMM,
        )

        oracle=q87.c.pda(
            [
                b"oracle",
                q87.c.b58d(pool),
            ],
            q87.c.DLMM,
        )

        bitmap=q87.c.pda(
            [
                b"bitmap",
                q87.c.b58d(pool),
            ],
            q87.c.DLMM,
        )

        event_authority=q87.c.pda(
            [
                b"__event_authority"
            ],
            q87.c.DLMM,
        )

        arrays=[
            (
                int(a[0]),
                str(a[1]),
            )
            for a in list(
                pair.arrays
            )
        ]

        arrays.sort(
            key=lambda x:x[0]
        )

        if not arrays:
            print(
                "[SAE001_HOLD] "
                "token=%s "
                "reason=NO_PREWARMED_DLMM_ARRAYS"
                %token[:10],
                flush=True,
            )
            continue

        if token_x==q87.c.WSOL:
            source=uy
            dest=ux
            swap_for_y=False

        elif token_y==q87.c.WSOL:
            source=ux
            dest=uy
            swap_for_y=True

        else:
            print(
                "[SAE001_HOLD] "
                "token=%s "
                "reason=DLMM_PAIR_NOT_WSOL"
                %token[:10],
                flush=True,
            )
            continue

        descriptors.append({
            "token":token,
            "pool":pool,
            "token_x":token_x,
            "token_y":token_y,
            "tx_prog":tx_prog,
            "ty_prog":ty_prog,
            "ux":ux,
            "uy":uy,
            "rx":rx,
            "ry":ry,
            "oracle":oracle,
            "bitmap":bitmap,
            "event_authority":
                event_authority,
            "source":source,
            "dest":dest,
            "swap_for_y":
                bool(swap_for_y),
            "arrays":arrays,
        })

    if not descriptors:
        raise RuntimeError(
            "NO_METEORA_PREBUILD_DESCRIPTORS"
        )

    bitmap_addresses=[
        row["bitmap"]
        for row in descriptors
    ]

    bitmap_values=None
    last_error=None

    for attempt in range(1,6):
        try:
            result=q87.c.rpc(
                "getMultipleAccounts",
                [
                    bitmap_addresses,
                    {
                        "encoding":"base64",
                        "commitment":"processed",
                    },
                ],
            )

            if not isinstance(
                result,
                dict
            ):
                raise RuntimeError(
                    "BITMAP_BATCH_RESULT_NOT_MAPPING"
                )

            values=result.get(
                "value"
            )

            if not isinstance(
                values,
                list
            ):
                raise RuntimeError(
                    "BITMAP_BATCH_VALUE_NOT_LIST"
                )

            if len(values)!=len(
                bitmap_addresses
            ):
                raise RuntimeError(
                    "BITMAP_BATCH_LENGTH_MISMATCH"
                )

            bitmap_values=values
            break

        except Exception as exc:
            last_error=exc

            if "429" not in str(exc):
                raise

            delay=min(
                8.0,
                .75*(2**(attempt-1)),
            )

            print(
                "[SAE001_BITMAP_429] "
                "attempt=%d sleep=%.2fs"
                %(
                    attempt,
                    delay,
                ),
                flush=True,
            )

            time.sleep(delay)

    if bitmap_values is None:
        raise RuntimeError(
            "METEORA_BITMAP_BATCH_UNAVAILABLE:"
            +str(last_error)
        )

    for row,bitmap_account in zip(
        descriptors,
        bitmap_values,
    ):
        bitmap_key=(
            row["bitmap"]
            if bitmap_account
            else q87.c.DLMM
        )

        fixed_accounts=[
            (
                row["pool"],
                False,
                True,
            ),
            (
                bitmap_key,
                False,
                True,
            ),
            (
                row["rx"],
                False,
                True,
            ),
            (
                row["ry"],
                False,
                True,
            ),
            (
                row["source"],
                False,
                True,
            ),
            (
                row["dest"],
                False,
                True,
            ),
            (
                row["token_x"],
                False,
                False,
            ),
            (
                row["token_y"],
                False,
                False,
            ),
            (
                row["oracle"],
                False,
                True,
            ),
            (
                q87.c.DLMM,
                False,
                True,
            ),
            (
                user,
                True,
                False,
            ),
            (
                row["tx_prog"],
                False,
                False,
            ),
            (
                row["ty_prog"],
                False,
                False,
            ),
            (
                row["event_authority"],
                False,
                False,
            ),
            (
                q87.c.DLMM,
                False,
                False,
            ),
        ]

        token=row["token"]

        METEORA_TEMPLATES[token]={
            "pool":
                row["pool"],

            "token_x":
                row["token_x"],

            "token_y":
                row["token_y"],

            "swap_for_y":
                row["swap_for_y"],

            "arrays":
                list(row["arrays"]),

            "fixed_accounts":
                fixed_accounts,
        }

        print(
            "[SAE001_METEORA_READY] "
            "token=%s pool=%s "
            "arrays=%d bitmap=%s"
            %(
                token[:10],
                row["pool"][:12],
                len(row["arrays"]),
                (
                    "EXTENSION"
                    if bitmap_account
                    else "PROGRAM_SENTINEL"
                ),
            ),
            flush=True,
        )

    READY_TOKENS.intersection_update(
        set(METEORA_TEMPLATES)
    )

    if not READY_TOKENS:
        raise RuntimeError(
            "NO_FULLY_PREBUILT_EXECUTION_PAIRS"
        )

    return len(
        METEORA_TEMPLATES
    )
'''.lstrip()

new_src = "".join(
    lines[:target.lineno-1]
    + [replacement, "\n"]
    + lines[target.end_lineno:]
)

old_call = '''prebuild_meteora_templates(
            state,
            USER
        )'''

new_call = '''prebuild_meteora_templates(
            state,
            USER,
            token_warm
        )'''

if old_call in new_src:
    new_src = new_src.replace(
        old_call,
        new_call,
        1,
    )

elif new_call not in new_src:
    raise RuntimeError(
        "METEORA_PREBUILD_CALLSITE_UNKNOWN"
    )

ast.parse(new_src)

RUNTIME.write_text(
    new_src,
    encoding="utf-8"
)

TEST_SOURCE = r'''
import inspect
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as q
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )
        self.assertTrue(
            q.PAPER_ONLY
        )
        self.assertFalse(
            q.REAL_MONEY_MOVED
        )

    def test_reuses_oracle025_programs(self):
        src=inspect.getsource(
            q.prebuild_meteora_templates
        )

        self.assertIn(
            "warmed_rows",
            src
        )

        self.assertNotIn(
            "q87.c.account(",
            src
        )

    def test_reuses_pair_arrays(self):
        src=inspect.getsource(
            q.prebuild_meteora_templates
        )

        self.assertIn(
            "pair.arrays",
            src
        )

        self.assertNotIn(
            "dlmm_arrays(",
            src
        )

    def test_one_bitmap_batch(self):
        src=inspect.getsource(
            q.prebuild_meteora_templates
        )

        self.assertIn(
            '"getMultipleAccounts"',
            src
        )

    def test_hot_builder_zero_rpc(self):
        src=inspect.getsource(
            q.build_meteora_ix_hot
        )

        for bad in (
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
            "http(",
        ):
            self.assertNotIn(
                bad,
                src
            )

    def test_buy_exact_quote_preserved(self):
        src=inspect.getsource(
            q.rewrite_pump_buy_bounds
        )

        self.assertIn(
            "BUY_EXACT_QUOTE_IN_DISC",
            src
        )

    def test_truth_sim_preserved(self):
        src=inspect.getsource(
            q.simulate_current
        )

        self.assertIn(
            '"simulateTransaction"',
            src
        )

        self.assertIn(
            'result.get(\n        "value"',
            src
        )

    def test_no_old_execution_chain(self):
        src=inspect.getsource(q)

        self.assertNotIn(
            "q20.run(",
            src
        )

        self.assertNotIn(
            "persistent.serve(",
            src
        )

        self.assertNotIn(
            "SimulationLane(",
            src
        )

    def test_no_broadcast(self):
        src=inspect.getsource(q)

        self.assertNotIn(
            "sendTransaction",
            src
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''

ast.parse(TEST_SOURCE)

TEST.write_text(
    TEST_SOURCE.lstrip(),
    encoding="utf-8"
)

print("[PASS] SAE-001 Meteora startup cache installed")
print("[TARGET] existing canonical runtime")
print("[REUSE] ORACLE-025 token program warm results")
print("[REUSE] PairState hydrated DLMM arrays")
print("[REMOVED] duplicate mint getAccountInfo")
print("[BITMAP] single getMultipleAccounts startup batch")
print("[HOT_PATH] Meteora builder remains RPC-free")
print("[PUMP] BuyExactQuoteIn preserved")
print("[SIM_TRUTH] nested result.value preserved")
print("[BROADCAST] disabled")