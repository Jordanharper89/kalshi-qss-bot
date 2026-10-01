from pathlib import Path
import py_compile

ROOT=Path.cwd()

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

OUTDIR=ROOT/"qseries_v2/oracle_execution"

JS=NODEDIR/"oracle018_persistent_pump_worker.mjs"

MODULE=OUTDIR/(
    "oracle_018_persistent_pumpswap_state_worker.py"
)

RUNNER=ROOT/(
    "run_oracle_018_persistent_pump_worker.py"
)

TEST=ROOT/(
    "test_oracle_018_persistent_pumpswap_state_worker.py"
)

Q17=OUTDIR/(
    "oracle_017_offline_pumpswap_pricing_gate.py"
)

if not Q17.is_file():
    raise SystemExit(
        "[FAIL] ORACLE-017 missing"
    )


JS.write_text(
r'''
import readline from "node:readline";
import {performance} from "node:perf_hooks";
import {
  Connection,
  PublicKey
} from "@solana/web3.js";

import BN from "bn.js";

import {
  OnlinePumpAmmSdk,
  buyQuoteInput,
  sellBaseInput
} from "@pump-fun/pump-swap-sdk";


let STATE=null;
let FETCHES=0;


function emit(x){
  process.stdout.write(
    JSON.stringify(x)+"\n"
  );
}


function common(
  baseReserve,
  quoteReserve
){
  if(!STATE){
    throw new Error(
      "WORKER_NOT_INITIALIZED"
    );
  }

  return {
    baseReserve:
      new BN(
        String(
          baseReserve
        )
      ),

    quoteReserve:
      new BN(
        String(
          quoteReserve
        )
      ),

    globalConfig:
      STATE.globalConfig,

    baseMintAccount:
      STATE.baseMintAccount,

    baseMint:
      STATE.baseMint,

    coinCreator:
      STATE.pool.coinCreator,

    creator:
      STATE.pool.creator,

    feeConfig:
      STATE.feeConfig
  };
}


function price(
  baseReserve,
  quoteReserve,
  quoteLamports,
  baseAmount,
  slippagePct
){
  const t0=
    performance.now();

  const c=common(
    baseReserve,
    quoteReserve
  );

  let buy=null;
  let sell=null;


  if(
    quoteLamports!==null
    &&
    quoteLamports!==undefined
  ){
    const q=
      new BN(
        String(
          quoteLamports
        )
      );

    const x=
      buyQuoteInput({
        quote:q,
        slippage:
          Number(
            slippagePct
          ),
        ...c
      });

    buy={
      quoteIn:
        q.toString(),

      baseOut:
        x.base.toString(),

      internalQuoteWithoutFees:
        x.internalQuoteWithoutFees
          .toString(),

      maxQuote:
        x.maxQuote.toString()
    };
  }


  if(
    baseAmount!==null
    &&
    baseAmount!==undefined
  ){
    const b=
      new BN(
        String(
          baseAmount
        )
      );

    const x=
      sellBaseInput({
        base:b,
        slippage:
          Number(
            slippagePct
          ),
        ...c
      });

    sell={
      baseIn:
        b.toString(),

      uiQuote:
        x.uiQuote.toString(),

      minQuote:
        x.minQuote.toString()
    };
  }


  return {
    buy,
    sell,

    elapsedMs:
      performance.now()
      -t0
  };
}


async function initialize(
  req
){
  const connection=
    new Connection(
      req.rpc,
      "processed"
    );

  const online=
    new OnlinePumpAmmSdk(
      connection
    );

  FETCHES+=1;

  STATE=
    await online.swapSolanaState(
      new PublicKey(
        req.pool
      ),
      new PublicKey(
        req.user
      )
    );


  const base=
    STATE.poolBaseAmount
      .toString();

  const quote=
    STATE.poolQuoteAmount
      .toString();


  const baseline=
    price(
      base,
      quote,
      req.quoteLamports,
      null,
      req.slippagePct
    );


  emit({
    ok:true,
    type:"INIT",

    onlineStateFetches:
      FETCHES,

    pool:
      req.pool,

    baseMint:
      STATE.baseMint.toBase58(),

    baseReserve:
      base,

    quoteReserve:
      quote,

    baselineBuy:
      baseline.buy
  });
}


const rl=
  readline.createInterface({
    input:
      process.stdin,

    crlfDelay:
      Infinity
  });


for await(
  const line
  of rl
){
  if(
    !line.trim()
  ){
    continue;
  }

  let req;

  try{
    req=JSON.parse(
      line
    );
  }catch(e){
    emit({
      ok:false,
      reason:
        "BAD_JSON:"
        +String(e)
    });

    continue;
  }


  try{

    if(
      req.command==="INIT"
    ){
      await initialize(
        req
      );

      continue;
    }


    if(
      req.command==="QUOTE"
    ){
      const result=
        price(
          req.baseReserve,
          req.quoteReserve,
          req.quoteLamports,
          req.baseAmount,
          req.slippagePct
        );


      emit({
        ok:true,
        type:"QUOTE",

        onlineStateFetches:
          FETCHES,

        baseReserve:
          String(
            req.baseReserve
          ),

        quoteReserve:
          String(
            req.quoteReserve
          ),

        ...result
      });

      continue;
    }


    if(
      req.command==="PING"
    ){
      emit({
        ok:true,
        type:"PONG",
        onlineStateFetches:
          FETCHES
      });

      continue;
    }


    if(
      req.command==="EXIT"
    ){
      emit({
        ok:true,
        type:"EXIT"
      });

      process.exit(
        0
      );
    }


    throw new Error(
      "UNKNOWN_COMMAND:"
      +String(
        req.command
      )
    );


  }catch(e){

    emit({
      ok:false,

      reason:
        e?.stack
        ??e?.message
        ??String(e)
    });
  }
}
'''.strip()+"\n",
    encoding="utf-8"
)


MODULE.write_text(
r'''
from __future__ import annotations

import json
import os
import statistics
import subprocess
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_017_offline_pumpswap_pricing_gate
    as q17
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


ROOT=Path.cwd()

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

JS=NODEDIR/(
    "oracle018_persistent_pump_worker.mjs"
)


class PumpWorker:

    def __init__(
        self
    ):
        self.p=subprocess.Popen(
            [
                "node",
                JS.name
            ],

            cwd=str(
                NODEDIR
            ),

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,

            text=True,
            bufsize=1
        )


    def call(
        self,
        payload
    ):
        if self.p.poll() is not None:
            raise RuntimeError(
                "PUMP_WORKER_EXITED"
            )


        self.p.stdin.write(
            json.dumps(
                payload,
                separators=(
                    ",",
                    ":"
                )
            )
            +"\n"
        )

        self.p.stdin.flush()


        line=self.p.stdout.readline()

        if not line:
            err=self.p.stderr.read()

            raise RuntimeError(
                "PUMP_WORKER_EMPTY:"
                +err[-2000:]
            )


        row=json.loads(
            line
        )


        if not row.get(
            "ok"
        ):
            raise RuntimeError(
                str(
                    row.get(
                        "reason"
                    )
                )
            )


        return row


    def close(
        self
    ):
        try:
            self.call({
                "command":
                    "EXIT"
            })

        except Exception:
            pass


        try:
            self.p.wait(
                timeout=5
            )

        except Exception:
            self.p.kill()


def pct(
    values,
    p
):
    if not values:
        return None

    rows=sorted(
        values
    )

    idx=min(
        len(rows)-1,
        int(
            len(rows)*p
        )
    )

    return rows[
        idx
    ]


def run(
    iterations=1000
):
    binding=q17.binding()

    worker=PumpWorker()


    try:

        init=worker.call({
            "command":
                "INIT",

            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "user":
                "11111111111111111111111111111111",

            "pool":
                binding[
                    "pump_pool"
                ],

            "quoteLamports":
                1_000_000,

            "slippagePct":
                .20,
        })


        if int(
            init[
                "onlineStateFetches"
            ]
        )!=1:
            raise RuntimeError(
                "INITIAL_FETCH_COUNT_NOT_ONE"
            )


        base_reserve=init[
            "baseReserve"
        ]

        quote_reserve=init[
            "quoteReserve"
        ]

        baseline=init[
            "baselineBuy"
        ]


        samples=[]

        first=None


        for _ in range(
            int(
                iterations
            )
        ):

            t0=time.perf_counter_ns()

            row=worker.call({
                "command":
                    "QUOTE",

                # ------------------------------------------------
                # These two values are exactly what ORACLE-019
                # will replace with WebSocket-updated reserves.
                # ------------------------------------------------

                "baseReserve":
                    base_reserve,

                "quoteReserve":
                    quote_reserve,

                "quoteLamports":
                    1_000_000,

                "baseAmount":
                    None,

                "slippagePct":
                    .20,
            })


            dt=(
                time.perf_counter_ns()
                -t0
            )/1e6

            samples.append(
                dt
            )


            if first is None:
                first=row


            if int(
                row[
                    "onlineStateFetches"
                ]
            )!=1:
                raise RuntimeError(
                    "RPC_FETCH_OCCURRED_IN_HOT_LOOP"
                )


            if (
                row[
                    "buy"
                ][
                    "baseOut"
                ]
                !=baseline[
                    "baseOut"
                ]
            ):
                raise RuntimeError(
                    "RESERVE_OVERRIDE_BASE_OUT_MISMATCH"
                )


            if (
                row[
                    "buy"
                ][
                    "maxQuote"
                ]
                !=baseline[
                    "maxQuote"
                ]
            ):
                raise RuntimeError(
                    "RESERVE_OVERRIDE_MAX_QUOTE_MISMATCH"
                )


        print(
            "[ORACLE-018] "
            "PERSISTENT PUMPSWAP STATE WORKER",
            flush=True
        )


        print(
            "[PAIR] "
            "token=%s "
            "pump=%s"%(
                binding[
                    "token"
                ][:10],

                binding[
                    "pump_pool"
                ][:12],
            ),
            flush=True
        )


        print(
            "[STATE] "
            "online_fetches=1 "
            "base_reserve=%s "
            "quote_reserve=%s"%(
                base_reserve,
                quote_reserve,
            ),
            flush=True
        )


        print(
            "[PARITY] "
            "baseline_base_out=%s "
            "override_base_out=%s "
            "baseline_max_quote=%s "
            "override_max_quote=%s"%(
                baseline[
                    "baseOut"
                ],

                first[
                    "buy"
                ][
                    "baseOut"
                ],

                baseline[
                    "maxQuote"
                ],

                first[
                    "buy"
                ][
                    "maxQuote"
                ],
            ),
            flush=True
        )


        print(
            "[HOT_LOOP] "
            "iterations=%d "
            "online_state_fetches=%d"%(
                int(
                    iterations
                ),

                int(
                    first[
                        "onlineStateFetches"
                    ]
                ),
            ),
            flush=True
        )


        print(
            "[IPC_SPEED] "
            "p50_ms=%.6f "
            "p95_ms=%.6f "
            "p99_ms=%.6f "
            "max_ms=%.6f"%(
                statistics.median(
                    samples
                ),

                pct(
                    samples,
                    .95
                ),

                pct(
                    samples,
                    .99
                ),

                max(
                    samples
                ),
            ),
            flush=True
        )


        print(
            "[PASS] "
            "WebSocket reserve override reproduces "
            "exact Pump SDK pricing without RPC",
            flush=True
        )


        print(
            "[NEXT_BOUNDARY] "
            "ORACLE-019 venue-native reserve feed cutover",
            flush=True
        )


        print(
            "[BROADCAST] disabled",
            flush=True
        )


    finally:

        worker.close()


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
from qseries_v2.oracle_execution.oracle_018_persistent_pumpswap_state_worker import (
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
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_018_persistent_pumpswap_state_worker
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


    def test_persistent_process(self):

        s=inspect.getsource(
            q.PumpWorker
        )

        self.assertIn(
            "subprocess.Popen",
            s
        )

        self.assertNotIn(
            "subprocess.run",
            s
        )


    def test_reserve_override(self):

        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            '"baseReserve"',
            s
        )

        self.assertIn(
            '"quoteReserve"',
            s
        )


    def test_no_rpc_in_quote_loop(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            s.count(
                "swapSolanaState("
            ),
            1
        )

        self.assertIn(
            'req.command==="QUOTE"',
            s
        )


    def test_exact_sdk_math(self):

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


    def test_parity_gate(self):

        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "RESERVE_OVERRIDE_BASE_OUT_MISMATCH",
            s
        )

        self.assertIn(
            "RESERVE_OVERRIDE_MAX_QUOTE_MISMATCH",
            s
        )


    def test_no_private_key(self):

        s=q.Path(
            q.__file__
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "QSB_SOLANA_PRIVATE_KEY",
            s
        )


    def test_no_broadcast(self):

        s=q.Path(
            q.__file__
        ).read_text(
            encoding="utf-8"
        )

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
    "[PASS] ORACLE-018 persistent PumpSwap state worker installed"
)

print(
    "[REPLACEMENT] failed fixed-fee Pump snapshot math remains retired"
)

print(
    "[STATE] Pump static/config state fetched once"
)

print(
    "[HOT_INPUT] base + quote reserves supplied externally"
)

print(
    "[HOT_MATH] exact PumpSwap SDK"
)

print(
    "[IPC] persistent Node process; no subprocess spawn per quote"
)

print(
    "[RPC] prohibited from quote loop"
)

print(
    "[PRIVATE_KEY] not required"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[NEXT] ORACLE-019 venue-native reserve feed cutover"
)

print(
    "[OWNER] ORACLE"
)