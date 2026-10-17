"use strict";
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey,SystemProgram}=req('@solana/web3.js');
const {NATIVE_MINT}=req('@solana/spl-token');
const BN=req('@coral-xyz/anchor').BN;
const pump=req('@pump-fun/pump-swap-sdk');
const pkg=req('@meteora-ag/dlmm'),DLMM=pkg.default||pkg.DLMM||pkg;
const old=require('./oracle115_budget_bounded_quotes.cjs');
const prev=require('./oracle116_liquidity_first.cjs');
const SRC=path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
const OUT=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_117_CANDIDATE_ROTATION.json');
const clean=e=>String(e?.message||e).replace(/api-key=[^&\s]+/gi,'api-key=[REDACTED]').replace(/https?:\/\/[^\s]+/gi,'[RPC_REDACTED]').slice(0,160);
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const order=(rows,start,count)=>rows.filter(r=>r.index>=start).slice(0,count);
const bounds=q=>({consumed:String(q.consumedInAmount),min:String(q.minOutAmount),out:String(q.outAmount)});
async function inspect(conn,r){
 const result={index:r.index,token:r.token,status:'HOLD'};
 const sdk=new pump.OnlinePumpAmmSdk(conn);
 const s=await sdk.swapSolanaState(new PublicKey(r.pump),SystemProgram.programId);
 const d=await DLMM.create(conn,new PublicKey(r.dlmm));
 const pm=[s.pool.baseMint.toBase58(),s.pool.quoteMint.toBase58()];
 const dm=[d.lbPair.tokenXMint.toBase58(),d.lbPair.tokenYMint.toBase58()];
 if(pm[0]!==r.token||pm[1]!==NATIVE_MINT.toBase58()||!dm.includes(r.token)||!dm.includes(NATIVE_MINT.toBase58()))return {...result,reason:'MINT_MISMATCH'};
 const budget='10000000',buy=old.boundedPumpBuy(s,budget);
 if(BigInt(buy.max_quote)>BigInt(budget))return {...result,reason:'BUDGET_INVARIANT'};
 const swapForY=dm[0]===r.token;
 const arrays=await d.getBinArrayForSwap(swapForY,4);
 let q;
 try{q=d.swapQuote(new BN(buy.base),swapForY,new BN(50),arrays,false)}
 catch(e){if(old.rate(e))throw e;return {...result,reason:'DLMM_QUOTE_FAILED',detail:clean(e)}}
 const verdict=prev.evaluate(q,buy,budget);
 return {...result,status:verdict.positive_gross?'POSITIVE_GROSS_QUOTE_ONLY':'HOLD',quote:verdict,bin_arrays:arrays.length,execution_admitted:false};
}
async function main(){
 const rows=old.rows(JSON.parse(fs.readFileSync(SRC,'utf8')));
 const start=Math.max(0,Math.min(rows.length,Number(process.env.ORACLE117_START||2)|0));
 const count=Math.max(1,Math.min(4,Number(process.env.ORACLE117_COUNT||2)|0));
 const report={revision:'ORACLE-117',status:'HOLD_NOT_LIVE',start,count,candidates:rows.length,results:[],signing:false,broadcast:false,execution_admitted:false};
 if(process.argv.includes('--live')){
  if(!process.env.SOLANA_RPC_URL)report.status='HOLD_RPC_URL_REQUIRED';
  else{
   const conn=new Connection(process.env.SOLANA_RPC_URL,{commitment:'confirmed',disableRetryOnRateLimit:true});
   report.status='HOLD_NO_ATOMIC_SIMULATION';
   for(const r of order(rows,start,count)){
    try{report.results.push(await inspect(conn,r))}
    catch(e){if(old.rate(e)){report.status='HOLD_RPC_RATE_LIMIT_STOP';report.error=clean(e);break}report.results.push({index:r.index,status:'HOLD',reason:'POOL_ERROR',detail:clean(e)})}
    if(report.results.length<count)await wait(2000);
   }
  }
 }
 fs.mkdirSync(path.dirname(OUT),{recursive:true});fs.writeFileSync(OUT,JSON.stringify(report,null,2));
 console.log('[ORACLE-117]',report.status,'checked='+report.results.length,'start='+start);
 for(const r of report.results)console.log('[PAIR]',JSON.stringify(r));
 console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',OUT);
}
if(require.main===module)main().catch(e=>{console.error('[HOLD]',clean(e));process.exitCode=1});
module.exports={order,bounds};
