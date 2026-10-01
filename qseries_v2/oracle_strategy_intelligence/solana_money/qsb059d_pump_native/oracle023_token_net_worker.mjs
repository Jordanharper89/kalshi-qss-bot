import readline from "node:readline";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const {Connection,PublicKey}=require("@solana/web3.js");
const {TOKEN_PROGRAM_ID,TOKEN_2022_PROGRAM_ID,getMint,getTransferFeeConfig,calculateEpochFee}=require("@solana/spl-token");
const rpc=process.env.SOLANA_RPC_URL || "https://api.mainnet-beta.solana.com";
const connection=new Connection(rpc,"confirmed");
const cache=new Map();
let epoch=null;
async function refreshEpoch(){ const e=await connection.getEpochInfo("confirmed"); epoch=BigInt(e.epoch); return epoch; }
async function warm(mintText){
  const mint=new PublicKey(mintText);
  const info=await connection.getAccountInfo(mint,"confirmed");
  if(!info) throw new Error("MINT_NOT_FOUND");
  if(info.owner.equals(TOKEN_PROGRAM_ID)){
    const row={program:TOKEN_PROGRAM_ID.toBase58(),cfg:null}; cache.set(mintText,row); return row;
  }
  if(!info.owner.equals(TOKEN_2022_PROGRAM_ID)) throw new Error("UNKNOWN_TOKEN_PROGRAM:"+info.owner.toBase58());
  const m=await getMint(connection,mint,"confirmed",TOKEN_2022_PROGRAM_ID);
  const cfg=getTransferFeeConfig(m);
  const row={program:TOKEN_2022_PROGRAM_ID.toBase58(),cfg}; cache.set(mintText,row);
  if(epoch===null) await refreshEpoch();
  return row;
}
async function net(mintText,grossText){
  let row=cache.get(mintText); if(!row) row=await warm(mintText);
  const gross=BigInt(String(grossText)); let fee=0n;
  if(row.program===TOKEN_2022_PROGRAM_ID.toBase58() && row.cfg){ if(epoch===null) await refreshEpoch(); fee=calculateEpochFee(row.cfg,epoch,gross); }
  const received=gross-fee; if(received<=0n) throw new Error("NET_RECEIVED_NONPOSITIVE");
  return {program:row.program,gross:gross.toString(),fee:fee.toString(),net:received.toString()};
}
const rl=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
for await (const line of rl){
  if(!line.trim()) continue;
  let req;
  try{
    req=JSON.parse(line); let result;
    if(req.op==="warm") result=await warm(String(req.mint));
    else if(req.op==="net") result=await net(String(req.mint),String(req.gross));
    else if(req.op==="refresh_epoch") result={epoch:(await refreshEpoch()).toString()};
    else if(req.op==="stats") result={cached_mints:cache.size,epoch:epoch===null?null:epoch.toString()};
    else throw new Error("UNKNOWN_OP:"+req.op);
    console.log(JSON.stringify({id:req.id,ok:true,...result}));
  }catch(e){ console.log(JSON.stringify({id:req?.id ?? null,ok:false,reason:e?.stack ?? e?.message ?? String(e)})); }
}
