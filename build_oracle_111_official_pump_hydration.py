from pathlib import Path
W=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker')
JS=r''' 'use strict';
const fs=require('fs'),path=require('path');
const {createRequire}=require('module');
const req=createRequire(path.join(__dirname,'package.json'));
const {Connection,PublicKey}=req('@solana/web3.js');
const pump=req('@pump-fun/pump-swap-sdk');
const meteora=req('@meteora-ag/dlmm');
const DLMM=meteora.default||meteora.DLMM||meteora;
const ROOT=process.cwd();
const registry=path.join(ROOT,'runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json');
const report=path.join(ROOT,'runtime_state/oracle/oracle_live_execution/ORACLE_111_OFFICIAL_HYDRATION.json');
function safeKey(v){try{return new PublicKey(v).toBase58()}catch{return null}}
function candidates(raw){return (raw.rows||[]).map((r,index)=>({index,token:safeKey(r.token),token_x:safeKey(r.token_x),token_y:safeKey(r.token_y),pump_pool:safeKey(r.pump_pool),meteora_pool:safeKey(r.meteora_pool),historical_direction:r.best_direction})).filter(r=>r.token&&r.pump_pool&&r.meteora_pool&&[r.token_x,r.token_y].includes(r.token));}
function err(e){return String(e&&e.message||e).replace(/(api-key=)[^&\s]+/gi,'$1[REDACTED]').slice(0,240)}
function pumpClient(conn){if(typeof pump.OnlinePumpAmmSdk!=='function')throw Error('ONLINE_PUMP_SDK_UNAVAILABLE');return new pump.OnlinePumpAmmSdk(conn)}
async function hydratePump(conn,address){const client=pumpClient(conn);if(typeof client.fetchPool!=='function')throw Error('FETCH_POOL_UNAVAILABLE');return await client.fetchPool(new PublicKey(address))}
async function hydrateDlmm(conn,address){if(typeof DLMM.create!=='function')throw Error('DLMM_CREATE_UNAVAILABLE');return await DLMM.create(conn,new PublicKey(address))}
async function run(){const raw=JSON.parse(fs.readFileSync(registry,'utf8'));const rows=candidates(raw);const live=process.argv.includes('--live');const result={revision:'ORACLE-111',status:'HOLD_LIVE_NOT_REQUESTED',source_age_seconds:Date.now()/1000-Number(raw.observed_unix||0),candidates:rows.length,signing:false,broadcast:false,scanner_unchanged:true,rows:[]};
if(live){if(!process.env.SOLANA_RPC_URL){result.status='HOLD_RPC_URL_REQUIRED'}else{const conn=new Connection(process.env.SOLANA_RPC_URL,'confirmed');const limit=Math.min(rows.length,Math.max(1,Number(process.env.ORACLE111_LIMIT||1)));for(const r of rows.slice(0,limit)){const item={index:r.index,pump_pool:r.pump_pool,meteora_pool:r.meteora_pool,token:r.token,status:'HOLD',reasons:[]};try{const pool=await hydratePump(conn,r.pump_pool);if(!pool)throw Error('EMPTY_PUMP_POOL');item.pump_hydrated=true;item.pump_base_mint=safeKey(pool.baseMint||pool.base_mint);item.pump_quote_mint=safeKey(pool.quoteMint||pool.quote_mint);if(item.pump_base_mint&&item.pump_quote_mint&&!([item.pump_base_mint,item.pump_quote_mint].includes(r.token)))item.reasons.push('PUMP_TOKEN_MISMATCH')}catch(e){item.pump_hydrated=false;item.reasons.push('PUMP_HYDRATION_FAILED');item.pump_error=err(e)}try{const dlmm=await hydrateDlmm(conn,r.meteora_pool);if(!dlmm)throw Error('EMPTY_DLMM');item.dlmm_hydrated=true;const state=dlmm.lbPair||{};item.dlmm_token_x=safeKey(state.tokenXMint||state.tokenX);item.dlmm_token_y=safeKey(state.tokenYMint||state.tokenY);if(item.dlmm_token_x&&item.dlmm_token_y&&!([item.dlmm_token_x,item.dlmm_token_y].includes(r.token)))item.reasons.push('DLMM_TOKEN_MISMATCH')}catch(e){item.dlmm_hydrated=false;item.reasons.push('DLMM_HYDRATION_FAILED');item.dlmm_error=err(e)}item.reasons.push('FRESH_EXACT_BIDIRECTIONAL_QUOTES_REQUIRED','NATIVE_ATOMIC_SIMULATION_REQUIRED');result.rows.push(item)}result.status='HOLD_FRESH_QUOTES_AND_ATOMIC_SIMULATION'}}
fs.mkdirSync(path.dirname(report),{recursive:true});fs.writeFileSync(report,JSON.stringify(result,null,2));console.log('[ORACLE-111]',result.status,'candidates='+result.candidates,'live_rows='+result.rows.length);for(const r of result.rows)console.log('[POOL]',r.index,'pump='+!!r.pump_hydrated,'dlmm='+!!r.dlmm_hydrated,'reasons='+r.reasons.join(','),'pump_error='+(r.pump_error||'none'),'dlmm_error='+(r.dlmm_error||'none'));console.log('[SIGNING] FALSE [BROADCAST] FALSE [SCANNER] UNCHANGED');console.log('[REPORT]',report)}
if(require.main===module)run().catch(e=>{console.error('[HOLD]',err(e));process.exitCode=1});module.exports={safeKey,candidates,pumpClient,hydratePump,hydrateDlmm};
'''
TEST=r''' 'use strict';const assert=require('assert');const m=require('./oracle111_official_hydration.cjs');const sol='So11111111111111111111111111111111111111112';const other='11111111111111111111111111111112';const row={token:sol,token_x:sol,token_y:other,pump_pool:sol,meteora_pool:other};assert.equal(m.candidates({rows:[row]}).length,1);assert.equal(m.candidates({rows:[{...row,token:'bad'}]}).length,0);assert.equal(m.safeKey('bad'),null);assert.equal(typeof m.hydratePump,'function');assert.equal(typeof m.hydrateDlmm,'function');console.log('[PASS] ORACLE-111 five offline checks');
'''
def main():
    if not (W/'oracle110_sdk_live_pool_probe.cjs').exists() or not (W/'node_modules').is_dir():
        raise SystemExit('[HOLD] ORACLE-110 worker or SDK modules missing')
    for name,src in [('oracle111_official_hydration.cjs',JS),('oracle111_official_hydration.test.cjs',TEST)]:
        (W/name).write_text(src.strip()+'\n',encoding='utf-8')
    print('[INSTALLED] ORACLE-111 official PumpSwap + Meteora hydration')
    print('[SCANNER] UNCHANGED [SIGNING] FALSE [BROADCAST] FALSE')
if __name__=='__main__':main()
