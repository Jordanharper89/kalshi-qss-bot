from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"runtime.py"
TEST=ROOT/"test_solana_atomic_exact_size_binding.py"

if not TARGET.is_file():
    raise RuntimeError("CANONICAL_RUNTIME_MISSING:"+str(TARGET))

src=TARGET.read_text(encoding="utf-8")

HELPER_MARKER='''def prebuild_templates(
    state,
    user
):'''

HELPERS=r'''
SYSTEM_TRANSFER_TAG=2
PUMP_TEMPLATE_QUOTE_LAMPORTS=1_000_000


def _system_transfer_lamports(ix):
    if ix.get("programId")!=q87.c.SYSTEM:
        return None

    try:
        raw=base64.b64decode(
            ix.get("data") or ""
        )
    except Exception:
        return None

    if len(raw)<12:
        return None

    tag=struct.unpack(
        "<I",
        raw[:4],
    )[0]

    if tag!=SYSTEM_TRANSFER_TAG:
        return None

    return int(
        struct.unpack(
            "<Q",
            raw[4:12],
        )[0]
    )


def _rewrite_system_transfer_lamports(
    ix,
    lamports,
):
    amount=_system_transfer_lamports(ix)

    if amount is None:
        raise RuntimeError(
            "SIZE_BIND_NOT_SYSTEM_TRANSFER"
        )

    out=copy.deepcopy(ix)

    raw=bytearray(
        base64.b64decode(
            out.get("data")
            or ""
        )
    )

    raw[4:12]=struct.pack(
        "<Q",
        int(lamports),
    )

    out["data"]=base64.b64encode(
        bytes(raw)
    ).decode()

    return out


def _wsol_funding_indices(
    ixs,
    user,
    pump_index,
):
    wsol_ata=q87.c.ata(
        user,
        q87.c.WSOL,
        q87.c.TOKEN,
    )

    rows=[]

    for i,ix in enumerate(ixs):
        if i>=int(pump_index):
            break

        amount=_system_transfer_lamports(ix)

        if amount is None:
            continue

        accounts=list(
            ix.get("accounts")
            or []
        )

        if len(accounts)<2:
            continue

        source=str(
            accounts[0].get("pubkey")
            or ""
        )

        dest=str(
            accounts[1].get("pubkey")
            or ""
        )

        if (
            source==str(user)
            and dest==str(wsol_ata)
        ):
            rows.append(
                (i,int(amount))
            )

    if len(rows)!=1:
        raise RuntimeError(
            "SIZE_BIND_WSOL_TRANSFER_COUNT:"
            +str(len(rows))
        )

    return rows


def _scaled_wsol_funding(
    quote_lamports,
    template_quote_lamports,
    template_funding_lamports,
):
    quote_lamports=int(quote_lamports)
    template_quote_lamports=int(
        template_quote_lamports
    )
    template_funding_lamports=int(
        template_funding_lamports
    )

    if (
        quote_lamports<=0
        or template_quote_lamports<=0
        or template_funding_lamports
        <template_quote_lamports
    ):
        raise RuntimeError(
            "SIZE_BIND_BAD_FUNDING_ENVELOPE"
        )

    return (
        quote_lamports
        *template_funding_lamports
        +template_quote_lamports
        -1
    )//template_quote_lamports


def _bind_wsol_funding(
    ixs,
    template,
    user,
    quote_lamports,
):
    rows=list(
        template.get(
            "wsol_funding_rows"
        )
        or []
    )

    if len(rows)!=1:
        raise RuntimeError(
            "SIZE_BIND_TEMPLATE_FUNDING_ROWS:"
            +str(len(rows))
        )

    index=int(rows[0]["index"])

    if (
        index<0
        or index>=len(ixs)
    ):
        raise RuntimeError(
            "SIZE_BIND_FUNDING_INDEX_RANGE"
        )

    template_amount=int(
        rows[0][
            "template_lamports"
        ]
    )

    expected=_scaled_wsol_funding(
        int(quote_lamports),
        int(
            template[
                "template_quote_lamports"
            ]
        ),
        template_amount,
    )

    ixs[index]=(
        _rewrite_system_transfer_lamports(
            ixs[index],
            expected,
        )
    )

    actual=_system_transfer_lamports(
        ixs[index]
    )

    if int(actual or -1)!=expected:
        raise RuntimeError(
            "SIZE_BIND_FUNDING_REWRITE_DRIFT:"
            +str(actual)
            +"/"
            +str(expected)
        )

    return expected


def _pump_spendable_quote(ix):
    raw=base64.b64decode(
        ix.get("data")
        or ""
    )

    if len(raw)<16:
        raise RuntimeError(
            "SIZE_BIND_PUMP_DATA_SHORT"
        )

    disc=bytes(raw[:8])

    if disc!=BUY_EXACT_QUOTE_IN_DISC:
        raise RuntimeError(
            "SIZE_BIND_PUMP_NOT_EXACT_QUOTE_IN:"
            +disc.hex()
        )

    return int(
        struct.unpack(
            "<Q",
            raw[8:16],
        )[0]
    )


def _assert_exact_size_binding(
    ixs,
    template,
    pump_index,
    quote_lamports,
    funding_lamports,
):
    quote_lamports=int(
        quote_lamports
    )

    pump_amount=_pump_spendable_quote(
        ixs[int(pump_index)]
    )

    if pump_amount!=quote_lamports:
        raise RuntimeError(
            "SIZE_BIND_PUMP_AMOUNT_MISMATCH:"
            +str(pump_amount)
            +"/"
            +str(quote_lamports)
        )

    expected_funding=(
        _scaled_wsol_funding(
            quote_lamports,
            int(
                template[
                    "template_quote_lamports"
                ]
            ),
            int(
                template[
                    "wsol_funding_rows"
                ][0][
                    "template_lamports"
                ]
            ),
        )
    )

    if int(funding_lamports)!=expected_funding:
        raise RuntimeError(
            "SIZE_BIND_WSOL_AMOUNT_MISMATCH:"
            +str(funding_lamports)
            +"/"
            +str(expected_funding)
        )

    if int(funding_lamports)<quote_lamports:
        raise RuntimeError(
            "SIZE_BIND_WSOL_UNDERFUNDED"
        )

    print(
        "[SIZE_BIND] "
        "quoted_size=%.3f "
        "spendable_quote_lamports=%d "
        "wsol_funding_lamports=%d "
        "template_quote=%d "
        "template_funding=%d "
        "status=PASS"
        %(
            quote_lamports/1e9,
            pump_amount,
            int(funding_lamports),
            int(
                template[
                    "template_quote_lamports"
                ]
            ),
            int(
                template[
                    "wsol_funding_rows"
                ][0][
                    "template_lamports"
                ]
            ),
        ),
        flush=True,
    )

    return True


'''

if "def _assert_exact_size_binding(" not in src:
    if HELPER_MARKER not in src:
        raise RuntimeError(
            "SIZE_BIND_HELPER_INSERT_MARKER_NOT_FOUND"
        )
    src=src.replace(
        HELPER_MARKER,
        HELPERS+"\n\n"+HELPER_MARKER,
        1,
    )

OLD_TEMPLATE=r'''                pos=pump_ix_position(
                    ixs
                )

                TEMPLATES[
                    token
                ]={
                    "pump_pool":
                        pool,

                    "instructions":[
                        copy.deepcopy(x)
                        for x in ixs
                    ],

                    "pump_index":
                        int(pos),
                }'''

NEW_TEMPLATE=r'''                pos=pump_ix_position(
                    ixs
                )

                funding_rows=[
                    {
                        "index":int(i),
                        "template_lamports":
                            int(amount),
                    }
                    for i,amount in
                    _wsol_funding_indices(
                        ixs,
                        user,
                        pos,
                    )
                ]

                TEMPLATES[
                    token
                ]={
                    "pump_pool":
                        pool,

                    "instructions":[
                        copy.deepcopy(x)
                        for x in ixs
                    ],

                    "pump_index":
                        int(pos),

                    "template_quote_lamports":
                        int(
                            PUMP_TEMPLATE_QUOTE_LAMPORTS
                        ),

                    "wsol_funding_rows":
                        funding_rows,
                }'''

if '"wsol_funding_rows":' not in src:
    if OLD_TEMPLATE not in src:
        raise RuntimeError(
            "SIZE_BIND_TEMPLATE_BLOCK_NOT_FOUND"
        )
    src=src.replace(
        OLD_TEMPLATE,
        NEW_TEMPLATE,
        1,
    )

OLD_ROUTE=r'''    ixs[
        pump_index
    ]=rewrite_pump_buy_bounds(
        ixs[
            pump_index
        ],
        start,
        base_out,
    )

    pump_ix=ixs[
        pump_index
    ]'''

NEW_ROUTE=r'''    ixs[
        pump_index
    ]=rewrite_pump_buy_bounds(
        ixs[
            pump_index
        ],
        start,
        base_out,
    )

    funding_lamports=(
        _bind_wsol_funding(
            ixs,
            template,
            user,
            start,
        )
    )

    _assert_exact_size_binding(
        ixs,
        template,
        pump_index,
        start,
        funding_lamports,
    )

    pump_ix=ixs[
        pump_index
    ]'''

if "funding_lamports=(" not in src:
    if OLD_ROUTE not in src:
        raise RuntimeError(
            "SIZE_BIND_ROUTE_BLOCK_NOT_FOUND"
        )
    src=src.replace(
        OLD_ROUTE,
        NEW_ROUTE,
        1,
    )

STARTUP_OLD=r'''    print(
        "[PUMP_EXECUTION_BOUND] "
        "BuyExactQuoteIn rewritten from exact "
        "same-snapshot spendableQuote + minBaseOut",
        flush=True,
    )'''

STARTUP_NEW=r'''    print(
        "[PUMP_EXECUTION_BOUND] "
        "BuyExactQuoteIn rewritten from exact "
        "same-snapshot spendableQuote + minBaseOut",
        flush=True,
    )

    print(
        "[TX_SIZE_BINDING] "
        "Pump spendableQuote=selected_size "
        "WSOL funding=SDK template ratio scaled to selected_size "
        "hot_path_rpc=FALSE hot_path_node=FALSE",
        flush=True,
    )'''

if "[TX_SIZE_BINDING]" not in src:
    if STARTUP_OLD not in src:
        raise RuntimeError(
            "SIZE_BIND_STARTUP_MARKER_NOT_FOUND"
        )
    src=src.replace(
        STARTUP_OLD,
        STARTUP_NEW,
        1,
    )

ast.parse(src)
TARGET.write_text(src,encoding="utf-8")

TEST_CODE=r'''import base64
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
'''

ast.parse(TEST_CODE)
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] canonical runtime exact transaction-size binding installed")
print("[ROOT_CAUSE] startup PumpSwap template was fixed at 1,000,000 quote lamports")
print("[ROOT_CAUSE] Pump instruction changed live but WSOL System transfer stayed at startup size")
print("[SIZE_BIND] Pump spendableQuoteIn now equals selected opportunity start_lamports")
print("[SIZE_BIND] WSOL funding preserves SDK startup funding/slippage ratio at selected size")
print("[HOT_PATH] no Node/RPC added per opportunity")
print("[FAIL_CLOSED] helper transfer and Pump spendable amount are physically asserted")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
