from pathlib import Path
import textwrap

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
WORKER = ROOT / 'oracle105_sdk_worker'
TARGET = WORKER / 'oracle108_registry_context.cjs'
PACKAGE = WORKER / 'package.json'
REGISTRY = Path('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json')

SOURCE = r'''
'use strict';
const fs = require('fs');
const path = require('path');
const {createRequire} = require('module');
const localRequire = createRequire(path.resolve(__dirname, 'package.json'));
const {PublicKey, Connection} = localRequire('@solana/web3.js');
const DIRECTIONS = new Set(['PUMP_TO_METEORA','METEORA_TO_PUMP']);
const KEY = '11111111111111111111111111111111';
function key(s) {
  if (typeof s !== 'string') throw Error('NOT_STRING');
  const p = new PublicKey(s);
  if (p.toBase58() === KEY) throw Error('DEFAULT_PUBLIC_KEY');
  return p.toBase58();
}
function readRegistry(filename) {
  const raw = JSON.parse(fs.readFileSync(filename,'utf8'));
  if (!Array.isArray(raw.rows)) throw Error('REGISTRY_ROWS_MISSING');
  return raw;
}
function validate(raw, now, maxAge) {
  const timestamp = Number(raw.observed_unix);
  const age = Number.isFinite(timestamp) ? now-timestamp : Infinity;
  const registryReasons=[];
  if (!Number.isFinite(timestamp)) registryReasons.push('MISSING_OBSERVED_UNIX');
  else if (age < -60) registryReasons.push('FUTURE_OBSERVED_UNIX');
  else if (age > maxAge) registryReasons.push('STALE_REGISTRY');
  if (raw.execution_authority === true || raw.broadcast === true) registryReasons.push('UNEXPECTED_SOURCE_EXECUTION_FLAGS');
  const rows=raw.rows.map((r,i)=>{
    const reasons=[...registryReasons];
    const normalized={index:i};
    for(const [field,dest] of [['pump_pool','pumpPool'],['meteora_pool','meteoraPool'],['token','token']]) {
      try { normalized[dest]=key(r[field]); } catch(e) {reasons.push('INVALID_'+field.toUpperCase()+':'+e.message);}
    }
    if(normalized.pumpPool && normalized.meteoraPool && normalized.pumpPool===normalized.meteoraPool) reasons.push('IDENTICAL_POOLS');
    if(!DIRECTIONS.has(r.best_direction)) reasons.push('INVALID_BEST_DIRECTION');
    else normalized.direction=r.best_direction;
    if(r.token_x && r.token_y) {
      try {
        const x=key(r.token_x), y=key(r.token_y);
        if(normalized.token && ![x,y].includes(normalized.token)) reasons.push('TOKEN_NOT_IN_DLMM_PAIR');
      } catch(e) {reasons.push('INVALID_TOKEN_PAIR:'+e.message);}
    } else reasons.push('TOKEN_PAIR_MISSING');
    return {index:i,ok:reasons.length===0,reasons,normalized};
  });
  return {observed_unix:timestamp,age_seconds:age,rows,accepted:rows.filter(x=>x.ok).length,rejected:rows.filter(x=>!x.ok).length};
}
async function hydrate(row, rpcUrl) {
  if (!rpcUrl) return {status:'HOLD_RPC_URL_REQUIRED'};
  const connection=new Connection(rpcUrl,'confirmed');
  const {pumpPool,meteoraPool}=row.normalized;
  const accounts=await connection.getMultipleAccountsInfo([new PublicKey(pumpPool),new PublicKey(meteoraPool)],'confirmed');
  if(!accounts[0] || !accounts[1]) return {status:'HOLD_POOL_ACCOUNT_MISSING',pump:!!accounts[0],meteora:!!accounts[1]};
  let dlmm;
  try {
    const imported=localRequire('@meteora-ag/dlmm');
    const DLMM=imported.default || imported.DLMM || imported;
    if(typeof DLMM.create!=='function') return {status:'HOLD_DLMM_CREATE_UNAVAILABLE'};
    dlmm=await DLMM.create(connection,new PublicKey(meteoraPool));
  } catch(e) {return {status:'HOLD_METEORA_HYDRATION',error:String(e.message).slice(0,160)};}
  let pump;
  try {
    const sdk=localRequire('@pump-fun/pump-swap-sdk');
    const SDK=sdk.PumpSdk || sdk.PumpSwapSDK || sdk.default;
    if(typeof SDK!=='function') return {status:'HOLD_PUMP_SDK_CONSTRUCTOR_UNVERIFIED',exports:Object.keys(sdk).slice(0,15)};
    pump=new SDK(connection);
    if(typeof pump.fetchPool!=='function' && typeof pump.getPool!=='function') return {status:'HOLD_PUMP_POOL_HYDRATOR_UNVERIFIED',methods:Object.getOwnPropertyNames(Object.getPrototypeOf(pump)).slice(0,25)};
    const method=typeof pump.fetchPool==='function'?'fetchPool':'getPool';
    await pump[method](new PublicKey(pumpPool));
  } catch(e) {return {status:'HOLD_PUMP_HYDRATION',error:String(e.message).slice(0,160)};}
  return {status:'SDK_POOLS_HYDRATED_NO_QUOTES',pump_pool:pumpPool,meteora_pool:meteoraPool,dlmm_initialized:!!dlmm,pump_initialized:!!pump};
}
async function main(){
  const args=process.argv.slice(2);
  const reg=args.includes('--registry')?args[args.indexOf('--registry')+1]:path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
  const maxAge=Number(process.env.ORACLE108_MAX_SOURCE_AGE_SECONDS||120);
  const report=validate(readRegistry(reg),Date.now()/1000,maxAge);
  const result={revision:'ORACLE-108',source:reg,accepted:report.accepted,rejected:report.rejected,age_seconds:report.age_seconds,rows:report.rows.map(({index,ok,reasons,normalized})=>({index,status:ok?'ACCEPTED':'REJECTED',reasons,pump_pool:normalized.pumpPool,meteora_pool:normalized.meteoraPool,direction:normalized.direction})),signing:false,broadcast:false};
  if(args.includes('--hydrate')) {
    const candidates=report.rows.filter(x=>x.ok);
    const limit=Math.max(0,Math.min(28,Number(args.includes('--limit')?args[args.indexOf('--limit')+1]:1)));
    result.hydration=[];
    for(const row of candidates.slice(0,limit)) result.hydration.push({index:row.index,...await hydrate(row,process.env.SOLANA_RPC_URL)});
  }
  result.status=report.accepted?'HOLD_FRESH_QUOTES_AND_ATOMIC_SIM_REQUIRED':'HOLD_NO_ADMITTED_FRESH_PAIRS';
  const out=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_108_REGISTRY_SDK_CONTEXT.json');
  fs.mkdirSync(path.dirname(out),{recursive:true});
  fs.writeFileSync(out,JSON.stringify(result,null,2));
  console.log('[ORACLE-108]',result.status,'accepted='+result.accepted,'rejected='+result.rejected,'signing=false broadcast=false');
  if(result.hydration) console.log('[HYDRATION]',JSON.stringify(result.hydration));
  console.log('[REPORT]',out);
}
if(require.main===module) main().catch(e=>{console.error('[HOLD]',String(e.message).slice(0,200));process.exitCode=1;});
module.exports={validate,readRegistry,hydrate};
'''

TEST = r'''
'use strict';
const assert=require('assert');
const {validate}=require('./oracle108_registry_context.cjs');
const A='So11111111111111111111111111111111111111112';
const B='11111111111111111111111111111112';
const C='11111111111111111111111111111113';
const D='11111111111111111111111111111114';
const base={pump_pool:A,meteora_pool:B,token:C,token_x:C,token_y:D,best_direction:'METEORA_TO_PUMP'};
const now=1800000000;
let v=validate({observed_unix:now,rows:[base]},now,120);
assert.equal(v.accepted,1);
v=validate({observed_unix:now-121,rows:[base]},now,120);
assert(v.rows[0].reasons.includes('STALE_REGISTRY'));
v=validate({observed_unix:now,rows:[{...base,best_direction:'OTHER'}]},now,120);
assert(v.rows[0].reasons.includes('INVALID_BEST_DIRECTION'));
v=validate({observed_unix:now,rows:[{...base,pump_pool:'bad'}]},now,120);
assert(v.rows[0].reasons.some(x=>x.startsWith('INVALID_PUMP_POOL')));
v=validate({observed_unix:now,rows:[{...base,token:D,token_x:A,token_y:C}]},now,120);
assert(v.rows[0].reasons.includes('TOKEN_NOT_IN_DLMM_PAIR'));
console.log('[PASS] ORACLE-108 five deterministic validation checks');
'''

def main():
    if not PACKAGE.is_file():
        raise SystemExit('[HOLD] ORACLE-105 worker package.json missing; no files changed')
    if not REGISTRY.is_file():
        raise SystemExit('[HOLD] Real 28-pair registry missing; no files changed')
    if not (WORKER / 'node_modules').is_dir():
        raise SystemExit('[HOLD] Worker node_modules missing; no files changed')
    import json
    obj=json.loads(REGISTRY.read_text(encoding='utf-8'))
    if not isinstance(obj.get('rows'),list):
        raise SystemExit('[HOLD] Registry rows invalid; no files changed')
    TARGET.write_text(SOURCE.strip()+'\n',encoding='utf-8')
    (WORKER/'oracle108_registry_context.test.cjs').write_text(TEST.strip()+'\n',encoding='utf-8')
    print('[INSTALLED] ORACLE-108 registry SDK context; registry rows='+str(len(obj['rows'])))
    print('[SCANNER] UNCHANGED [SIGNING] FALSE [BROADCAST] FALSE')

if __name__=='__main__':
    main()
