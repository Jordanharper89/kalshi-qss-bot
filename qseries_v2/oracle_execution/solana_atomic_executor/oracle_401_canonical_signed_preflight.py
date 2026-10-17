
from __future__ import annotations
"""ORACLE-401: real canonical scanner -> native SDK -> signed SIMULATION ONLY.
No transaction broadcasting, no funds movement; scanner frozen; no new WebSockets.
"""
import argparse, base64, hashlib, importlib, json, os, sqlite3, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PKG='qseries_v2.oracle_execution.solana_atomic_executor'
STATE=ROOT/'runtime_state/oracle/final_boss_dual'
REPORT=STATE/'oracle_401_native_signed_preflight.json'
GRID=set(range(10_000_000,100_000_001,5_000_000))
SENTINEL='So11111111111111111111111111111111111111112'
class Hold(RuntimeError):pass

def imp(name):return importlib.import_module(PKG+'.'+name)

def checks():
    imp('oracle_399_final_boss_execution_owner').source_hashes()
    m=imp('oracle_399_native_sdk_bridge')
    native=m.native_source_contract()
    if not all(x['status']=='SOURCE_CONTRACT_VISIBLE' for x in native.values()):
        raise Hold('NATIVE_SOURCE_CONTRACT_DRIFT')
    reverse_src=(ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle_378_native_reverse_atomic.py').read_text(encoding='utf-8-sig')
    reverse_drift="dlmm='LBUZKhRxPF3XUpBCjp4YzTKgLccwBBzZYRSqNeZerDo'" in reverse_src
    return {'scanner_hashes':4,'native_source_contracts':len(native),
            'reverse_validator_program_id_drift':reverse_drift}

def exact_nomination(row, core):
    """Only use the real ORACLE-363 validated canonical event object."""
    if not isinstance(row,dict) or row.get('schema')!='ORACLE363_ATOMIC_REPRICE_REQUEST_V1':
        raise Hold('CANONICAL_363_EVENT_SCHEMA_REQUIRED')
    if type(row.get('size_lamports')) is not int or row['size_lamports'] not in GRID:
        raise Hold('SIZE_NOT_ON_CANONICAL_19_STEP_GRID')
    if row.get('direction') not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
        raise Hold('INVALID_DIRECTION')
    if core.stage1_nomination(row):raise Hold('FRESH_CANDIDATE_STAGE1_FAILED')
    return row

def token_amount(raw):
    if not isinstance(raw,dict):raise Hold('SIM_TOKEN_ACCOUNT_MISSING')
    data=raw.get('data')
    if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':
        raise Hold('SIM_TOKEN_ACCOUNT_DATA_MISSING')
    try:packet=base64.b64decode(data[0],validate=True)
    except Exception:raise Hold('SIM_TOKEN_ACCOUNT_DATA_INVALID') from None
    if len(packet)<72:raise Hold('SIM_TOKEN_ACCOUNT_SHORT')
    return int.from_bytes(packet[64:72],'little')

def simulated_balances(sim,proof,fee):
    """Conservative, no credit for intermediate-token residue or uncertain fees."""
    value=sim.get('value') if isinstance(sim,dict) else None
    if not isinstance(value,dict) or value.get('err') is not None:
        raise Hold('SIGNED_SIMULATION_REJECTED')
    accounts=value.get('accounts')
    if not isinstance(accounts,list) or len(accounts)!=3:
        raise Hold('SIGNED_SIMULATED_WALLET_ACCOUNTS_MISSING')
    if not all(type(proof.get(k)) is int for k in ('sol_before_lamports','wsol_before_raw','token_before_raw')):
        raise Hold('SIGNED_SIM_PRE_BALANCE_BASELINES_MISSING')
    if type(fee) is not int or fee<0:raise Hold('MESSAGE_FEE_NOT_VERIFIED')
    try:
        wallet_post=int(accounts[0]['lamports'])
        wsol_post=token_amount(accounts[1]); token_post=token_amount(accounts[2])
    except (TypeError,ValueError,KeyError):raise Hold('SIMULATED_BALANCES_INVALID') from None
    residue=token_post-proof['token_before_raw']
    if residue!=0:raise Hold('INTERMEDIATE_TOKEN_RESIDUE_UNRECONCILED')
    # Fee deducted AGAIN conservatively in case simulation wallet delta already contains it.
    net=(wallet_post-proof['sol_before_lamports'])+(wsol_post-proof['wsol_before_raw'])-fee
    if net<=0:raise Hold('SIGNED_SIM_FEE_ADJUSTED_NET_NONPOSITIVE')
    return {'fee_adjusted_conservative_sim_net_lamports':net,'token_residue_raw':0,'fee_lamports':fee}

def signer(wallet):
    """Explicit --signed-sim only. Never logs or writes the key material."""
    secret=os.environ.get('QSB_SOLANA_PRIVATE_KEY','')
    if not secret:raise Hold('QSB_SOLANA_PRIVATE_KEY_MISSING_NO_SIGNING')
    try:
        from solders.keypair import Keypair
        if secret.lstrip().startswith('['):
            numbers=json.loads(secret)
            raw=bytes(numbers)
            key=Keypair.from_bytes(raw) if len(raw)==64 else Keypair.from_seed(raw)
        else:key=Keypair.from_base58_string(secret)
    except Exception:raise Hold('WALLET_SECRET_FORMAT_UNSUPPORTED') from None
    if str(key.pubkey())!=wallet:raise Hold('WALLET_SIGNER_ADDRESS_MISMATCH')
    return key

def signed_preflight(row,proof,wallet,key,native_rpc):
    from solders.transaction import VersionedTransaction
    from solders.message import to_bytes_versioned
    bridge=imp('oracle_399_native_sdk_bridge')
    try:raw=base64.b64decode(proof['unsigned_transaction_b64'],validate=True)
    except Exception:raise Hold('NATIVE_UNSIGNED_BYTES_INVALID') from None
    if len(raw)>1232:raise Hold('NATIVE_PACKET_TOO_LARGE')
    tx=VersionedTransaction.from_bytes(raw)
    if len(tx.signatures)!=1 or str(tx.message.account_keys[0])!=wallet:
        raise Hold('SINGLE_WALLET_SIGNER_CONTRACT_FAILED')
    message=to_bytes_versioned(tx.message)
    if any(bytes(x) != bytes(64) for x in tx.signatures):
        raise Hold('NATIVE_TRANSACTION_NOT_UNSIGNED')
    if time.time_ns()-proof.get('bank_timestamp_ns',0)>850_000_000:
        raise Hold('NATIVE_SNAPSHOT_STALE_BEFORE_SIGNING')
    if imp('oracle_368_source_boundary_repair').stage1_nomination(row):
        raise Hold('CANONICAL_EVENT_EXPIRED_BEFORE_SIGNING')
    # Reject uninspected auxiliary fund-movement programs, even if a two-swap graph exists.
    allowed={bridge.PUMP,bridge.DLMM,'ComputeBudget111111111111111111111111111111',
             'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'}
    static=[str(v) for v in tx.message.account_keys]
    for ix in tx.message.instructions:
        if ix.program_id_index>=len(static) or static[ix.program_id_index] not in allowed:
            raise Hold('UNREVIEWED_AUXILIARY_INSTRUCTION_CANNOT_SIGN')
        if static[ix.program_id_index]=='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL' and bytes(ix.data)!=b'\x01':
            raise Hold('ATA_INSTRUCTION_NOT_IDEMPOTENT_CREATE')
    # Sign only AFTER identity, age, program, and ATA instruction checks.
    signed=VersionedTransaction.populate(tx.message,[key.sign_message(message)])
    signed_raw=bytes(signed)
    if len(signed_raw)>1232:raise Hold('SIGNED_PACKET_TOO_LARGE')
    minslot=proof['bank_slot']
    bridge.signed_v0_witness(signed_raw,row['direction'],wallet,str(tx.message.recent_blockhash),
                             rpc_alt=native_rpc,context_slot=minslot)
    fee_result=native_rpc('getFeeForMessage',[base64.b64encode(message).decode(),
                        {'commitment':'processed','minContextSlot':minslot}])
    fee=fee_result.get('value') if isinstance(fee_result,dict) else None
    if type(fee) is not int or not 0<=fee<=250_000:
        raise Hold('MESSAGE_FEE_MISSING_OR_OVER_CAP')
    if not proof.get('wallet_wsol_ata') or not proof.get('wallet_token_ata'):
        raise Hold('NATIVE_WALLET_ACCOUNT_BINDINGS_MISSING')
    config={'encoding':'base64','sigVerify':True,'replaceRecentBlockhash':False,
            'commitment':'processed','minContextSlot':minslot,
            'accounts':{'encoding':'base64',
            'addresses':[wallet,proof['wallet_wsol_ata'],proof['wallet_token_ata']]}}
    sim=native_rpc('simulateTransaction',[base64.b64encode(signed_raw).decode(),config])
    if not isinstance(sim,dict) or sim.get('context',{}).get('slot',0)<minslot:
        raise Hold('SIMULATION_BANK_BEHIND_NATIVE_QUOTE')
    economic=simulated_balances(sim,proof,fee)
    return {'status':'SIGNED_SIM_FEE_POSITIVE_PROTECTED_MINOUT_NOT_YET_CERTIFIED',
            'direction':row['direction'],'size_lamports':row['size_lamports'],
            'event_id':row['event_id'],'bank_slot':minslot,'sim_context_slot':sim['context']['slot'],
            'signature_verified_locally':True,'signature_prefix':str(signed.signatures[0])[:12],
            **economic}

def observe(seconds,wallet,do_sign=False,poll_ms=5):
    if not 1<=seconds<=120 or not 5<=poll_ms<=100:raise Hold('RUNTIME_BOUNDS_INVALID')
    checks()
    if not wallet or len(wallet)<32:raise Hold('PUBLIC_WALLET_REQUIRED')
    native=imp('oracle_370_native_atomic_executor')
    rev=imp('oracle_378_native_reverse_atomic')
    core=imp('oracle_368_source_boundary_repair')
    bus=imp('oracle_344_scanner_align')
    ingr=imp('oracle_363_verified_scanner_bus_binding')
    scheduling=imp('oracle_379_five_goal_executor')
    lock_module=imp('oracle_359_lock_safe_handoff')
    # Key is only loaded for explicit simulation, never passed to Node or an RPC.
    key=signer(wallet) if do_sign else None
    # One native provider warm, reusing original Q25/Q18/Q87 and SDK helpers.
    provider=rev.CompatibleNativeProvider(native,wallet)
    provider.prewarm()
    metrics=scheduling.Metrics()
    Ingress=scheduling.make_ingress(ingr,metrics)
    state={'captured':0,'native_unsigned':0,'signed_sim_pass':0,'attempts':0,'last_hold':'NO_FRESH_EVENT',
           'status':'HOLD_NO_FRESH_CANONICAL_NOMINATION','source':'ORACLE363_SQLITE'}
    def callback(row):
        state['captured']+=1
        if state['signed_sim_pass']>=1 or state['attempts']>=5 or (state['native_unsigned']>=1 and not do_sign):return
        state['attempts']+=1
        try:
            exact_nomination(row,core)
            if row['direction']=='METEORA_TO_PUMP' and checks()['reverse_validator_program_id_drift']:
                raise Hold('ORACLE378_REVERSE_PROGRAM_ID_MISMATCH')
            proof=provider.prepare_unsigned(row)
            issue=core.bank_native_gate(row,proof)
            if issue:raise Hold('NATIVE_SAME_BANK_GATE_'+str(issue))
            state['native_unsigned']+=1
            state['status']='NATIVE_UNSIGNED_SAME_BANK_PASS_SIGNED_SIM_NOT_REQUESTED'
            if do_sign:
                result=signed_preflight(row,proof,wallet,key,native._rpc)
                state.update(result)
                state['signed_sim_pass']+=1
        except Exception as e:
            # Do NOT expose exception bodies: might contain provider URLs/API tokens.
            code=str(e) if isinstance(e,Hold) else type(e).__name__
            state['last_hold']=code[:100]
            state['status']='HOLD_'+code[:80]
    gate=Ingress(ttl_ms=2500,max_age_ms=1500)
    gate.callback=callback
    db=None
    try:
        with lock_module.ExclusiveLock():
            db=bus.bus()
            db.execute('PRAGMA query_only=ON')
            hb=bus.validate_scanner(db)
            if not isinstance(hb,dict) or hb.get('ok') is not True:
                raise Hold('SCANNER_HEALTH_VALIDATOR_NOT_PASS')
            cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
            gate.attach(hb,cursor)
            deadline=time.monotonic()+seconds;next_health=time.monotonic()
            while time.monotonic()<deadline and state['signed_sim_pass']==0 and not gate.failed and state['attempts']<5 and (do_sign or state['native_unsigned']==0):
                if time.monotonic()>=next_health:
                    gate.health(bus.validate_scanner(db))
                    next_health=time.monotonic()+.25
                rows,new_cursor=bus.new_events(db,cursor)
                for raw in rows:
                    gate.accept(raw)
                    if state['signed_sim_pass'] or (state['native_unsigned'] and not do_sign):break
                cursor=new_cursor
                if not rows:time.sleep(poll_ms/1000)
            if gate.failed:raise Hold('SCANNER_HEALTH_OR_PRODUCER_CHANGED')
    finally:
        if db is not None:db.close()
    return state

def audit():
    x=checks()
    return {'build':'ORACLE401','freeze':'PASS',**x,'extra_ws':False,'broadcast':False,
            'signer_only_on_explicit_signed_sim':True,
            'status':'READY_FOR_BOUNDED_NATIVE_PREFLIGHT_NOT_SIGNED_SIM_CERTIFIED'}

def tests():
    assert len(GRID)==19
    class Core:
        @staticmethod
        def stage1_nomination(row):return None
    r={'schema':'ORACLE363_ATOMIC_REPRICE_REQUEST_V1',
       'size_lamports':25_000_000,'direction':'METEORA_TO_PUMP'}
    exact_nomination(r,Core)
    for bad in ({**r,'size_lamports':7},{**r,'direction':'UNKNOWN'},
                {**r,'schema':'FORGED'}):
        try:exact_nomination(bad,Core);raise AssertionError('invalid candidate accepted')
        except Hold:pass
    d=bytearray(165);d[64:72]=(17).to_bytes(8,'little')
    account={'data':[base64.b64encode(d).decode(),'base64']}
    assert token_amount(account)==17
    p={'sol_before_lamports':1000,'wsol_before_raw':100,'token_before_raw':17}
    sim={'value':{'err':None,'accounts':[{'lamports':1000},
                   {'data':[base64.b64encode((d[:64]+(200).to_bytes(8,'little')+d[72:])).decode(),'base64']},
                   account]}}
    assert simulated_balances(sim,p,10)['fee_adjusted_conservative_sim_net_lamports']==90
    try:simulated_balances(sim,p,101);raise AssertionError('nonprofit accepted')
    except Hold:pass
    try:simulated_balances(sim,{**p,'token_before_raw':1},10);raise AssertionError('residue accepted')
    except Hold:pass
    print('[PASS] ORACLE401 real 363 event contract, 19-size gate, no fake protected PnL, fee/residue checks')
    print('[SCOPE] Fixture tests only. Signed simulation requires live canonical nomination and explicit --signed-sim')

def main():
    ap=argparse.ArgumentParser()
    modes=ap.add_mutually_exclusive_group(required=True)
    for mode in ('test','audit','observe','signed-sim'):modes.add_argument('--'+mode,action='store_true')
    ap.add_argument('--wallet',default=os.environ.get('QSB_SOLANA_WALLET',''))
    ap.add_argument('--seconds',type=int,default=30)
    a=ap.parse_args()
    try:
        if a.test:tests();return 0
        if a.audit:result=audit()
        else:result=observe(a.seconds,a.wallet,do_sign=a.signed_sim)
        STATE.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
        print('[ORACLE401_RESULT]',json.dumps(result,sort_keys=True))
        print('[REPORT]',REPORT.relative_to(ROOT))
        return 0 if a.audit or result.get('signed_sim_pass',0)>0 or result.get('native_unsigned',0)>0 else 2
    except Exception as e:
        safe=str(e) if isinstance(e,Hold) else type(e).__name__
        # Non-Hold exception strings are never printed; may include secret/RPC URL.
        print('[ORACLE401_HOLD]',safe[:100]);return 2

if __name__=='__main__':raise SystemExit(main())
