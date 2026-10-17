from pathlib import Path
import subprocess, shutil
W=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker')
JS=r''' 'use strict';
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey,SystemProgram}=req('@solana/web3.js');
const {NATIVE_MINT}=req('@solana/spl-token');
const BN=req('@coral-xyz/anchor').BN;
const pump=req('@pump-fun/pump-swap-sdk');
const dlmmPkg=req('@meteora-ag/dlmm'),DLMM=dlmmPkg.default||dlmmPkg.DLMM||dlmmPkg;
const SRC=path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
const OUT=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_114_PUMP_FIRST_QUOTES.json');
const mint=x=>{try{return new PublicKey(x).toBase58()}catch{return null}};
const clean=e=>String(e?.message||e).replace(/api-key=[^&\s]+/gi,'api-key=[REDACTED]').replace(/https?:\/\/[^\s]+/gi,'[RPC_URL_REDACTED]').slice(0,160);
const rate=e=>/429|Too Many Requests|rate.limit/i.test(String(e?.message||e));
const rows=raw=>(raw.rows||[]).map((r,i)=>({index:i,token:mint(r.token),pump:mint(r.pump_pool),dlmm:mint(r.meteora_pool)})).filter(r=>r.token&&r.pump&&r.dlmm);
const slippage=new BN(50);
function argsFromState(s){const {pool,poolBaseAmount,poolQuoteAmount,globalConfig,feeConfig,baseMint,baseMintAccount}=s;
 if(!pool||!poolBaseAmount||!poolQuoteAmount||!globalConfig)throw Error('PUMP_STATE_INCOMPLETE');
 return {baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,virtualQuoteReserves:pool.virtualQuoteReserves,feeBucketsTotal:pool.protocolFees&&pool.creatorFees?pool.protocolFees.add(pool.creatorFees):undefined,globalConfig,feeConfig,baseMint,baseMintAccount,coinCreator:pool.coinCreator,creator:pool.creator,quoteMint:pool.quoteMint,isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};}
function pumpBuyQuote(s,lamports){if(typeof pump.buyQuoteInput!=='function')throw Error('OFFICIAL_BUY_QUOTE_INPUT_UNAVAILABLE');
 const q=pump.buyQuoteInput({...argsFromState(s),quote:new BN(lamports),slippage});
 if(!q?.base||!q?.maxQuote)throw Error('PUMP_QUOTE_SHAPE_INVALID');
 const base=BigInt(q.base.toString()),max=BigInt(q.maxQuote.toString());
 if(base<=0n||max<=0n)throw Error('PUMP_QUOTE_NONPOSITIVE');
 return {base:base.toString(),max_quote:max.toString()};}
async function inspect(conn,r){const o={index:r.index,token:r.token,status:'HOLD',reasons:[],quotes:[]};
 const online=new pump.OnlinePumpAmmSdk(conn);let s,d;
 try{s=await online.swapSolanaState(new PublicKey(r.pump),SystemProgram.programId);o.pump=true;
 d=await DLMM.create(conn,new PublicKey(r.dlmm));o.dlmm=true;}catch(e){if(rate(e))throw e;o.reasons.push('HYDRATION:'+clean(e));return o}
 const sol=NATIVE_MINT.toBase58(),pm=[mint(s.pool.baseMint),mint(s.pool.quoteMint)],dm=[mint(d.lbPair.tokenXMint),mint(d.lbPair.tokenYMint)];
 if(pm[0]!==r.token||pm[1]!==sol||!dm.includes(sol)||!dm.includes(r.token)){o.reasons.push('POOL_MINT_MISMATCH');return o}
 const swapForY=dm[0]===r.token;
 let arrays;
 try{arrays=await d.getBinArrayForSwap(swapForY,4)}catch(e){if(rate(e))throw e;o.reasons.push('BIN_ARRAYS:'+clean(e));return o}
 for(const lamports of ['10000000','15000000','20000000','25000000','30000000']){
  const q={direction:'PUMP_TO_METEORA',input_lamports:lamports,status:'HOLD'};
  try{const buy=pumpBuyQuote(s,lamports);q.pump_token_out=buy.base;q.pump_max_sol_in=buy.max_quote;
   if(BigInt(buy.max_quote)>BigInt(lamports)){q.reason='PUMP_MAX_COST_EXCEEDS_SIZE';o.quotes.push(q);continue}
   const dl=d.swapQuote(new BN(buy.base),swapForY,new BN(50),arrays,false);
   q.meteora_consumed=String(dl.consumedInAmount);q.meteora_sol_out=String(dl.outAmount);q.meteora_min_sol_out=String(dl.minOutAmount);
   if(q.meteora_consumed!==buy.base){q.reason='DLMM_PARTIAL_FILL';}
   else{q.gross_delta_lamports=(BigInt(q.meteora_sol_out)-BigInt(lamports)).toString();q.reason='NATIVE_ATOMIC_AND_NET_FEES_NOT_CERTIFIED';}
  }catch(e){if(rate(e))throw e;q.reason='OFFICIAL_QUOTE_FAILED';q.detail=clean(e)}o.quotes.push(q)
 }
 o.reasons.push('NO_EXECUTION_ADMISSION');return o;
}
async function main(){const r=rows(JSON.parse(fs.readFileSync(SRC,'utf8'))),report={revision:'ORACLE-114',status:'HOLD_NOT_LIVE',candidates:r.length,rows:[],signing:false,broadcast:false,scanner_unchanged:true};
 if(process.argv.includes('--live')){if(!process.env.SOLANA_RPC_URL)report.status='HOLD_RPC_URL_REQUIRED';else{
  const conn=new Connection(process.env.SOLANA_RPC_URL,{commitment:'confirmed',disableRetryOnRateLimit:true});report.status='HOLD_ATOMIC_SIMULATION_REQUIRED';
  const limit=Math.max(1,Math.min(2,Number(process.env.ORACLE114_LIMIT||1)||1));
  for(const row of r.slice(0,limit)){try{report.rows.push(await inspect(conn,row))}catch(e){report.status=rate(e)?'HOLD_RPC_429':'HOLD_RPC_ERROR';report.error=clean(e);break}}
 }}
 fs.mkdirSync(path.dirname(OUT),{recursive:true});fs.writeFileSync(OUT,JSON.stringify(report,null,2));
 console.log('[ORACLE-114]',report.status,'candidates='+r.length,'checked='+report.rows.length);
 for(const r of report.rows){console.log('[PAIR]',r.index,'pump='+!!r.pump,'dlmm='+!!r.dlmm,'reasons='+r.reasons.join(','));for(const q of r.quotes)console.log('[QUOTE]',JSON.stringify(q))}
 console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',OUT)
}
if(require.main===module)main().catch(e=>{console.error('[HOLD]',clean(e));process.exitCode=1});
module.exports={rows,argsFromState,pumpBuyQuote,rate};
'''
TEST=r''' 'use strict';
const assert=require('assert'),m=require('./oracle114_pump_first_quotes.cjs');
const k='So11111111111111111111111111111111111111112';
assert.equal(m.rows({rows:[{token:k,pump_pool:k,meteora_pool:k}]}).length,1);
assert.equal(m.rows({rows:[{token:'bad',pump_pool:k,meteora_pool:k}]}).length,0);
assert(m.rate(new Error('429 Too Many Requests')));
assert.throws(()=>m.argsFromState({}),/PUMP_STATE_INCOMPLETE/);
assert.equal(typeof m.pumpBuyQuote,'function');
console.log('[PASS] ORACLE-114 five offline contract checks');
'''
def main():
    if not (W/'oracle113_bounded_sdk_quotes.cjs').exists(): raise SystemExit('[HOLD] ORACLE-113 not installed')
    W.mkdir(parents=True,exist_ok=True)
    for name,source in [('oracle114_pump_first_quotes.cjs',JS),('oracle114_pump_first_quotes.test.cjs',TEST)]:
        (W/name).write_text(source.strip()+'\n',encoding='utf-8')
    print('[INSTALLED] ORACLE-114 official PumpSwap-first + Meteora second-leg quote path')
    print('[SCANNER] UNCHANGED [SIGNING] FALSE [BROADCAST] FALSE')
if __name__=='__main__':main()
