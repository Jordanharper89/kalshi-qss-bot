from pathlib import Path
W=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker')
JS=r''' 'use strict';
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey}=req('@solana/web3.js');
const {NATIVE_MINT}=req('@solana/spl-token');
const BN=req('@coral-xyz/anchor').BN;
const pump=req('@pump-fun/pump-swap-sdk');
const pkg=req('@meteora-ag/dlmm'),DLMM=pkg.default||pkg.DLMM||pkg;
const source=path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
const destination=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_113_BOUNDED_QUOTES.json');
const mint=x=>{try{return new PublicKey(x).toBase58()}catch{return null}};
const scrub=x=>String(x?.message||x).replace(/(api-key=)[^&\s]+/gi,'$1[REDACTED]').replace(/https?:\/\/[^\s]+/gi,'[RPC_URL_REDACTED]').slice(0,160);
const is429=e=>/429|Too Many Requests|rate.limit/i.test(String(e?.message||e));
function candidates(raw){return(raw.rows||[]).map((r,i)=>({index:i,token:mint(r.token),pump_pool:mint(r.pump_pool),meteora_pool:mint(r.meteora_pool)})).filter(r=>r.token&&r.pump_pool&&r.meteora_pool)}
function limits(env){const n=Number(env.ORACLE113_LIMIT||2);return Number.isInteger(n)?Math.max(1,Math.min(n,4)):2}
function connection(url){return new Connection(url,{commitment:'confirmed',disableRetryOnRateLimit:true,confirmTransactionInitialTimeout:12000});}
async function inspect(conn,r){const o={index:r.index,pump_pool:r.pump_pool,meteora_pool:r.meteora_pool,status:'HOLD',reasons:[],quotes:[]};
 const online=new pump.OnlinePumpAmmSdk(conn);let p,d;
 try{p=await online.fetchPool(new PublicKey(r.pump_pool));o.pump_hydrated=true;}catch(e){if(is429(e))throw e;o.reasons.push('PUMP_HYDRATION_FAILED:'+scrub(e));return o}
 try{d=await DLMM.create(conn,new PublicKey(r.meteora_pool));o.dlmm_hydrated=true;}catch(e){if(is429(e))throw e;o.reasons.push('DLMM_HYDRATION_FAILED:'+scrub(e));return o}
 const sol=NATIVE_MINT.toBase58(),pm=[mint(p.baseMint),mint(p.quoteMint)],dm=[mint(d.lbPair.tokenXMint),mint(d.lbPair.tokenYMint)];
 if(!pm.includes(sol)||!dm.includes(sol)||!pm.includes(r.token)||!dm.includes(r.token)){o.reasons.push('PAIR_MINT_IDENTITY_MISMATCH');return o}
 for(const swapForY of [true,false]){
  const input=swapForY?dm[0]:dm[1],output=swapForY?dm[1]:dm[0];
  const row={direction:input===sol?'METEORA_TO_PUMP':'PUMP_TO_METEORA',input_mint:input,output_mint:output,status:'HOLD'};
  try{
   const arrays=await d.getBinArrayForSwap(swapForY,4);
   const rawAmount=input===sol?'10000000':null;
   if(!rawAmount){row.reason='PUMP_FIRST_LEG_OUTPUT_REQUIRED';o.quotes.push(row);continue}
   const q=d.swapQuote(new BN(rawAmount),swapForY,new BN(50),arrays,true);
   row.requested_in=rawAmount;row.consumed_in=String(q.consumedInAmount);row.out=String(q.outAmount);row.min_out=String(q.minOutAmount);row.bin_arrays=(q.binArraysPubkey||[]).map(String);
   row.partial_fill=row.consumed_in!==rawAmount;
   row.reason=row.partial_fill?'PARTIAL_FILL_NOT_EXECUTION_ADMITTED':'PUMP_SELL_QUOTE_AND_ATOMIC_SIMULATION_REQUIRED';
  }catch(e){if(is429(e))throw e;row.reason='DLMM_QUOTE_FAILED';row.detail=scrub(e)}
  o.quotes.push(row);
 }
 o.reasons.push('TWO_LEG_EXECUTABLE_NET_PROFIT_NOT_CERTIFIED');return o;
}
async function main(){const raw=JSON.parse(fs.readFileSync(source,'utf8')),rows=candidates(raw);const report={revision:'ORACLE-113',status:'HOLD_LIVE_NOT_REQUESTED',candidates:rows.length,rows:[],signing:false,broadcast:false,scanner_unchanged:true};
 if(process.argv.includes('--live')){
  if(!process.env.SOLANA_RPC_URL)report.status='HOLD_RPC_URL_REQUIRED';else{
   const conn=connection(process.env.SOLANA_RPC_URL),max=limits(process.env);report.status='HOLD_TWO_LEG_ATOMIC_SIMULATION_REQUIRED';
   for(const r of rows.slice(0,max)){
    try{report.rows.push(await inspect(conn,r))}catch(e){report.status=is429(e)?'HOLD_RPC_RATE_LIMIT':'HOLD_RPC_ERROR';report.error=scrub(e);break}
   }
  }
 }
 fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,JSON.stringify(report,null,2));
 console.log('[ORACLE-113]',report.status,'candidates='+rows.length,'checked='+report.rows.length);
 for(const r of report.rows){console.log('[PAIR]',r.index,'pump='+!!r.pump_hydrated,'dlmm='+!!r.dlmm_hydrated,'reasons='+r.reasons.join(','));for(const q of r.quotes)console.log('[QUOTE]',JSON.stringify(q))}
 console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',destination);
}
if(require.main===module)main().catch(e=>{console.error('[HOLD]',scrub(e));process.exitCode=1});
module.exports={candidates,limits,is429};
'''
TEST=r''' 'use strict';const a=require('assert'),m=require('./oracle113_bounded_sdk_quotes.cjs');const k='So11111111111111111111111111111111111111112';a.equal(m.candidates({rows:[{token:k,pump_pool:k,meteora_pool:k}]}).length,1);a.equal(m.candidates({rows:[{token:'x',pump_pool:k,meteora_pool:k}]}).length,0);a.equal(m.limits({ORACLE113_LIMIT:'28'}),4);a.equal(m.limits({ORACLE113_LIMIT:'2'}),2);a.equal(m.is429(new Error('429 Too Many Requests')),true);console.log('[PASS] ORACLE-113 five offline checks');'''
def main():
    if not (W/'oracle112_live_quote_bridge.cjs').exists():raise SystemExit('[HOLD] ORACLE-112 worker missing')
    W.mkdir(parents=True,exist_ok=True)
    for n,s in [('oracle113_bounded_sdk_quotes.cjs',JS),('oracle113_bounded_sdk_quotes.test.cjs',TEST)]: (W/n).write_text(s.strip()+'\n',encoding='utf-8')
    print('[INSTALLED] ORACLE-113 bounded native quote worker')
    print('[SCANNER] UNCHANGED [SIGNING] FALSE [BROADCAST] FALSE')
if __name__=='__main__':main()
