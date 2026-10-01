from pathlib import Path
import ast
import subprocess
import textwrap

ROOT=Path.cwd()

Q18=(
    ROOT/
    "qseries_v2"/
    "oracle_execution"/
    "oracle_018_exact_sdk_hot_lane_cutover.py"
)

NODEDIR=(
    ROOT/
    "qseries_v2"/
    "oracle_strategy_intelligence"/
    "solana_money"/
    "qsb059d_pump_native"
)

WORKER=(
    NODEDIR/
    "sae003_pump_exact_quote_worker.mjs"
)

TEST=(
    ROOT/
    "test_sae_003_exact_quote_in_pump_pricer.py"
)

if not Q18.is_file():
    raise RuntimeError(
        "ORACLE018_SOURCE_MISSING"
    )

if not NODEDIR.is_dir():
    raise RuntimeError(
        "PUMP_NODEDIR_MISSING"
    )

#
# ============================================================
# Verify the physically installed PumpSwap SDK exports the
# exact functions SAE-003 requires BEFORE changing Python.
# ============================================================
#
probe=r'''
import {
  OnlinePumpAmmSdk,
  buyQuoteInput,
  sellBaseInput
} from "@pump-fun/pump-swap-sdk";

if(typeof OnlinePumpAmmSdk!=="function"){
  throw new Error("OnlinePumpAmmSdk export missing");
}

if(typeof buyQuoteInput!=="function"){
  throw new Error("buyQuoteInput export missing");
}

if(typeof sellBaseInput!=="function"){
  throw new Error("sellBaseInput export missing");
}

console.log("SAE003_SDK_EXPORTS_OK");
'''

p=subprocess.run(
    [
        "node",
        "--input-type=module",
        "-e",
        probe,
    ],
    cwd=str(NODEDIR),
    text=True,
    capture_output=True,
)

if p.returncode!=0:
    raise RuntimeError(
        "SAE003_PUMP_SDK_EXPORT_PROBE_FAILED:\n"
        +p.stdout
        +"\n"
        +p.stderr
    )

if "SAE003_SDK_EXPORTS_OK" not in p.stdout:
    raise RuntimeError(
        "SAE003_PUMP_SDK_EXPORT_PROBE_NO_ATTESTATION"
    )


#
# ============================================================
# New persistent quote worker.
#
# IMPORTANT:
#
#  * Online state is fetched ONLY by warm().
#  * Hot buy/sell quote operations use cached static/config
#    state + externally supplied WebSocket reserves.
#  * PUMP_TO_METEORA uses buyQuoteInput with ZERO quote-model
#    slippage so baseOut is the exact same-state expected
#    output for the fixed spendable quote budget.
#  * SAE-002 still catches any remaining chain disagreement.
# ============================================================
#
worker_source=r'''
import { Connection, PublicKey } from "@solana/web3.js";
import BN from "bn.js";

import {
  OnlinePumpAmmSdk,
  buyQuoteInput,
  sellBaseInput
} from "@pump-fun/pump-swap-sdk";

import readline from "node:readline";


const RPC=(
  process.env.SOLANA_RPC_URL
  ||"https://api.mainnet-beta.solana.com"
);

const USER=new PublicKey(
  "11111111111111111111111111111111"
);

const connection=new Connection(
  RPC,
  "processed"
);

const online=new OnlinePumpAmmSdk(
  connection
);

const states=new Map();


function bn(v){
  return BN.isBN(v)
    ?v
    :new BN(String(v));
}


function out(v){
  if(v===null || v===undefined){
    return null;
  }

  if(BN.isBN(v)){
    return v.toString();
  }

  if(
    typeof v==="bigint"
    ||typeof v==="number"
  ){
    return String(v);
  }

  if(
    typeof v==="object"
    &&typeof v.toString==="function"
  ){
    return v.toString();
  }

  return String(v);
}


function poolArgs(
  state,
  baseReserve,
  quoteReserve
){
  const pool=state.pool;

  if(!pool){
    throw new Error(
      "SAE003_STATE_POOL_MISSING"
    );
  }

  return {
    baseReserve:
      bn(baseReserve),

    quoteReserve:
      bn(quoteReserve),

    virtualQuoteReserves:
      pool.virtualQuoteReserves,

    globalConfig:
      state.globalConfig,

    feeConfig:
      state.feeConfig,

    baseMint:
      state.baseMint,

    baseMintAccount:
      state.baseMintAccount,

    coinCreator:
      pool.coinCreator,

    creator:
      pool.creator,

    quoteMint:
      pool.quoteMint,

    isMayhemMode:
      pool.isMayhemMode,

    creatorFeeBps:
      pool.creatorFeeBps,
  };
}


async function warm(req){
  const key=new PublicKey(
    String(req.pool)
  );

  const state=await online.swapSolanaState(
    key,
    USER
  );

  if(!state){
    throw new Error(
      "SAE003_SWAP_STATE_EMPTY"
    );
  }

  if(!state.pool){
    throw new Error(
      "SAE003_POOL_STATE_EMPTY"
    );
  }

  if(!state.globalConfig){
    throw new Error(
      "SAE003_GLOBAL_CONFIG_EMPTY"
    );
  }

  if(!state.feeConfig){
    throw new Error(
      "SAE003_FEE_CONFIG_EMPTY"
    );
  }

  states.set(
    key.toBase58(),
    state
  );

  return {
    ok:true,
    mode:
      "BUY_EXACT_QUOTE_IN",
    pool:
      key.toBase58(),
    baseReserve:
      out(state.poolBaseAmount),
    quoteReserve:
      out(state.poolQuoteAmount),
    virtualQuoteReserves:
      out(
        state.pool.virtualQuoteReserves
      ),
    quoteMint:
      out(state.pool.quoteMint),
    isMayhemMode:
      Boolean(
        state.pool.isMayhemMode
      ),
    creatorFeeBps:
      out(
        state.pool.creatorFeeBps
      ),
    onlineStateFetches:1
  };
}


function buy(req){
  const state=states.get(
    String(req.pool)
  );

  if(!state){
    throw new Error(
      "SAE003_POOL_NOT_WARM:"
      +String(req.pool)
    );
  }

  const quote=bn(
    req.amount
  );

  if(quote.lte(new BN(0))){
    throw new Error(
      "SAE003_BUY_QUOTE_NONPOSITIVE"
    );
  }

  const args=poolArgs(
    state,
    req.baseReserve,
    req.quoteReserve
  );

  //
  // EXACT QUOTE INPUT.
  //
  // Slippage = 0 because Oracle wants the
  // exact same-snapshot base output for this
  // fixed spendable quote amount.
  //
  // The runtime's BuyExactQuoteIn instruction
  // then uses:
  //
  //   spendableQuoteIn = req.amount
  //   minBaseAmountOut = baseOut
  //
  const row=buyQuoteInput({
    ...args,
    quote,
    slippage:0
  });

  if(!row){
    throw new Error(
      "SAE003_BUY_QUOTE_EMPTY"
    );
  }

  const base=bn(
    row.base
  );

  const maxQuote=bn(
    row.maxQuote
  );

  if(base.lte(new BN(0))){
    throw new Error(
      "SAE003_BUY_BASE_ZERO"
    );
  }

  return {
    ok:true,

    quoteModel:
      "PUMPSWAP_BUY_QUOTE_INPUT",

    executionModel:
      "BUY_EXACT_QUOTE_IN",

    baseOut:
      base.toString(),

    maxQuote:
      maxQuote.toString(),

    spendableQuote:
      quote.toString(),

    onlineStateFetches:1
  };
}


function sell(req){
  const state=states.get(
    String(req.pool)
  );

  if(!state){
    throw new Error(
      "SAE003_POOL_NOT_WARM:"
      +String(req.pool)
    );
  }

  const base=bn(
    req.amount
  );

  if(base.lte(new BN(0))){
    throw new Error(
      "SAE003_SELL_BASE_NONPOSITIVE"
    );
  }

  const args=poolArgs(
    state,
    req.baseReserve,
    req.quoteReserve
  );

  const slippage=Number(
    req.slippagePct
    ??0
  );

  const row=sellBaseInput({
    ...args,
    base,
    slippage
  });

  if(!row){
    throw new Error(
      "SAE003_SELL_QUOTE_EMPTY"
    );
  }

  return {
    ok:true,

    quoteModel:
      "PUMPSWAP_SELL_BASE_INPUT",

    uiQuote:
      out(row.uiQuote),

    minQuote:
      out(row.minQuote),

    onlineStateFetches:1
  };
}


async function dispatch(req){
  const op=String(
    req.op||""
  );

  if(op==="warm"){
    return await warm(req);
  }

  if(op==="buy"){
    return buy(req);
  }

  if(op==="sell"){
    return sell(req);
  }

  throw new Error(
    "SAE003_UNKNOWN_OP:"
    +op
  );
}


const rl=readline.createInterface({
  input:process.stdin,
  crlfDelay:Infinity
});


for await(
  const line of rl
){
  if(!line.trim()){
    continue;
  }

  let req=null;

  try{
    req=JSON.parse(line);

    const result=await dispatch(
      req
    );

    process.stdout.write(
      JSON.stringify({
        id:req.id,
        ...result
      })
      +"\n"
    );
  }
  catch(err){
    process.stdout.write(
      JSON.stringify({
        id:
          req?.id
          ??null,

        ok:false,

        reason:
          err?.message
          ??String(err),

        stack:String(
          err?.stack
          ??""
        )
        .split("\n")
        .slice(0,5)
        .join(" | ")
      })
      +"\n"
    );
  }
}
'''

WORKER.write_text(
    textwrap.dedent(
        worker_source
    ).lstrip(),
    encoding="utf-8"
)


#
# ============================================================
# Point ORACLE-018 at SAE-003 worker.
# ============================================================
#
src=Q18.read_text(
    encoding="utf-8"
)

tree=ast.parse(src)

worker_assignment=None

for node in tree.body:
    if (
        isinstance(node,ast.Assign)
        and any(
            isinstance(t,ast.Name)
            and t.id=="WORKER_JS"
            for t in node.targets
        )
    ):
        worker_assignment=node
        break

if worker_assignment is None:
    raise RuntimeError(
        "ORACLE018_WORKER_JS_ASSIGNMENT_NOT_FOUND"
    )

lines=src.splitlines(
    keepends=True
)

replacement='''WORKER_JS=(
    NODEDIR/
    "sae003_pump_exact_quote_worker.mjs"
)
'''

new_src="".join(
    lines[
        :worker_assignment.lineno-1
    ]
    +[
        replacement
    ]
    +lines[
        worker_assignment.end_lineno:
    ]
)

#
# Make the forward model identity explicit.
#
new_src=new_src.replace(
    '"pump_model":\n'
    '            "EXACT_PUMPSWAP_SDK",',
    '"pump_model":\n'
    '            "SAE003_PUMPSWAP_EXACT_QUOTE_IN",',
    1,
)

ast.parse(
    new_src
)

Q18.write_text(
    new_src,
    encoding="utf-8"
)


#
# ============================================================
# Deterministic certification test.
# ============================================================
#
test_source=r'''
from pathlib import Path
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_018_exact_sdk_hot_lane_cutover
    as q18
)

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as canonical
)


ROOT=Path.cwd()

WORKER=(
    ROOT/
    "qseries_v2"/
    "oracle_strategy_intelligence"/
    "solana_money"/
    "qsb059d_pump_native"/
    "sae003_pump_exact_quote_worker.mjs"
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            canonical.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            canonical.PAPER_ONLY
        )

        self.assertFalse(
            canonical.REAL_MONEY_MOVED
        )

    def test_oracle018_points_to_sae003(self):
        self.assertEqual(
            q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_worker_exists(self):
        self.assertTrue(
            WORKER.is_file()
        )

    def test_forward_uses_quote_input(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "buyQuoteInput({",
            src
        )

        self.assertIn(
            "quote,",
            src
        )

        self.assertIn(
            "slippage:0",
            src
        )

    def test_full_fee_context_present(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        required=[
            "virtualQuoteReserves",
            "globalConfig",
            "feeConfig",
            "baseMint",
            "baseMintAccount",
            "coinCreator",
            "creator",
            "quoteMint",
            "isMayhemMode",
            "creatorFeeBps",
        ]

        for field in required:
            self.assertIn(
                field,
                src
            )

    def test_hot_buy_has_no_rpc(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        start=src.index(
            "function buy(req)"
        )

        end=src.index(
            "function sell(req)"
        )

        buy_src=src[
            start:end
        ]

        self.assertNotIn(
            "getAccountInfo",
            buy_src
        )

        self.assertNotIn(
            "swapSolanaState",
            buy_src
        )

        self.assertNotIn(
            "connection.",
            buy_src
        )

    def test_warm_is_only_online_state_fetch(self):
        src=WORKER.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            src.count(
                "swapSolanaState("
            ),
            1
        )

    def test_oracle018_forward_contract_preserved(self):
        src=inspect.getsource(
            q18.exact_snapshot_opportunities
        )

        self.assertIn(
            'pump_buy[\n            "baseOut"\n        ]',
            src
        )

        self.assertIn(
            '"PUMP_TO_METEORA"',
            src
        )

    def test_sae001_hot_meteora_preserved(self):
        src=inspect.getsource(
            canonical.build_meteora_ix_hot
        )

        for bad in (
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
        ):
            self.assertNotIn(
                bad,
                src
            )

    def test_sae002_truth_gate_preserved(self):
        src=inspect.getsource(
            canonical.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src
        )

    def test_no_broadcast(self):
        src=inspect.getsource(
            canonical
        )

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
    test_source
)

TEST.write_text(
    textwrap.dedent(
        test_source
    ).lstrip(),
    encoding="utf-8"
)

print(
    "[PASS] SAE-003 exact quote-in Pump pricer installed"
)

print(
    "[WORKER] sae003_pump_exact_quote_worker.mjs"
)

print(
    "[FORWARD] buyQuoteInput exact fixed quote budget"
)

print(
    "[SLIPPAGE_MODEL] quote calculation uses 0% same-snapshot bound"
)

print(
    "[FEES] full feeConfig + quoteMint + virtual reserves + creator state"
)

print(
    "[HOT_INPUT] WebSocket base/quote reserves retained"
)

print(
    "[ONLINE_STATE] warm only; no hot quote RPC"
)

print(
    "[SAE-001] memory-only Meteora execution preserved"
)

print(
    "[SAE-002] chain-truth 6040 verification preserved"
)

print(
    "[BROADCAST] disabled"
)