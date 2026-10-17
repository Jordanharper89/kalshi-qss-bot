"""ORACLE-107: frozen-scanner output to official-SDK pool identity bridge (read-only)."""
from pathlib import Path
import sys

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker')
FILES = {
'oracle107.mjs': r'''import fs from 'node:fs';
import {PublicKey} from '@solana/web3.js';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const DLMM=require('@meteora-ag/dlmm');
const {OnlinePumpAmmSdk}=require('@pump-fun/pump-swap-sdk');
const hold=x=>{throw Error('ORACLE107_HOLD_'+x)};
const pk=x=>{try{return new PublicKey(x).toBase58()}catch{return null}};
const get=(x,...keys)=>{for(const k of keys)if(x?.[k]!=null)return x[k];return null};
const isObj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const same=(a,b)=>a&&b&&a===b;
export function identify(row){
 if(!isObj(row))hold('ROW_NOT_OBJECT');
 const pump=pk(get(row,'pump_pool','pumpswap_pool','pumpPool','pump_pool_address'));
 const meteora=pk(get(row,'meteora_pool','dlmm_pool','meteoraPool','lb_pair','lbPair'));
 const token=pk(get(row,'token','token_mint','tokenMint','mint'));
 const direction=get(row,'direction','route');
 if(!pump||!meteora||!token)hold('EXPLICIT_POOL_AND_TOKEN_IDS_REQUIRED');
 if(same(pump,meteora)||same(pump,token)||same(meteora,token))hold('DUPLICATE_IDENTITIES');
 if(!['PUMP_TO_METEORA','METEORA_TO_PUMP'].includes(direction))hold('DIRECTION_REQUIRED');
 return {pump_pool:pump,meteora_pool:meteora,token,direction};
}
export function candidates(document){
 if(Array.isArray(document))return document;
 if(!isObj(document))hold('DOCUMENT_SHAPE');
 for(const k of ['opportunities','pairs','routes','candidates','items']){
  if(Array.isArray(document[k]))return document[k];
 }
 if(document.pump_pool||document.pumpswap_pool||document.pumpPool)return [document];
 hold('NO_SUPPORTED_ROWS');
}
export function discover(document){
 const rows=candidates(document),accepted=[],holds=[];
 for(let i=0;i<rows.length;i++){
  try{accepted.push({source_index:i,...identify(rows[i])})}
  catch(e){holds.push({source_index:i,reason:String(e.message)})}
 }
 return {source_rows:rows.length,accepted,holds,signing:false,broadcast:false};
}
export function sdkAvailable(){
 if(typeof DLMM.create!=='function'||typeof DLMM.prototype.swap!=='function')hold('METEORA_SDK');
 if(typeof OnlinePumpAmmSdk.prototype.fetchPool!=='function'||typeof OnlinePumpAmmSdk.prototype.swapSolanaState!=='function')hold('PUMP_SDK');
 return true;
}
export async function hydrateMeteora(connection,identity){
 sdkAvailable();
 if(!connection||typeof connection.getAccountInfo!=='function')hold('RPC_CONNECTION_REQUIRED');
 const pool=await DLMM.create(connection,new PublicKey(identity.meteora_pool));
 if(!pool||typeof pool.swap!=='function'||typeof pool.getBinArrayForSwap!=='function')hold('METEORA_HYDRATION');
 return pool;
}
export function requirePumpState(context){
 if(!context?.pumpSdk||!context?.pumpState)hold('OFFICIAL_PUMP_HYDRATION_REQUIRED');
 if(typeof context.pumpSdk.buyInstructions!=='function'||typeof context.pumpSdk.sellInstructions!=='function')hold('PUMP_BUILDER_REQUIRED');
 return context;
}
if(process.argv[1]?.endsWith('oracle107.mjs')){
 try{
  sdkAvailable();
  const file=process.argv[2];
  if(!file){console.log(JSON.stringify({status:'HOLD_SCANNER_SOURCE_REQUIRED',sdk_interfaces:'PASS',signing:false,broadcast:false}));}
  else{
   const result=discover(JSON.parse(fs.readFileSync(file,'utf8')));
   console.log(JSON.stringify({status:result.accepted.length?'POOL_IDENTITIES_DISCOVERED_NO_LIVE_HYDRATION':'HOLD_NO_EXPLICIT_POOL_IDENTITIES',...result}));
   if(!result.accepted.length)process.exitCode=2;
  }
 }catch(e){console.error(String(e.message));process.exitCode=1}
}
''',
'test/oracle107.test.mjs': r'''import test from 'node:test';
import assert from 'node:assert/strict';
import {discover,identify,sdkAvailable,requirePumpState} from '../oracle107.mjs';
const a='So11111111111111111111111111111111111111112';
const b='11111111111111111111111111111111';
const c='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA';
const good={pump_pool:a,meteora_pool:b,token:c,direction:'PUMP_TO_METEORA'};
test('installed official SDK hydration interfaces',()=>assert.equal(sdkAvailable(),true));
test('accept explicit pool identities',()=>assert.equal(identify(good).pump_pool,a));
test('reject capture with only instruction accounts',()=>assert.equal(discover({candidates:[{name:'capture',instructions:[{accounts:[]}]}]}).accepted.length,0));
test('reject missing direction',()=>assert.throws(()=>identify({...good,direction:null}),/DIRECTION_REQUIRED/));
test('reject duplicate pool',()=>assert.throws(()=>identify({...good,meteora_pool:a}),/DUPLICATE_IDENTITIES/));
test('reject absent PumpSwap hydrated state',()=>assert.throws(()=>requirePumpState({}),/OFFICIAL_PUMP_HYDRATION_REQUIRED/));
test('mixed rows preserve rejection lineage',()=>assert.equal(discover({pairs:[good,{}]}).holds.length,1));
''',
'ORACLE107_README.txt': '''ORACLE-107 is a read-only, offline source-to-SDK identity bridge.
Run: node oracle107.mjs <existing-scanner-json-file>
Only explicitly named PumpSwap pool, Meteora pool, token mint, direction are admitted.
Old ORACLE-094 PUBLIC_ACCOUNT_KEYS_ONLY captures intentionally HOLD.
Meteora SDK hydration is implemented as a callable function; it requires a real
Connection and exact pool identity. PumpSwap SDK constructor/hydration and exact
pricing are NOT connected yet. This is NOT a live executable trade path.
No RPC calls from CLI, no key access, signing, broadcasting or scanner edits.
'''
}
def check():
    assert 'sendTransaction' not in FILES['oracle107.mjs']
    assert 'DLMM.create' in FILES['oracle107.mjs']
    assert 'PUBLIC_ACCOUNT_KEYS_ONLY' in FILES['ORACLE107_README.txt']
    print('[PASS] ORACLE107_INSTALLER_STATIC_TESTS')
def install():
    if not (ROOT/'oracle106.mjs').is_file():
        raise SystemExit('[HOLD] Run from repository root after ORACLE-106')
    for name, content in FILES.items():
        path=ROOT/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content,encoding='utf-8')
        print('[INSTALLED]',path)
    print('[STATUS] READ_ONLY_SOURCE_BRIDGE_INSTALLED; LIVE_PUMP_HYDRATION_NOT_CONNECTED')
    print('[SAFETY] NO_RPC_FROM_CLI NO_SIGNING NO_BROADCAST SCANNER_FROZEN')
if __name__=='__main__':
    check()
    if '--test' not in sys.argv: install()