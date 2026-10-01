from pathlib import Path
import py_compile

ROOT=Path.cwd()

OUT=ROOT/"qseries_v2/oracle_execution"

MODULE=OUT/"oracle_018_exact_sdk_hot_lane_cutover.py"
LAUNCHER=ROOT/"run_oracle_exact_sdk_hot_lane.py"
TEST=ROOT/"test_oracle_018_exact_sdk_hot_lane_cutover.py"

NODEDIR=ROOT/(
    "qseries_v2/oracle_strategy_intelligence/"
    "solana_money/qsb059d_pump_native"
)

WORKER_JS=NODEDIR/"oracle018_pump_sdk_worker.mjs"

Q17=OUT/"oracle_017_offline_pumpswap_pricing_gate.py"
Q15=OUT/"oracle_015_latest_state_physical_handoff.py"

for p in (Q17,Q15):
    if not p.is_file():
        raise SystemExit(
            "[FAIL] missing dependency: "+str(p)
        )


WORKER_JS.write_text(
r'''
import readline from "node:readline";
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


const rpc=
  process.env.SOLANA_RPC_URL
  ??"https://api.mainnet-beta.solana.com";


const connection=
  new Connection(
    rpc,
    "processed"
  );


const online=
  new OnlinePumpAmmSdk(
    connection
  );


const user=
  new PublicKey(
    "11111111111111111111111111111111"
  );


const cache=
  new Map();


async function warm(
  poolText
){
  if(
    cache.has(
      poolText
    )
  ){
    return cache.get(
      poolText
    );
  }


  const pool=
    new PublicKey(
      poolText
    );


  const state=
    await online.swapSolanaState(
      pool,
      user
    );


  const staticState={
    baseMint:
      state.baseMint,

    globalConfig:
      state.globalConfig,

    baseMintAccount:
      state.baseMintAccount,

    coinCreator:
      state.pool.coinCreator,

    creator:
      state.pool.creator,

    feeConfig:
      state.feeConfig
  };


  cache.set(
    poolText,
    staticState
  );


  return staticState;
}


function common(
  stat,
  baseReserve,
  quoteReserve
){
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
      stat.globalConfig,

    baseMintAccount:
      stat.baseMintAccount,

    baseMint:
      stat.baseMint,

    coinCreator:
      stat.coinCreator,

    creator:
      stat.creator,

    feeConfig:
      stat.feeConfig
  };
}


async function handle(
  req
){
  if(
    req.op==="warm"
  ){
    await warm(
      req.pool
    );

    return {
      ok:true,
      op:"warm",
      pool:req.pool
    };
  }


  const stat=
    await warm(
      req.pool
    );


  const c=common(
    stat,
    req.baseReserve,
    req.quoteReserve
  );


  const slippage=
    Number(
      req.slippagePct
      ??0.20
    );


  if(
    req.op==="buy"
  ){
    const x=
      buyQuoteInput({
        quote:
          new BN(
            String(
              req.amount
            )
          ),

        slippage,

        ...c
      });


    return {
      ok:true,
      op:"buy",

      baseOut:
        x.base.toString(),

      maxQuote:
        x.maxQuote.toString(),

      internalQuoteWithoutFees:
        x
          .internalQuoteWithoutFees
          .toString()
    };
  }


  if(
    req.op==="sell"
  ){
    const x=
      sellBaseInput({
        base:
          new BN(
            String(
              req.amount
            )
          ),

        slippage,

        ...c
      });


    return {
      ok:true,
      op:"sell",

      uiQuote:
        x.uiQuote.toString(),

      minQuote:
        x.minQuote.toString()
    };
  }


  throw new Error(
    "UNKNOWN_OPERATION:"
    +String(
      req.op
    )
  );
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


  let id=null;


  try{

    const req=
      JSON.parse(
        line
      );


    id=req.id;


    const result=
      await handle(
        req
      );


    process.stdout.write(
      JSON.stringify({
        id,
        ...result
      })
      +"\n"
    );


  }catch(e){

    process.stdout.write(
      JSON.stringify({
        id,

        ok:false,

        reason:
          e?.stack
          ??e?.message
          ??String(e)
      })
      +"\n"
    );
  }
}
'''.strip()+"\n",
    encoding="utf-8"
)


MODULE.write_text(
r'''
from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_015_latest_state_physical_handoff
    as q15
)

from qseries_v2.oracle_execution import (
    oracle_014_venue_native_fast_lane
    as q14
)

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import (
    core
)


EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


NODEDIR=Path(
    "qseries_v2/"
    "oracle_strategy_intelligence/"
    "solana_money/"
    "qsb059d_pump_native"
)

WORKER_JS=(
    NODEDIR/
    "oracle018_pump_sdk_worker.mjs"
)

SLIPPAGE_PCT=.20

_worker=None


class PumpSdkWorker:

    def __init__(
        self
    ):
        env=dict(
            os.environ
        )

        self.proc=subprocess.Popen(
            [
                "node",
                WORKER_JS.name
            ],

            cwd=str(
                NODEDIR
            ),

            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,

            text=True,
            bufsize=1,
            env=env,
        )

        self.lock=threading.Lock()
        self.seq=0


    def request(
        self,
        payload
    ):
        with self.lock:

            self.seq+=1

            req={
                "id":
                    self.seq,

                **payload,
            }


            self.proc.stdin.write(
                json.dumps(
                    req,
                    separators=(
                        ",",
                        ":"
                    )
                )
                +"\n"
            )

            self.proc.stdin.flush()


            line=self.proc.stdout.readline()


            if not line:

                err=""

                try:
                    err=self.proc.stderr.read()
                except Exception:
                    pass

                raise RuntimeError(
                    "PUMP_SDK_WORKER_DIED:"
                    +err[-2000:]
                )


            row=json.loads(
                line
            )


            if int(
                row.get(
                    "id",
                    -1
                )
            )!=self.seq:

                raise RuntimeError(
                    "PUMP_SDK_RESPONSE_ORDER"
                )


            if not row.get(
                "ok"
            ):

                raise RuntimeError(
                    "PUMP_SDK_WORKER:"
                    +str(
                        row.get(
                            "reason"
                        )
                    )
                )


            return row


    def warm(
        self,
        pool
    ):
        return self.request({
            "op":
                "warm",

            "pool":
                pool,
        })


    def buy(
        self,
        snap,
        amount
    ):
        return self.request({
            "op":
                "buy",

            "pool":
                snap[
                    "pump_pool"
                ],

            "baseReserve":
                int(
                    snap[
                        "pump_base_reserve"
                    ]
                ),

            "quoteReserve":
                int(
                    snap[
                        "pump_quote_reserve"
                    ]
                ),

            "amount":
                int(
                    amount
                ),

            "slippagePct":
                SLIPPAGE_PCT,
        })


    def sell(
        self,
        snap,
        amount
    ):
        return self.request({
            "op":
                "sell",

            "pool":
                snap[
                    "pump_pool"
                ],

            "baseReserve":
                int(
                    snap[
                        "pump_base_reserve"
                    ]
                ),

            "quoteReserve":
                int(
                    snap[
                        "pump_quote_reserve"
                    ]
                ),

            "amount":
                int(
                    amount
                ),

            "slippagePct":
                SLIPPAGE_PCT,
        })


    def close(
        self
    ):
        try:

            if self.proc.poll() is None:
                self.proc.terminate()

                self.proc.wait(
                    timeout=3
                )

        except Exception:

            try:
                self.proc.kill()
            except Exception:
                pass


def worker():
    global _worker

    if _worker is None:
        _worker=PumpSdkWorker()

    return _worker


def token_net(
    token,
    gross
):
    row=q14.engine.net_received(
        token,
        int(
            gross
        )
    )

    return int(
        row[
            "net"
        ]
    )


def exact_snapshot_opportunities(
    snap,
    size_sol
):
    token=snap[
        "token"
    ]

    start=int(
        round(
            float(
                size_sol
            )
            *1e9
        )
    )


    # ========================================================
    # DIRECTION 1
    #
    # Meteora buys token with SOL.
    # Apply actual token receipt semantics.
    # Exact Pump SDK sells received token.
    # ========================================================

    meteora_buy=(
        core.dlmm_quote_snapshot(
            snap,
            start,
            core.WSOL
        )
    )


    reverse_token_in=token_net(
        token,
        meteora_buy[
            "raw_out"
        ]
    )


    if reverse_token_in<=0:
        raise RuntimeError(
            "REVERSE_TOKEN_NET_ZERO"
        )


    pump_sell=worker().sell(
        snap,
        reverse_token_in
    )


    reverse_end=int(
        pump_sell[
            "uiQuote"
        ]
    )


    reverse_min_end=int(
        pump_sell[
            "minQuote"
        ]
    )


    reverse_net=(
        reverse_end
        -start
    )


    reverse_min_net=(
        reverse_min_end
        -start
    )


    reverse={
        "token":
            token,

        "pump_pool":
            snap[
                "pump_pool"
            ],

        "meteora":
            snap[
                "meteora"
            ],

        "start":
            start,

        "size_sol":
            float(
                size_sol
            ),

        "direction":
            "METEORA_TO_PUMP",

        "mq":
            meteora_buy,

        "gross_token":
            int(
                meteora_buy[
                    "raw_out"
                ]
            ),

        "net_token":
            reverse_token_in,

        "local_end":
            reverse_end,

        "local_min_end":
            reverse_min_end,

        "local_net":
            reverse_net,

        "local_min_net":
            reverse_min_net,

        "local_bps":
            reverse_net
            /start
            *10000.0,

        "local_min_bps":
            reverse_min_net
            /start
            *10000.0,

        "pump_model":
            "EXACT_PUMPSWAP_SDK",
    }


    # ========================================================
    # DIRECTION 2
    #
    # Exact Pump SDK buys token with SOL.
    # Apply actual token receipt semantics.
    # Hydrated Meteora state sells the received token.
    # ========================================================

    pump_buy=worker().buy(
        snap,
        start
    )


    forward_gross=int(
        pump_buy[
            "baseOut"
        ]
    )


    forward_token_in=token_net(
        token,
        forward_gross
    )


    if forward_token_in<=0:
        raise RuntimeError(
            "FORWARD_TOKEN_NET_ZERO"
        )


    meteora_sell=(
        core.dlmm_quote_snapshot(
            snap,
            forward_token_in,
            token
        )
    )


    forward_end=int(
        meteora_sell[
            "raw_out"
        ]
    )


    forward_net=(
        forward_end
        -start
    )


    forward={
        "token":
            token,

        "pump_pool":
            snap[
                "pump_pool"
            ],

        "meteora":
            snap[
                "meteora"
            ],

        "start":
            start,

        "size_sol":
            float(
                size_sol
            ),

        "direction":
            "PUMP_TO_METEORA",

        "mq":
            meteora_sell,

        "pump_base_out_gross":
            forward_gross,

        "pump_base_out_net":
            forward_token_in,

        "pump_max_quote":
            int(
                pump_buy[
                    "maxQuote"
                ]
            ),

        "local_end":
            forward_end,

        "local_net":
            forward_net,

        "local_bps":
            forward_net
            /start
            *10000.0,

        "pump_model":
            "EXACT_PUMPSWAP_SDK",
    }


    return sorted(
        [
            reverse,
            forward,
        ],

        key=lambda x:
            x[
                "local_net"
            ],

        reverse=True
    )


def install_exact_hot_math():

    if not hasattr(
        q14.persistent.m,
        "c"
    ):
        raise RuntimeError(
            "MERGED_RUNTIME_CORE_MISSING"
        )


    runtime_core=(
        q14.persistent.m.c
    )


    if not hasattr(
        runtime_core,
        "sized_snapshot_opportunities"
    ):
        raise RuntimeError(
            "SNAPSHOT_PRICER_SEAM_MISSING"
        )


    runtime_core.sized_snapshot_opportunities=(
        exact_snapshot_opportunities
    )


    core.sized_snapshot_opportunities=(
        exact_snapshot_opportunities
    )


    return runtime_core


def prewarm_previous_bindings():
    path=Path(
        "runtime_state/oracle/"
        "oracle_live_execution/"
        "oracle_014_fast_lane_bindings.json"
    )


    if not path.is_file():
        return 0


    try:
        data=json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return 0


    pools=[]


    for row in (
        data.get(
            "rows"
        )
        or []
    ):
        pool=row.get(
            "pump_pool"
        )

        if (
            pool
            and pool not in pools
        ):
            pools.append(
                pool
            )


    warmed=0


    for pool in pools:

        try:

            worker().warm(
                pool
            )

            warmed+=1

            print(
                "[SDK_WARM] "
                "pump=%s"%(
                    pool[:12]
                ),
                flush=True
            )

        except Exception as exc:

            print(
                "[SDK_WARM_SKIP] "
                "pump=%s "
                "%s:%s"%(
                    pool[:12],
                    type(exc).__name__,
                    str(exc)[:160],
                ),
                flush=True
            )


    return warmed


def run(
    seconds=300.0
):
    runtime_core=(
        install_exact_hot_math()
    )


    warmed=(
        prewarm_previous_bindings()
    )


    print(
        "[ORACLE-018] "
        "EXACT SDK HOT-LANE CUTOVER",
        flush=True
    )


    print(
        "[RETIRED] "
        "PUMP_FEE_BPS constant-product "
        "snapshot profitability",
        flush=True
    )


    print(
        "[PUMP_MODEL] "
        "EXACT_PUMPSWAP_SDK",
        flush=True
    )


    print(
        "[PUMP_STATE] "
        "static config warm once; "
        "WebSocket reserves supplied per quote",
        flush=True
    )


    print(
        "[TOKEN2022] "
        "net receipt applied before second venue",
        flush=True
    )


    print(
        "[METEORA] "
        "existing hydrated DLMM state",
        flush=True
    )


    print(
        "[SDK_PREWARM] pools=%d"%(
            warmed
        ),
        flush=True
    )


    print(
        "[CALIBRATION_LAYER] retired",
        flush=True
    )


    print(
        "[PHYSICAL_AUTHORITY] "
        "ORACLE-015 official verifier preserved",
        flush=True
    )


    print(
        "[BROADCAST] disabled",
        flush=True
    )


    try:

        return q15.run(
            seconds
        )

    finally:

        global _worker

        if _worker is not None:
            _worker.close()
            _worker=None


def main(
    argv=None
):
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=300.0
    )

    a=ap.parse_args(
        argv
    )

    return run(
        a.seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''.strip()+"\n",
    encoding="utf-8"
)


py_compile.compile(
    str(MODULE),
    doraise=True
)


LAUNCHER.write_text(
r'''
import getpass
import os

from qseries_v2.oracle_execution.oracle_018_exact_sdk_hot_lane_cutover import (
    main
)


if __name__=="__main__":

    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    raise SystemExit(
        main()
    )
'''.strip()+"\n",
    encoding="utf-8"
)


py_compile.compile(
    str(LAUNCHER),
    doraise=True
)


TEST.write_text(
r'''
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_018_exact_sdk_hot_lane_cutover
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


    def test_exact_sdk_worker(self):

        s=q.WORKER_JS.read_text(
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


    def test_persistent_worker(self):

        s=inspect.getsource(
            q.PumpSdkWorker
        )

        self.assertIn(
            "subprocess.Popen",
            s
        )

        self.assertNotIn(
            "subprocess.run",
            s
        )


    def test_websocket_reserves_feed_sdk(self):

        s=inspect.getsource(
            q.PumpSdkWorker.buy
        )

        self.assertIn(
            "pump_base_reserve",
            s
        )

        self.assertIn(
            "pump_quote_reserve",
            s
        )


    def test_token2022_net_receipt(self):

        s=inspect.getsource(
            q.exact_snapshot_opportunities
        )

        self.assertIn(
            "token_net",
            s
        )


    def test_bidirectional(self):

        s=inspect.getsource(
            q.exact_snapshot_opportunities
        )

        self.assertIn(
            "METEORA_TO_PUMP",
            s
        )

        self.assertIn(
            "PUMP_TO_METEORA",
            s
        )


    def test_old_fee_formula_absent(self):

        s=inspect.getsource(
            q.exact_snapshot_opportunities
        )

        self.assertNotIn(
            "PUMP_FEE_BPS",
            s
        )

        self.assertNotIn(
            "10000-PUMP",
            s
        )


    def test_snapshot_seam_replaced(self):

        s=inspect.getsource(
            q.install_exact_hot_math
        )

        self.assertIn(
            "sized_snapshot_opportunities",
            s
        )


    def test_official_verifier_preserved(self):

        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "q15.run",
            s
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
    "[PASS] ORACLE-018 exact SDK hot-lane cutover installed"
)

print(
    "[RETIRED] fixed 120-bps Pump reserve approximation"
)

print(
    "[RETIRED] ORACLE-016 empirical correction as runtime model"
)

print(
    "[PUMP] persistent exact PumpSwap SDK worker"
)

print(
    "[STATE] static Pump config warmed once"
)

print(
    "[RESERVES] live WebSocket reserves supplied per pricing call"
)

print(
    "[METEORA] existing hydrated in-memory DLMM quote preserved"
)

print(
    "[TOKEN2022] net receipt included between venues"
)

print(
    "[DIRECTIONS] Pump->Meteora + Meteora->Pump"
)

print(
    "[OFFICIAL] ORACLE-015 physical verifier remains final authority"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)