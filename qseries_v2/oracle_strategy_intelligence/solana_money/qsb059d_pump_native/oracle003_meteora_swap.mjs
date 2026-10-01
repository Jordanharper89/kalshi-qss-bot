import fs from "node:fs";
import {createRequire} from "node:module";

const require=createRequire(import.meta.url);

const dlmm=require("@meteora-ag/dlmm");
const DLMM=dlmm.default ?? dlmm;

const {
  Connection,
  PublicKey
}=require("@solana/web3.js");

const BN=require("bn.js");

const req=JSON.parse(
  fs.readFileSync(0,"utf8")
);

const connection=
  new Connection(
    req.rpc,
    "processed"
  );

const user=
  new PublicKey(req.user);

const poolAddress=
  new PublicKey(req.pool);

const inToken=
  new PublicKey(req.inputMint);

const outToken=
  new PublicKey(req.outputMint);

const amount=
  new BN(String(req.amount));

const slippage=
  new BN(
    String(req.slippageBps)
  );

function pk(v){
  if(v instanceof PublicKey){
    return v;
  }

  if(v?.mint?.address){
    return new PublicKey(
      v.mint.address.toString()
    );
  }

  if(v?.mint){
    return new PublicKey(
      v.mint.toString()
    );
  }

  if(v?.publicKey){
    return new PublicKey(
      v.publicKey.toString()
    );
  }

  return new PublicKey(String(v));
}

function encode(ix){
  return {
    programId:
      ix.programId.toBase58(),

    accounts:
      ix.keys.map(k=>({
        pubkey:
          k.pubkey.toBase58(),

        isSigner:
          !!k.isSigner,

        isWritable:
          !!k.isWritable
      })),

    data:
      Buffer.from(ix.data)
        .toString("base64")
  };
}

function liquidityError(e){
  const s=String(
    e?.message ?? e
  );

  return (
    s.includes(
      "SWAP_QUOTE_INSUFFICIENT_LIQUIDITY"
    )
    ||
    s.includes(
      "Insufficient liquidity"
    )
  );
}

try{
  const pool=
    await DLMM.create(
      connection,
      poolAddress,
      {
        cluster:"mainnet-beta",
        skipSolWrappingOperation:true
      }
    );

  const x=pk(pool.tokenX);
  const y=pk(pool.tokenY);

  let swapForY;

  if(
    inToken.equals(x)
    &&
    outToken.equals(y)
  ){
    swapForY=true;
  }
  else if(
    inToken.equals(y)
    &&
    outToken.equals(x)
  ){
    swapForY=false;
  }
  else{
    throw new Error(
      "POOL_MINT_BINDING_MISMATCH"
    );
  }

  let quote=null;
  let source=null;
  let loadedCount=0;
  let last=null;

  for(
    const count of
    [4,8,16,32,64]
  ){
    try{
      const bins=
        await pool.getBinArrayForSwap(
          swapForY,
          count
        );

      loadedCount=bins.length;

      const q=
        pool.swapQuote(
          amount,
          swapForY,
          slippage,
          bins,
          false
        );

      if(
        !q.consumedInAmount.eq(
          amount
        )
      ){
        throw new Error(
          "METEORA_PARTIAL_INPUT:"
          +q.consumedInAmount.toString()
          +":"
          +amount.toString()
        );
      }

      quote=q;
      source=
        "DIRECTIONAL_"+count;

      break;

    }catch(e){
      last=e;

      if(!liquidityError(e)){
        throw e;
      }
    }
  }

  // ---------------------------------------------------------
  // Exhaustive physical fallback:
  // fetch EVERY initialized bin array known to the pool.
  // ---------------------------------------------------------

  if(!quote){
    const allBins=
      await pool.getBinArrays();

    loadedCount=
      allBins.length;

    try{
      const q=
        pool.swapQuote(
          amount,
          swapForY,
          slippage,
          allBins,
          false
        );

      if(
        !q.consumedInAmount.eq(
          amount
        )
      ){
        throw new Error(
          "METEORA_PARTIAL_INPUT:"
          +q.consumedInAmount.toString()
          +":"
          +amount.toString()
        );
      }

      quote=q;
      source=
        "ALL_INITIALIZED_BIN_ARRAYS";

    }catch(e){
      if(liquidityError(e)){
        throw new Error(
          "METEORA_PHYSICAL_LIQUIDITY_INSUFFICIENT:"
          +"loaded_arrays="
          +allBins.length
          +":"
          +String(
            e?.message ?? e
          )
        );
      }

      throw e;
    }
  }

  if(!quote){
    throw (
      last ??
      new Error(
        "NO_COMPLETE_METEORA_QUOTE"
      )
    );
  }

  const tx=
    await pool.swap({
      inToken,
      outToken,

      inAmount:
        quote.consumedInAmount,

      minOutAmount:
        quote.minOutAmount,

      lbPair:
        pool.pubkey,

      user,

      binArraysPubkey:
        quote.binArraysPubkey
    });

  const txs=
    Array.isArray(tx)
    ?tx:[tx];

  const instructions=
    txs.flatMap(
      z=>z.instructions ?? []
    );

  if(!instructions.length){
    throw new Error(
      "METEORA_NO_SWAP_INSTRUCTIONS"
    );
  }

  console.log(
    JSON.stringify({
      ok:true,

      quoteSource:
        source,

      loadedBinArrays:
        loadedCount,

      consumedIn:
        quote.consumedInAmount
          .toString(),

      out:
        quote.outAmount
          .toString(),

      minOut:
        quote.minOutAmount
          .toString(),

      binArrays:
        quote.binArraysPubkey.map(
          z=>z.toBase58()
        ),

      instructions:
        instructions.map(encode)
    })
  );

}catch(e){
  console.log(
    JSON.stringify({
      ok:false,

      reason:
        e?.stack ??
        e?.message ??
        String(e)
    })
  );
}
