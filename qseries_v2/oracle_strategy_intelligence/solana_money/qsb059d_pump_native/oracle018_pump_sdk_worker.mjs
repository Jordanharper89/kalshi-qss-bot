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
