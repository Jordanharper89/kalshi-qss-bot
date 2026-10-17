import fs from "node:fs";
import BN from "bn.js";
import {Connection,PublicKey} from "@solana/web3.js";
import {OnlinePumpAmmSdk,PUMP_AMM_SDK} from "@pump-fun/pump-swap-sdk";

const req=JSON.parse(fs.readFileSync(0,"utf8"));
const connection=new Connection(req.rpc,"processed");
const user=new PublicKey(req.user);
const pool=new PublicKey(req.pool);
const amount=new BN(String(req.baseAmount));
const slippage=Number(req.slippagePct ?? 0.2);

function encIx(ix){
  return {
    programId:ix.programId.toBase58(),
    accounts:ix.keys.map(k=>({
      pubkey:k.pubkey.toBase58(),
      isSigner:!!k.isSigner,
      isWritable:!!k.isWritable
    })),
    data:Buffer.from(ix.data).toString("base64")
  };
}

try{
  const online=new OnlinePumpAmmSdk(connection);
  const state=await online.swapSolanaState(pool,user);
  const ixs=await PUMP_AMM_SDK.sellBaseInput(state,amount,slippage);

  if(!Array.isArray(ixs)||ixs.length===0){
    throw new Error("PUMP_SELL_INSTRUCTIONS_EMPTY");
  }

  const pumpIxs=ixs.filter(ix=>ix.programId.toBase58()===req.pumpProgram);

  if(pumpIxs.length!==1){
    throw new Error("PUMP_SELL_IX_COUNT:"+pumpIxs.length);
  }

  const raw=Buffer.from(pumpIxs[0].data);

  if(raw.length<24){
    throw new Error("PUMP_SELL_DATA_TOO_SHORT:"+raw.length);
  }

  console.log(JSON.stringify({
    ok:true,
    baseIn:raw.readBigUInt64LE(8).toString(),
    minQuoteOut:raw.readBigUInt64LE(16).toString(),
    instructions:ixs.map(encIx)
  }));
}catch(e){
  console.log(JSON.stringify({
    ok:false,
    reason:e?.stack ?? e?.message ?? String(e)
  }));
}
