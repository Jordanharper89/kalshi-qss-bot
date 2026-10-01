import fs from "node:fs";
import BN from "bn.js";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const _dlmm=require("@meteora-ag/dlmm");
const DLMM=_dlmm.default ?? _dlmm;
import {
  Connection,
  PublicKey
} from "@solana/web3.js";

const req=JSON.parse(
  fs.readFileSync(0,"utf8")
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

const poolAddress=
  new PublicKey(
    req.pool
  );

const inToken=
  new PublicKey(
    req.inputMint
  );

const outToken=
  new PublicKey(
    req.outputMint
  );

const inAmount=
  new BN(
    String(req.inputAmount)
  );

const slippageBps=
  new BN(
    String(req.slippageBps ?? 20)
  );

function asPk(v){
  if(v instanceof PublicKey){
    return v;
  }

  if(v?.publicKey){
    return new PublicKey(
      v.publicKey.toString()
    );
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

  return new PublicKey(
    String(v)
  );
}

function encIx(ix){
  return {
    programId:
      ix.programId.toBase58(),

    accounts:
      ix.keys.map(
        k=>({
          pubkey:
            k.pubkey.toBase58(),

          isSigner:
            !!k.isSigner,

          isWritable:
            !!k.isWritable
        })
      ),

    data:
      Buffer.from(
        ix.data
      ).toString("base64")
  };
}

try{
  const pool=
    await DLMM.create(
      connection,
      poolAddress,
      {
        cluster:
          "mainnet-beta",

        skipSolWrappingOperation:
          true
      }
    );

  const tokenX=
    asPk(
      pool.tokenX
    );

  const tokenY=
    asPk(
      pool.tokenY
    );

  let swapForY;

  if(
    inToken.equals(tokenX)
    &&
    outToken.equals(tokenY)
  ){
    swapForY=true;
  }
  else if(
    inToken.equals(tokenY)
    &&
    outToken.equals(tokenX)
  ){
    swapForY=false;
  }
  else{
    throw new Error(
      "METEORA_POOL_MINT_BINDING_MISMATCH:"
      +tokenX.toBase58()
      +":"
      +tokenY.toBase58()
    );
  }

  const binArrays=
    await pool.getBinArrayForSwap(
      swapForY,
      4
    );

  const quote=
    pool.swapQuote(
      inAmount,
      swapForY,
      slippageBps,
      binArrays,
      false
    );

  const consumed=
    new BN(
      quote.consumedInAmount.toString()
    );

  const outAmount=
    new BN(
      quote.outAmount.toString()
    );

  const minOutAmount=
    new BN(
      quote.minOutAmount.toString()
    );

  if(
    !consumed.eq(inAmount)
  ){
    throw new Error(
      "METEORA_PARTIAL_INPUT:"
      +consumed.toString()
      +":"
      +inAmount.toString()
    );
  }

  if(
    outAmount.lte(
      new BN(0)
    )
  ){
    throw new Error(
      "METEORA_OUTPUT_NONPOSITIVE"
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
    ? tx
    : [tx];

  const instructions=
    txs.flatMap(
      x=>x.instructions ?? []
    );

  if(
    instructions.length===0
  ){
    throw new Error(
      "METEORA_SWAP_INSTRUCTIONS_EMPTY"
    );
  }

  const DLMM_PROGRAM=
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";

  if(
    !instructions.some(
      x=>
        x.programId.toBase58()
        ===DLMM_PROGRAM
    )
  ){
    throw new Error(
      "METEORA_DLMM_PROGRAM_IX_MISSING"
    );
  }

  console.log(
    JSON.stringify({
      ok:true,

      sdk:
        "@meteora-ag/dlmm",

      sdkVersion:
        "1.9.14",

      builder:
        "OFFICIAL_SWAP2",

      tokenX:
        tokenX.toBase58(),

      tokenY:
        tokenY.toBase58(),

      swapForY,

      consumedInAmount:
        consumed.toString(),

      outAmount:
        outAmount.toString(),

      minOutAmount:
        minOutAmount.toString(),

      binArraysPubkey:
        quote.binArraysPubkey.map(
          x=>x.toBase58()
        ),

      instructions:
        instructions.map(encIx)
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
