"""ORACLE-377 full installer: Official PumpSwap sellInstructions native reverse -> unsigned atomic v0 -> simulation.

Reuses frozen ORACLE-322, ORACLE-374 persistent handoff, ORACLE-370 same-bank provider,
and ORACLE-366 canonical fee/simulation gate. No key loading, signing, broadcast,
trading permission, or unverified static PumpSwap account-list synthesis.

The reverse builder uses official installed @meteora-ag/dlmm and
@pump-fun/pump-swap-sdk. It MUST fail closed if the SDK quote, exact bank,
account setup, v0/ALT, or transaction shape cannot be independently verified.
"""
from __future__ import annotations
import argparse, base64, hashlib, importlib, json, os, re, subprocess, sys, tempfile, time, unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET=ROOT/'oracle_377_native_reverse_atomic.py'
# Isolated, pinned Node dependencies: never mutate ORACLE-322's SDK runtime.
NODEDIR=ROOT/'oracle_376_native_sdk'  # Reuse installed isolated dependencies
NODE=NODEDIR/'oracle_377_sdk_reverse_unsigned.mjs'
PKGJSON=NODEDIR/'package.json'
NATIVE_DEPS={
    'name':'oracle-376-native-reverse',
    'private':True,
    'type':'module',
    'dependencies':{
        '@pump-fun/pump-swap-sdk':'2.1.0',
        '@meteora-ag/dlmm':'1.9.14',
        '@solana/web3.js':'1.99.0',
        'bn.js':'5.2.2',
    },
}
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_377_persistent_native_report.json')
MINI=Path('runtime_state/oracle/final_boss_dual/oracle_377_capability_report.json')
SCANNER_EPOCH_MAX_SLIP=2
MAX_WIRE_BYTES=1232
EXECUTION_AUTHORITY=False
SIGNING=False
BROADCAST=False
CANARY_LAMPORTS=10_000_000
PUBKEY=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

# This node helper generates SDK-native instructions. It never signs or sends.
# No invented PumpSwap account ordering; Meteora uses SDK swap2 account handling.
NODE_SOURCE=r'''import {Connection,PublicKey,TransactionMessage,VersionedTransaction} from '@solana/web3.js';
import BN from 'bn.js';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const dlmmPackage=require('@meteora-ag/dlmm');
const DLMM=dlmmPackage.default??dlmmPackage.DLMM??dlmmPackage;
import {PUMP_AMM_SDK,OnlinePumpAmmSdk,sellBaseInput} from '@pump-fun/pump-swap-sdk';
import {readFileSync} from 'node:fs';

const PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA';
const DLMM_PROGRAM='LBUZKhRxPF3XUpBCjp4YzTKgLccwBBzZYRSqNeZerDo';
const WSOL='So11111111111111111111111111111111111111112';
function hold(code){throw new Error(code)}
function pub(s){return new PublicKey(String(s))}
function str(v){return String(v?.toString?.()??'')}
function rawIxs(obj){if(Array.isArray(obj))return obj;
 if(obj?.instructions&&Array.isArray(obj.instructions))return obj.instructions;
 if(obj?.transaction?.instructions)return obj.transaction.instructions;
 if(obj?.instructions?.length)return [...obj.instructions];
 if(obj?.message?.instructions)hold('SDK_TRANSACTION_COMPILED_ALREADY');
 return obj?.instructions??null;}
const ALLOWED=new Set([PUMP,DLMM_PROGRAM,'11111111111111111111111111111111',
 'ComputeBudget111111111111111111111111111111',
 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL']);
async function construct(x){
 if(!process.env.SOLANA_RPC_URL?.startsWith('https://'))hold('HTTPS_RPC_REQUIRED');
 const connection=new Connection(process.env.SOLANA_RPC_URL,{commitment:'processed'});
 const wallet=pub(x.wallet), pumpPool=pub(x.pump_pool), poolKey=pub(x.meteora_pool), mint=pub(x.token);
 if(Number(x.size_lamports)!==10000000)hold('REVERSE_SIZE_NOT_010');
 if(!Number.isInteger(x.expected_gross_token)||x.expected_gross_token<=0 ||
    !Number.isInteger(x.expected_net_token)||x.expected_net_token<=0)hold('REVERSE_TOKEN_AMOUNTS_INVALID');
 const slotBefore=await connection.getSlot('processed');
 const pool=await DLMM.create(connection,poolKey,{cluster:'mainnet-beta'});
 const xt=str(pool.tokenX?.publicKey??pool.tokenX?.mint?.address);
 const yt=str(pool.tokenY?.publicKey??pool.tokenY?.mint?.address);
 if(!((xt===WSOL && yt===str(mint))||(yt===WSOL && xt===str(mint))))hold('DLMM_MINT_BINDING_MISMATCH');
 const swapForY=xt===WSOL;
 const bins=await pool.getBinArrayForSwap(swapForY,6);
 const quote=pool.swapQuote(new BN(String(x.size_lamports)),swapForY,new BN(0),bins,false);
 const consumed=Number(str(quote.consumedInAmount));
 const quotedOut=Number(str(quote.outAmount));
 if(consumed!==x.size_lamports)hold('DLMM_PARTIAL_FILL_REJECT');
 if(quotedOut!==x.expected_gross_token)hold('DLMM_BANK_QUOTE_PARITY_FAIL');
 const dlmmTx=await pool.swap({inToken:pub(WSOL),outToken:mint,
     inAmount:quote.consumedInAmount,minOutAmount:quote.minOutAmount,
     lbPair:poolKey,user:wallet,binArraysPubkey:quote.binArraysPubkey});
 const dlmmIxs=rawIxs(dlmmTx);
 if(!Array.isArray(dlmmIxs)||!dlmmIxs.length)hold('DLMM_NATIVE_IX_MISSING');
 const online=new OnlinePumpAmmSdk(connection);
 const state=await online.swapSolanaState(pumpPool,wallet);
 if(!state?.pool)hold('PUMP_SDK_STATE_NOT_READY');
 if(str(state.pool.baseMint)!==str(mint) && str(state.baseMint)!==str(mint))hold('PUMP_TOKEN_MISMATCH');
 if(typeof state.pool.protocolFees?.add!=='function' || !BN.isBN(state.pool.creatorFees))
   hold('PUMP_V2_FEE_BUCKETS_UNAVAILABLE');
 const args={baseReserve:new BN(String(x.pump_base_reserve)),quoteReserve:new BN(String(x.pump_quote_reserve)),
 virtualQuoteReserves:state.pool.virtualQuoteReserves,
 feeBucketsTotal:state.pool.protocolFees.add(state.pool.creatorFees),globalConfig:state.globalConfig,
 feeConfig:state.feeConfig,baseMint:state.baseMint,baseMintAccount:state.baseMintAccount,
 coinCreator:state.pool.coinCreator,creator:state.pool.creator,quoteMint:state.pool.quoteMint,
 isMayhemMode:state.pool.isMayhemMode,creatorFeeBps:state.pool.creatorFeeBps};
 const sellQuote=sellBaseInput({...args,base:new BN(String(x.expected_net_token)),slippage:0});
 const expectedMin=Number(str(sellQuote.minQuote));
 if(!Number.isSafeInteger(expectedMin)||expectedMin<x.expected_min_sol_out)hold('PUMP_SDK_MIN_QUOTE_PARITY_FAIL');
 // SDK's user-fee and token program accounts are preserved verbatim.
 const pumpSdk=PUMP_AMM_SDK;
 if(typeof pumpSdk?.sellInstructions!=='function')hold('PUMP_SDK_SELL_METHOD_MISSING');
 const sell=await pumpSdk.sellInstructions(state,new BN(String(x.expected_net_token)),new BN(String(expectedMin)));
 const sellIxs=rawIxs(sell);
 if(!Array.isArray(sellIxs)||!sellIxs.length)hold('PUMP_SDK_SELL_IX_MISSING');
 const preIxs=[...dlmmIxs,...sellIxs];
 if(preIxs.some(ix=>!ALLOWED.has(str(ix.programId))))hold('UNAPPROVED_NATIVE_PROGRAM');
 if(preIxs.some(ix=>['11111111111111111111111111111111',
   'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'].includes(str(ix.programId))))
   hold('SDK_REQUIRES_ACCOUNT_SETUP_OR_SOL_MOVEMENT');

 const legs=preIxs.filter(ix=>str(ix.programId)===PUMP||str(ix.programId)===DLMM_PROGRAM);
 if(legs.length!==2||str(legs[0].programId)!==DLMM_PROGRAM||str(legs[1].programId)!==PUMP)
   hold('REVERSE_ATOMIC_LEG_ORDER_INVALID');
 if(legs.some(ix=>!Array.isArray(ix.keys)||ix.keys.length<12))hold('SDK_REQUIRED_ACCOUNTS_MISSING');
 const dk=new Set(legs[0].keys.map(k=>str(k.pubkey)));
 const pk=new Set(legs[1].keys.map(k=>str(k.pubkey)));
 if(!dk.has(str(poolKey)) || !pk.has(str(pumpPool)) || !dk.has(str(wallet)) || !pk.has(str(wallet)))
   hold('SDK_NATIVE_POOL_WALLET_BINDING_INVALID');
 if(!legs[1].keys.some(k=>k.isSigner && str(k.pubkey)===str(wallet)))
   hold('PUMP_SELL_SIGNER_META_MISSING');
 // Reject a cleanup that closes a transient account before the second leg.
 const nativeIds=preIxs.map(ix=>str(ix.programId));
 const dlmmIndex=nativeIds.indexOf(DLMM_PROGRAM),pumpIndex=nativeIds.indexOf(PUMP);
 if(preIxs.slice(dlmmIndex+1,pumpIndex).some(ix=>ix.programId?.toBase58()==='11111111111111111111111111111111'))
   hold('INTER_LEG_SYSTEM_MUTATION_UNVERIFIED');
 const blockhash=await connection.getLatestBlockhash('processed');
 const lookups=[];
 if(x.alt_address){
   const alt=await connection.getAddressLookupTable(pub(x.alt_address),{commitment:'processed'});
   if(!alt?.value)hold('CANONICAL_ALT_ONCHAIN_MISSING');
   if(alt.value.state.deactivationSlot!==BigInt('18446744073709551615'))hold('CANONICAL_ALT_DEACTIVATED');
   lookups.push(alt.value);
 }
 const message=new TransactionMessage({payerKey:wallet,recentBlockhash:blockhash.blockhash,instructions:preIxs})
   .compileToV0Message(lookups);
 const tx=new VersionedTransaction(message);
 const raw=Buffer.from(tx.serialize());
 if(raw.length>1232)hold('NATIVE_V0_PACKET_TOO_LARGE');
 const slotAfter=await connection.getSlot('processed');
 if(slotBefore!==x.bank_slot||slotAfter!==x.bank_slot)hold('SDK_READBACK_NOT_SINGLE_BANK');
 return {ok:true,version:0,serialized_bytes:raw.length,
   unsigned_transaction_b64:raw.toString('base64'),
   message_b64:Buffer.from(message.serialize()).toString('base64'),
   bank_slot:x.bank_slot,slot_before:slotBefore,slot_after:slotAfter,
   gross_token:quotedOut,net_token:x.expected_net_token,
   meteora_min_out:Number(str(quote.minOutAmount)),pump_min_out:expectedMin,
   legs:['DLMM_BUY','PUMP_SELL'],lookup_count:message.addressTableLookups.length,
   native_legs:2,actual_native_instruction_count:preIxs.length};
}
// One-shot structured stdin: payload contains public keys, public amounts only.
try{
 const req=JSON.parse(readFileSync(0,'utf8'));
 const r=await construct(req);
 process.stdout.write(JSON.stringify(r)+'\n');
}catch(e){
 const msg=String(e?.message||'').match(/^[A-Z][A-Z0-9_]{3,80}$/)?.[0]||'SDK_NATIVE_BUILDER_ERROR';
 process.stdout.write(JSON.stringify({ok:false,reason:msg})+'\n');
 process.exitCode=2;
}
'''

class Hold(RuntimeError):pass

def safe_code(exc):
    s=str(exc)
    return s if re.fullmatch(r'[A-Z][A-Z0-9_]{3,100}',s) else 'ORACLE377_'+type(exc).__name__.upper()

def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,mode='w',encoding='utf-8',delete=False) as f:
        json.dump(value,f,indent=2,sort_keys=True); tmp=f.name
    os.replace(tmp,path)

def install():
    data=Path(__file__).resolve().read_bytes()
    compile(data.decode('utf-8'),str(TARGET),'exec')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile(dir=TARGET.parent,mode='wb',delete=False) as f:
            f.write(data);t=f.name
        os.replace(t,TARGET)
    NODEDIR.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=NODEDIR,mode='w',encoding='utf-8',delete=False) as f:
        f.write(NODE_SOURCE);n=f.name
    os.replace(n,NODE)
    manifest=json.dumps(NATIVE_DEPS,indent=2,sort_keys=True)+'\n'
    if PKGJSON.exists():
        try:
            existing=json.loads(PKGJSON.read_text(encoding='utf-8'))
        except (OSError,ValueError):raise Hold('ISOLATED_SDK_PACKAGE_INVALID') from None
        if existing.get('dependencies')!=NATIVE_DEPS['dependencies']:
            raise Hold('ISOLATED_SDK_PACKAGE_MANIFEST_DRIFT')
    else:
        PKGJSON.write_text(manifest,encoding='utf-8')
    if TARGET.read_bytes()!=data or NODE.read_text(encoding='utf-8')!=NODE_SOURCE:
        raise Hold('INSTALL_INTEGRITY_MISMATCH')
    print('[ORACLE377_INSTALL_PASS]',TARGET,'sdk_helper='+str(NODE),'sha256='+hashlib.sha256(data).hexdigest(),flush=True)

def modules():
    native=importlib.import_module(PKG+'.oracle_370_native_atomic_executor')
    pipeline=importlib.import_module(PKG+'.oracle_366_atomic_certification_pipeline')
    persistent=importlib.import_module(PKG+'.oracle_374_persistent_dual_native_handoff')
    return native,pipeline,persistent

def audit():
    native,pipeline,persistent=modules()
    persistent.audit()
    if (EXECUTION_AUTHORITY is not False or SIGNING is not False or BROADCAST is not False or
        native.EXECUTION_AUTHORITY is not False or native.BROADCAST is not False):
        raise Hold('EXECUTION_FIREWALL_VIOLATED')
    if TARGET.read_bytes()!=Path(__file__).resolve().read_bytes() or NODE.read_text(encoding='utf-8')!=NODE_SOURCE:
        raise Hold('ORACLE377_SOURCE_INTEGRITY_FAILURE')
    if json.loads(PKGJSON.read_text(encoding='utf-8')).get('dependencies')!=NATIVE_DEPS['dependencies']:
        raise Hold('ISOLATED_SDK_PACKAGE_MANIFEST_DRIFT')
    if not callable(getattr(pipeline,'simulation_gate',None)) or not callable(getattr(pipeline,'bank_native_gate',None)):
        raise Hold('CANONICAL_SIM_GATE_MISSING')
    res=subprocess.run(['node','--check',str(NODE)],capture_output=True,timeout=10)
    if res.returncode:raise Hold('NATIVE_NODE_SYNTAX_INVALID')
    print('[ORACLE377_AUDIT_PASS] 322_FROZEN 374_PERSISTENT 370_SAME_BANK '
          'OFFICIAL_SDK_REVERSE_V0_ALT ZERO_SIGNING ZERO_BROADCAST',flush=True)

def discover_alt():
    path=Path('runtime_state/oracle/solana_atomic_executor/canonical_alt.json')
    from_env=os.environ.get('QSB_CANONICAL_ALT','').strip()
    if from_env and PUBKEY.fullmatch(from_env):return from_env
    if not path.exists():return ''
    try:
        x=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return ''
    def walk(v,depth=0):
        if depth>5:return ''
        if isinstance(v,dict):
            for k,z in v.items():
                if k.lower() in ('alt_address','alt_pubkey','lookup_table_address','canonical_alt_address','address_lookup_table','alt') and isinstance(z,str) and PUBKEY.fullmatch(z):return z
            for z in v.values():
                p=walk(z,depth+1)
                if p:return p
        if isinstance(v,list):
            for z in v:
                p=walk(z,depth+1)
                if p:return p
        return ''
    return walk(x)

def require_reverse_sdk_result(x):
    if not isinstance(x,dict) or x.get('ok') is not True:raise Hold('NATIVE_SDK_RESULT_INVALID')
    if x.get('legs')!=['DLMM_BUY','PUMP_SELL'] or x.get('native_legs')!=2:
        raise Hold('REVERSE_NATIVE_INSTRUCTION_ORDER_INVALID')
    if x.get('version')!=0 or type(x.get('serialized_bytes')) is not int or not 0<x['serialized_bytes']<=MAX_WIRE_BYTES:
        raise Hold('UNSIGNED_V0_PACKET_SIZE_INVALID')
    if any(type(x.get(k)) is not int or x[k]<=0 for k in ('gross_token','net_token','pump_min_out','meteora_min_out')):
        raise Hold('SDK_AMOUNT_WITNESS_INVALID')
    if type(x.get('slot_before')) is not int or x['slot_before']!=x.get('bank_slot') or x.get('slot_after')!=x['bank_slot']:
        raise Hold('SDK_SAME_BANK_CONTEXT_UNVERIFIED')
    try:
        raw=base64.b64decode(x['unsigned_transaction_b64'],validate=True)
        msg=base64.b64decode(x['message_b64'],validate=True)
    except (ValueError,KeyError,TypeError):raise Hold('SDK_V0_WIRE_ENCODING_INVALID') from None
    if len(raw)!=x['serialized_bytes'] or len(msg)>=len(raw):
        raise Hold('SDK_V0_WIRE_LENGTH_MISMATCH')
    native,pipeline,_=modules()
    if not pipeline.unsigned_v0_witness(raw,msg):raise Hold('SDK_UNSIGNED_V0_WITNESS_FAILED')
    verify_compiled_legs(raw,x.get('lookup_count'))
    return raw,msg

def child_environment():
    """Do not pass wallet/seed secrets to subprocesses. Parent env untouched."""
    deny=re.compile(r'(PRIVATE.?KEY|SECRET|MNEMONIC|SEED|RECOVERY.?PHRASE|KEYPAIR)',re.I)
    return {k:v for k,v in os.environ.items() if not deny.search(k)}

def verify_compiled_legs(tx,expected_lookups):
    """Do not trust SDK-reported leg labels; inspect compiled v0 program indices."""
    try:
        from solders.transaction import VersionedTransaction
        decoded=VersionedTransaction.from_bytes(tx)
        message=decoded.message
        if not hasattr(message,'address_table_lookups'):
            raise Hold('NATIVE_V0_REQUIRED')
        tables=list(message.address_table_lookups)
        if type(expected_lookups) is not int or len(tables)!=expected_lookups:
            raise Hold('ALT_LOOKUP_WITNESS_MISMATCH')
        keys=[str(key) for key in message.account_keys]
        progs=[]
        for ix in message.instructions:
            i=int(ix.program_id_index)
            if not 0<=i<len(keys):raise Hold('PROGRAM_LOADED_FROM_UNVERIFIED_ALT')
            progs.append(keys[i])
        pump='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
        dlmm='LBUZKhRxPF3XUpBCjp4YzTKgLccwBBzZYRSqNeZerDo'
        if progs.count(pump)!=1 or progs.count(dlmm)!=1:
            raise Hold('COMPILED_ATOMIC_NATIVE_LEGS_NOT_EXACT')
        if progs.index(dlmm)>progs.index(pump):
            raise Hold('COMPILED_REVERSE_ORDER_INCORRECT')
        allowed={pump,dlmm,'11111111111111111111111111111111',
             'ComputeBudget111111111111111111111111111111',
             'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
             'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
             'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'}
        if set(progs)-allowed:raise Hold('COMPILED_UNAPPROVED_NATIVE_PROGRAM')
        return True
    except Hold:raise
    except Exception:raise Hold('COMPILED_NATIVE_GRAPH_UNREADABLE') from None

def _sdk_reverse(payload,timeout=15):
    if not NODE.exists():raise Hold('NATIVE_REVERSE_HELPER_NOT_INSTALLED')
    if not os.environ.get('SOLANA_RPC_URL','').startswith('https://'):
        raise Hold('HTTPS_SOLANA_RPC_REQUIRED')
    try:
        p=subprocess.run(['node',str(NODE)],input=json.dumps(payload),text=True,
                         capture_output=True,timeout=timeout,env=child_environment(),cwd=Path.cwd())
    except (OSError,subprocess.TimeoutExpired):raise Hold('SDK_REVERSE_WORKER_TIMEOUT_OR_MISSING') from None
    try:x=json.loads(p.stdout.strip())
    except (ValueError,TypeError):raise Hold('SDK_REVERSE_WORKER_INVALID_OUTPUT') from None
    if p.returncode or not isinstance(x,dict) or x.get('ok') is not True:
        code=x.get('reason','SDK_NATIVE_BUILDER_ERROR') if isinstance(x,dict) else 'SDK_NATIVE_BUILDER_ERROR'
        raise Hold(code if re.fullmatch(r'[A-Z][A-Z0-9_]{3,80}',str(code)) else 'SDK_NATIVE_BUILDER_ERROR')
    return x

def quote_reverse_only(old,snap,size):
    """Reuses exact Q18 reverse math without invoking unrelated forward BUY."""
    q18=old.q18
    mq=q18.core.dlmm_quote_snapshot(snap,size,q18.core.WSOL)
    base=int(mq['raw_out'])
    token=str(snap['token'])
    net=int(q18.token_net(token,base))
    if net<=0:raise Hold('REVERSE_NET_TOKEN_ZERO')
    pump=q18.worker().sell(snap,net)
    end=int(pump['uiQuote']); minimum=int(pump['minQuote'])
    if end<=0 or minimum<=0:raise Hold('REVERSE_PUMP_QUOTE_INVALID')
    return {'direction':'METEORA_TO_PUMP','start':size,'gross_token':base,
       'net_token':net,'local_end':end,'local_min_end':minimum,
       'local_net':end-size,'local_min_net':minimum-size,'mq':mq}

class DualNativeProvider:
    """Attaches to ORACLE-374. Reverse always proves the exact 370 bank before SDK work."""
    def __init__(self,native,wallet):
        self.native=native
        self.forward=native.NativeQ87Provider(wallet)
        self.old=None;self.rpc_url=self.forward.rpc_url
        self.recovered=0
        self.counters=Counter()
        self.prewarm_at=0
        self.refresh_attempts=0
    def prewarm(self):
        self.forward.prewarm();self.old=self.forward.old;self.prewarm_at=time.monotonic()
    def controlled_replenish(self,token):
        """Refresh canonical Q25 discovery at most once per 60 seconds.

        A nomination triggering replenishment is NEVER traded: caller HOLDs,
        forcing a new fresh scanner event to establish price and bank identity.
        """
        t=time.monotonic()
        if getattr(self,'last_replenish',-1e9)+60>t:
            raise Hold('NATIVE_WARM_REFRESH_COOLDOWN')
        self.last_replenish=t
        old=self.old
        try:
            state,_=old.q25.q60b2.prepare_once(Path.cwd())
            allpairs=list(state.get('pairs') or [])
            if token not in {str(p.token) for p in allpairs}:
                raise Hold('NOMINATED_TOKEN_ABSENT_CANONICAL_DISCOVERY')
            old.q25.bind_cached_state(state)
            warmed=old.install_proven_hot_math(state)
            old.prebuild_templates(state,self.forward.wallet)
            old.prebuild_meteora_templates(state,self.forward.wallet,warmed)
            self.forward.state=state
            self.forward.pairs={str(p.token):p for p in allpairs}
            self.forward.indexes={str(p.token):i for i,p in enumerate(allpairs)}
            self.forward.programs={str(x['token']):str(x['program']) for x in warmed}
            self.refresh_attempts+=1
        except Hold:raise
        except Exception:raise Hold('CANONICAL_CONTROLLED_REPLENISH_FAILED') from None
        raise Hold('REPLENISHED_REQUIRE_NEW_SCANNER_NOMINATION')
    def prepare_unsigned(self,row):
        direction=row.get('direction')
        if direction=='PUMP_TO_METEORA':
            try:return self.forward.prepare_unsigned(row)
            except self.native.Hold as exc:
                if str(exc)=='NATIVE_TEMPLATE_NOT_READY':self.controlled_replenish(row.get('token'))
                raise
            except RuntimeError as exc:
                # Reuse ORACLE-373's cold worker recovery, no arbitrary retries.
                reason=str(exc)
                if reason.startswith('PUMP_SDK_WORKER:SAE003_POOL_NOT_WARM:'):
                    token=row.get('token')
                    pair=self.forward.pairs.get(token)
                    if pair is None:raise Hold('COLD_POOL_NOT_REGISTERED') from None
                    self.old.q18.worker().warm(str(pair.pump_pool))
                    self.recovered+=1
                    return self.forward.prepare_unsigned(row)
                raise Hold('PUMP_SDK_UNCLASSIFIED_NATIVE_ERROR') from None
        if direction!='METEORA_TO_PUMP':raise Hold('UNSUPPORTED_NATIVE_DIRECTION')
        return self.prepare_unsigned_reverse(row)
    def prepare_unsigned_reverse(self,row):
        native,pipeline,_=modules()
        issue=pipeline.stage1_nomination(row)
        if issue:raise Hold(issue)
        if row.get('size_lamports')!=CANARY_LAMPORTS:raise Hold('REVERSE_010_ONLY_UNTIL_CERTIFIED')
        if not self.forward.initialized:self.prewarm()
        token=row['token']
        if token not in self.forward.pairs or token not in self.old.READY_TOKENS:
            self.controlled_replenish(token)
        with self.forward.lock:
            bank_slot,count,fingerprint,snap,bank_ns=self.forward._bank(token)
            if not row['scanner_slot']<=bank_slot<=row['scanner_slot']+SCANNER_EPOCH_MAX_SLIP:
                raise Hold('BANK_SLOT_DRIFT_REJECT')
            if snap['pump_pool']!=row['pump_pool'] or snap['meteora']['address']!=row['meteora_pool']:
                raise Hold('POOL_IDENTITY_CHANGED')
            q=quote_reverse_only(self.old,snap,CANARY_LAMPORTS)
            gross=int(q['local_net'])
            # Protected profit is min executable output, not midpoint quote.
            protected=int(q['local_min_net'])
            if gross<=0 or protected<=0:raise Hold('REVERSE_MIN_OUT_NOT_PROFITABLE')
            wsol,token_ata,wsol_before,token_before,sol_before=self.forward._wallet_accounts(token)
            if wsol_before<CANARY_LAMPORTS:raise Hold('WALLET_WSOL_BALANCE_TOO_LOW')
            if type(snap.get('pump_base_reserve')) is not int or type(snap.get('pump_quote_reserve')) is not int:
                raise Hold('CANONICAL_PUMP_RESERVES_INVALID')
            payload={'wallet':self.forward.wallet,'token':token,'pump_pool':row['pump_pool'],
                'meteora_pool':row['meteora_pool'],'size_lamports':CANARY_LAMPORTS,
                'expected_gross_token':int(q['gross_token']),'expected_net_token':int(q['net_token']),
                'expected_min_sol_out':int(q['local_min_end']),
                'pump_base_reserve':snap['pump_base_reserve'],
                'pump_quote_reserve':snap['pump_quote_reserve'],
                'bank_slot':bank_slot,'alt_address':discover_alt()}
            x=_sdk_reverse(payload)
            tx,msg=require_reverse_sdk_result(x)
            if (x['gross_token']!=q['gross_token'] or x['net_token']!=q['net_token'] or
                x['pump_min_out']<q['local_min_end']):
                raise Hold('REVERSE_EXECUTION_QUOTE_PARITY_FAIL')
            # An ALT claim requires real address table lookup references in the v0 message.
            # No signed message or wallet secret ever enters the Node process.
            if not x.get('lookup_count'):raise Hold('REVERSE_CANONICAL_ALT_UNUSED')
            extra=max(25_000,gross//20)
            proof={'event_id':row['event_id'],'token':token,'direction':'METEORA_TO_PUMP',
                'size_lamports':CANARY_LAMPORTS,'pump_pool':row['pump_pool'],
                'meteora_pool':row['meteora_pool'],'bank_slot':bank_slot,
                'bank_fingerprint':fingerprint,'bank_account_count':count,
                'bank_timestamp_ns':bank_ns,'q18_same_bank_gross_lamports':gross,
                'executor_same_bank_gross_lamports':gross,
                'single_bank_context_verified':True,'token_accounts_ready':True,
                'wsol_ready':True,'native_unsigned':True,'signing':False,'broadcast':False,
                'version':0,'alt_resolved':True,'legs':['DLMM_BUY','PUMP_SELL'],
                'atomic_single_transaction':True,'unsigned_transaction_b64':x['unsigned_transaction_b64'],
                'message_b64':x['message_b64'],'serialized_bytes':len(tx),
                'transfer_fee_lamports':0,'rent_cost_lamports':0,'tip_lamports':0,
                'residue_lamports':0,'adverse_buffer_lamports':extra}
            failure=pipeline.bank_native_gate(row,proof)
            if failure:raise Hold(failure)
            return proof

def deps():
    """Install exact, official SDK packages in an isolated directory only.

    Do not reconfigure the main scanner SDK folder or expose wallet keys to npm.
    """
    if not NODE.exists() or not PKGJSON.exists():raise Hold('ORACLE377_INSTALL_FIRST')
    env=child_environment()
    for name in ('SOLANA_RPC_URL','SOLANA_WS_URL','HELIUS_API_KEY'):
        env.pop(name,None)
    try:
        result=subprocess.run([('npm.cmd' if os.name=='nt' else 'npm'),'install','--no-audit','--no-fund','--ignore-scripts'],
            cwd=NODEDIR,env=env,timeout=180,capture_output=True,text=True)
    except (OSError,subprocess.TimeoutExpired):raise Hold('ISOLATED_NPM_INSTALL_UNAVAILABLE') from None
    if result.returncode:raise Hold('ISOLATED_NPM_DEPENDENCIES_INSTALL_FAILED')
    print('[ORACLE377_PINNED_NODE_DEPS_PASS] isolated_node_modules',flush=True)

def sdk_check():
    """Read-only local SDK compatibility probe. Imports packages but makes no RPC."""
    if not NODEDIR.exists():raise Hold('NATIVE_NODE_PACKAGE_DIR_MISSING')
    pkg=NODEDIR/'node_modules'/'@pump-fun'/'pump-swap-sdk'/'package.json'
    if not pkg.exists():raise Hold('ISOLATED_SDK_DEPS_INSTALL_REQUIRED')
    try:v=json.loads(pkg.read_text(encoding='utf-8')).get('version')
    except (ValueError,OSError):raise Hold('ISOLATED_PUMP_SDK_VERSION_UNKNOWN') from None
    if v!='2.1.0':raise Hold('PUMP_SDK_VERSION_MISMATCH')
    js=("import * as p from '@pump-fun/pump-swap-sdk'; "
        "import {createRequire} from 'node:module'; "
        "const require=createRequire(import.meta.url); "
        "const mp=require('@meteora-ag/dlmm'); const m=mp.default??mp.DLMM??mp; "
        "import * as w from '@solana/web3.js'; "
        "const flags={PumpSell:typeof p.PUMP_AMM_SDK?.sellInstructions==='function',"
        "PumpState:typeof p.OnlinePumpAmmSdk==='function',"
        "PumpQuote:typeof p.sellBaseInput==='function',"
        "MeteoraCreate:typeof m?.create==='function',"
        "Web3V0:typeof w.TransactionMessage==='function' && typeof w.VersionedTransaction==='function'}; "
        "process.stdout.write(JSON.stringify(flags)); "
        "process.exitCode=Object.values(flags).every(Boolean)?0:2;")
    try:r=subprocess.run(['node','--input-type=module','-e',js],cwd=NODEDIR,
            capture_output=True,text=True,timeout=20,env=child_environment())
    except (OSError,subprocess.TimeoutExpired):raise Hold('SDK_DEPENDENCY_CHECK_UNAVAILABLE') from None
    if r.returncode:
        if 'ERR_MODULE_NOT_FOUND' in r.stderr or 'Cannot find package' in r.stderr:
            raise Hold('SDK_NODE_PACKAGE_NOT_INSTALLED')
        try:
            flags=json.loads(r.stdout)
            if isinstance(flags,dict):
                missing=','.join(k for k,v in flags.items() if v is not True)
                print('[ORACLE377_SDK_API_MISSING]',missing,flush=True)
                raise Hold('SDK_INSTALLED_INTERFACE_MISMATCH')
        except (ValueError,TypeError):pass
        raise Hold('SDK_PACKAGE_IMPORT_FAILED')
    print('[ORACLE377_SDK_CHECK_PASS]',r.stdout.strip(),flush=True)

def run(minutes,poll_ms,wallet):
    native,pipeline,persistent=modules()
    audit()
    if not PUBKEY.fullmatch(wallet):raise Hold('PUBLIC_WALLET_REQUIRED')
    old_cls=persistent.RecoveringNativeProvider
    old_report=persistent.REPORT
    class Adapter(DualNativeProvider):
        def __init__(self,native_arg,wallet_arg):super().__init__(native_arg,wallet_arg)
    persistent.RecoveringNativeProvider=Adapter
    persistent.REPORT=REPORT
    try:
        code=persistent.launch(minutes=minutes,poll_ms=poll_ms,wallet_pubkey=wallet)
    finally:
        persistent.RecoveringNativeProvider=old_cls
        persistent.REPORT=old_report
    if REPORT.exists():
        try:rep=json.loads(REPORT.read_text(encoding='utf-8'))
        except (OSError,ValueError):rep={}
        rep['build']='ORACLE377'
        rep['native_reverse_integration']='SDK_NATIVE_UNSIGNED_ONLY'
        rep['signed_simulation_certified']=False
        rep['actual_money_sent']=False
        save_json(REPORT,rep)
    print('[ORACLE377_REPORT]',REPORT,flush=True)
    return code

def tests():
    class Test(unittest.TestCase):
        def test_syntax(self):compile(Path(__file__).read_text(encoding='utf-8'),__file__,'exec')
        def test_node_check(self):
            p=subprocess.run(['node','--check','--input-type=module'],input=NODE_SOURCE,text=True,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr[:300])
        def test_unsigned_authority(self):
            self.assertFalse(EXECUTION_AUTHORITY or SIGNING or BROADCAST)
        def test_official_current_pump_builder(self):
            self.assertIn('pumpSdk.sellInstructions',NODE_SOURCE)
            self.assertNotIn('swapBaseInstructions',NODE_SOURCE)
        def test_sell_minimum_bound_is_explicit(self):
            self.assertIn('new BN(String(expectedMin))',NODE_SOURCE)
        def test_npm_secret_scrub(self):
            import inspect
            body=inspect.getsource(deps)
            self.assertIn("'SOLANA_RPC_URL'",body)
            self.assertIn("'SOLANA_WS_URL'",body)
        def test_isolated_pinned_package(self):
            self.assertEqual(NATIVE_DEPS['dependencies']['@pump-fun/pump-swap-sdk'],'2.1.0')
            self.assertEqual(NATIVE_DEPS['dependencies']['@meteora-ag/dlmm'],'1.9.14')
            self.assertIn('oracle_376_native_sdk',str(NODEDIR))
        def test_commonjs_meteora_loader(self):
            self.assertIn("require('@meteora-ag/dlmm')",NODE_SOURCE)
            self.assertNotIn("import DLMM from '@meteora-ag/dlmm'",NODE_SOURCE)
        def test_fee_buckets_required(self):
            self.assertIn('feeBucketsTotal:',NODE_SOURCE)
            self.assertIn('PUMP_V2_FEE_BUCKETS_UNAVAILABLE',NODE_SOURCE)
        def test_no_arbitrary_sell_buy_account_count(self):
            self.assertNotIn('legs[1].keys.length<26',NODE_SOURCE)
            self.assertIn('PUMP_SELL_SIGNER_META_MISSING',NODE_SOURCE)
        def test_sdk_check_requires_current_pump_api(self):
            import inspect
            self.assertIn('PUMP_AMM_SDK?.sellInstructions',inspect.getsource(sdk_check))
        def test_no_js_transaction_signer(self):
            self.assertNotIn('.sign(',NODE_SOURCE)
            self.assertNotIn('sendTransaction(',NODE_SOURCE)
            self.assertNotIn('sendAndConfirmTransaction(',NODE_SOURCE)
            self.assertNotIn('Keypair.',NODE_SOURCE)
        def test_order_checked(self):self.assertIn("['DLMM_BUY','PUMP_SELL']",NODE_SOURCE)
        def test_independent_compiled_graph(self):self.assertTrue(callable(verify_compiled_legs))
        def test_alt_deactivation_checked(self):self.assertIn('CANONICAL_ALT_DEACTIVATED',NODE_SOURCE)
        def test_no_partial_dlmm(self):self.assertIn('DLMM_PARTIAL_FILL_REJECT',NODE_SOURCE)
        def test_no_unpriced_account_setup(self):self.assertIn('SDK_REQUIRES_ACCOUNT_SETUP_OR_SOL_MOVEMENT',NODE_SOURCE)
        def test_sdk_slot_agreement(self):self.assertIn('SDK_READBACK_NOT_SINGLE_BANK',NODE_SOURCE)
        def test_zero_key_log(self):self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',NODE_SOURCE)
        def test_reject_wrong_legs(self):
            with self.assertRaisesRegex(Hold,'REVERSE_NATIVE_INSTRUCTION_ORDER_INVALID'):
                require_reverse_sdk_result({'ok':True,'legs':['PUMP_BUY','DLMM_SELL'],'native_legs':2})
        def test_reject_oversize(self):
            with self.assertRaisesRegex(Hold,'UNSIGNED_V0_PACKET_SIZE_INVALID'):
                require_reverse_sdk_result({'ok':True,'legs':['DLMM_BUY','PUMP_SELL'],'native_legs':2,'version':0,'serialized_bytes':1233})
        def test_reject_sdk_bank_drift(self):
            with self.assertRaisesRegex(Hold,'SDK_SAME_BANK_CONTEXT_UNVERIFIED'):
                require_reverse_sdk_result({'ok':True,'legs':['DLMM_BUY','PUMP_SELL'],'native_legs':2,'version':0,'serialized_bytes':200,
                       'gross_token':10,'net_token':10,'pump_min_out':10,'meteora_min_out':10,
                       'slot_before':11,'bank_slot':10,'slot_after':10})
        def test_forward_delegates(self):
            class Native:
                class NativeQ87Provider:
                    def __init__(self,w):self.rpc_url=''
                    def prepare_unsigned(self,row):return {'ok':'forward'}
            p=DualNativeProvider(Native,'pub')
            self.assertEqual(p.prepare_unsigned({'direction':'PUMP_TO_METEORA'}),{'ok':'forward'})
        def test_reverse_never_calls_forward(self):
            class Native:
                class NativeQ87Provider:
                    def __init__(self,w):self.rpc_url=''
                    def prepare_unsigned(self,row):raise AssertionError('forward accessed')
            p=DualNativeProvider(Native,'pub')
            with patch.object(p,'prepare_unsigned_reverse',return_value={'ok':'reverse'}):
                self.assertEqual(p.prepare_unsigned({'direction':'METEORA_TO_PUMP'}),{'ok':'reverse'})
        def test_unknown_direction_rejected(self):
            class Native:
                class NativeQ87Provider:
                    def __init__(self,w):self.rpc_url=''
            with self.assertRaisesRegex(Hold,'UNSUPPORTED_NATIVE_DIRECTION'):
                DualNativeProvider(Native,'pub').prepare_unsigned({'direction':'BOGUS'})
        def test_missing_alt_safe(self):
            with patch('pathlib.Path.exists',return_value=False):self.assertEqual(discover_alt(),'')
        def test_sdk_invalid_output(self):
            with self.assertRaisesRegex(Hold,'NATIVE_SDK_RESULT_INVALID'):
                require_reverse_sdk_result({'ok':False})
        def test_reverse_quote_does_not_call_forward(self):
            class Q:
                class core:
                    WSOL='WSOL'
                    @staticmethod
                    def dlmm_quote_snapshot(s,size,w):return {'raw_out':125,'swap_for_y':True}
                @staticmethod
                def token_net(token,amount):return amount-5
                @staticmethod
                def worker():
                    class Worker:
                        def sell(self,snap,amt):return {'uiQuote':'10000500','minQuote':'10000100'}
                    return Worker()
                @staticmethod
                def exact_snapshot_opportunities(*args):raise AssertionError('FORWARD_BUY_CALLED')
            class Old:q18=Q
            result=quote_reverse_only(Old(),{'token':'T'},10000000)
            self.assertEqual(result['gross_token'],125)
            self.assertEqual(result['net_token'],120)
            self.assertEqual(result['local_min_net'],100)
        def test_child_secret_environment_scrubbed(self):
            with patch.dict(os.environ,{'QSB_SOLANA_PRIVATE_KEY':'hidden','QSB_SEED_PHRASE':'hidden',
                'SOLANA_RPC_URL':'https://local.invalid'}):
                env=child_environment()
                self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',env)
                self.assertNotIn('QSB_SEED_PHRASE',env)
                self.assertIn('SOLANA_RPC_URL',env)
        def test_sdk_not_installed(self):
            with patch.object(Path,'exists',return_value=False):
                with self.assertRaisesRegex(Hold,'NATIVE_REVERSE_HELPER_NOT_INSTALLED'):_sdk_reverse({})
        def test_report_firewall(self):
            self.assertEqual(CANARY_LAMPORTS,10_000_000)
    result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Test))
    print('[ORACLE377_TEST_PASS]' if result.wasSuccessful() else '[ORACLE377_TEST_FAIL]',result.testsRun,flush=True)
    return result.wasSuccessful()

def main():
    ap=argparse.ArgumentParser()
    for arg in ('install','test','audit','deps','sdk-check','run'):ap.add_argument('--'+arg,action='store_true')
    ap.add_argument('--minutes',type=int,default=10)
    ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--wallet-pubkey',default=os.getenv('QSB_SOLANA_WALLET',''))
    a=ap.parse_args()
    if not (a.install or a.test or a.audit or a.deps or a.sdk_check or a.run):ap.error('SPECIFY_ACTION')
    if a.install:install()
    if a.test and not tests():return 1
    if a.audit:audit()
    if a.deps:deps()
    if a.sdk_check:sdk_check()
    if a.run:return run(a.minutes,a.poll_ms,a.wallet_pubkey)
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Hold as exc:
        print('[ORACLE377_HOLD]',safe_code(exc),flush=True);raise SystemExit(2)
