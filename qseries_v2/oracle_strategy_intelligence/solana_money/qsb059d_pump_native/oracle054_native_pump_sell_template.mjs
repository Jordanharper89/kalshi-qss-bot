import fs from "node:fs";
import BN from "bn.js";
import {Connection,PublicKey} from "@solana/web3.js";
import {OnlinePumpAmmSdk,PUMP_AMM_SDK} from "@pump-fun/pump-swap-sdk";

const req=JSON.parse(fs.readFileSync(0,"utf8"));

function enc(ix){
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
 const user=new PublicKey(req.user);
 const pool=new PublicKey(req.pool);
 const online=new OnlinePumpAmmSdk(
  new Connection(req.rpc,"processed")
 );
 const state=await online.swapSolanaState(pool,user);
 const amount=new BN(String(req.templateBaseUnits));
 const ixs=await PUMP_AMM_SDK.sellBaseInput(
  state,amount,Number(req.slippagePct)
 );
 const pump=ixs.filter(
  i=>i.programId.toBase58()===req.pumpProgram
 );
 if(pump.length!==1)
  throw Error("PUMP_SELL_INSTRUCTION_COUNT:"+pump.length);
 if(!pump[0].keys.some(
  k=>k.pubkey.toBase58()===req.pool
 ))throw Error("PUMP_POOL_NOT_BOUND");

 const data=Buffer.from(pump[0].data);
 if(data.length<24 ||
    data.readBigUInt64LE(8)!==BigInt(req.templateBaseUnits))
  throw Error("PUMP_SELL_DATA_CONTRACT");
 if(!Array.isArray(ixs)||ixs.length<2)
  throw Error("NATIVE_HELPERS_MISSING");

 console.log(JSON.stringify({
  ok:true,
  stateSnapshots:1,
  amount:String(amount),
  instructions:ixs.map(enc)
 }));
}catch(e){
 console.log(JSON.stringify({
  ok:false,error:String(e?.message??e)
 }));
}
