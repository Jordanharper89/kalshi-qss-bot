'use strict';
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey}=req('@solana/web3.js');
const registry=path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
const output=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_109_LIVE_IDENTITY.json');
const directions=new Set(['PUMP_TO_METEORA','METEORA_TO_PUMP']);
const PUMP_PROGRAM='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmKxK1vQ9aK6';
function pub(v){try{if(typeof v!=='string')return null;let p=new PublicKey(v);return p.toBase58()===PublicKey.default.toBase58()?null:p.toBase58()}catch{return null}}
function prepare(raw,now){
 const age=Number.isFinite(Number(raw.observed_unix))?now-Number(raw.observed_unix):null;
 return {age_seconds:age,rows:(raw.rows||[]).map((r,i)=>{
 const reasons=[],p=pub(r.pump_pool),m=pub(r.meteora_pool),t=pub(r.token),x=pub(r.token_x),y=pub(r.token_y);
 if(!p)reasons.push('INVALID_PUMP_POOL');if(!m)reasons.push('INVALID_METEORA_POOL');if(!t)reasons.push('INVALID_TOKEN');
 if(p&&m&&p===m)reasons.push('DUPLICATE_POOL_ADDRESS');
 if(!x||!y)reasons.push('INVALID_TOKEN_PAIR');else if(t&&t!==x&&t!==y)reasons.push('TOKEN_NOT_IN_DLMM_PAIR');
 const historical=typeof r.best_direction==='string'?r.best_direction:null;
 const direction=directions.has(historical)?historical:null;
 if(!direction)reasons.push('HISTORICAL_DIRECTION_UNUSABLE');
 return {index:i,pump_pool:p,meteora_pool:m,token:t,token_x:x,token_y:y,historical_direction:historical,direction,identity_valid:!reasons.some(v=>v!=='HISTORICAL_DIRECTION_UNUSABLE'),reasons,live_verified:false,execution_admitted:false};
 })};
}
async function verify(report,url){
 if(!url)return 'HOLD_RPC_URL_REQUIRED';
 const conn=new Connection(url,'confirmed');
 const candidates=report.rows.filter(r=>r.identity_valid);
 const keys=[...new Set(candidates.flatMap(r=>[r.pump_pool,r.meteora_pool]))];
 const accounts=new Map();
 for(let i=0;i<keys.length;i+=100){
  const batch=keys.slice(i,i+100);
  const values=await conn.getMultipleAccountsInfo(batch.map(k=>new PublicKey(k)),'confirmed');
  batch.forEach((k,j)=>accounts.set(k,values[j]));
 }
 for(const r of candidates){
  const p=accounts.get(r.pump_pool),m=accounts.get(r.meteora_pool);
  if(!p)r.reasons.push('PUMP_ACCOUNT_NOT_FOUND');
  if(!m)r.reasons.push('METEORA_ACCOUNT_NOT_FOUND');
  if(p)r.pump_owner=p.owner.toBase58();
  if(m)r.meteora_owner=m.owner.toBase58();
  // SDK-specific program-owner certification is a separate gate; never infer it from account existence.
  if(p&&m){r.live_verified=true;r.reasons.push('HOLD_SDK_OWNER_AND_MINT_VERIFICATION');}
 }
 return 'HOLD_OFFICIAL_SDK_HYDRATION_AND_FRESH_QUOTES';
}
async function main(){
 const raw=JSON.parse(fs.readFileSync(registry,'utf8'));
 if(!Array.isArray(raw.rows))throw Error('REGISTRY_ROWS_MISSING');
 const report=prepare(raw,Date.now()/1000);
 const live=process.argv.includes('--verify-live');
 let status='HOLD_LIVE_ACCOUNT_VERIFICATION_REQUIRED';
 if(live){try{status=await verify(report,process.env.SOLANA_RPC_URL)}catch(e){status='HOLD_RPC_VERIFICATION_FAILED';report.rpc_error=String(e.message).slice(0,180)}}
 const out={revision:'ORACLE-109',status,source:registry,age_seconds:report.age_seconds,identity_candidates:report.rows.filter(r=>r.identity_valid).length,live_account_verified:report.rows.filter(r=>r.live_verified).length,execution_admitted:0,signing:false,broadcast:false,rows:report.rows};
 fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(out,null,2));
 const counts={};for(const r of out.rows)for(const reason of r.reasons)counts[reason]=(counts[reason]||0)+1;
 console.log('[ORACLE-109]',status,'identity_candidates='+out.identity_candidates,'live_account_verified='+out.live_account_verified,'execution_admitted=0');
 console.log('[REASONS]',JSON.stringify(counts));console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',output);
}
if(require.main===module)main().catch(e=>{console.error('[HOLD]',String(e.message));process.exitCode=1});
module.exports={prepare,verify};
