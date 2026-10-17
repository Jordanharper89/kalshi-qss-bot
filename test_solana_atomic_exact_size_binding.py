import base64
import struct
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r


class FakeC:
    SYSTEM="11111111111111111111111111111111"
    WSOL="So11111111111111111111111111111111111111112"
    TOKEN="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

    @staticmethod
    def ata(user,mint,program):
        return "WSOL_ATA"


class FakeQ87:
    c=FakeC()


def system_transfer(user,dest,lamports):
    raw=struct.pack(
        "<IQ",
        2,
        int(lamports),
    )
    return {
        "programId":FakeC.SYSTEM,
        "accounts":[
            {"pubkey":user,"isSigner":True,"isWritable":True},
            {"pubkey":dest,"isSigner":False,"isWritable":True},
        ],
        "data":base64.b64encode(raw).decode(),
    }


def pump_ix(spendable):
    raw=(
        r.BUY_EXACT_QUOTE_IN_DISC
        +struct.pack("<Q",int(spendable))
        +struct.pack("<Q",1)
    )
    return {
        "programId":"PUMP",
        "accounts":[],
        "data":base64.b64encode(raw).decode(),
    }


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_q87=r.q87
        r.q87=FakeQ87()

    @classmethod
    def tearDownClass(cls):
        r.q87=cls.old_q87

    def template(self):
        return {
            "template_quote_lamports":1_000_000,
            "wsol_funding_rows":[
                {"index":0,"template_lamports":1_002_000}
            ],
        }

    def test_all_approved_sizes_scale(self):
        expected={
            1_000_000:1_002_000,
            10_000_000:10_020_000,
            25_000_000:25_050_000,
            50_000_000:50_100_000,
            100_000_000:100_200_000,
            180_000_000:180_360_000,
            280_000_000:280_560_000,
            500_000_000:501_000_000,
            1_000_000_000:1_002_000_000,
            1_400_000_000:1_402_800_000,
        }

        for quote,want in expected.items():
            with self.subTest(quote=quote):
                self.assertEqual(
                    r._scaled_wsol_funding(
                        quote,
                        1_000_000,
                        1_002_000,
                    ),
                    want,
                )

    def test_exact_system_transfer_rewrite(self):
        ix=system_transfer("USER","WSOL_ATA",1_002_000)
        out=r._rewrite_system_transfer_lamports(
            ix,
            1_402_800_000,
        )
        self.assertEqual(
            r._system_transfer_lamports(out),
            1_402_800_000,
        )
        self.assertEqual(
            r._system_transfer_lamports(ix),
            1_002_000,
        )

    def test_find_only_user_to_wsol_transfer(self):
        ixs=[
            system_transfer("USER","WSOL_ATA",1_002_000),
            pump_ix(1_000_000),
        ]
        self.assertEqual(
            r._wsol_funding_indices(ixs,"USER",1),
            [(0,1_002_000)],
        )

    def test_bind_1p4_sol(self):
        ixs=[
            system_transfer("USER","WSOL_ATA",1_002_000),
            pump_ix(1_400_000_000),
        ]
        template=self.template()
        funding=r._bind_wsol_funding(
            ixs,
            template,
            "USER",
            1_400_000_000,
        )
        self.assertEqual(funding,1_402_800_000)
        self.assertEqual(
            r._system_transfer_lamports(ixs[0]),
            1_402_800_000,
        )
        self.assertTrue(
            r._assert_exact_size_binding(
                ixs,
                template,
                1,
                1_400_000_000,
                funding,
            )
        )

    def test_mismatch_fails_closed(self):
        ixs=[
            system_transfer("USER","WSOL_ATA",1_002_000),
            pump_ix(100_000_000),
        ]
        with self.assertRaisesRegex(
            RuntimeError,
            "SIZE_BIND_WSOL_AMOUNT_MISMATCH",
        ):
            r._assert_exact_size_binding(
                ixs,
                self.template(),
                1,
                100_000_000,
                1_002_000,
            )

    def test_no_broadcast(self):
        source=(
            r.Path(r.__file__)
            .read_text(encoding="utf-8")
        )
        self.assertIn("[BROADCAST] disabled",source)
        self.assertNotIn("sendTransaction",source)


if __name__=="__main__":
    unittest.main(verbosity=2)
