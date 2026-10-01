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
