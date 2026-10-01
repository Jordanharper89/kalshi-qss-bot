from pathlib import Path
import py_compile
import re

P=Path(
    "qseries_v2/oracle_execution/"
    "oracle_003_unified_physical_execution_engine.py"
)

TEST=Path(
    "test_oracle_003c_pump_slippage_envelope_repair.py"
)

if not P.is_file():
    raise SystemExit(
        "[FAIL] ORACLE-003 missing"
    )

s=P.read_text(
    encoding="utf-8"
)

# ============================================================
# REPLACE ONLY THE PUMP BUY PARSER / CAPITAL ENVELOPE
#
# Strategy principal: 1,000,000 lamports
# Pump slippage: existing configured SLIPPAGE_BPS
# Legal maximum spend:
#
# ceil(principal * (10000 + bps) / 10000)
#
# At 20 bps:
# 1,000,000 -> 1,002,000 lamports
# ============================================================

pat=re.compile(
    r'def pump_min_base_out\('
    r'[\s\S]*?'
    r'(?=\n\ndef net_received\()'
)

new=r'''def pump_max_quote_envelope():
    bps=int(
        base.q87.las.q59
        .SLIPPAGE_BPS
    )

    if bps<0:
        raise RuntimeError(
            "NEGATIVE_PUMP_SLIPPAGE"
        )

    # integer ceiling
    return (
        MICRO_LAMPORTS
        *(10000+bps)
        +9999
    )//10000


def pump_min_base_out(
    pump_ix
):
    raw=base64.b64decode(
        pump_ix.get("data") or ""
    )

    BUY=bytes([
        102,6,61,18,
        1,218,235,234
    ])

    BUY_EXACT=bytes([
        198,46,21,82,
        180,217,232,112
    ])

    if len(raw)<24:
        raise RuntimeError(
            "PUMP_DATA_TOO_SHORT"
        )

    disc=raw[:8]

    a=int.from_bytes(
        raw[8:16],
        "little"
    )

    b=int.from_bytes(
        raw[16:24],
        "little"
    )

    allowed=(
        pump_max_quote_envelope()
    )

    if disc==BUY:
        # PumpSwap BUY:
        #
        # a = exact base_amount_out
        # b = max_quote_amount_in
        #
        # 0.001 SOL remains the quoted strategy capital.
        # max_quote_amount_in may only exceed that principal
        # by the already-configured slippage envelope.
        base_amount_out=a
        max_quote_amount_in=b

        if (
            max_quote_amount_in
            >allowed
        ):
            raise RuntimeError(
                "PUMP_MAX_QUOTE_OUTSIDE_SLIPPAGE_ENVELOPE:"
                +str(max_quote_amount_in)
                +":allowed="
                +str(allowed)
            )

        if base_amount_out<=0:
            raise RuntimeError(
                "PUMP_BASE_AMOUNT_ZERO"
            )

        return base_amount_out

    if disc==BUY_EXACT:
        # PumpSwap BUY_EXACT_QUOTE_IN:
        #
        # a = spendable_quote_in
        # b = min_base_amount_out
        #
        # This form is exact-input and therefore may not exceed
        # the 0.001 SOL strategy principal itself.
        spendable_quote_in=a
        min_base_amount_out=b

        if (
            spendable_quote_in
            >MICRO_LAMPORTS
        ):
            raise RuntimeError(
                "PUMP_EXACT_INPUT_EXCEEDS_PRINCIPAL:"
                +str(
                    spendable_quote_in
                )
            )

        if min_base_amount_out<=0:
            raise RuntimeError(
                "PUMP_MINIMUM_ZERO"
            )

        return min_base_amount_out

    raise RuntimeError(
        "PUMP_UNKNOWN_BUY_DISCRIMINATOR:"
        +disc.hex()
    )
'''

if not pat.search(s):
    raise SystemExit(
        "[FAIL] ORACLE-003B Pump parser seam missing"
    )

s=pat.sub(
    new.rstrip(),
    s,
    count=1
)

P.write_text(
    s,
    encoding="utf-8"
)

py_compile.compile(
    str(P),
    doraise=True
)

TEST.write_text(
r'''import base64
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_principal_unchanged(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_20bps_envelope(self):
        old=(
            q.base.q87.las.q59
            .SLIPPAGE_BPS
        )

        try:
            q.base.q87.las.q59.SLIPPAGE_BPS=20

            self.assertEqual(
                q.pump_max_quote_envelope(),
                1_002_000
            )

        finally:
            q.base.q87.las.q59.SLIPPAGE_BPS=old


    def test_buy_accepts_1002000(self):
        old=(
            q.base.q87.las.q59
            .SLIPPAGE_BPS
        )

        try:
            q.base.q87.las.q59.SLIPPAGE_BPS=20

            disc=bytes([
                102,6,61,18,
                1,218,235,234
            ])

            base_out=123456789
            max_quote=1_002_000

            raw=(
                disc
                +base_out.to_bytes(
                    8,
                    "little"
                )
                +max_quote.to_bytes(
                    8,
                    "little"
                )
            )

            ix={
                "data":
                    base64.b64encode(
                        raw
                    ).decode()
            }

            self.assertEqual(
                q.pump_min_base_out(ix),
                base_out
            )

        finally:
            q.base.q87.las.q59.SLIPPAGE_BPS=old


    def test_buy_rejects_above_envelope(self):
        old=(
            q.base.q87.las.q59
            .SLIPPAGE_BPS
        )

        try:
            q.base.q87.las.q59.SLIPPAGE_BPS=20

            disc=bytes([
                102,6,61,18,
                1,218,235,234
            ])

            raw=(
                disc
                +(100).to_bytes(
                    8,
                    "little"
                )
                +(1_002_001).to_bytes(
                    8,
                    "little"
                )
            )

            ix={
                "data":
                    base64.b64encode(
                        raw
                    ).decode()
            }

            with self.assertRaisesRegex(
                RuntimeError,
                "OUTSIDE_SLIPPAGE_ENVELOPE"
            ):
                q.pump_min_base_out(ix)

        finally:
            q.base.q87.las.q59.SLIPPAGE_BPS=old


    def test_same_strategy(self):
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


    def test_signed_simulation_still_required(self):
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
    "[PASS] ORACLE-003C Pump slippage envelope repaired"
)

print(
    "[PRINCIPAL] 1000000 lamports = 0.001000000 SOL"
)

print(
    "[PUMP_MAX] configured 20bps => 1002000 lamports maximum"
)

print(
    "[STRATEGY] PumpSwap -> Meteora DLMM unchanged"
)

print(
    "[CAPITAL] no production sizing increase"
)

print(
    "[MODE] physical paper certification only"
)