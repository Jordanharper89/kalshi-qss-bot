from pathlib import Path
import json

W=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker')
R=Path('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json')
JS=r''' 'use strict';
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey}=req('@solana/web3.js');
const pump=req('@pump-fun/pump-swap-sdk');
const meteora=req('@meteora-ag/dlmm');
const DLMM=meteora.default||meteora.DLMM||meteora;
const out=path.resolve('runtime_state/oracle/oracle_live_execution/ORACLE_110_SDK_LIVE_POOL_PROBE.json');
const reg=path.resolve('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
function pk(v){try{return new PublicKey(v).toBase58()}catch{return null}}
function unique(raw){let seen=new Set();return raw.rows.map((r,i)=>({index:i,token:pk(r.token),pump_pool:pk(r.pump_pool),meteora_pool:pk(r.meteora_pool),token_x:pk(r.token_x),token_y:pk(r.token_y),historical_direction:r.best_direction})).filter(r=>{if(!r.token||!r.pump_pool||!r.meteora_pool||!r.token_x||!r.token_y||![r.token_x,r.token_y].includes(r.token))return false;let id=r.pump_pool+':'+r.meteora_pool;if(seen.has(id))return false;seen.add(id);return true})}
function methods(obj){let found=new Set();for(let p=obj,n=0;p&&n<4;p=Object.getPrototypeOf(p),n++)for(let k of Object.getOwnPropertyNames(p))if(typeof obj[k]==='function')found.add(k);return [...found].sort()}
function inspect(){return {pump_exports:Object.keys(pump).sort(),meteora_exports:Object.keys(meteora).sort(),dlmm_create_available:typeof DLMM.create==='function',pump_sdk_methods:typeof pump.PumpSdk==='function'?methods(pump.PumpSdk.prototype):[],pump_amm_methods:typeof pump.PumpAmmSdk==='function'?methods(pump.PumpAmmSdk.prototype):[]}}
async function main(){let raw=JSON.parse(fs.readFileSync(reg,'utf8'));let rows=unique(raw);let result={revision:'ORACLE-110',status:'HOLD_LIVE_HYDRATION_NOT_REQUESTED',historical_age_seconds:Date.now()/1000-Number(raw.observed_unix),identity_candidates:rows.length,signing:false,broadcast:false,scanner_unchanged:true,interfaces:inspect(),rows:[]};
if(process.argv.includes('--live')){
 const url=process.env.SOLANA_RPC_URL;
 if(!url){result.status='HOLD_RPC_URL_REQUIRED'}
 else {let conn=new Connection(url,'confirmed');let limit=Math.min(28,Math.max(1,Number(process.env.ORACLE110_LIMIT||1)));let selected=rows.slice(0,limit);let keys=[...new Set(selected.flatMap(r=>[r.pump_pool,r.meteora_pool]))];let accountMap=new Map();
 try{for(let i=0;i<keys.length;i+=100){let batch=keys.slice(i,i+100);let infos=await conn.getMultipleAccountsInfo(batch.map(k=>new PublicKey(k)),'confirmed');batch.forEach((k,j)=>accountMap.set(k,infos[j]));}
 for(let r of selected){let entry={index:r.index,token:r.token,pump_pool:r.pump_pool,meteora_pool:r.meteora_pool,status:'HOLD',reasons:[]};let pa=accountMap.get(r.pump_pool),ma=accountMap.get(r.meteora_pool);if(!pa)entry.reasons.push('PUMP_ACCOUNT_MISSING');if(!ma)entry.reasons.push('METEORA_ACCOUNT_MISSING');if(pa)entry.pump_owner=pa.owner.toBase58();if(ma)entry.meteora_owner=ma.owner.toBase58();
 if(ma&&typeof DLMM.create==='function'){try{let d=await DLMM.create(conn,new PublicKey(r.meteora_pool));entry.dlmm_hydrated=!!d;entry.dlmm_public_fields=Object.keys(d).filter(k=>!/(secret|private|keypair)/i.test(k)).slice(0,30)}catch(e){entry.reasons.push('DLMM_HYDRATION_FAILED');entry.dlmm_error=String(e.message).slice(0,180)}}
 if(pa){entry.reasons.push('PUMP_OFFICIAL_HYDRATOR_NOT_CERTIFIED');}
 entry.reasons.push('FRESH_EXACT_TWO_LEG_QUOTES_NOT_CERTIFIED');entry.reasons.push('ATOMIC_SIMULATION_NOT_CERTIFIED');result.rows.push(entry)}result.status='HOLD_NATIVE_QUOTE_AND_ATOMIC_SIMULATION';
 }catch(e){result.status='HOLD_RPC_FAILED';result.error=String(e.message).slice(0,180)} }
}
fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(result,null,2));console.log('[ORACLE-110]',result.status,'candidates='+result.identity_candidates,'live_rows='+result.rows.length);for(let r of result.rows)console.log('[POOL]',r.index,'dlmm='+!!r.dlmm_hydrated,'reasons='+r.reasons.join(','));console.log('[SDK]',JSON.stringify({pump_exports:result.interfaces.pump_exports.filter(k=>/sdk|pool|amm/i.test(k)),dlmm_create:result.interfaces.dlmm_create_available}));console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',out)}
if(require.main===module)main().catch(e=>{console.error('[HOLD]',String(e.message).slice(0,180));process.exitCode=1});module.exports={unique,inspect};
'''
TEST=r''' 'use strict';const assert=require('assert');const {unique,inspect}=require('./oracle110_sdk_live_pool_probe.cjs');const a='So11111111111111111111111111111111111111112',b='11111111111111111111111111111112',c='11111111111111111111111111111113',d='11111111111111111111111111111114';const r={token:a,token_x:a,token_y:b,pump_pool:c,meteora_pool:d,best_direction:null};assert.equal(unique({rows:[r,r]}).length,1);assert.equal(unique({rows:[{...r,token:c}]}).length,0);assert.equal(unique({rows:[{...r,pump_pool:'invalid'}]}).length,0);assert(Array.isArray(inspect().pump_exports));console.log('[PASS] ORACLE-110 four offline SDK/identity checks');
'''
def main():
    if not (W/'package.json').is_file() or not (W/'node_modules').is_dir() or not R.is_file():
        raise SystemExit('[HOLD] Existing SDK worker or registry missing')
    raw=json.loads(R.read_text(encoding='utf-8'))
    if not isinstance(raw.get('rows'),list):raise SystemExit('[HOLD] Invalid registry rows')
    (W/'oracle110_sdk_live_pool_probe.cjs').write_text(JS.strip()+'\n',encoding='utf-8')
    (W/'oracle110_sdk_live_pool_probe.test.cjs').write_text(TEST.strip()+'\n',encoding='utf-8')
    print('[INSTALLED] ORACLE-110; registry_rows='+str(len(raw['rows'])))
    print('[SCANNER] UNCHANGED [SIGNING] FALSE [BROADCAST] FALSE')
if __name__=='__main__':main()
