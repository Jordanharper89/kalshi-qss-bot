"""ORACLE-106 full installer: SDK-native two-leg builder, simulation only."""
from pathlib import Path
import sys

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker')
FILES = {
'oracle106.mjs': r'''import {createRequire} from 'node:module';
import {TransactionInstruction} from '@solana/web3.js';
import {compileAndSimulate, validateNativeLegs} from './worker.mjs';
const require=createRequire(import.meta.url);
const DLMM=require('@meteora-ag/dlmm');
const {PumpAmmSdk}=require('@pump-fun/pump-swap-sdk');
const hold=(reason)=>{throw Error('ORACLE106_HOLD_'+reason)};
const integer=(x)=>Number.isSafeInteger(x)&&x>0;
const ixArray=(x)=>{
 if(Array.isArray(x)) return x;
 if(x?.instructions && Array.isArray(x.instructions)) return x.instructions;
 hold('SDK_RETURN_NOT_INSTRUCTIONS');
};
export function verifySdk(){
 if(typeof DLMM.create!=='function'||typeof DLMM.prototype.swap!=='function'||
    typeof DLMM.prototype.swapQuote!=='function'||typeof DLMM.prototype.getBinArrayForSwap!=='function'||
    typeof PumpAmmSdk.prototype.buyInstructions!=='function'||typeof PumpAmmSdk.prototype.sellInstructions!=='function') hold('SDK_INTERFACE');
 return {pump:'OFFICIAL_BUY_SELL',meteora:'OFFICIAL_DLMM_SWAP',signing:false,broadcast:false};
}
// Caller supplies SDK-hydrated state and exact integer quote bounds from the frozen scanner.
// No guessed accounts, price approximation, or fake reserve math.
export async function nativeLegs(c){
 verifySdk();
 if(!c||!['PUMP_TO_METEORA','METEORA_TO_PUMP'].includes(c.direction)) hold('DIRECTION');
 if(!c.pumpSdk||!c.pumpState||!c.meteoraPool||!c.meteoraSwapParams) hold('HYDRATED_CONTEXT_REQUIRED');
 if(!integer(c.pumpBaseAmount)||!integer(c.pumpQuoteBound)) hold('PUMP_EXACT_BOUNDS_REQUIRED');
 if(typeof c.meteoraPool.swap!=='function') hold('METEORA_POOL_INVALID');
 if(!['buy','sell'].includes(c.pumpAction)) hold('PUMP_ACTION');
 if((c.direction==='PUMP_TO_METEORA'&&c.pumpAction!=='buy')||
    (c.direction==='METEORA_TO_PUMP'&&c.pumpAction!=='sell')) hold('DIRECTION_ACTION_MISMATCH');
 const p=c.pumpAction==='buy'
  ? await c.pumpSdk.buyInstructions(c.pumpState,c.pumpBaseAmount,c.pumpQuoteBound)
  : await c.pumpSdk.sellInstructions(c.pumpState,c.pumpBaseAmount,c.pumpQuoteBound);
 const m=await c.meteoraPool.swap(c.meteoraSwapParams);
 const pumpInstructions=ixArray(p);
 const meteoraInstructions=ixArray(m);
 if(!pumpInstructions.every(x=>x instanceof TransactionInstruction)||
    !meteoraInstructions.every(x=>x instanceof TransactionInstruction)) hold('NON_NATIVE_INSTRUCTIONS');
 validateNativeLegs(c.direction,pumpInstructions,meteoraInstructions);
 return {pumpInstructions,meteoraInstructions};
}
export async function simulateSdkAtomic(c){
 const legs=await nativeLegs(c);
 if(!c.connection||!c.opportunity) hold('SIMULATION_CONTEXT_REQUIRED');
 return compileAndSimulate({connection:c.connection,opportunity:c.opportunity,...legs,
  altAddresses:c.altAddresses||[]});
}
if(process.argv[1]?.endsWith('oracle106.mjs')) {
 try {console.log(JSON.stringify({status:'HOLD_LIVE_SDK_CONTEXT_REQUIRED',...verifySdk()}));}
 catch(e){console.error(e.message);process.exitCode=1;}
}
''',
'test/oracle106.test.mjs': r'''import test from 'node:test';
import assert from 'node:assert/strict';
import {PublicKey,TransactionInstruction,Transaction} from '@solana/web3.js';
import {verifySdk,nativeLegs} from '../oracle106.mjs';
const P='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwCZZ3a6Zk7L';
const M='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo';
const ix=(p)=>new TransactionInstruction({programId:new PublicKey(p),keys:[],data:Buffer.from([1])});
const fixture=(direction)=>({direction,pumpAction:direction==='PUMP_TO_METEORA'?'buy':'sell',
 pumpBaseAmount:1,pumpQuoteBound:1,pumpState:{},
 pumpSdk:{buyInstructions:async()=>[ix(P)],sellInstructions:async()=>[ix(P)]},
 meteoraPool:{swap:async()=>new Transaction().add(ix(M))},meteoraSwapParams:{}});
test('real installed SDK interfaces',()=>assert.equal(verifySdk().broadcast,false));
test('forward official SDK instructions',async()=>assert.equal((await nativeLegs(fixture('PUMP_TO_METEORA'))).meteoraInstructions.length,1));
test('reverse official SDK instructions',async()=>assert.equal((await nativeLegs(fixture('METEORA_TO_PUMP'))).pumpInstructions.length,1));
test('reject wrong action',async()=>assert.rejects(nativeLegs({...fixture('PUMP_TO_METEORA'),pumpAction:'sell'}),/DIRECTION_ACTION_MISMATCH/));
test('reject missing hydrated pool',async()=>assert.rejects(nativeLegs({...fixture('PUMP_TO_METEORA'),meteoraPool:null}),/HYDRATED_CONTEXT_REQUIRED/));
test('reject fake Meteora instruction',async()=>assert.rejects(nativeLegs({...fixture('PUMP_TO_METEORA'),meteoraPool:{swap:async()=>({instructions:[{}]})}}),/NON_NATIVE_INSTRUCTIONS/));
''',
'ORACLE106_README.txt': '''ORACLE-106 installs SDK-native instruction builder and simulation handoff.
Existing scanner and ORACLE-105 worker remain unchanged.
IMPORTANT: This is not a live connected executor. The scanner must supply
hydrated SDK pool objects, swap state, exact integer bounds, and a real RPC
connection. No secrets, signatures, broadcast, or realized profit are used.
Run: npm test && node oracle106.mjs
'''
}
def test():
    assert 'sendTransaction' not in FILES['oracle106.mjs']
    assert 'sign(' not in FILES['oracle106.mjs']
    assert 'compileAndSimulate' in FILES['oracle106.mjs']
    assert 'DLMM=require' in FILES['oracle106.mjs']
    print('[PASS] ORACLE106_STATIC_TESTS')
def install():
    if not (ROOT/'worker.mjs').is_file():
        raise SystemExit('[HOLD] Run from repository root; ORACLE-105 worker not found')
    for name,body in FILES.items():
        target=ROOT/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(body,encoding='utf-8')
        print('[INSTALLED]',target)
    print('[STATUS] OFFICIAL_SDK_NATIVE_LEGS_READY; LIVE_POOL_CONTEXT_NOT_CONNECTED')
    print('[SAFETY] NO_SIGNING NO_BROADCAST SCANNER_UNCHANGED')
if __name__=='__main__':
    test()
    if '--test' not in sys.argv: install()
