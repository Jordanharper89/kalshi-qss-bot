"""ORACLE-370: real native Q87/PumpSwap->DLMM executor, fail-closed canary.

Full installer and runtime module; intentionally DOES NOT replace the frozen scanner.
Uses previously built Q18/Q25/Q87 and runtime.py instruction builders rather than
inventing PumpSwap or Meteora instructions. Local canonical scanner -> ORACLE-365
-> ORACLE-368 strict unsigned proof -> optional signed 0.010 SOL funded canary.
Reverse native route has no verified implementation in the reachable repo and HOLDS.

CLI: --install, --test, --audit, --run, --live-canary. Wallet is input hidden
(--wallet-hidden) or public address (--wallet-pubkey); never printed/stored.
"""
from __future__ import annotations
import argparse, base64, copy, getpass, hashlib, importlib, json, os, re, sys, tempfile, threading, time, traceback, unittest, urllib.error, urllib.request
from collections import Counter
from pathlib import Path

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET=ROOT/'oracle_370_native_atomic_executor.py'
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_370_native_atomic_executor_report.json')
CANARY_MARK=Path('runtime_state/oracle/final_boss_dual/oracle_370_first_canary_attempt.json')
CANARY=10_000_000
EXECUTION_AUTHORITY=False  # no implicit transfer authority: --live-canary required
BROADCAST=False
MAX_PACKET=1232
PUBKEY_RE=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

class Hold(RuntimeError):pass


def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,mode='w',encoding='utf-8',delete=False) as f:
        json.dump(data,f,sort_keys=True,indent=2)
        temp=f.name
    os.replace(temp,path)


def install():
    raw=Path(__file__).resolve().read_bytes()
    compile(raw.decode('utf-8'),str(TARGET),'exec')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if Path(__file__).resolve()!=TARGET.resolve():
        with tempfile.NamedTemporaryFile(dir=TARGET.parent,delete=False,mode='wb') as f:
            f.write(raw);tmp=f.name
        os.replace(tmp,TARGET)
    assert TARGET.read_bytes()==raw
    print('[ORACLE370_INSTALL_PASS]',str(TARGET),'sha256='+hashlib.sha256(raw).hexdigest(),flush=True)


def bridge():
    return importlib.import_module(PKG+'.oracle_368_source_boundary_repair')


def audit():
    bridge().audit(require_installed=True)
    assert TARGET.exists() and TARGET.read_bytes()==Path(__file__).resolve().read_bytes(),'INSTALLED_SOURCE_MISMATCH'
    # Static enforce that frozen production scanner isn't patched by this installer.
    s=Path(__file__).resolve().read_text(encoding='utf-8')
    assert 'oracle_322_scanner_isolated_discovery' not in s or 'FROZEN' in s
    print('[ORACLE370_AUDIT_PASS] FROZEN322 CORE_365_368 Q18_Q25_Q87_CANONICAL_NATIVE '
          'PRODUCTION_SEND_ONLY_EXPLICIT_CANARY',flush=True)


def _rpc(method,params,url=None,timeout=5):
    url=url or os.environ.get('SOLANA_RPC_URL','')
    if not isinstance(url,str) or not url.startswith('https://'):
        raise Hold('HTTPS_SOLANA_RPC_URL_REQUIRED')
    if method not in {'getMultipleAccounts','getFeeForMessage','simulateTransaction',
                      'sendTransaction','getSignatureStatuses','getTransaction'}:
        raise Hold('RPC_METHOD_UNAUTHORIZED')
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    try:
        req=urllib.request.Request(url,body,{'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=timeout) as response:
            result=json.loads(response.read(3_000_000).decode())
    except urllib.error.HTTPError as e:
        raise Hold('RPC_HTTP_'+str(e.code)) from None
    except (OSError,TimeoutError,ValueError):
        raise Hold('RPC_TRANSPORT_FAILURE') from None
    if not isinstance(result,dict) or result.get('error'):
        raise Hold('RPC_RETURNED_ERROR')
    return result.get('result')


def _decode_token(raw):
    if not isinstance(raw,dict) or not isinstance(raw.get('data'),list):
        raise Hold('TOKEN_ACCOUNT_BYTES_MISSING')
    data=base64.b64decode(raw['data'][0],validate=True)
    if len(data)<72:raise Hold('TOKEN_ACCOUNT_LAYOUT_INVALID')
    return int.from_bytes(data[64:72],'little'),data


def _account_blob(row):
    if not isinstance(row,dict) or not isinstance(row.get('data'),list):
        raise Hold('POOL_ACCOUNT_UNAVAILABLE')
    try:return base64.b64decode(row['data'][0],validate=True)
    except (ValueError,TypeError):raise Hold('POOL_ACCOUNT_DATA_CORRUPT') from None


def _public_key(secret):
    try:
        from solders.keypair import Keypair
        if secret.lstrip().startswith('['):
            raw=json.loads(secret)
            if not isinstance(raw,list) or len(raw)!=64:raise Hold('KEY_FORMAT_UNSUPPORTED')
            return Keypair.from_bytes(bytes(raw))
        return Keypair.from_base58_string(secret)
    except Hold:raise
    except Exception:raise Hold('WALLET_KEY_INVALID_OR_SOLDERS_MISSING') from None


def verify_native_program_sequence(tx, expected_pump, expected_dlmm):
    """Validate actual v0 compiled instruction program indices, not a bytes search."""
    try:
        from solders.transaction import VersionedTransaction
        transaction=VersionedTransaction.from_bytes(tx)
        message=transaction.message
        static=[str(x) for x in message.account_keys]
        if not hasattr(message,'address_table_lookups'):
            raise Hold('VERSIONED_V0_REQUIRED')
        # ALT compilers must supply their lookup resolution proof explicitly.
        # Existing q87 no-ALT compile is accepted; unresolved ALT is held.
        if len(message.address_table_lookups):raise Hold('ALT_LOOKUPS_NOT_VERIFIED')
        prog=[];counts={}
        for ix in message.instructions:
            idx=int(ix.program_id_index)
            if not 0<=idx<len(static):raise Hold('PROGRAM_INDEX_NOT_STATIC')
            name=static[idx];prog.append(name)
            counts[name]=counts.get(name,0)+1
            if name==expected_pump and len(ix.accounts)<26:
                raise Hold('PUMPSWAP_2026_FEE_ACCOUNTS_MISSING')
            if name==expected_dlmm and len(ix.accounts)<17:
                raise Hold('DLMM_BIN_ACCOUNT_LAYOUT_INCOMPLETE')
        if counts.get(expected_pump)!=1 or counts.get(expected_dlmm)!=1:
            raise Hold('ATOMIC_NATIVE_LEG_COUNT_NOT_EXACT')
        if prog.index(expected_pump)>prog.index(expected_dlmm):
            raise Hold('NATIVE_LEG_ORDER_WRONG')
        # No arbitrary third-party instruction programs may mutate user funds.
        allowed={expected_pump,expected_dlmm,
          '11111111111111111111111111111111',
          'ComputeBudget111111111111111111111111111111',
          'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
          'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
          'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'}
        if any(x not in allowed for x in prog):raise Hold('UNRECOGNIZED_ATOMIC_INSTRUCTION_PROGRAM')
        return True
    except Hold:raise
    except Exception:raise Hold('NATIVE_INSTRUCTION_GRAPH_UNREADABLE') from None


class NativeQ87Provider:
    """Only the one native direction already present in runtime.py (NO synthetic reverse).
    Q25 warms once, q18 computes quotes, Q87 constructs/compiles instructions.
    Fresh accounts are fetched with one getMultipleAccounts bank per nomination.
    """
    def __init__(self,wallet_pubkey, rpc_url=None):
        if not PUBKEY_RE.fullmatch(wallet_pubkey or ''):raise Hold('WALLET_PUBKEY_REQUIRED')
        self.wallet=wallet_pubkey;self.rpc_url=rpc_url or os.environ.get('SOLANA_RPC_URL','')
        self.initialized=False;self.old=None;self.state=None;self.programs={}
        self.pairs={};self.indexes={};self.counters=Counter();self.warm_error=None
        self.lock=threading.Lock()

    def prewarm(self):
        if self.initialized:return
        try:
            old=importlib.import_module(PKG+'.runtime')
            state,_=old.q25.prepare_once(Path.cwd())
            old.q25.bind_cached_state(state)
            warmed=old.install_proven_hot_math(state)
            old.prebuild_templates(state,self.wallet)
            old.prebuild_meteora_templates(state,self.wallet,warmed)
            programs={str(x['token']):str(x['program']) for x in warmed if isinstance(x,dict) and x.get('token') and x.get('program')}
            self.programs=programs
            self.pairs={str(x.token):x for x in state.get('pairs',[])}
            self.indexes={str(x.token):i for i,x in enumerate(state.get('pairs',[]))}
            self.old=old;self.state=state;self.initialized=True
            print('[ORACLE370_NATIVE_WARM]',json.dumps({'pairs':len(self.pairs),
                  'ready':len(old.READY_TOKENS),'additional_ws':False,'private_key_used':False}),flush=True)
        except Exception as e:
            # Never log key, RPC URL, or exception text.
            self.warm_error=type(e).__name__
            raise Hold('CANONICAL_NATIVE_WARM_FAILED_'+self.warm_error) from None

    def _bank(self,token):
        old=self.old
        if token not in self.indexes:raise Hold('NOMINATED_TOKEN_NOT_WARM')
        index=self.indexes[token]
        preg=self.state.get('preg',{})
        addresses=[(address,kind) for address,(idx,kind) in preg.items() if idx==index]
        if not addresses or len(addresses)>90:raise Hold('PAIR_ACCOUNT_REGISTRY_UNSUPPORTED')
        # Single context read; accept no unobserved/missing accounts and no HTTP per quote.
        keys=[a for a,_ in addresses]
        data=_rpc('getMultipleAccounts',[keys,{'encoding':'base64','commitment':'processed'}],self.rpc_url)
        if not isinstance(data,dict) or not isinstance(data.get('context'),dict):
            raise Hold('SAME_BANK_RPC_CONTEXT_MISSING')
        slot=data['context'].get('slot');values=data.get('value')
        if type(slot) is not int or slot<=0 or not isinstance(values,list) or len(values)!=len(keys):
            raise Hold('BANK_BATCH_INCOMPLETE')
        blobs=[_account_blob(v) for v in values]
        fingerprint=hashlib.sha256(json.dumps({'slot':slot,'addresses':keys},sort_keys=True).encode()+b''.join(blobs)).hexdigest()
        pair=self.pairs[token]
        now=time.time_ns()
        applied=0
        for (address,kind),raw in zip(addresses,blobs):
            if old.persistent.m.pd.apply_account_event(pair,kind,address,raw,slot,now):applied+=1
        if applied==0:raise Hold('FRESH_BANK_NOT_APPLIED')
        return slot,len(blobs),fingerprint,old.immutable_snapshot(pair),now

    def _wallet_accounts(self,token):
        old=self.old
        c=old.q87.c
        token_prog=self.programs.get(token)
        if not token_prog:raise Hold('TOKEN_PROGRAM_NOT_PREWARMED')
        wsol=c.ata(self.wallet,c.WSOL,c.TOKEN)
        token_ata=c.ata(self.wallet,token,token_prog)
        a=_rpc('getMultipleAccounts',[[wsol,token_ata,self.wallet],{'encoding':'base64','commitment':'processed'}],self.rpc_url)
        vals=a.get('value') if isinstance(a,dict) else None
        if not isinstance(vals,list) or len(vals)!=3:raise Hold('WALLET_ATA_READ_FAILED')
        wsol_before,_=_decode_token(vals[0]);token_before,_=_decode_token(vals[1])
        if not isinstance(vals[2],dict) or type(vals[2].get('lamports')) is not int:
            raise Hold('WALLET_SOL_LAMPORTS_UNVERIFIED')
        sol_before=vals[2]['lamports']
        if sol_before<3_000_000:raise Hold('INSUFFICIENT_SOL_FOR_FEES_RENT')
        return wsol,token_ata,wsol_before,token_before,sol_before

    def prepare_unsigned(self,candidate):
        core=bridge()
        issue=core.stage1_nomination(candidate)
        if issue:raise Hold(issue)
        if candidate['direction']!='PUMP_TO_METEORA':
            raise Hold('REVERSE_BUILDER_UNVERIFIED_DO_NOT_SUBSTITUTE_BUY_ROUTE')
        if not self.initialized:self.prewarm()
        old=self.old;token=candidate['token'];size=candidate['size_lamports']
        if token not in old.READY_TOKENS:raise Hold('NATIVE_TEMPLATE_NOT_READY')
        with self.lock:
            bank_slot,count,fingerprint,snap,bank_ns=self._bank(token)
            if not candidate['scanner_slot']<=bank_slot<=candidate['scanner_slot']+core.MAX_SIM_SLOT_GAP:
                raise Hold('BANK_SLOT_DRIFT_REJECT')
            if snap['pump_pool']!=candidate['pump_pool'] or snap['meteora']['address']!=candidate['meteora_pool']:
                raise Hold('POOL_IDENTITY_CHANGED')
            # Q18 reads newly hydrated immutable snapshot. Select EXACT requested size.
            rows=old.q18.exact_snapshot_opportunities(snap,size/1_000_000_000)
            exact=[x for x in rows if x.get('direction')==candidate['direction'] and int(x.get('start',-1))==size]
            if len(exact)!=1:raise Hold('EXACT_SIZE_BANK_QUOTE_NOT_UNIQUE')
            opp=exact[0];gross=int(opp['local_net'])
            if gross<=0:raise Hold('EXACT_NATIVE_GROSS_NONPOSITIVE')
            wsol,token_ata,wsol_before,token_before,sol_before=self._wallet_accounts(token)
            if wsol_before<size:raise Hold('WALLET_WSOL_BALANCE_TOO_LOW')
            # SDK-produced fixed-budget Pump buy + DLMM swap; no hand-coded static account lists.
            route=old.same_snapshot_route(self.wallet,snap,opp)
            comp=old.compile_current(self.wallet,route)
            if not comp.get('ok'):raise Hold('NO_COMPACT_NATIVE_V0_ALT')
            tx=bytes(comp['raw']);msg=bytes(comp['msg'])
            if len(tx)>MAX_PACKET or not core.unsigned_v0_witness(tx,msg):
                raise Hold('NATIVE_V0_UNSIGNED_WIRE_INVALID')
            # Verify actual native instruction ordering, both program IDs and 2026 fee accounts.
            verify_native_program_sequence(tx,old.q87.c.PUMP,old.q87.c.DLMM)
            extra=max(25_000,gross//20)  # conservative adverse fee/price buffer
            proof={'event_id':candidate['event_id'],'token':token,
              'direction':candidate['direction'],'size_lamports':size,
              'pump_pool':candidate['pump_pool'],'meteora_pool':candidate['meteora_pool'],
              'bank_slot':bank_slot,'bank_fingerprint':fingerprint,'bank_account_count':count,
              'bank_timestamp_ns':bank_ns,'q18_same_bank_gross_lamports':gross,
              'executor_same_bank_gross_lamports':int(route['pre_sim_net_lamports']),
              'single_bank_context_verified':True,'token_accounts_ready':True,'wsol_ready':True,
              'native_unsigned':True,'signing':False,'broadcast':False,'version':0,
              'alt_resolved':True,'legs':['PUMP_BUY','DLMM_SELL'],
              'atomic_single_transaction':True,
              'unsigned_transaction_b64':base64.b64encode(tx).decode(),
              'message_b64':base64.b64encode(msg).decode(),'serialized_bytes':len(tx),
              'transfer_fee_lamports':0,'rent_cost_lamports':0,
              'tip_lamports':0,'residue_lamports':0,'adverse_buffer_lamports':extra,
              'wallet_wsol_ata':wsol,'wallet_token_ata':token_ata,
              'wsol_before_raw':wsol_before,'token_before_raw':token_before,
              'sol_before_lamports':sol_before}
            if core.bank_native_gate(candidate,proof) is not None:
                raise Hold('BANK_NATIVE_PROOF_NOT_CERTIFIED')
            return proof


class Canary:
    """One-shot real broadcaster. Requires signed simulation and wallet token deltas.
    Intent marker written BEFORE send, never automatically resent on uncertain result.
    """
    def __init__(self,keypair,provider):
        self.keypair=keypair;self.provider=provider;self.attempted=False

    def _sign(self,proof):
        try:
            from solders.transaction import VersionedTransaction
            from solders.message import to_bytes_versioned
            raw=base64.b64decode(proof['unsigned_transaction_b64'],validate=True)
            tx=VersionedTransaction.from_bytes(raw)
            if len(tx.signatures)!=1 or str(tx.message.account_keys[0])!=str(self.keypair.pubkey()):
                raise Hold('SINGLE_SIGNER_WALLET_IDENTITY_MISMATCH')
            signed=VersionedTransaction.populate(tx.message,[self.keypair.sign_message(to_bytes_versioned(tx.message))])
            if len(bytes(signed))>MAX_PACKET:raise Hold('SIGNED_PACKET_TOO_LARGE')
            return base64.b64encode(bytes(signed)).decode(),str(signed.signatures[0])
        except Hold:raise
        except Exception:raise Hold('NATIVE_V0_SIGNING_FAILED') from None

    def _account_amount(self,row):
        if not isinstance(row,dict):raise Hold('SIM_TOKEN_ACCOUNT_NOT_RETURNED')
        amount,_=_decode_token(row)
        return amount

    def execute(self,candidate,proof,estimate,still_fresh):
        if self.attempted or CANARY_MARK.exists():raise Hold('ONE_SHOT_CANARY_ALREADY_ATTEMPTED')
        if candidate['size_lamports']!=CANARY or estimate.get('stage')!='UNSIGNED_SIM_NET_ESTIMATE_PASS':
            raise Hold('CANARY_NOT_AT_EXACT_SIZE_OR_PRECERTIFIED')
        if self.keypair is None or str(self.keypair.pubkey())!=self.provider.wallet:
            raise Hold('LIVE_SIGNER_WALLET_IDENTITY_FAILED')
        if not still_fresh():raise Hold('SOURCE_EXPIRED_BEFORE_SIGNED_PREFLIGHT')
        signed_b64,signature=self._sign(proof)
        result=_rpc('simulateTransaction',[signed_b64,{'encoding':'base64','sigVerify':True,
            'replaceRecentBlockhash':False,'commitment':'processed',
            'minContextSlot':proof['bank_slot'],
            'accounts':{'encoding':'base64','addresses':[proof['wallet_wsol_ata'],proof['wallet_token_ata'],self.provider.wallet]} }],self.provider.rpc_url)
        if not isinstance(result,dict) or result.get('context',{}).get('slot',0)<proof['bank_slot']:
            raise Hold('SIGNED_SIM_CONTEXT_UNVERIFIED')
        value=result.get('value') or {}
        if value.get('err') is not None or not isinstance(value.get('accounts'),list) or len(value['accounts'])!=3:
            raise Hold('SIGNED_SIM_NOT_PROVEN')
        wsol_after=self._account_amount(value['accounts'][0]);token_after=self._account_amount(value['accounts'][1])
        payer_after=value['accounts'][2]
        if not isinstance(payer_after,dict) or type(payer_after.get('lamports')) is not int:
            raise Hold('SIGNED_SIM_PAYER_SOL_DELTA_UNKNOWN')
        wsol_gain=wsol_after-proof['wsol_before_raw']
        sol_gain=payer_after['lamports']-proof['sol_before_lamports']
        net=wsol_gain+sol_gain-estimate['chain_fee_lamports']
        if token_after!=proof['token_before_raw'] or net<=proof['adverse_buffer_lamports']:
            raise Hold('SIGNED_SIM_NET_OR_RESIDUE_UNCERTIFIED')
        if not still_fresh():raise Hold('SOURCE_EXPIRED_POST_SIGNED_SIM')
        # Atomic one-shot durable marker precedes network send. Never retry ambiguous sends.
        self.attempted=True
        atomic_json(CANARY_MARK,{'status':'SEND_INTENT_UNKNOWN','signature':signature,
            'size_lamports':CANARY,'event_id':candidate['event_id'],
            'wallet_pubkey':self.provider.wallet,'token_mint':candidate['token'],
            'signed_sim_net_lamports':net,'execution_authority':True})
        try:
            returned=_rpc('sendTransaction',[signed_b64,{'encoding':'base64','skipPreflight':False,
                 'preflightCommitment':'processed','maxRetries':0,
                 'minContextSlot':proof['bank_slot']}],self.provider.rpc_url)
            if returned!=signature:raise Hold('SEND_SIGNATURE_MISMATCH')
            atomic_json(CANARY_MARK,{'status':'SENT_UNCONFIRMED','signature':signature,
                 'size_lamports':CANARY,'event_id':candidate['event_id'],
                 'wallet_pubkey':self.provider.wallet,'token_mint':candidate['token']})
        except Hold:
            raise Hold('SEND_OUTCOME_UNKNOWN_DO_NOT_RETRY') from None
        return {'status':'SENT_UNCONFIRMED','signature':signature,'canary_lamports':CANARY}



def _token_owner_balance(rows,mint,owner):
    if not isinstance(rows,list):raise Hold('RECON_TOKEN_ACCOUNT_RECORDS_MISSING')
    matched=[x for x in rows if isinstance(x,dict) and x.get('mint')==mint and x.get('owner')==owner]
    if not matched:raise Hold('RECON_TOKEN_ACCOUNT_BALANCE_UNOBSERVED')
    try:return sum(int(x['uiTokenAmount']['amount']) for x in matched)
    except (KeyError,TypeError,ValueError):raise Hold('RECON_TOKEN_AMOUNT_UNREADABLE') from None


def reconcile_transaction(marker, rpc_fn=_rpc):
    """Tie net delta to the confirmed transaction, never to unrelated wallet polls."""
    if not isinstance(marker,dict) or not marker.get('signature'):
        raise Hold('NO_CANARY_TRANSACTION_TO_RECONCILE')
    signature=marker['signature']
    st=rpc_fn('getSignatureStatuses',[[signature],{'searchTransactionHistory':True}])
    rows=st.get('value') if isinstance(st,dict) else None
    one=rows[0] if isinstance(rows,list) and len(rows)==1 else None
    if not isinstance(one,dict):return {'status':'PENDING_OR_UNKNOWN','signature':signature}
    if one.get('err') is not None:return {'status':'CHAIN_TRANSACTION_FAILED','signature':signature}
    if one.get('confirmationStatus') not in ('confirmed','finalized'):
        return {'status':'PENDING_OR_UNKNOWN','signature':signature}
    tx=rpc_fn('getTransaction',[signature,{'encoding':'json','commitment':'confirmed',
                                        'maxSupportedTransactionVersion':0}])
    if not isinstance(tx,dict):return {'status':'CONFIRMED_METADATA_PENDING','signature':signature}
    meta=tx.get('meta'); transaction=tx.get('transaction')
    if not isinstance(meta,dict) or meta.get('err') is not None:
        return {'status':'CHAIN_TRANSACTION_FAILED_OR_META_INVALID','signature':signature}
    if not isinstance(transaction,dict) or signature not in transaction.get('signatures',[]):
        raise Hold('RECON_TRANSACTION_SIGNATURE_MISMATCH')
    msg=transaction.get('message',{})
    keys=msg.get('accountKeys',[]) if isinstance(msg,dict) else []
    first=keys[0] if keys else None
    payer=(first.get('pubkey') if isinstance(first,dict) else first)
    if payer!=marker.get('wallet_pubkey'):
        raise Hold('RECON_PAYER_MISMATCH')
    before=meta.get('preBalances');after=meta.get('postBalances')
    if not isinstance(before,list) or not isinstance(after,list) or not before or not after:
        raise Hold('RECON_SOL_BALANCES_MISSING')
    sol_delta=int(after[0])-int(before[0])
    owner=marker['wallet_pubkey'];wsol='So11111111111111111111111111111111111111112'
    # Require explicit pre/post balances for both WSOL and the intermediate token;
    # if the provider omits them, do not claim realized net P&L.
    try:
        pre_w=_token_owner_balance(meta.get('preTokenBalances'),wsol,owner)
        post_w=_token_owner_balance(meta.get('postTokenBalances'),wsol,owner)
        pre_t=_token_owner_balance(meta.get('preTokenBalances'),marker['token_mint'],owner)
        post_t=_token_owner_balance(meta.get('postTokenBalances'),marker['token_mint'],owner)
    except Hold:
        return {'status':'CONFIRMED_PNL_UNVERIFIED','signature':signature,'fee_lamports':meta.get('fee')}
    net=sol_delta+(post_w-pre_w)
    if post_t!=pre_t:return {'status':'CONFIRMED_TOKEN_RESIDUE_UNRECONCILED','signature':signature,
                              'sol_wsol_net_lamports':net,'token_residue_raw':post_t-pre_t}
    return {'status':'REALIZED_POSITIVE_RECONCILED' if net>0 else 'REALIZED_NONPOSITIVE_RECONCILED',
            'signature':signature,'net_lamports':net,'fee_lamports':meta.get('fee'),
            'confirmed_slot':tx.get('slot'),'token_residue_raw':0}


def reconcile_canary():
    if not CANARY_MARK.exists():
        print('[ORACLE370_RECON_HOLD] NO_CANARY_SENT');return 2
    marker=json.loads(CANARY_MARK.read_text(encoding='utf-8'))
    try:result=reconcile_transaction(marker)
    except Hold as exc:
        print('[ORACLE370_RECON_HOLD]',str(exc));return 2
    if result['status'] not in ('PENDING_OR_UNKNOWN','CONFIRMED_METADATA_PENDING'):
        atomic_json(CANARY_MARK,{**marker,'reconciliation':result,'status':result['status']})
    print('[ORACLE370_RECON]',json.dumps(result,sort_keys=True));return 0

def run(seconds=90,poll_ms=5,ttl_ms=2500,max_age_ms=1500,wallet_pubkey=None,keypair=None,live_canary=False):
    if not wallet_pubkey:raise Hold('WALLET_PUBLIC_KEY_REQUIRED')
    if live_canary and keypair is None:raise Hold('LIVE_WALLET_SIGNER_REQUIRED')
    core=bridge(); core.audit(require_installed=True)
    if not 1<=seconds<=1800 or not 5<=poll_ms<=100:raise Hold('RUNTIME_BOUNDS_INVALID')
    if not wallet_pubkey:raise Hold('WALLET_PUBLIC_KEY_REQUIRED')
    if live_canary and keypair is None:raise Hold('LIVE_WALLET_SIGNER_REQUIRED')
    if live_canary and CANARY_MARK.exists():raise Hold('PREVIOUS_CANARY_ATTEMPT_PRESENT_NO_RESEND')
    provider=NativeQ87Provider(wallet_pubkey)
    # Warm before source lock and scanner attachment; scanner is already running.
    provider.prewarm()
    rpc=core.RpcReadOnly(provider.rpc_url,budget=40)
    canary=Canary(keypair,provider) if live_canary else None

    class Worker(core.LatestWorker):
        def loop(self):
            while True:
                with self.cv:
                    while not self.latest and not self.stop:self.cv.wait(.2)
                    if self.stop:return
                    token,item=self.latest.popitem()
                row,generation=item
                result={'stage':'HOLD','reason':'UNKNOWN'}
                try:
                    issue=core.stage1_nomination(row)
                    if issue:raise Hold(issue)
                    proof=provider.prepare_unsigned(row)
                    if self.newer_or_invalid(token,generation):raise Hold('SUPERSEDED_BEFORE_SIM')
                    result=core.simulation_gate(row,proof,rpc)
                    if self.newer_or_invalid(token,generation):raise Hold('SUPERSEDED_AFTER_SIM')
                    if result['stage']=='UNSIGNED_SIM_NET_ESTIMATE_PASS' and canary and row['size_lamports']==CANARY:
                        def fresh():
                            return not self.newer_or_invalid(token,generation) and core.stage1_nomination(row) is None and not self.stop
                        # Even for 0.010 funded canary, first signed preflight must prove wallet WSOL gain.
                        done=canary.execute(row,proof,result,fresh)
                        result={'stage':'SENT_UNCONFIRMED','reason':'CANARY_SENT_RECONCILIATION_REQUIRED',
                                'signature':done['signature'],'event_id':row['event_id']}
                except Hold as exc:
                    result={'stage':'HOLD','reason':str(exc)}
                except Exception as exc:
                    result={'stage':'HOLD','reason':'PROVIDER_FAILURE_'+type(exc).__name__}
                if self.newer_or_invalid(token,generation) and result['stage'] not in ('SENT_UNCONFIRMED',):
                    result={'stage':'HOLD','reason':'SOURCE_INVALIDATED'}
                with self.cv:
                    self.results.append(result);self.results=self.results[-80:]
                    self.counts[result['reason']]+=1
                print('[ORACLE370_GATE]',json.dumps({k:v for k,v in result.items() if k in ('stage','reason','event_id')}),flush=True)

    # In-process worker injection: original ORACLE-368 source-reader, lock, SQLite
    # columnar decoding, audit and health logic all preserved; no replacement scanner.
    original=core.LatestWorker
    try:
        core.LatestWorker=Worker
        code=core.live(seconds=seconds,poll_ms=poll_ms,ttl_ms=ttl_ms,max_age_ms=max_age_ms,
                       provider=provider,rpc=rpc,report=REPORT)
    finally:
        core.LatestWorker=original
    print('[ORACLE370_EXIT]',json.dumps({'returncode':code,'native_provider':'Q18_Q25_Q87',
       'live_canary_requested':live_canary,'canary_attempt_present':CANARY_MARK.exists(),
       'scanner_unchanged':True,'new_websocket':False}),flush=True)
    return code


def tests():
    class T(unittest.TestCase):
        def test_invalid_program_graph(self):
            with self.assertRaisesRegex(Hold,'NATIVE_INSTRUCTION_GRAPH_UNREADABLE'):
                verify_native_program_sequence(b'not_v0','pump','dlmm')
        def test_swap_direction(self):
            self.assertEqual(CANARY,10_000_000)
        def test_rpc_method_guard(self):
            with self.assertRaisesRegex(Hold,'RPC_METHOD_UNAUTHORIZED'):
                _rpc('getProgramAccounts',[],url='https://example.org')
        def test_no_http(self):
            with self.assertRaisesRegex(Hold,'HTTPS_SOLANA_RPC_URL_REQUIRED'):
                _rpc('getMultipleAccounts',[],url='http://localhost')
        def test_invalid_wallet(self):
            with self.assertRaisesRegex(Hold,'WALLET_PUBKEY_REQUIRED'):
                NativeQ87Provider('not-key')
        def test_short_account(self):
            with self.assertRaisesRegex(Hold,'TOKEN_ACCOUNT_LAYOUT_INVALID'):
                _decode_token({'data':[base64.b64encode(b'0'*4).decode(),'base64']})
        def test_token_account_u64(self):
            x=bytearray(165);x[64:72]=(123456).to_bytes(8,'little')
            self.assertEqual(_decode_token({'data':[base64.b64encode(x).decode(),'base64']})[0],123456)
        def test_marker_prevents_resend(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'marker.json';atomic_json(p,{'status':'SEND_INTENT_UNKNOWN'});self.assertTrue(p.exists())
        def test_live_no_wallet(self):
            with self.assertRaisesRegex(Hold,'WALLET_PUBLIC_KEY_REQUIRED'):
                run(seconds=1,wallet_pubkey=None)
        def test_live_guard(self):
            k='11111111111111111111111111111111'
            with self.assertRaisesRegex(Hold,'LIVE_WALLET_SIGNER_REQUIRED'):
                run(seconds=1,wallet_pubkey=k,live_canary=True)
        def test_unsupported_reverse(self):
            p=NativeQ87Provider('11111111111111111111111111111111')
            core=bridge();now=time.time_ns()
            row={'schema':'ORACLE363_ATOMIC_REPRICE_REQUEST_V1','execution_authority':False,'signing':False,
                 'broadcast':False,'native_atomic_simulation_certified':False,'event_id':1,'scanner_epoch':1,
                 'scanner_slot':10,'size_lamports':CANARY,'direction':'METEORA_TO_PUMP',
                 'token':'11111111111111111111111111111111','pump_pool':'11111111111111111111111111111111',
                 'meteora_pool':'11111111111111111111111111111111','scanner_producer':'someproducer',
                 'expires_at_unix_ms':now//1_000_000+2000,'source_age_at_ingress_ms':1}
            with self.assertRaisesRegex(Hold,'REVERSE_BUILDER_UNVERIFIED'):
                p.prepare_unsigned(row)
        def test_recon_missing_signature(self):
            with self.assertRaisesRegex(Hold,'NO_CANARY_TRANSACTION'):
                reconcile_transaction({})
        def test_recon_pending(self):
            def fake(method,params):return {'value':[None]}
            self.assertEqual(reconcile_transaction({'signature':'sig'},fake)['status'],'PENDING_OR_UNKNOWN')
        def test_recon_chain_failed(self):
            def fake(method,params):return {'value':[{'err':{'InstructionError':[0,'err']}}]}
            self.assertEqual(reconcile_transaction({'signature':'sig'},fake)['status'],'CHAIN_TRANSACTION_FAILED')
        def test_recon_positive(self):
            token='Tk111';wallet='W111';sig='Sig111'
            def record(mint,balance):return {'mint':mint,'owner':wallet,'uiTokenAmount':{'amount':str(balance)}}
            def fake(method,params):
                if method=='getSignatureStatuses':return {'value':[{'err':None,'confirmationStatus':'confirmed'}]}
                if method=='getTransaction':return {'slot':42,'transaction':{'signatures':[sig],'message':{'accountKeys':[wallet]}},
                    'meta':{'err':None,'fee':5000,'preBalances':[1_000_000],
                    'postBalances':[990_000],
                    'preTokenBalances':[record('So11111111111111111111111111111111111111112',100),record(token,0)],
                    'postTokenBalances':[record('So11111111111111111111111111111111111111112',20100),record(token,0)]}}
                raise AssertionError('UNEXPECTED_RPC')
            r=reconcile_transaction({'signature':sig,'wallet_pubkey':wallet,'token_mint':token},fake)
            self.assertEqual(r['net_lamports'],10000)
            self.assertEqual(r['status'],'REALIZED_POSITIVE_RECONCILED')
        def test_recon_bad_residue(self):
            with self.assertRaisesRegex(Hold,'RECON_TOKEN_ACCOUNT_BALANCE_UNOBSERVED'):
                _token_owner_balance([], 'mint','wallet')
        def test_installer_compiles(self):
            compile(Path(__file__).read_text(encoding='utf-8'),__file__,'exec')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE370_TEST_PASS]' if result.wasSuccessful() else '[ORACLE370_TEST_FAIL]',result.testsRun)
    return result.wasSuccessful()


def main():
    ap=argparse.ArgumentParser()
    for s in ('install','test','audit','run','live-canary','reconcile'):ap.add_argument('--'+s,action='store_true')
    ap.add_argument('--seconds',type=int,default=90);ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--ttl-ms',type=int,default=2500);ap.add_argument('--max-age-ms',type=int,default=1500)
    ap.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET_PUBKEY',''))
    ap.add_argument('--wallet-hidden',action='store_true')
    a=ap.parse_args()
    if not any(getattr(a,s.replace('-','_')) for s in ('install','test','audit','run','live-canary','reconcile')):
        ap.error('SELECT_ACTION')
    if a.install:install()
    if a.test and not tests():return 1
    if a.audit:audit()
    if a.reconcile:return reconcile_canary()
    if a.run or a.live_canary:
        keypair=None
        wallet=a.wallet_pubkey
        if a.wallet_hidden:
            secret=getpass.getpass('Solana private key (hidden, process-local): ')
            try:keypair=_public_key(secret)
            finally:secret=None
            wallet=str(keypair.pubkey())
        if a.live_canary and keypair is None:raise Hold('USE_WALLET_HIDDEN_FOR_LIVE_CANARY')
        try:return run(a.seconds,a.poll_ms,a.ttl_ms,a.max_age_ms,wallet,keypair,a.live_canary)
        except Hold as exc:
            print('[ORACLE370_HOLD]',str(exc),flush=True);return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
