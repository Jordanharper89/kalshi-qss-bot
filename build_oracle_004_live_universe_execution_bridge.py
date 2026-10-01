from pathlib import Path
import py_compile

ROOT=Path.cwd()

ENGINE=ROOT/(
    "qseries_v2/oracle_execution/"
    "oracle_003_unified_physical_execution_engine.py"
)

TEST=ROOT/"test_oracle_004_live_universe_execution_bridge.py"

if not ENGINE.is_file():
    raise SystemExit(
        "[FAIL] ORACLE-003 unified physical engine missing"
    )

src=ENGINE.read_text(
    encoding="utf-8"
)

# ------------------------------------------------------------
# Import certified dynamic PumpSwap -> Meteora universe.
# QARB-080 remains discovery/binding/learning only.
# ORACLE-003 remains the sole physical execution path.
# ------------------------------------------------------------

imports='''
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_080_single_runtime_dynamic_mriya_supervisor as q80
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_081_proven_arbitrage_lifecycle_certification as q81
)
'''

anchor='''from qseries_v2.oracle_execution import (
    oracle_001_live_solana_executor
    as base
)
'''

if (
    "qarb_080_single_runtime_dynamic_mriya_supervisor as q80"
    not in src
):
    if anchor not in src:
        raise SystemExit(
            "[FAIL] ORACLE-003 import seam missing"
        )

    src=src.replace(
        anchor,
        anchor+imports,
        1
    )


bridge=r'''
def live_universe_rows(root):
    import subprocess
    import sys

    root=Path(root)

    discovery=None
    fresh=[]
    selected=[]

    try:
        discovery=subprocess.Popen(
            [
                sys.executable,
                "run_qarb_043b_paced_mriya_token_discovery.py"
            ],
            cwd=str(root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Match the certified QARB-080 startup discovery window.
        time.sleep(6.0)

        _,fresh=q80.q45.classify()

        selected=q80.select_rows(
            root,
            fresh
        )

    finally:
        if discovery is not None:
            try:
                discovery.terminate()
                discovery.wait(
                    timeout=5
                )

            except Exception:
                try:
                    discovery.kill()
                except Exception:
                    pass

    cert=q81.certify(
        root
    )

    proven=set(
        cert.get(
            "recyclable_proven_tokens",
            []
        )
    )

    rows=[]
    rejected=0

    for row in selected:

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
            rejected+=1
            continue

        x=dict(
            row
        )

        # Live physical sizing is always owned by Oracle.
        # Historical learned production sizes do not leak here.
        x[
            "size_sol"
        ]=MICRO_SOL

        x[
            "micro_lamports"
        ]=MICRO_LAMPORTS

        x[
            "_oracle_proven_priority"
        ]=(
            token in proven
        )

        rows.append(
            x
        )

    # Previously proven/recyclable tokens get first evaluation,
    # but proof NEVER bypasses current physical profitability.
    rows.sort(
        key=lambda x:(
            1
            if x.get(
                "_oracle_proven_priority"
            )
            else 0,

            float(
                x.get(
                    "last_seen_epoch"
                )
                or 0.0
            )
        ),
        reverse=True
    )

    max_rows=int(
        os.getenv(
            "ORACLE_PUMP_METEORA_MAX_CANDIDATES",
            "32"
        )
    )

    rows=rows[
        :max(
            1,
            max_rows
        )
    ]

    print(
        "[LIVE_UNIVERSE] "
        "fresh=%d "
        "selected=%d "
        "physical_bound=%d "
        "proven_priority=%d "
        "rejected_unbound=%d"%(
            len(fresh),
            len(selected),
            len(rows),

            sum(
                bool(
                    x.get(
                        "_oracle_proven_priority"
                    )
                )
                for x in rows
            ),

            rejected,
        ),
        flush=True
    )

    for row in rows:

        print(
            "[UNIVERSE_ROW] "
            "token=%s "
            "proven=%s "
            "pump=%s "
            "meteora=%s"%(
                row[
                    "token"
                ][:10],

                bool(
                    row.get(
                        "_oracle_proven_priority"
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
'''

if "def live_universe_rows(root):" not in src:

    marker="\ndef run(\n"

    pos=src.find(
        marker
    )

    if pos<0:
        raise SystemExit(
            "[FAIL] ORACLE-003 run seam missing"
        )

    src=(
        src[:pos]
        +"\n"
        +bridge.strip()
        +"\n\n"
        +src[pos+1:]
    )


old='''    rows=base.load_micro_rows(
        root
    )'''

new='''    rows=live_universe_rows(
        root
    )

    if not rows:
        print(
            "[ORACLE_HOLD] "
            "NO_CURRENT_BOUND_PUMP_METEORA_UNIVERSE",
            flush=True
        )

        return 2'''

if old in src:

    src=src.replace(
        old,
        new,
        1
    )

elif new not in src:

    raise SystemExit(
        "[FAIL] frozen three-token intake seam missing"
    )


src=src.replace(
    "[ORACLE-003] UNIFIED PHYSICAL EXECUTION",
    "[ORACLE-004] LIVE-UNIVERSE PHYSICAL EXECUTION"
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


    def test_live_universe(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "q80.q45.classify",
            s
        )

        self.assertIn(
            "q80.select_rows",
            s
        )

        self.assertIn(
            "recyclable_proven_tokens",
            s
        )


    def test_old_fixture_retired(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "live_universe_rows",
            s
        )

        self.assertNotIn(
            "base.load_micro_rows",
            s
        )


    def test_physical_gate_preserved(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_strategy_preserved(self):
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
    "[PASS] ORACLE-004 live-universe execution bridge installed"
)

print(
    "[INTAKE] QARB-080 current discovery + binding memory"
)

print(
    "[PRIORITY] QARB-081 proven/recyclable first"
)

print(
    "[BREADTH] up to 32 current exact-bound Pump/Meteora tokens"
)

print(
    "[PHYSICAL] current profitability + signed simulation still mandatory"
)

print(
    "[STRATEGY] PumpSwap -> Meteora DLMM"
)

print(
    "[CAP] exact strategy principal 0.001 SOL"
)

print(
    "[OWNER] ORACLE"
)