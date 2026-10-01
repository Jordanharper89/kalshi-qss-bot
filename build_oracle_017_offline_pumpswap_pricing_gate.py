from pathlib import Path
import py_compile

ROOT=Path.cwd()

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

OUTDIR=ROOT/"qseries_v2/oracle_execution"

JS=NODEDIR/"oracle017_offline_pump_gate.mjs"
MODULE=OUTDIR/"oracle_017_offline_pumpswap_pricing_gate.py"
RUNNER=ROOT/"run_oracle_017_offline_pump_gate.py"
TEST=ROOT/"test_oracle_017_offline_pumpswap_pricing_gate.py"

BINDINGS=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_014_fast_lane_bindings.json"
)

NODEDIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTDIR.mkdir(
    parents=True,
    exist_ok=True
)


JS.write_text(
r'''
import fs from "node:fs";
import { performance } from "node:perf_hooks";
import { Connection, PublicKey } from "@solana/web3.js";
import BN from "bn.js";

import {
  OnlinePumpAmmSdk,
  buyQuoteInput,
  sellBaseInput
} from "@pump-fun/pump-swap-sdk";


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


const online=
  new OnlinePumpAmmSdk(
    connection
  );


const poolKey=
  new PublicKey(
    req.pool
  );


const user=
  new PublicKey(
    req.user
  );


const quoteIn=
  new BN(
    String(
      req.quoteLamports
    )
  );


const slippage=
  Number(
    req.slippagePct
  );


const state=
  await online.swapSolanaState(
    poolKey,
    user
  );


const common=()=>({
  baseReserve:
    state.poolBaseAmount,

  quoteReserve:
    state.poolQuoteAmount,

  globalConfig:
    state.globalConfig,

  baseMintAccount:
    state.baseMintAccount,

  baseMint:
    state.baseMint,

  coinCreator:
    state.pool.coinCreator,

  creator:
    state.pool.creator,

  feeConfig:
    state.feeConfig
});


function exactBuy(
  amount
){
  return buyQuoteInput({
    quote:
      amount,

    slippage,

    ...common()
  });
}


function exactSell(
  amount
){
  return sellBaseInput({
    base:
      amount,

    slippage,

    ...common()
  });
}


// ----------------------------------------------------------
// ONE online state acquisition above.
//
// Everything below is pure SDK pricing from already-loaded
// Pump state. No Connection is passed into these functions.
// ----------------------------------------------------------

const firstBuy=
  exactBuy(
    quoteIn
  );


if(
  firstBuy.base.lte(
    new BN(0)
  )
){
  throw new Error(
    "OFFLINE_BUY_ZERO"
  );
}


const firstSell=
  exactSell(
    firstBuy.base
  );


if(
  firstSell.uiQuote.lte(
    new BN(0)
  )
){
  throw new Error(
    "OFFLINE_SELL_ZERO"
  );
}


const iterations=
  Number(
    req.iterations
    ??1000
  );


const samples=[];


for(
  let i=0;
  i<iterations;
  i++
){

  const t0=
    performance.now();


  const b=
    exactBuy(
      quoteIn
    );


  const s=
    exactSell(
      b.base
    );


  const dt=
    performance.now()
    -t0;


  samples.push(
    dt
  );


  if(
    b.base.lte(
      new BN(0)
    )
    ||
    s.uiQuote.lte(
      new BN(0)
    )
  ){
    throw new Error(
      "OFFLINE_PRICING_NONPOSITIVE"
    );
  }
}


samples.sort(
  (
    a,
    b
  )=>a-b
);


function percentile(
  p
){
  if(
    !samples.length
  ){
    return null;
  }

  const idx=
    Math.min(
      samples.length-1,
      Math.floor(
        samples.length*p
      )
    );

  return samples[
    idx
  ];
}


console.log(
  JSON.stringify({
    ok:
      true,

    mode:
      "OFFLINE_PUMP_PRICING",

    onlineStateFetches:
      1,

    offlineIterations:
      iterations,

    pool:
      req.pool,

    baseMint:
      state.baseMint.toBase58(),

    baseReserve:
      state.poolBaseAmount.toString(),

    quoteReserve:
      state.poolQuoteAmount.toString(),

    quoteInput:
      quoteIn.toString(),

    buyBaseOut:
      firstBuy.base.toString(),

    buyInternalQuoteWithoutFees:
      firstBuy
        .internalQuoteWithoutFees
        .toString(),

    buyMaxQuote:
      firstBuy.maxQuote.toString(),

    sellBaseIn:
      firstBuy.base.toString(),

    sellUiQuote:
      firstSell.uiQuote.toString(),

    sellMinQuote:
      firstSell.minQuote.toString(),

    pureRoundTripNetLamports:
      firstSell.uiQuote
        .sub(
          quoteIn
        )
        .toString(),

    p50Ms:
      percentile(
        .50
      ),

    p95Ms:
      percentile(
        .95
      ),

    p99Ms:
      percentile(
        .99
      ),

    maxMs:
      (
        samples[
          samples.length-1
        ]
        ??null
      )
  })
);
'''.strip()+"\n",
    encoding="utf-8"
)


MODULE.write_text(
r'''
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


ROOT=Path.cwd()

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

JS=NODEDIR/(
    "oracle017_offline_pump_gate.mjs"
)

BINDINGS=ROOT/(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_014_fast_lane_bindings.json"
)


def binding():
    if not BINDINGS.is_file():
        raise RuntimeError(
            "ORACLE014_BINDINGS_MISSING"
        )

    data=json.loads(
        BINDINGS.read_text(
            encoding="utf-8"
        )
    )

    rows=(
        data.get(
            "rows"
        )
        or []
    )

    for row in rows:

        pool=row.get(
            "pump_pool"
        )

        token=row.get(
            "token"
        )

        if pool and token:

            return {
                "token":
                    token,

                "pump_pool":
                    pool,
            }

    raise RuntimeError(
        "NO_PUMP_BINDING"
    )


def run():
    b=binding()

    req={
        "rpc":
            os.getenv(
                "SOLANA_RPC_URL",
                "https://api.mainnet-beta.solana.com"
            ),

        # Valid public key only.
        # No signer/private key required for this gate.
        "user":
            "11111111111111111111111111111111",

        "pool":
            b[
                "pump_pool"
            ],

        "quoteLamports":
            1_000_000,

        "slippagePct":
            .20,

        "iterations":
            1000,
    }


    p=subprocess.run(
        [
            "node",
            JS.name
        ],

        cwd=str(
            NODEDIR
        ),

        input=json.dumps(
            req
        ),

        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,

        text=True,
        timeout=90,
    )


    if p.returncode!=0:

        raise RuntimeError(
            "ORACLE017_NODE_FAIL:"
            +p.stderr[-3000:]
        )


    lines=[
        x
        for x in p.stdout.splitlines()
        if x.strip()
    ]


    if not lines:

        raise RuntimeError(
            "ORACLE017_EMPTY_OUTPUT"
        )


    row=json.loads(
        lines[-1]
    )


    if not row.get(
        "ok"
    ):

        raise RuntimeError(
            "ORACLE017_OFFLINE_FAIL"
        )


    if int(
        row[
            "onlineStateFetches"
        ]
    )!=1:

        raise RuntimeError(
            "ONLINE_FETCH_COUNT_NOT_ONE"
        )


    if int(
        row[
            "offlineIterations"
        ]
    )<1000:

        raise RuntimeError(
            "OFFLINE_LOOP_TOO_SMALL"
        )


    print(
        "[ORACLE-017] "
        "OFFLINE PUMPSWAP PRICING GATE",
        flush=True
    )


    print(
        "[PAIR] "
        "token=%s "
        "pump=%s"%(
            b[
                "token"
            ][:10],

            b[
                "pump_pool"
            ][:12],
        ),
        flush=True
    )


    print(
        "[STATE_FETCH] "
        "online_once=%d"%(
            row[
                "onlineStateFetches"
            ]
        ),
        flush=True
    )


    print(
        "[OFFLINE_ITERATIONS] %d"%(
            row[
                "offlineIterations"
            ]
        ),
        flush=True
    )


    print(
        "[PUMP_BUY] "
        "quote_in=%s "
        "base_out=%s "
        "max_quote=%s"%(
            row[
                "quoteInput"
            ],

            row[
                "buyBaseOut"
            ],

            row[
                "buyMaxQuote"
            ],
        ),
        flush=True
    )


    print(
        "[PUMP_SELL] "
        "base_in=%s "
        "ui_quote=%s "
        "min_quote=%s"%(
            row[
                "sellBaseIn"
            ],

            row[
                "sellUiQuote"
            ],

            row[
                "sellMinQuote"
            ],
        ),
        flush=True
    )


    print(
        "[PURE_PUMP_ROUNDTRIP] "
        "net_lamports=%s"%(
            row[
                "pureRoundTripNetLamports"
            ]
        ),
        flush=True
    )


    print(
        "[OFFLINE_SPEED] "
        "p50_ms=%.6f "
        "p95_ms=%.6f "
        "p99_ms=%.6f "
        "max_ms=%.6f"%(
            float(
                row[
                    "p50Ms"
                ]
            ),

            float(
                row[
                    "p95Ms"
                ]
            ),

            float(
                row[
                    "p99Ms"
                ]
            ),

            float(
                row[
                    "maxMs"
                ]
            ),
        ),
        flush=True
    )


    print(
        "[PASS] "
        "PumpSwap exact SDK pricing runs "
        "offline after one state acquisition",
        flush=True
    )


    print(
        "[NEXT_BOUNDARY] "
        "feed WebSocket-updated reserves into "
        "this exact SDK math",
        flush=True
    )


    print(
        "[BROADCAST] disabled",
        flush=True
    )


    return 0


if __name__=="__main__":
    raise SystemExit(
        run()
    )
'''.strip()+"\n",
    encoding="utf-8"
)


RUNNER.write_text(
r'''
from qseries_v2.oracle_execution.oracle_017_offline_pumpswap_pricing_gate import (
    run
)

if __name__=="__main__":
    raise SystemExit(
        run()
    )
'''.strip()+"\n",
    encoding="utf-8"
)


TEST.write_text(
r'''
import unittest
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_017_offline_pumpswap_pricing_gate
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

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


    def test_no_private_key(self):

        s=Path(
            q.__file__
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "QSB_SOLANA_PRIVATE_KEY",
            s
        )

        self.assertNotIn(
            "sendTransaction",
            s
        )


    def test_offline_helper_exists(self):

        self.assertTrue(
            q.JS.is_file()
        )


    def test_exact_sdk_exports(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "buyQuoteInput",
            s
        )

        self.assertIn(
            "sellBaseInput",
            s
        )

        self.assertIn(
            "OnlinePumpAmmSdk",
            s
        )


    def test_single_online_state_fetch(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            s.count(
                "swapSolanaState("
            ),
            1
        )


    def test_large_offline_loop(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "offlineIterations",
            s
        )

        self.assertIn(
            "p99Ms",
            s
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
'''.strip()+"\n",
    encoding="utf-8"
)


for p in (
    MODULE,
    RUNNER,
    TEST,
):
    py_compile.compile(
        str(p),
        doraise=True
    )


print(
    "[PASS] ORACLE-017 offline PumpSwap pricing gate installed"
)

print(
    "[RETIRED] fixed 120-bps reserve approximation"
)

print(
    "[SDK] exact buyQuoteInput + sellBaseInput"
)

print(
    "[STATE] one online acquisition"
)

print(
    "[HOT_MATH] 1000 offline SDK round trips"
)

print(
    "[PRIVATE_KEY] not required"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)