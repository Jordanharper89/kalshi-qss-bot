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
