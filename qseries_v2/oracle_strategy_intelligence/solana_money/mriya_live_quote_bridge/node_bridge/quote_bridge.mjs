import fs from "node:fs";
import BN from "bn.js";
import DLMM from "@meteora-ag/dlmm";
import { Connection, PublicKey } from "@solana/web3.js";
import { OnlinePumpAmmSdk, sellBaseInput } from "@pump-fun/pump-swap-sdk";

const req=JSON.parse(fs.readFileSync(0,"utf8"));
const t0=Date.now();
const connection=new Connection(req.rpc,"processed");
const token=new PublicKey(req.token);
const wsol=new PublicKey(req.wsol);
const user=new PublicKey(req.targetWallet);

function b58(x){
  if(!x)return null;
  if(typeof x==="string")return x;
  if(typeof x.toBase58==="function")return x.toBase58();
  if(x.address && typeof x.address.toBase58==="function")return x.address.toBase58();
  if(x.publicKey && typeof x.publicKey.toBase58==="function")return x.publicKey.toBase58();
  return String(x);
}
function decimals(x){
  for(const k of ["decimals","decimal"]){
    if(x && Number.isInteger(Number(x[k])))return Number(x[k]);
  }
  if(x?.mint && Number.isInteger(Number(x.mint.decimals)))return Number(x.mint.decimals);
  return null;
}
function addressOfPoolRow(o){
  if(!o || typeof o!=="object")return null;
  for(const k of ["address","pool_address","poolAddress","pubkey","public_key","lb_pair","lbPair"]){
    const v=o[k]; if(typeof v==="string" && v.length>=32 && v.length<=50)return v;
  }
  return null;
}
function flatten(x,out=[]){
  if(Array.isArray(x)){for(const y of x)flatten(y,out);}
  else if(x && typeof x==="object"){out.push(x);for(const v of Object.values(x))if(v&&typeof v==="object")flatten(v,out);}
  return out;
}
async function discoverMeteoraPool(){
  const u=`https://dlmm.datapi.meteora.ag/pools?page=1&page_size=100&query=${encodeURIComponent(req.token)}`;
  const r=await fetch(u,{headers:{"accept":"application/json"}});
  if(!r.ok)throw new Error(`METEORA_DATA_API_${r.status}`);
  const j=await r.json();const candidates=[];
  for(const o of flatten(j)){
    const s=JSON.stringify(o);
    if(s.includes(req.token) && s.includes(req.wsol)){
      const a=addressOfPoolRow(o);if(a)candidates.push(a);
    }
  }
  for(const a of [...new Set(candidates)]){
    try{
      const pool=await DLMM.create(connection,new PublicKey(a),{cluster:"mainnet-beta"});
      const x=b58(pool.tokenX?.mint?.address ?? pool.tokenX?.publicKey ?? pool.tokenX?.mint);
      const y=b58(pool.tokenY?.mint?.address ?? pool.tokenY?.publicKey ?? pool.tokenY?.mint);
      if(new Set([x,y]).has(req.token) && new Set([x,y]).has(req.wsol))return {address:a,pool,x,y};
    }catch{}
  }
  // Fallback: official SDK discovery if indexed API response shape changes.
  const pairs=await DLMM.getLbPairs(connection,{cluster:"mainnet-beta"});
  for(const row of pairs){
    const a=b58(row.publicKey ?? row.pubkey ?? row.address);
    if(!a)continue;
    try{
      const pool=await DLMM.create(connection,new PublicKey(a),{cluster:"mainnet-beta"});
      const x=b58(pool.tokenX?.mint?.address ?? pool.tokenX?.publicKey ?? pool.tokenX?.mint);
      const y=b58(pool.tokenY?.mint?.address ?? pool.tokenY?.publicKey ?? pool.tokenY?.mint);
      if(new Set([x,y]).has(req.token) && new Set([x,y]).has(req.wsol))return {address:a,pool,x,y};
    }catch{}
  }
  throw new Error("METEORA_TARGET_POOL_NOT_FOUND");
}
function canonicalPumpPoolPda(baseMint,quoteMint){
  const pumpProgram=new PublicKey("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P");
  const ammProgram=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
  const [creator]=PublicKey.findProgramAddressSync([Buffer.from("pool-authority"),baseMint.toBuffer()],pumpProgram);
  const index=Buffer.alloc(2);index.writeUInt16LE(0);
  const [pool]=PublicKey.findProgramAddressSync([Buffer.from("pool"),index,creator.toBuffer(),baseMint.toBuffer(),quoteMint.toBuffer()],ammProgram);
  return pool;
}
try{
  const slotStart=await connection.getSlot("processed");
  const m=await discoverMeteoraPool();
  const pool=m.pool;
  const x=b58(pool.tokenX?.mint?.address ?? pool.tokenX?.publicKey ?? pool.tokenX?.mint);
  const y=b58(pool.tokenY?.mint?.address ?? pool.tokenY?.publicKey ?? pool.tokenY?.mint);
  const xDec=decimals(pool.tokenX);const yDec=decimals(pool.tokenY);
  if(xDec===null || yDec===null)throw new Error("METEORA_TOKEN_DECIMALS_UNAVAILABLE");
  const swapForY=(x===req.wsol && y===req.token);
  if(!swapForY && !(y===req.wsol && x===req.token))throw new Error("METEORA_DIRECTION_UNRESOLVED");
  const inDec=swapForY?xDec:yDec;const outDec=swapForY?yDec:xDec;
  const rawIn=new BN(Math.round(req.startSol*(10**inDec)).toString());
  const bins=await pool.getBinArrayForSwap(swapForY,4);
  const mq=pool.swapQuote(rawIn,swapForY,new BN(0),bins,false);
  const rawTokenOut=new BN(mq.outAmount.toString());
  const tokenOutUi=Number(rawTokenOut.toString())/(10**outDec);

  const pumpPool=canonicalPumpPoolPda(token,wsol);
  const online=new OnlinePumpAmmSdk(connection);
  const state=await online.swapSolanaState(pumpPool,user);
  const baseDec=Number(state.baseMintAccount?.decimals ?? outDec);
  const pumpRawIn=new BN(Math.floor(tokenOutUi*(10**baseDec)).toString());
  const args={
    baseReserve:state.poolBaseAmount,
    quoteReserve:state.poolQuoteAmount,
    virtualQuoteReserves:state.pool.virtualQuoteReserves,
    globalConfig:state.globalConfig,
    feeConfig:state.feeConfig,
    baseMint:state.baseMint,
    baseMintAccount:state.baseMintAccount,
    coinCreator:state.pool.coinCreator,
    creator:state.pool.creator,
    quoteMint:state.pool.quoteMint,
    isMayhemMode:state.pool.isMayhemMode,
    creatorFeeBps:state.pool.creatorFeeBps,
    base:pumpRawIn,
    slippage:0,
  };
  const pq=sellBaseInput(args);
  const quoteOut=pq.uiQuote ?? pq.minQuote;
  if(!quoteOut)throw new Error("PUMPSWAP_QUOTE_OUTPUT_MISSING");
  const quoteDec=Number(state.quoteMintAccount?.decimals ?? 9);
  const solOutUi=Number(quoteOut.toString())/(10**quoteDec);
  const slotEnd=await connection.getSlot("processed");
  const netSol=solOutUi-Number(req.startSol)-Number(req.txCostSol||0);
  const netBps=netSol/Number(req.startSol)*10000;
  const slotSpread=Math.abs(slotEnd-slotStart);
  const qualified=slotSpread<=2 && netBps>=10;
  console.log(JSON.stringify({ok:true,meteoraPool:m.address,pumpPool:pumpPool.toBase58(),
    tokenOutUi,solOutUi,meteoraRawOut:rawTokenOut.toString(),pumpRawIn:pumpRawIn.toString(),
    slotStart,slotEnd,slotSpread,elapsedMs:Date.now()-t0,netSol,netBps,qualified,
    meteoraPriceImpact:String(mq.priceImpact ?? ""),executionAuthority:false}));
}catch(e){
  console.log(JSON.stringify({ok:false,reason:e?.message??String(e),stack:String(e?.stack??"").split("\n").slice(0,4).join(" | ")}));
  process.exit(0);
}
