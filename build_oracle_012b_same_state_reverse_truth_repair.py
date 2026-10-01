from pathlib import Path
import py_compile

ROOT=Path.cwd()

OUTDIR=ROOT/"qseries_v2/oracle_execution"

MODULE=OUTDIR/(
    "oracle_012_bidirectional_physical_market_scanner.py"
)

TEST=ROOT/(
    "test_oracle_012b_same_state_reverse_truth_repair.py"
)

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

SELL_JS=NODEDIR/"oracle012_pump_sell.mjs"


if not MODULE.is_file():
    raise SystemExit(
        "[FAIL] ORACLE-012 module missing"
    )

if not SELL_JS.is_file():
    raise SystemExit(
        "[FAIL] ORACLE-012 Pump sell helper missing"
    )


# ============================================================
# NODE:
# Fetch Pump state ONCE.
# Build both sell instructions from the exact same state.
# ============================================================

SELL_JS.write_text(
r'''
import fs from "node:fs";
import {createRequire} from "node:module";

const require=createRequire(
  import.meta.url
);

const {
  Connection,
  PublicKey
}=require(
  "@solana/web3.js"
);

const {
  OnlinePumpAmmSdk,
  PUMP_AMM_SDK
}=require(
  "@pump-fun/pump-swap-sdk"
);

const BN=require(
  "bn.js"
);

const req=JSON.parse(
  fs.readFileSync(
    0,
    "utf8"
  )
);

const connection=
  new Connection(
    req.rpc,
    "processed"
  );

const user=
  new PublicKey(
    req.user
  );

const pool=
  new PublicKey(
    req.pool
  );

const slippage=
  Number(
    req.slippagePct
  );

const amounts=
  (
    req.baseAmounts
    ??[]
  ).map(
    x=>new BN(
      String(x)
    )
  );

if(
  amounts.length!==2
){
  throw new Error(
    "EXPECTED_TWO_BASE_AMOUNTS"
  );
}

function parsePumpSell(
  ixs,
  expectedAmount
){
  const pumpIxs=
    ixs.filter(
      ix=>
        ix.programId.toBase58()
        ===req.pumpProgram
    );

  if(
    pumpIxs.length!==1
  ){
    throw new Error(
      "PUMP_SELL_IX_COUNT:"
      +pumpIxs.length
    );
  }

  const raw=
    Buffer.from(
      pumpIxs[0].data
    );

  if(
    raw.length<24
  ){
    throw new Error(
      "PUMP_SELL_DATA_TOO_SHORT:"
      +raw.length
    );
  }

  const baseIn=
    raw.readBigUInt64LE(
      8
    );

  const minQuoteOut=
    raw.readBigUInt64LE(
      16
    );

  if(
    baseIn.toString()
    !==expectedAmount.toString()
  ){
    throw new Error(
      "PUMP_SELL_INPUT_MISMATCH:"
      +baseIn.toString()
      +":expected="
      +expectedAmount.toString()
    );
  }

  return {
    baseIn:
      baseIn.toString(),

    minQuoteOut:
      minQuoteOut.toString()
  };
}

try{

  const online=
    new OnlinePumpAmmSdk(
      connection
    );

  // ---------------------------------------------------------
  // CRITICAL:
  // ONE physical Pump state snapshot for both calculations.
  // ---------------------------------------------------------

  const state=
    await online.swapSolanaState(
      pool,
      user
    );

  const firstIxs=
    await PUMP_AMM_SDK.sellBaseInput(
      state,
      amounts[0],
      slippage
    );

  const secondIxs=
    await PUMP_AMM_SDK.sellBaseInput(
      state,
      amounts[1],
      slippage
    );

  const first=
    parsePumpSell(
      firstIxs,
      amounts[0]
    );

  const second=
    parsePumpSell(
      secondIxs,
      amounts[1]
    );

  console.log(
    JSON.stringify({
      ok:true,

      stateSnapshots:
        1,

      first,
      second
    })
  );

}catch(e){

  console.log(
    JSON.stringify({
      ok:false,

      reason:
        e?.stack
        ??e?.message
        ??String(e)
    })
  );
}
'''.strip()+"\n",
    encoding="utf-8"
)


src=MODULE.read_text(
    encoding="utf-8"
)


start=src.find(
    "def official_pump_sell(\n"
)

end=src.find(
    "\ndef evaluate_reverse(\n",
    start
)

if (
    start<0
    or end<0
):
    raise SystemExit(
        "[FAIL] ORACLE-012 Pump sell seam missing"
    )


new_func=r'''
def official_pump_sell_pair(
    user,
    pair,
    quote_token_amount,
    guaranteed_token_amount
):
    quote_token_amount=int(
        quote_token_amount
    )

    guaranteed_token_amount=int(
        guaranteed_token_amount
    )

    if (
        quote_token_amount<=0
        or guaranteed_token_amount<=0
    ):
        raise RuntimeError(
            "PUMP_SELL_NONPOSITIVE_INPUT"
        )

    if (
        guaranteed_token_amount
        >quote_token_amount
    ):
        raise RuntimeError(
            "REVERSE_TOKEN_ORDER_VIOLATION:"
            +str(
                guaranteed_token_amount
            )
            +">"
            +str(
                quote_token_amount
            )
        )

    row=node_json(
        PUMP_SELL_JS,
        {
            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "user":
                user,

            "pool":
                pair.pump_pool,

            "baseAmounts":[
                quote_token_amount,
                guaranteed_token_amount,
            ],

            "slippagePct":
                (
                    int(
                        engine.base.q87.las.q59
                        .SLIPPAGE_BPS
                    )
                    /100.0
                ),

            "pumpProgram":
                engine.base.q87.c.PUMP,
        }
    )

    if int(
        row.get(
            "stateSnapshots",
            0
        )
    )!=1:
        raise RuntimeError(
            "PUMP_STATE_NOT_SINGLE_SNAPSHOT"
        )

    first=(
        row[
            "first"
        ]
    )

    second=(
        row[
            "second"
        ]
    )

    quote_base=int(
        first[
            "baseIn"
        ]
    )

    guaranteed_base=int(
        second[
            "baseIn"
        ]
    )

    quote_min=int(
        first[
            "minQuoteOut"
        ]
    )

    guaranteed_min=int(
        second[
            "minQuoteOut"
        ]
    )

    if (
        quote_base
        !=quote_token_amount
    ):
        raise RuntimeError(
            "PUMP_QUOTE_INPUT_MISMATCH"
        )

    if (
        guaranteed_base
        !=guaranteed_token_amount
    ):
        raise RuntimeError(
            "PUMP_GUARANTEED_INPUT_MISMATCH"
        )

    # Same AMM state + larger token input MUST NOT
    # produce a smaller minimum quote output.
    if (
        quote_token_amount
        >=guaranteed_token_amount
        and quote_min
        <guaranteed_min
    ):
        raise RuntimeError(
            "PUMP_SELL_MONOTONICITY_VIOLATION:"
            +str(
                quote_min
            )
            +"<"
            +str(
                guaranteed_min
            )
        )

    return {
        "state_snapshots":
            1,

        "quote_base_in":
            quote_base,

        "quote_min_quote_out":
            quote_min,

        "guaranteed_base_in":
            guaranteed_base,

        "guaranteed_min_quote_out":
            guaranteed_min,
    }
'''

src=(
    src[:start]
    +new_func.strip()
    +"\n"
    +src[end:]
)


old=r'''        pump_quote=official_pump_sell(
            user,
            pair,
            quote_tokens
        )

        pump_guaranteed=official_pump_sell(
            user,
            pair,
            guaranteed_tokens
        )


        quote_end=int(
            pump_quote[
                "min_quote_out"
            ]
        )

        guaranteed_end=int(
            pump_guaranteed[
                "min_quote_out"
            ]
        )'''


new=r'''        pump_pair=official_pump_sell_pair(
            user,
            pair,
            quote_tokens,
            guaranteed_tokens
        )

        quote_end=int(
            pump_pair[
                "quote_min_quote_out"
            ]
        )

        guaranteed_end=int(
            pump_pair[
                "guaranteed_min_quote_out"
            ]
        )

        if guaranteed_end>quote_end:
            raise RuntimeError(
                "REVERSE_END_MONOTONICITY_VIOLATION:"
                +str(
                    guaranteed_end
                )
                +">"
                +str(
                    quote_end
                )
            )'''


if old not in src:
    raise SystemExit(
        "[FAIL] reverse double-state seam missing"
    )


src=src.replace(
    old,
    new,
    1
)


# Add state-snapshot evidence into result.
old2=r'''            "quote_end_lamports":
                quote_end,

            "guaranteed_end_lamports":
                guaranteed_end,'''


new2=r'''            "pump_state_snapshots":
                int(
                    pump_pair[
                        "state_snapshots"
                    ]
                ),

            "quote_end_lamports":
                quote_end,

            "guaranteed_end_lamports":
                guaranteed_end,'''


if old2 not in src:
    raise SystemExit(
        "[FAIL] reverse result seam missing"
    )


src=src.replace(
    old2,
    new2,
    1
)


MODULE.write_text(
    src,
    encoding="utf-8"
)


py_compile.compile(
    str(MODULE),
    doraise=True
)


TEST.write_text(
r'''
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_012_bidirectional_physical_market_scanner
    as q
)


class T(unittest.TestCase):

    def test_safety(self):

        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )


    def test_single_state_pair_api(self):

        s=inspect.getsource(
            q.official_pump_sell_pair
        )

        self.assertIn(
            "baseAmounts",
            s
        )

        self.assertIn(
            "stateSnapshots",
            s
        )


    def test_old_double_call_retired(self):

        s=inspect.getsource(
            q.evaluate_reverse
        )

        self.assertNotIn(
            "official_pump_sell(",
            s
        )

        self.assertEqual(
            s.count(
                "official_pump_sell_pair("
            ),
            1
        )


    def test_monotonicity_guard(self):

        s=inspect.getsource(
            q.official_pump_sell_pair
        )

        self.assertIn(
            "PUMP_SELL_MONOTONICITY_VIOLATION",
            s
        )


    def test_reverse_end_guard(self):

        s=inspect.getsource(
            q.evaluate_reverse
        )

        self.assertIn(
            "REVERSE_END_MONOTONICITY_VIOLATION",
            s
        )


    def test_two_directions_preserved(self):

        self.assertEqual(
            q.PUMP_TO_METEORA,
            "PUMP_TO_METEORA"
        )

        self.assertEqual(
            q.METEORA_TO_PUMP,
            "METEORA_TO_PUMP"
        )


    def test_no_broadcast(self):

        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            s=f.read()

        self.assertNotIn(
            "sendTransaction",
            s
        )

        self.assertNotIn(
            "send_once(",
            s
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
'''.strip()+"\n",
    encoding="utf-8"
)


py_compile.compile(
    str(TEST),
    doraise=True
)


print(
    "[PASS] ORACLE-012B same-state reverse truth repair installed"
)

print(
    "[PUMP] quote + guaranteed sells use ONE SDK state snapshot"
)

print(
    "[MONOTONICITY] larger token input cannot produce smaller min SOL output"
)

print(
    "[REVERSE] Meteora -> PumpSwap preserved"
)

print(
    "[FORWARD] PumpSwap -> Meteora unchanged"
)

print(
    "[REFINE_GATE] unchanged"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)