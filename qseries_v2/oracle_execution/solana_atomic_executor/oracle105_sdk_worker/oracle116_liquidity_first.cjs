"use strict";
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey,SystemProgram}=req('@solana/web3.js');
const {NATIVE_MINT}=req('@solana/spl-token');
const BN=req('@coral-xyz/anchor').BN;
const pump=req('@pump-fun/pump-swap-sdk');
const dlmmPkg=req('@meteora-ag/dlmm'),DLMM=dlmmPkg.default||dlmmPkg.DLMM||dlmmPkg;
const prior=require('./oracle115_budget_bounded_quotes.cjs');
const SRC=path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
const OUT=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_116_LIQUIDITY_FIRST.json');
const MINT=NATIVE_MINT.toBase58();
const clean=e=>String(e?.message||e).replace(/api-key=[^&\s]+/gi,'api-key=[REDACTED]').replace(/https?:\/\/[^\s]+/gi,'[RPC_REDACTED]').slice(0,180);
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const limits=x=>Math.min(8,Math.max(1,Number.isFinite(Number(x))?Math.floor(Number(x)):2));
function evaluate(dl,buy,budget){
 const consumed=BigInt(String(dl.consumedInAmount)),out=BigInt(String(dl.outAmount)),min=BigInt(String(dl.minOutAmount));
 if(consumed!==BigInt(buy.base))return {status:'HOLD',reason:'PARTIAL_FILL',consumed:consumed.toString()};
 if(out<=0n||min<=0n||min>out)return {status:'HOLD',reason:'INVALID_OUTPUT'};
 const delta=min-BigInt(budget);
 return {status:'QUOTED',pump_token_out:buy.base,pump_max_sol_in:buy.max_quote,meteora_min_sol_out:min.toString(),conservative_gross_delta_lamports:delta.toString(),positive_gross:delta>0n,reason:'ATOMIC_SIMULATION_AND_FEES_REQUIRED'};
}
async function check(conn,r){
 const result={index:r.index,token:r.token,pump_pool:r.pump,meteora_pool:r.dlmm,status:'HOLD',reasons:[]};
 const online=new pump.OnlinePumpAmmSdk(conn);
 const state=await online.swapSolanaState(new PublicKey(r.pump),SystemProgram.programId);
 const d=await DLMM.create(conn,new PublicKey(r.dlmm));
 const pm=[state.pool.baseMint.toBase58(),state.pool.quoteMint.toBase58()];
 const dm=[d.lbPair.tokenXMint.toBase58(),d.lbPair.tokenYMint.toBase58()];
 if(pm[0]!==r.token||pm[1]!==MINT||!dm.includes(r.token)||!dm.includes(MINT)){
  result.reasons.push('MINT_MISMATCH');return result;
 }
 result.hydrated=true;
 const budget='10000000';
 const buy=prior.boundedPumpBuy(state,budget);
 if(BigInt(buy.max_quote)>BigInt(budget))throw Error('BUDGET_INVARIANT');
 const swapForY=dm[0]===r.token;
 const arrays=await d.getBinArrayForSwap(swapForY,4);
 try{
  const quote=d.swapQuote(new BN(buy.base),swapForY,new BN(50),arrays,false);
  result.quote=evaluate(quote,buy,budget);
 }catch(e){if(prior.rate(e))throw e;result.quote={status:'HOLD',reason:'DLMM_LIQUIDITY_OR_QUOTE_FAILURE',detail:clean(e)};}
 result.status=result.quote.status==='QUOTED'?'QUOTE_ONLY':'HOLD';
 return result;
}
async function run(){
 const candidates=prior.rows(JSON.parse(fs.readFileSync(SRC,'utf8')));
 const report={revision:'ORACLE-116',status:'HOLD_NOT_LIVE',candidates:candidates.length,rows:[],signing:false,broadcast:false,scanner_unchanged:true,execution_admitted:0};
 if(process.argv.includes('--live')){
  if(!process.env.SOLANA_RPC_URL)report.status='HOLD_RPC_URL_REQUIRED';
  else{
   const conn=new Connection(process.env.SOLANA_RPC_URL,{commitment:'confirmed',disableRetryOnRateLimit:true});
   report.status='HOLD_NO_COMPLETE_PROFITABLE_ATOMIC_SIMULATION';
   for(const r of candidates.slice(0,limits(process.env.ORACLE116_LIMIT||2))){
    try{report.rows.push(await check(conn,r));}
    catch(e){if(prior.rate(e)){report.status='HOLD_RPC_429_STOPPED';report.error=clean(e);break;}
      report.rows.push({index:r.index,status:'HOLD',reason:'POOL_CHECK_FAILED',detail:clean(e)});}
    if(report.rows.length<limits(process.env.ORACLE116_LIMIT||2))await pause(1500);
   }
  }
 }
 fs.mkdirSync(path.dirname(OUT),{recursive:true});fs.writeFileSync(OUT,JSON.stringify(report,null,2));
 console.log('[ORACLE-116]',report.status,'candidates='+candidates.length,'checked='+report.rows.length);
 for(const r of report.rows)console.log('[PAIR]',JSON.stringify(r));
 console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',OUT);
}
if(require.main===module)run().catch(e=>{console.error('[HOLD]',clean(e));process.exitCode=1});
module.exports={limits,evaluate};
