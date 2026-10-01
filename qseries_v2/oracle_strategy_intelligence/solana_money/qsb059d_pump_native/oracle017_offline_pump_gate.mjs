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
