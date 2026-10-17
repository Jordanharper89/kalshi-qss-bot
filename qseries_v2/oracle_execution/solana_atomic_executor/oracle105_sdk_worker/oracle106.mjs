import {createRequire} from 'node:module';
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
