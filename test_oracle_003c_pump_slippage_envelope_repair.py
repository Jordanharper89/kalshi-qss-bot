import base64
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
