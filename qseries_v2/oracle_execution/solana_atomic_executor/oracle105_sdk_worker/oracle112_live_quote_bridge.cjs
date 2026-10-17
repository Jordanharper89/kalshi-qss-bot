'use strict';
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey}=req('@solana/web3.js');
const {NATIVE_MINT}=req('@solana/spl-token');
const BN=req('@coral-xyz/anchor').BN;
const pump=req('@pump-fun/pump-swap-sdk');
const dlmmPkg=req('@meteora-ag/dlmm');
const DLMM=dlmmPkg.default||dlmmPkg.DLMM||dlmmPkg;
const source=path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
const destination=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_112_FRESH_QUOTES.json');
const key=x=>{try{return new PublicKey(x).toBase58()}catch{return null}};
const error=e=>String(e?.message||e).replace(/(api-key=)[^&\s]+/gi,'$1[REDACTED]').slice(0,200);
function validRows(raw){return (raw.rows||[]).map((r,index)=>({index,token:key(r.token),pump_pool:key(r.pump_pool),meteora_pool:key(r.meteora_pool),historical_direction:r.best_direction})).filter(x=>x.token&&x.pump_pool&&x.meteora_pool)}
function candidateAmounts(){return [10000000n,15000000n,20000000n,25000000n,30000000n]}
function sdkMethods(){return {pump_fetch:typeof pump.OnlinePumpAmmSdk?.prototype.fetchPool==='function',pump_swap_state:typeof pump.OnlinePumpAmmSdk?.prototype.swapSolanaState==='function',dlmm_quote:typeof DLMM.prototype.swapQuote==='function',dlmm_bins:typeof DLMM.prototype.getBinArrayForSwap==='function'}}
async function inspectPair(conn,r){
 const out={index:r.index,token:r.token,pump_pool:r.pump_pool,meteora_pool:r.meteora_pool,status:'HOLD',reasons:[],quotes:[]};
 let p,d;
 try{p=await new pump.OnlinePumpAmmSdk(conn).fetchPool(new PublicKey(r.pump_pool));out.pump_hydrated=!!p;out.pump_mints=[key(p.baseMint),key(p.quoteMint)];if(!out.pump_mints.includes(r.token))out.reasons.push('PUMP_TOKEN_MISMATCH');}catch(e){out.reasons.push('PUMP_HYDRATION_FAILED');out.pump_error=error(e)}
 try{d=await DLMM.create(conn,new PublicKey(r.meteora_pool));out.dlmm_hydrated=!!d;out.dlmm_mints=[key(d.lbPair.tokenXMint),key(d.lbPair.tokenYMint)];if(!out.dlmm_mints.includes(r.token))out.reasons.push('DLMM_TOKEN_MISMATCH');}catch(e){out.reasons.push('DLMM_HYDRATION_FAILED');out.dlmm_error=error(e)}
 if(!p||!d||out.reasons.length)return out;
 const native=NATIVE_MINT.toBase58();
 if(!out.pump_mints.includes(native)||!out.dlmm_mints.includes(native)){out.reasons.push('NOT_DIRECT_SOL_PAIR');return out}
 if(out.pump_mints.find(x=>x!==native)!==out.dlmm_mints.find(x=>x!==native)){out.reasons.push('POOL_BASE_MINT_DISAGREEMENT');return out}
 for(const amount of candidateAmounts()){
  for(const direction of ['PUMP_TO_METEORA','METEORA_TO_PUMP']){
   const item={direction,input_lamports:amount.toString(),status:'HOLD',reasons:[]};
   // Meteora native-input leg can be priced independently without inventing PumpSwap output.
   if(direction==='METEORA_TO_PUMP'){
    try{
     const swapForY=key(d.lbPair.tokenXMint)===native;
     const bins=await d.getBinArrayForSwap(swapForY);
     const q=d.swapQuote(new BN(amount.toString()),swapForY,new BN(50),bins,false);
     item.meteora_quote={in_amount:String(q.consumedInAmount??amount),out_amount:String(q.outAmount),min_out_amount:String(q.minOutAmount),bin_arrays:(q.binArraysPubkey||[]).map(String)};
     if(!q.outAmount||!q.minOutAmount)item.reasons.push('DLMM_QUOTE_MISSING_OUTPUT');
    }catch(e){item.reasons.push('DLMM_QUOTE_FAILED');item.detail=error(e)}
   }
   item.reasons.push('PUMP_EXACT_QUOTE_NOT_YET_CONNECTED','TWO_LEG_NET_PROFIT_UNVERIFIED','ATOMIC_SIMULATION_NOT_CERTIFIED');
   out.quotes.push(item);
  }
 }
 out.reasons.push('TWO_LEG_QUOTE_INCOMPLETE');return out;
}
async function main(){const raw=JSON.parse(fs.readFileSync(source,'utf8'));const rows=validRows(raw);const live=process.argv.includes('--live');const result={revision:'ORACLE-112',status:'HOLD_LIVE_NOT_REQUESTED',source_age_seconds:Date.now()/1000-Number(raw.observed_unix||0),candidates:rows.length,sdk:sdkMethods(),signing:false,broadcast:false,scanner_unchanged:true,rows:[]};
 if(live){if(!process.env.SOLANA_RPC_URL)result.status='HOLD_RPC_URL_REQUIRED';else{const conn=new Connection(process.env.SOLANA_RPC_URL,'confirmed');const limit=Math.min(rows.length,Math.max(1,Number(process.env.ORACLE112_LIMIT||1)));for(const r of rows.slice(0,limit))result.rows.push(await inspectPair(conn,r));result.status='HOLD_TWO_LEG_NATIVE_QUOTE_AND_SIMULATION'}}
 fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,JSON.stringify(result,null,2));console.log('[ORACLE-112]',result.status,'candidates='+rows.length,'live_rows='+result.rows.length);for(const r of result.rows){console.log('[PAIR]',r.index,'pump='+!!r.pump_hydrated,'dlmm='+!!r.dlmm_hydrated,'quote_attempts='+r.quotes.length,'reasons='+r.reasons.join(','));for(const q of r.quotes)if(q.meteora_quote)console.log('[DLMM_FRESH_QUOTE]',q.direction,q.input_lamports,JSON.stringify(q.meteora_quote));else if(q.detail)console.log('[QUOTE_HOLD]',q.direction,q.input_lamports,q.detail)}console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',destination)}
if(require.main===module)main().catch(e=>{console.error('[HOLD]',error(e));process.exitCode=1});module.exports={validRows,candidateAmounts,sdkMethods};
