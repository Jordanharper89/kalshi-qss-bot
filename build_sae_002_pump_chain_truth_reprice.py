from pathlib import Path
import ast

ROOT=Path.cwd()

RUNTIME=(
    ROOT/
    "qseries_v2"/
    "oracle_execution"/
    "solana_atomic_executor"/
    "runtime.py"
)

TEST=ROOT/"test_sae_002_pump_chain_truth_reprice.py"

if not RUNTIME.is_file():
    raise RuntimeError(
        "CANONICAL_RUNTIME_MISSING"
    )

src=RUNTIME.read_text(
    encoding="utf-8"
)

tree=ast.parse(src)

attack_node=None

for node in tree.body:
    if (
        isinstance(node,ast.FunctionDef)
        and node.name=="attack"
    ):
        attack_node=node
        break

if attack_node is None:
    raise RuntimeError(
        "CANONICAL_ATTACK_NOT_FOUND"
    )

lines=src.splitlines(
    keepends=True
)

replacement=r'''
def pump_6040_actual_base_out(sim):
    if not isinstance(sim,dict):
        return None

    err=sim.get("err")

    if not (
        isinstance(err,dict)
        and err.get(
            "InstructionError"
        )
    ):
        return None

    rows=err[
        "InstructionError"
    ]

    if (
        not isinstance(rows,list)
        or len(rows)<2
        or not isinstance(
            rows[1],
            dict
        )
        or int(
            rows[1].get(
                "Custom",
                -1
            )
        )!=6040
    ):
        return None

    logs=[
        str(x)
        for x in (
            sim.get("logs")
            or []
        )
    ]

    saw_6040=False

    for line in logs:

        if (
            "BuySlippageBelowMinBaseAmountOut"
            in line
        ):
            saw_6040=True
            continue

        if (
            saw_6040
            and "Program log: Left:"
            in line
        ):
            raw=line.split(
                "Left:",
                1
            )[1].strip()

            try:
                value=int(raw)
            except Exception:
                return None

            return (
                value
                if value>0
                else None
            )

    return None


def reprice_from_pump_chain_truth(
    snap,
    opportunity,
    actual_base_out
):
    token=str(
        snap["token"]
    )

    start=int(
        opportunity[
            "start"
        ]
    )

    actual_base_out=int(
        actual_base_out
    )

    if actual_base_out<=0:
        raise RuntimeError(
            "SAE002_BAD_CHAIN_BASE_OUT"
        )

    #
    # Apply the already-certified Token /
    # Token-2022 receipt semantics.
    #
    actual_net_token=int(
        q18.token_net(
            token,
            actual_base_out,
        )
    )

    if actual_net_token<=0:
        raise RuntimeError(
            "SAE002_CHAIN_TOKEN_NET_ZERO"
        )

    #
    # Reprice Meteora from the amount
    # PumpSwap itself says the transaction
    # can actually buy.
    #
    mq=q18.core.dlmm_quote_snapshot(
        snap,
        actual_net_token,
        token,
    )

    end=int(
        mq["raw_out"]
    )

    net=end-start

    out=dict(
        opportunity
    )

    out[
        "pump_base_out_gross"
    ]=actual_base_out

    out[
        "pump_base_out_net"
    ]=actual_net_token

    out["mq"]=mq
    out["local_end"]=end
    out["local_net"]=net

    out["local_bps"]=(
        net/start*10000.0
    )

    out[
        "pump_chain_truth"
    ]=True

    return out


def _canonical_sim_logs(sim):
    for line in (
        sim.get("logs")
        or []
    )[-15:]:

        print(
            "[CANONICAL_SIM_LOG] "
            +str(line),
            flush=True,
        )


def _execute_route_once(
    user,
    snap,
    opportunity
):
    t=time.perf_counter_ns()

    route=same_snapshot_route(
        user,
        snap,
        opportunity,
    )

    build_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    t=time.perf_counter_ns()

    compiled=compile_current(
        user,
        route,
    )

    compile_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    if not compiled.get("ok"):
        return {
            "ok":False,
            "phase":"compile",
            "build_ms":build_ms,
            "compile_ms":compile_ms,
            "compiled":compiled,
        }

    t=time.perf_counter_ns()

    sim=simulate_current(
        compiled,
        user,
    )

    sim_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    return {
        "ok":True,
        "build_ms":build_ms,
        "compile_ms":compile_ms,
        "sim_ms":sim_ms,
        "compiled":compiled,
        "sim":sim,
    }


def attack(
    lane,
    token,
    snap,
    opportunity,
    slot,
    received_ns,
    generation
):
    if lane.newer_waiting(
        token,
        generation
    ):
        return

    original_base_out=int(
        opportunity[
            "pump_base_out_gross"
        ]
    )

    first=_execute_route_once(
        USER,
        snap,
        opportunity,
    )

    if not first.get("ok"):

        print(
            "[CANONICAL_COMPILE_REJECT] "
            "token=%s reason=%s"
            %(
                token[:10],
                first.get(
                    "compiled",
                    {}
                ).get(
                    "reason",
                    "UNKNOWN"
                ),
            ),
            flush=True,
        )

        return

    if lane.newer_waiting(
        token,
        generation
    ):

        print(
            "[CANONICAL_SUPERSEDED] "
            "token=%s phase=first_sim"
            %token[:10],
            flush=True,
        )

        return

    sim=first["sim"]

    #
    # ========================================================
    # FIRST POSSIBILITY:
    # Transaction already works.
    # ========================================================
    #
    if sim.get("err") is None:

        total_ms=(
            time.perf_counter_ns()
            -received_ns
        )/1e6

        print(
            "[CANONICAL_SIM_PASS] "
            "token=%s "
            "slot=%s "
            "size=%.3f "
            "quote_bps=%+.2f "
            "candidate=%s "
            "bytes=%d "
            "units=%s "
            "build_ms=%.3f "
            "compile_ms=%.3f "
            "sim_ms=%.3f "
            "event_to_sim_ms=%.3f "
            "pump_truth=ORIGINAL"
            %(
                token[:10],
                slot,
                float(
                    opportunity[
                        "size_sol"
                    ]
                ),
                float(
                    opportunity[
                        "local_bps"
                    ]
                ),
                first[
                    "compiled"
                ][
                    "candidate"
                ],
                first[
                    "compiled"
                ][
                    "bytes"
                ],
                str(
                    sim.get("units")
                ),
                first[
                    "build_ms"
                ],
                first[
                    "compile_ms"
                ],
                first[
                    "sim_ms"
                ],
                total_ms,
            ),
            flush=True,
        )

        return

    #
    # ========================================================
    # SECOND POSSIBILITY:
    # PumpSwap gave exact chain output through 6040.
    # ========================================================
    #
    actual_base_out=(
        pump_6040_actual_base_out(
            sim
        )
    )

    if actual_base_out is None:

        print(
            "[CANONICAL_SIM_REJECT] "
            "token=%s "
            "slot=%s "
            "size=%.3f "
            "quote_bps=%+.2f "
            "candidate=%s "
            "bytes=%d "
            "err=%s "
            "build_ms=%.3f "
            "compile_ms=%.3f "
            "sim_ms=%.3f"
            %(
                token[:10],
                slot,
                float(
                    opportunity[
                        "size_sol"
                    ]
                ),
                float(
                    opportunity[
                        "local_bps"
                    ]
                ),
                first[
                    "compiled"
                ][
                    "candidate"
                ],
                first[
                    "compiled"
                ][
                    "bytes"
                ],
                str(
                    sim.get("err")
                ),
                first[
                    "build_ms"
                ],
                first[
                    "compile_ms"
                ],
                first[
                    "sim_ms"
                ],
            ),
            flush=True,
        )

        _canonical_sim_logs(
            sim
        )

        return

    drift=(
        actual_base_out
        -original_base_out
    )

    drift_bps=(
        drift
        /original_base_out
        *10000.0
    )

    corrected=(
        reprice_from_pump_chain_truth(
            snap,
            opportunity,
            actual_base_out,
        )
    )

    print(
        "[SAE002_PUMP_CHAIN_TRUTH] "
        "token=%s "
        "slot=%s "
        "predicted_base=%d "
        "chain_base=%d "
        "drift=%+d "
        "drift_bps=%+.2f "
        "old_quote_bps=%+.2f "
        "corrected_quote_bps=%+.2f"
        %(
            token[:10],
            slot,
            original_base_out,
            actual_base_out,
            drift,
            drift_bps,
            float(
                opportunity[
                    "local_bps"
                ]
            ),
            float(
                corrected[
                    "local_bps"
                ]
            ),
        ),
        flush=True,
    )

    #
    # Chain truth killed the opportunity.
    #
    if int(
        corrected[
            "local_net"
        ]
    )<=0:

        print(
            "[SAE002_CHAIN_REPRICE_HOLD] "
            "token=%s "
            "slot=%s "
            "corrected_net=%+d "
            "corrected_bps=%+.2f"
            %(
                token[:10],
                slot,
                int(
                    corrected[
                        "local_net"
                    ]
                ),
                float(
                    corrected[
                        "local_bps"
                    ]
                ),
            ),
            flush=True,
        )

        return

    if lane.newer_waiting(
        token,
        generation
    ):

        print(
            "[CANONICAL_SUPERSEDED] "
            "token=%s "
            "phase=chain_reprice"
            %token[:10],
            flush=True,
        )

        return

    #
    # ONE retry only.
    #
    # The retry uses:
    #
    #   Pump minBaseOut = PumpSwap chain truth
    #   Meteora amountIn = transfer-adjusted chain truth
    #
    second=_execute_route_once(
        USER,
        snap,
        corrected,
    )

    if not second.get("ok"):

        print(
            "[SAE002_REPRICE_COMPILE_REJECT] "
            "token=%s reason=%s"
            %(
                token[:10],
                second.get(
                    "compiled",
                    {}
                ).get(
                    "reason",
                    "UNKNOWN"
                ),
            ),
            flush=True,
        )

        return

    sim2=second["sim"]

    total_ms=(
        time.perf_counter_ns()
        -received_ns
    )/1e6

    if sim2.get("err") is not None:

        print(
            "[SAE002_REPRICE_SIM_REJECT] "
            "token=%s "
            "slot=%s "
            "size=%.3f "
            "corrected_bps=%+.2f "
            "candidate=%s "
            "bytes=%d "
            "err=%s "
            "retry_build_ms=%.3f "
            "retry_compile_ms=%.3f "
            "retry_sim_ms=%.3f "
            "event_to_final_ms=%.3f"
            %(
                token[:10],
                slot,
                float(
                    corrected[
                        "size_sol"
                    ]
                ),
                float(
                    corrected[
                        "local_bps"
                    ]
                ),
                second[
                    "compiled"
                ][
                    "candidate"
                ],
                second[
                    "compiled"
                ][
                    "bytes"
                ],
                str(
                    sim2.get("err")
                ),
                second[
                    "build_ms"
                ],
                second[
                    "compile_ms"
                ],
                second[
                    "sim_ms"
                ],
                total_ms,
            ),
            flush=True,
        )

        _canonical_sim_logs(
            sim2
        )

        return

    print(
        "[CANONICAL_SIM_PASS] "
        "token=%s "
        "slot=%s "
        "size=%.3f "
        "quote_bps=%+.2f "
        "candidate=%s "
        "bytes=%d "
        "units=%s "
        "retry_build_ms=%.3f "
        "retry_compile_ms=%.3f "
        "retry_sim_ms=%.3f "
        "event_to_sim_ms=%.3f "
        "pump_truth=CHAIN_6040"
        %(
            token[:10],
            slot,
            float(
                corrected[
                    "size_sol"
                ]
            ),
            float(
                corrected[
                    "local_bps"
                ]
            ),
            second[
                "compiled"
            ][
                "candidate"
            ],
            second[
                "compiled"
            ][
                "bytes"
            ],
            str(
                sim2.get("units")
            ),
            second[
                "build_ms"
            ],
            second[
                "compile_ms"
            ],
            second[
                "sim_ms"
            ],
            total_ms,
        ),
        flush=True,
    )
'''.lstrip()

new_src="".join(
    lines[:attack_node.lineno-1]
    +[
        replacement,
        "\n",
    ]
    +lines[
        attack_node.end_lineno:
    ]
)

ast.parse(
    new_src
)

RUNTIME.write_text(
    new_src,
    encoding="utf-8"
)


TEST_SOURCE=r'''
import inspect
import unittest
from unittest.mock import patch

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

    def test_6040_left_parser(self):

        sim={
            "err":{
                "InstructionError":[
                    3,
                    {
                        "Custom":6040
                    },
                ]
            },
            "logs":[
                "Program log: AnchorError Error Code: BuySlippageBelowMinBaseAmountOut",
                "Program log: Left: 14030784113",
                "Program log: Right: 14927620303",
            ],
        }

        self.assertEqual(
            q.pump_6040_actual_base_out(
                sim
            ),
            14030784113,
        )

    def test_non_6040_not_recovered(self):

        sim={
            "err":{
                "InstructionError":[
                    3,
                    {
                        "Custom":6004
                    },
                ]
            },
            "logs":[
                "Program log: Left: 123"
            ],
        }

        self.assertIsNone(
            q.pump_6040_actual_base_out(
                sim
            )
        )

    def test_chain_reprice_uses_token_net_and_dlmm(self):

        opportunity={
            "start":1000,
            "size_sol":.000001,
            "local_bps":100.0,
            "local_net":10,
            "pump_base_out_gross":2000,
            "pump_base_out_net":1900,
            "pump_max_quote":1000,
            "mq":{
                "raw_out":1010
            },
        }

        snap={
            "token":"TOKEN",
            "meteora":{},
            "dlmm_state":object(),
        }

        with patch.object(
            q.q18,
            "token_net",
            return_value=1800,
        ):
            with patch.object(
                q.q18.core,
                "dlmm_quote_snapshot",
                return_value={
                    "raw_out":1050,
                    "bins_crossed":1,
                    "swap_for_y":True,
                    "arrays":[],
                },
            ):
                x=q.reprice_from_pump_chain_truth(
                    snap,
                    opportunity,
                    1900,
                )

        self.assertEqual(
            x["pump_base_out_gross"],
            1900,
        )

        self.assertEqual(
            x["pump_base_out_net"],
            1800,
        )

        self.assertEqual(
            x["local_end"],
            1050,
        )

        self.assertEqual(
            x["local_net"],
            50,
        )

        self.assertTrue(
            x["pump_chain_truth"]
        )

    def test_attack_has_one_6040_retry(self):

        src=inspect.getsource(
            q.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src,
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src,
        )

        self.assertIn(
            "[SAE002_PUMP_CHAIN_TRUTH]",
            src,
        )

        self.assertIn(
            "[SAE002_CHAIN_REPRICE_HOLD]",
            src,
        )

        self.assertIn(
            "[SAE002_REPRICE_SIM_REJECT]",
            src,
        )

    def test_hot_meteora_builder_stays_rpc_free(self):

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
                src,
            )

    def test_exact_quote_instruction_preserved(self):

        src=inspect.getsource(
            q.rewrite_pump_buy_bounds
        )

        self.assertIn(
            "BUY_EXACT_QUOTE_IN_DISC",
            src,
        )

    def test_truth_sim_preserved(self):

        src=inspect.getsource(
            q.simulate_current
        )

        self.assertIn(
            '"simulateTransaction"',
            src,
        )

        self.assertIn(
            'result.get(\n        "value"',
            src,
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

ast.parse(
    TEST_SOURCE
)

TEST.write_text(
    TEST_SOURCE.lstrip(),
    encoding="utf-8"
)

print("[PASS] SAE-002 Pump chain-truth reprice installed")
print("[INPUT] PumpSwap 6040 Left value = executable chain base output")
print("[REPRICE] Token/Token-2022 net receipt recalculated")
print("[REPRICE] Meteora leg recalculated from chain Pump output")
print("[GATE] corrected opportunity must remain positive")
print("[RETRY] maximum one corrected atomic simulation")
print("[SLIPPAGE] not loosened by arbitrary percentage")
print("[SAE-001] memory-only Meteora builder preserved")
print("[BROADCAST] disabled")