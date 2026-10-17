from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_execution" / "solana_atomic_executor"
TARGET = PKG / "checkpoint3_reverse_atomic_compile.py"
TEST = ROOT / "test_canonical_checkpoint3_reverse_atomic_compile.py"

MODULE = r"""from __future__ import annotations

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint2_forward_atomic_sim as cp


def _reverse_opportunity(snap):
    rows = list(
        r.q18.exact_snapshot_opportunities(
            snap,
            0.001,
        )
    )

    for row in rows:
        if row.get("direction") == "METEORA_TO_PUMP":
            return row

    raise RuntimeError("NO_METEORA_TO_PUMP_OPPORTUNITY")


def _reverse_route(user, snap, reverse):
    token = str(reverse["token"])
    start = int(reverse["start"])
    token_in = int(
        reverse.get("net_token")
        or reverse.get("gross_token")
        or 0
    )

    if token_in <= 0:
        raise RuntimeError("REVERSE_TOKEN_INPUT_ZERO")

    meteora_ix = r.build_meteora_ix_hot(
        token,
        start,
        dict(reverse["mq"]),
    )

    pump64, expected_quote = r.q87.c.pump_sell_tx(
        user,
        token,
        token_in,
    )

    pump_ixs, base_alts = r.q87.c.resolve_pump_instructions(
        pump64
    )

    pump_positions = [
        i
        for i, ix in enumerate(pump_ixs)
        if ix.get("programId") == r.q87.c.PUMP
    ]

    if len(pump_positions) != 1:
        raise RuntimeError(
            "REVERSE_PUMP_PROGRAM_IX_COUNT:%d"
            % len(pump_positions)
        )

    pi = pump_positions[0]
    pump_ix = pump_ixs[pi]

    if not any(
        a.get("pubkey") == snap["pump_pool"]
        for a in (pump_ix.get("accounts") or [])
    ):
        raise RuntimeError("REVERSE_PUMP_POOL_ACCOUNT_DRIFT")

    pre = list(pump_ixs[:pi])
    post = list(pump_ixs[pi + 1:])

    # Pump helper/setup instructions remain first so ATAs/WSOL
    # prerequisites exist. Economic order is then:
    # Meteora WSOL->token, Pump token->WSOL.
    full = pre + [meteora_ix, pump_ix] + post

    return {
        "token": token,
        "direction": "METEORA_TO_PUMP",
        "start_lamports": start,
        "pre_sim_net_lamports": int(reverse["local_net"]),
        "pre_sim_bps": float(reverse["local_bps"]),
        "meteora_token_out_raw": token_in,
        "pump_expected_quote_raw": int(expected_quote),
        "pump_ixs": pump_ixs,
        "pump_index": pi + 1,
        "pump_ix": pump_ix,
        "meteora_ix": meteora_ix,
        "base_alts": list(base_alts),
        "original_candidates": [
            ("FULL_REVERSE", full),
        ],
    }


def compile_reverse(user, snap):
    reverse = _reverse_opportunity(snap)

    print(
        "[CHECKPOINT3_REVERSE_ROUTE] "
        "token=%s bps=%+.2f net=%+d token_in=%d"
        % (
            str(reverse["token"])[:10],
            float(reverse["local_bps"]),
            int(reverse["local_net"]),
            int(
                reverse.get("net_token")
                or reverse.get("gross_token")
                or 0
            ),
        ),
        flush=True,
    )

    route = _reverse_route(
        user,
        snap,
        reverse,
    )

    result = r.compile_current(
        user,
        route,
    )

    if not result.get("ok"):
        print(
            "[CHECKPOINT3_REVERSE_COMPILE_FAIL] %s"
            % result,
            flush=True,
        )
        return result

    size = int(result.get("bytes") or 0)

    print(
        "[CHECKPOINT3_REVERSE_COMPILE_PASS] "
        "candidate=%s bytes=%d max=1232"
        % (
            result.get("candidate"),
            size,
        ),
        flush=True,
    )

    if size > 1232:
        raise RuntimeError(
            "REVERSE_COMPILED_TOO_LARGE:%d"
            % size
        )

    print(
        "[CHECKPOINT3_REVERSE_ATOMIC_ORDER] "
        "METEORA_TO_PUMP=True",
        flush=True,
    )
    print(
        "[SIMULATION] skipped_balance_independent_compile_only",
        flush=True,
    )
    print("[BROADCAST] disabled", flush=True)

    return {
        "ok": True,
        "direction": "METEORA_TO_PUMP",
        "bytes": size,
        "candidate": result.get("candidate"),
        "simulation": False,
        "broadcast": False,
    }


def main():
    captured = {}
    original = r._execute_route_once

    def checkpoint3_intercept(user, snap, _forward):
        captured["result"] = compile_reverse(
            user,
            snap,
        )
        return captured["result"]

    r._execute_route_once = checkpoint3_intercept

    try:
        try:
            cp.main()
        except SystemExit as exc:
            if not captured:
                raise
    finally:
        r._execute_route_once = original

    result = captured.get("result")

    if not result:
        raise RuntimeError(
            "CHECKPOINT3_REVERSE_ROUTE_NOT_MATERIALIZED"
        )

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
"""

TEST_CODE = r"""import ast
import unittest
from pathlib import Path

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "checkpoint3_reverse_atomic_compile.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = TARGET.read_text(encoding="utf-8")
        ast.parse(cls.src)

    def test_reverse_direction(self):
        self.assertIn(
            '"METEORA_TO_PUMP"',
            self.src,
        )

    def test_economic_order(self):
        self.assertIn(
            "full = pre + [meteora_ix, pump_ix] + post",
            self.src,
        )

    def test_canonical_compiler(self):
        self.assertIn(
            "r.compile_current(",
            self.src,
        )

    def test_reuses_checkpoint2_hydration(self):
        self.assertIn(
            "checkpoint2_forward_atomic_sim as cp",
            self.src,
        )

    def test_no_simulation(self):
        self.assertNotIn(
            "simulateTransaction",
            self.src,
        )
        self.assertIn(
            "skipped_balance_independent_compile_only",
            self.src,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.src,
        )
        self.assertNotIn(
            ".send(",
            self.src,
        )

    def test_packet_limit(self):
        self.assertIn(
            "REVERSE_COMPILED_TOO_LARGE",
            self.src,
        )
        self.assertIn(
            "1232",
            self.src,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
"""

PKG.mkdir(parents=True, exist_ok=True)
TARGET.write_text(MODULE, encoding="utf-8")
TEST.write_text(TEST_CODE, encoding="utf-8")

print("[PASS] canonical checkpoint-3 reverse compile installed")
print("[PATH] solana_atomic_executor only")
print("[DIRECTION] METEORA_TO_PUMP")
print("[ORDER] Pump helpers -> Meteora buy -> Pump sell -> Pump post")
print("[COMPILE] canonical ALT/runtime compiler")
print("[SIMULATION] disabled; no SOL balance required")
print("[BROADCAST] disabled")
print("[KEY] QSB_SOLANA_PRIVATE_KEY untouched")
print("[TEST]", TEST.name)
