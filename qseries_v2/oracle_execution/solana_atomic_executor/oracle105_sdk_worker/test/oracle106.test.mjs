import test from 'node:test';
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
