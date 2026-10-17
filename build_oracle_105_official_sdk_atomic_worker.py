"""ORACLE-105: install official-SDK atomic worker; no signing or broadcast."""
from pathlib import Path
import json, subprocess, sys

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker')
FILES = {
'package.json': r'''{
  "name": "oracle105-sdk-atomic-worker",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {"test": "node --test test/*.test.mjs", "check": "node --check worker.mjs"},
  "dependencies": {
    "@solana/web3.js": "^1.98.0",
    "@solana/spl-token": "^0.4.0",
    "@pump-fun/pump-swap-sdk": "latest",
    "@meteora-ag/dlmm": "latest"
  }
}
''',
'worker.mjs': r'''import fs from 'node:fs';
import {Connection, PublicKey, TransactionInstruction, TransactionMessage, VersionedTransaction, AddressLookupTableAccount} from '@solana/web3.js';

const PUMP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwCZZ3a6Zk7L';
const DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo';
const SIZES = new Set([10000000,15000000,20000000,25000000,30000000]);
const fail = (message) => { throw Error('ORACLE105_HOLD_' + message); };
const key = (s) => new PublicKey(s);
const ixProgram = (ix) => ix.programId.toBase58();

// Native SDK instruction output only. No manual discriminator, account-layout, or instruction-byte construction.
export function validateOpportunity(o) {
  if (!o || !['PUMP_TO_METEORA','METEORA_TO_PUMP'].includes(o.direction)) fail('DIRECTION');
  if (!Number.isSafeInteger(o.start_lamports) || !SIZES.has(o.start_lamports)) fail('SIZE');
  if (typeof o.token !== 'string' || !o.token || !o.pool || !o.payer) fail('IDENTITY');
  if (!Number.isSafeInteger(o.slot) || o.slot < 1) fail('SLOT');
  if (!Number.isSafeInteger(o.expires_slot) || o.expires_slot < o.slot) fail('EXPIRY');
  if (!Number.isSafeInteger(o.min_profit_lamports) || o.min_profit_lamports <= 0) fail('MIN_PROFIT');
  return o;
}

export function validateNativeLegs(direction, pumpInstructions, meteoraInstructions) {
  for (const [name, arr, program] of [['PUMP',pumpInstructions,PUMP],['METEORA',meteoraInstructions,DLMM]]) {
    if (!Array.isArray(arr) || arr.length === 0 || !arr.every(x => x instanceof TransactionInstruction)) fail(name+'_SDK_IX_REQUIRED');
    if (arr.filter(x => ixProgram(x) === program).length !== 1) fail(name+'_ONE_SWAP_REQUIRED');
    if (arr.some(x => ixProgram(x) === (name === 'PUMP' ? DLMM : PUMP))) fail('CROSS_LEG');
  }
  return direction === 'PUMP_TO_METEORA' ? [...pumpInstructions,...meteoraInstructions] : [...meteoraInstructions,...pumpInstructions];
}

export async function loadAlts(connection, addresses) {
  const result=[];
  for (const address of addresses || []) {
    const response = await connection.getAddressLookupTable(key(address));
    if (!response.value || !(response.value instanceof AddressLookupTableAccount)) fail('ALT_MISSING');
    if (response.value.state.deactivationSlot !== 18446744073709551615n) fail('ALT_DEACTIVATED');
    result.push(response.value);
  }
  return result;
}

export async function compileAndSimulate({connection, opportunity, pumpInstructions, meteoraInstructions, altAddresses=[], signer}) {
  const o=validateOpportunity(opportunity);
  const payer=key(o.payer);
  const slot=await connection.getSlot('processed');
  if (slot > o.expires_slot || slot < o.slot) fail('STALE_OR_FUTURE_SLOT');
  const instructions=validateNativeLegs(o.direction,pumpInstructions,meteoraInstructions);
  const alts=await loadAlts(connection,altAddresses);
  const {blockhash,lastValidBlockHeight}=await connection.getLatestBlockhash('processed');
  const message=new TransactionMessage({payerKey:payer,recentBlockhash:blockhash,instructions}).compileToV0Message(alts);
  const tx=new VersionedTransaction(message);
  const unsignedBytes=tx.serialize();
  if (unsignedBytes.length>1232) fail('PACKET_TOO_LARGE_'+unsignedBytes.length);
  // Real RPC simulation of complete two-leg message; signature verification is intentionally disabled.
  const simulation=await connection.simulateTransaction(tx,{sigVerify:false,replaceRecentBlockhash:true,commitment:'processed'});
  if (simulation.value.err) fail('SIMULATION_'+JSON.stringify(simulation.value.err));
  const afterSlot=await connection.getSlot('processed');
  if (afterSlot>o.expires_slot) fail('EXPIRED_AFTER_SIM');
  // Simulation success alone is NOT a profitability proof. Token balance deltas must be independently reconciled.
  return {status:'SIMULATION_PASSED_PNL_UNCERTIFIED',wire_bytes:unsignedBytes.length,slot:afterSlot,
    compute_units:simulation.value.unitsConsumed??null,logs:simulation.value.logs??[],
    blockhash,lastValidBlockHeight,signing:false,broadcast:false};
}

// Official SDK adapters must receive real SDK-compatible pool/account contexts, not guessed raw layouts.
export async function buildOfficialSdkLegs(context) {
  const pumpModule=await import('@pump-fun/pump-swap-sdk');
  const dlmmModule=await import('@meteora-ag/dlmm');
  const pumpSDK=context?.pumpSdk;
  const meteoraPool=context?.meteoraPool;
  if (!pumpModule || !dlmmModule || !pumpSDK || !meteoraPool) fail('SDK_CONTEXT_NOT_HYDRATED');
  if (typeof context.pumpBuild !== 'function' || typeof context.meteoraBuild !== 'function') fail('SDK_BUILD_CALLBACKS_REQUIRED');
  // Callbacks must call official SDK methods and return their native TransactionInstruction arrays.
  const pumpInstructions=await context.pumpBuild(pumpSDK,context);
  const meteoraInstructions=await context.meteoraBuild(meteoraPool,context);
  return {pumpInstructions,meteoraInstructions};
}

async function main() {
  const file=process.argv[2];
  if (!file) fail('OPPORTUNITY_JSON_REQUIRED');
  const opportunity=validateOpportunity(JSON.parse(fs.readFileSync(file,'utf8')));
  // A standalone JSON quote cannot reconstruct authenticated SDK pool objects, signer, or executable instructions.
  console.log(JSON.stringify({status:'HOLD_SDK_POOL_CONTEXT_REQUIRED',opportunity_valid:true,
    token:opportunity.token,signing:false,broadcast:false}));
}
if (process.argv[1]?.endsWith('worker.mjs')) main().catch(e=>{console.error(e.message);process.exitCode=1;});
''',
'test/worker.test.mjs': r'''import test from 'node:test';
import assert from 'node:assert/strict';
import {TransactionInstruction,PublicKey} from '@solana/web3.js';
import {validateOpportunity,validateNativeLegs} from '../worker.mjs';
const PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwCZZ3a6Zk7L';
const DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo';
const ix=(program)=>new TransactionInstruction({programId:new PublicKey(program),keys:[],data:Buffer.from([1])});
const o={direction:'PUMP_TO_METEORA',start_lamports:10000000,token:'token',pool:'pool',payer:PUMP,slot:10,expires_slot:12,min_profit_lamports:1};
test('accept valid opportunity',()=>assert.equal(validateOpportunity(o).start_lamports,10000000));
test('reject unauthorized size',()=>assert.throws(()=>validateOpportunity({...o,start_lamports:100000000}),/SIZE/));
test('reject no profit',()=>assert.throws(()=>validateOpportunity({...o,min_profit_lamports:0}),/MIN_PROFIT/));
test('require real SDK instruction instances',()=>assert.throws(()=>validateNativeLegs(o.direction,[{}],[ix(DLMM)]),/SDK_IX_REQUIRED/));
test('require one native swap per leg',()=>assert.throws(()=>validateNativeLegs(o.direction,[ix(PUMP),ix(PUMP)],[ix(DLMM)]),/ONE_SWAP_REQUIRED/));
test('preserve forward order',()=>assert.deepEqual(validateNativeLegs(o.direction,[ix(PUMP)],[ix(DLMM)]).map(x=>x.programId.toBase58()),[PUMP,DLMM]));
test('preserve reverse order',()=>assert.deepEqual(validateNativeLegs('METEORA_TO_PUMP',[ix(PUMP)],[ix(DLMM)]).map(x=>x.programId.toBase58()),[DLMM,PUMP]));
''',
'README.txt': '''ORACLE-105: Official-SDK-based fail-closed atomic simulation worker.
No custom swap layouts. No signing. No broadcast. No scanner modifications.

SETUP (Windows CMD, venv active):
cd qseries_v2\\oracle_execution\\solana_atomic_executor\\oracle105_sdk_worker
npm install
npm test
node --check worker.mjs

INTEGRATION STATUS: SDK-based instruction adapter requires the actual hydrated PumpSwap and
Meteora pool objects and SDK calls matching installed SDK versions. A scanner quote alone
is insufficient. buildOfficialSdkLegs requires explicit SDK build callbacks; this build
intentionally does not pretend a generic callback is a verified integration.

SIMULATION STATUS: unsigned complete transaction simulation; not signed simulation.
No verified profit calculation or transaction broadcasting is implemented.
'''
}

def install():
    for name, content in FILES.items():
        p=ROOT/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(content,encoding='utf-8')
        print('[INSTALLED]',p)
    print('[BOUNDARY] NO_SIGNING NO_BROADCAST NO_SCANNER_CHANGE')
    print('[STATUS] SDK_CONTEXT_INTEGRATION_REQUIRED')

def test():
    assert 'sendTransaction' not in FILES['worker.mjs']
    assert 'sign(' not in FILES['worker.mjs']
    assert 'simulateTransaction' in FILES['worker.mjs']
    assert 'compileToV0Message' in FILES['worker.mjs']
    assert '@pump-fun/pump-swap-sdk' in FILES['package.json']
    assert '@meteora-ag/dlmm' in FILES['package.json']
    print('[PASS] ORACLE105_INSTALLER_STATIC_TESTS')

if __name__=='__main__':
    if '--test' in sys.argv: test()
    else: test(); install()
