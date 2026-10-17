
from pathlib import Path
import argparse, asyncio, base64, copy, json, os, shutil, struct, time, types, unittest

TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_atomic_closeout.py')
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_ATOMIC_CLOSEOUT.json')
VERSION='ORACLE_ATOMIC_CLOSEOUT_V20_NATIVE_SWAP2_CONTRACT'
CANARY=10_000_000
P2M,M2P='PUMP_TO_METEORA','METEORA_TO_PUMP'
SWAP=bytes([248,198,158,145,225,117,135,200])
SWAP2=bytes([65,75,63,76,235,91,91,136])
MEMO='MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
ALT='HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'
ALT_OWNER='AddressLookupTab1e1111111111111111111111111'
FEE_BUFFER=30_000
MAX_LOCAL_CHECKS=24
FRESHNESS_MS=1500

def deny(*args,**kwargs):
    raise RuntimeError('NO_SIGNING_NO_BROADCAST_NO_ALT_MUTATION')

def quote_ok(q):
    try:
        return q['direction']==P2M and int(q['start'])==CANARY and int(q['local_net'])>0
    except (KeyError,TypeError,ValueError):
        return False

class VisitPool:
    def __init__(self,pool,index_fn):
        self.pool,self.index_fn=pool,index_fn
        self.indices=[]
    def __getattr__(self,name):
        return getattr(self.pool,name)
    def is_loaded(self,bin_id):
        index=int(self.index_fn(bin_id))
        if not self.indices or self.indices[-1]!=index:
            self.indices.append(index)
        return self.pool.is_loaded(bin_id)

def exact_replay(snap,template,amount,swap,quote_fn,index_fn):
    if amount<=0 or type(swap) is not bool:
        raise RuntimeError('INVALID_EXECUTION_INPUT')
    v=VisitPool(snap['dlmm_state'],index_fn)
    q=quote_fn(v,amount,swap_for_y=swap,strict=True)
    if not getattr(q,'complete',False) or int(getattr(q,'remaining_in',0) or 0):
        raise RuntimeError('PARTIAL_DLMM_QUOTE')
    if not v.indices or len(v.indices)>3:
        raise RuntimeError('BIN_ARRAY_COUNT_UNSUPPORTED')
    start=int(index_fn(snap['dlmm_state'].active_id))
    if v.indices[0]!=start:
        raise RuntimeError('ACTIVE_ARRAY_NOT_FIRST')
    step=-1 if swap else 1
    if any((b-a)*step<=0 for a,b in zip(v.indices,v.indices[1:])):
        raise RuntimeError('BIN_DIRECTION_DRIFT')
    arrays=list(template['arrays'])
    mapping={int(i):str(addr) for i,addr in arrays}
    if len(mapping)!=len(arrays):
        raise RuntimeError('DUPLICATE_ARRAY_INDEX')
    if any(i not in mapping or i not in snap['dlmm_state'].loaded_arrays for i in v.indices):
        raise RuntimeError('TRAVERSED_ARRAY_NOT_HYDRATED')
    return int(q.amount_out),[mapping[i] for i in v.indices]

def normalize_swap2(ix,expected_pool,program):
    raw=base64.b64decode(ix['data'],validate=True)
    accounts=copy.deepcopy(list(ix['accounts']))
    if raw[:8]==SWAP and len(raw)==24:
        if len(accounts)<15 or accounts[14]['pubkey']!=program:
            raise RuntimeError('LEGACY_SWAP_ACCOUNTS_INVALID')
        raw=SWAP2+raw[8:24]+bytes(4)
        accounts.insert(13,{
            'pubkey':MEMO,
            'isSigner':False,
            'isWritable':False
        })
    elif raw[:8]==SWAP2 and len(raw)==28:
        pass
    else:
        raise RuntimeError('UNSUPPORTED_METEORA_SWAP_ENCODING')
    if (raw[:8]!=SWAP2 or len(raw)!=28 or raw[24:]!=bytes(4)
        or len(accounts)<16 or accounts[0]['pubkey']!=expected_pool
        or accounts[13]['pubkey']!=MEMO or accounts[15]['pubkey']!=program
        or ix['programId']!=program):
        raise RuntimeError('SWAP2_ACCOUNT_OR_DATA_DRIFT')
    if accounts[13].get('isSigner') or accounts[13].get('isWritable'):
        raise RuntimeError('MEMO_ACCOUNT_FLAGS_INVALID')
    amount,min_out=struct.unpack_from('<QQ',raw,8)
    if amount<=0 or min_out<=0:
        raise RuntimeError('SWAP2_INVALID_AMOUNT')
    result=dict(ix)
    result['data']=base64.b64encode(raw).decode()
    result['accounts']=accounts
    return result,amount,min_out

def protected_margin(min_out,start,fee_reserve):
    if start!=CANARY or min_out<=start or fee_reserve<0:
        raise RuntimeError('NO_PROTECTED_SURPLUS')
    margin=min_out-start-fee_reserve
    if margin<=0:
        raise RuntimeError('PROTECTED_MARGIN_AFTER_FEE_RESERVE_NOT_POSITIVE')
    return margin

def build_bound(rt,wallet,snap,q,quote_fn,index_fn,fee_reserve=FEE_BUFFER):
    if not quote_ok(q):
        raise RuntimeError('NOT_POSITIVE_EXACT_0010_P2M')
    template=rt.METEORA_TEMPLATES.get(str(snap['token']))
    if not isinstance(template,dict):
        raise RuntimeError('NO_DLMM_TEMPLATE')
    swap=q['mq'].get('swap_for_y')
    if type(swap) is not bool or swap!=template['swap_for_y']:
        raise RuntimeError('QUOTE_DIRECTION_UNBOUND')
    if str(snap['meteora']['token_x'] if swap else snap['meteora']['token_y'])!=str(snap['token']):
        raise RuntimeError('INPUT_MINT_NOT_PUMP_TOKEN')
    route=rt.same_snapshot_route(wallet,snap,q)
    m,native_input,min_output=normalize_swap2(
        route['meteora_ix'],
        str(snap['meteora']['address']),
        rt.q87.c.DLMM
    )
    gross=int(q['pump_base_out_gross'])
    net=int(q['pump_base_out_net'])
    if not 0<native_input<=net<=gross:
        raise RuntimeError('NATIVE_TOKEN_AMOUNT_INVALID')
    claimed=int(q['mq']['raw_out'])
    replay_gross,_=exact_replay(snap,template,net,swap,quote_fn,index_fn)
    if replay_gross!=claimed:
        raise RuntimeError('QUOTE_REPLAY_MISMATCH')
    real_out,real_arrays=exact_replay(snap,template,native_input,swap,quote_fn,index_fn)
    if min_output>real_out:
        raise RuntimeError('NATIVE_MIN_OUTPUT_EXCEEDS_EXECUTABLE_QUOTE')
    margin=protected_margin(min_output,CANARY,fee_reserve)
    pump=route['pump_ix']
    pdata=base64.b64decode(pump['data'],validate=True)
    if (pump['programId']!=rt.q87.c.PUMP or len(pdata)<24
        or pdata[:8]!=rt.BUY_EXACT_QUOTE_IN_DISC
        or not any(a['pubkey']==snap['pump_pool'] for a in pump['accounts'])):
        raise RuntimeError('PUMP_EXACT_QUOTE_IN_UNBOUND')
    old_spend,old_min=struct.unpack_from('<QQ',pdata,8)
    if old_spend>CANARY:
        raise RuntimeError('PUMP_SPEND_EXCEEDS_0010')
    bound=rt.rewrite_pump_buy_bounds(pump,CANARY,max(old_min,gross))
    check=base64.b64decode(bound['data'],validate=True)
    if (len(check)!=len(pdata) or check[24:]!=pdata[24:]
        or check[:8]!=rt.BUY_EXACT_QUOTE_IN_DISC
        or struct.unpack_from('<QQ',check,8)!=(CANARY,max(old_min,gross))):
        raise RuntimeError('PUMP_BOUND_OR_TRAILER_CORRUPTED')
    ps=copy.deepcopy(route['pump_ixs'])
    ps[int(route['pump_index'])]=bound
    m['accounts']=copy.deepcopy(m['accounts'][:16])+[
        {'pubkey':addr,'isSigner':False,'isWritable':True}
        for addr in real_arrays
    ]
    rows=rt.q87.las.q59.candidate_instruction_sets(ps,m)
    full=next((ixs for name,ixs in rows if name=='FULL'),None)
    if (not full or sum(x['programId']==rt.q87.c.PUMP for x in full)!=1
        or sum(x['programId']==rt.q87.c.DLMM for x in full)!=1):
        raise RuntimeError('FULL_TWO_LEG_ATOMIC_INSTRUCTIONS_MISSING')
    return full,{
        'quoted_token_input':net,
        'native_token_input':native_input,
        'token_input_difference':net-native_input,
        'quoted_dlmm_output':claimed,
        'native_quoted_output':real_out,
        'native_minimum_output':min_output,
        'native_bin_arrays':real_arrays,
        'protected_margin_after_fee_reserve':margin,
        'fee_reserve':fee_reserve,
        'native_instruction':'SWAP2',
        'actual_fees_and_residue_certified':False
    }

def verify_alt(core):
    row=core.rpc('getAccountInfo',[
        ALT,{'encoding':'base64','commitment':'processed'}
    ])['value']
    if not row or row.get('owner')!=ALT_OWNER:
        raise RuntimeError('ALT_OWNER_INVALID')
    raw=base64.b64decode(row['data'][0],validate=True)
    if (len(raw)<56 or (len(raw)-56)%32
        or struct.unpack_from('<I',raw,0)[0]!=1
        or struct.unpack_from('<Q',raw,4)[0]!=(1<<64)-1):
        raise RuntimeError('ALT_NOT_ACTIVE')
    return ALT

def report_base(run_id):
    return dict(
        build=VERSION,run_id=run_id,status='HOLD',
        ready=0,notifications=0,priced_events=0,
        evaluations={P2M:0,M2P:0},best_quotes={},
        local_check_pass=0,local_check_reject={},
        local_check_count=0,attempts=[],holds=[],
        signing=False,broadcast=False,canary_sent=False,
        profit_certified=False
    )

def write_report(root,report):
    path=root/REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(
        json.dumps(report,indent=2,sort_keys=True)+'\n',
        encoding='utf-8'
    )
    temp.replace(path)

def child(root,seconds,run_id):
    report=report_base(run_id)
    lane=None
    try:
        if any(
            'PRIVATE_KEY' in x.upper() or 'SECRET_KEY' in x.upper()
            for x in os.environ
        ):
            raise RuntimeError('SECRET_PRESENT_IN_READONLY_RUNTIME')
        from solders.pubkey import Pubkey
        from meteora_dlmm import quote as dlmm_quote
        from meteora_dlmm.decode import array_index_of
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
        from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
        from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
        from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
        from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25

        wallet=os.environ.get('QSB_SOLANA_WALLET','').strip()
        Pubkey.from_string(wallet)
        core=rt.q87.c
        real_rpc=core.rpc

        def readonly(method,params):
            if not isinstance(method,str) or not (
                method.startswith('get') or method=='simulateTransaction'
            ):
                raise RuntimeError('NON_READONLY_RPC_BLOCKED')
            return real_rpc(method,params)

        core.rpc=readonly
        core.keypair=core.signed_tx=core.send=deny
        state,_=q25.prepare_once(root)
        q25.bind_cached_state(state)
        warm=rt.install_proven_hot_math(state)
        pairs=list(state.get('pairs') or [])
        addresses=list(state.get('addresses') or [])

        if not pairs or not addresses or not state.get('preg'):
            raise RuntimeError('MISSING_WARM_PAIR_INVENTORY')

        rt.USER=wallet
        rt.prebuild_templates(state,wallet)
        rt.prebuild_meteora_templates(state,wallet,warm)
        ready=set(rt.READY_TOKENS)
        report['ready']=len(ready)

        if not ready:
            raise RuntimeError('NO_READY_PAIRS')

        for pair in pairs:
            if str(pair.token) in ready:
                q18.worker().warm(str(pair.pump_pool))

        lane=q20.LatestStateLane()
        ticket={
            'sent':False,'busy':False,
            'checks':0,'compiled':0,'alt':None
        }

        def price(self,token,row):
            snap,slot,received,generation=row

            if self.newer_waiting(token,generation):
                return
            if (time.perf_counter_ns()-received)/1e6>FRESHNESS_MS:
                return

            try:
                quotes=q18.exact_snapshot_opportunities(snap,.010)
            except Exception as ex:
                key='PRICING_'+type(ex).__name__
                report['local_check_reject'][key]=(
                    report['local_check_reject'].get(key,0)+1
                )
                return

            for q in quotes:
                d=q.get('direction')
                if d not in (P2M,M2P):
                    continue

                report['evaluations'][d]+=1
                net=int(q['local_net'])

                if (
                    d not in report['best_quotes']
                    or net>report['best_quotes'][d]['quote_lamports']
                ):
                    report['best_quotes'][d]=dict(
                        quote_lamports=net,
                        slot=int(slot),
                        token=str(token)
                    )

                if (
                    not quote_ok(q)
                    or ticket['sent']
                    or ticket['busy']
                    or ticket['checks']>=MAX_LOCAL_CHECKS
                ):
                    continue

                ticket['checks']+=1
                report['local_check_count']=ticket['checks']

                try:
                    fee_reserve=max(
                        FEE_BUFFER,
                        int(state.get('landing') or 0)
                    )
                    ixs,bounds=build_bound(
                        rt,wallet,snap,q,
                        dlmm_quote,array_index_of,
                        fee_reserve
                    )
                    report['local_check_pass']+=1
                except Exception as ex:
                    code=(
                        type(ex).__name__+':'
                        +str(ex).split(':',1)[0][:90]
                    )
                    report['local_check_reject'][code]=(
                        report['local_check_reject'].get(code,0)+1
                    )
                    continue

                if (
                    self.newer_waiting(token,generation)
                    or (time.perf_counter_ns()-received)/1e6>FRESHNESS_MS
                ):
                    code='STALE_BEFORE_RPC'
                    report['local_check_reject'][code]=(
                        report['local_check_reject'].get(code,0)+1
                    )
                    continue

                if ticket['compiled']>=2:
                    continue

                ticket['busy']=True
                attempt=dict(
                    status='HOLD',
                    slot=int(slot),
                    token=str(token),
                    bounds=bounds
                )

                try:
                    if ticket['alt'] is None:
                        ticket['alt']=verify_alt(core)

                    blockhash=core.rpc(
                        'getLatestBlockhash',
                        [{'commitment':'processed'}]
                    )['value']['blockhash']

                    built=rt.q87.compile_candidate(
                        wallet,ixs,[[ticket['alt']]],blockhash
                    )

                    ticket['compiled']+=1

                    if not built.get('ok'):
                        raise RuntimeError('ATOMIC_COMPILE_REJECTED')

                    raw=bytes(built['unsigned'])
                    attempt['tx_bytes']=len(raw)

                    if (
                        len(raw)>1232
                        or raw[:65]!=bytes([1])+bytes(64)
                        or raw[65:66]!=bytes([128])
                    ):
                        raise RuntimeError('UNSIGNED_ATOMIC_V0_INVALID')

                    if (
                        self.newer_waiting(token,generation)
                        or (time.perf_counter_ns()-received)/1e6>FRESHNESS_MS
                    ):
                        raise RuntimeError('STALE_BEFORE_SIMULATION')

                    ticket['sent']=True

                    response=core.rpc(
                        'simulateTransaction',
                        [
                            base64.b64encode(raw).decode(),
                            {
                                'encoding':'base64',
                                'sigVerify':False,
                                'replaceRecentBlockhash':True,
                                'commitment':'processed'
                            }
                        ]
                    )['value']

                    attempt['error']=response.get('err')
                    attempt['compute_units']=response.get('unitsConsumed')
                    attempt['logs_tail']=list(
                        response.get('logs') or []
                    )[-5:]
                    attempt['status']=(
                        'UNSIGNED_SIM_PASS_ECONOMICS_HOLD'
                        if response.get('err') is None
                        else 'SIMULATION_REJECTED'
                    )

                except Exception as ex:
                    attempt['reason']=(
                        type(ex).__name__+':'+str(ex)[:100]
                    )
                finally:
                    ticket['busy']=False
                    report['attempts'].append(attempt)

                break

        lane._price=types.MethodType(price,lane)
        lane.start()

        p=q19.persistent
        shards=p.m._shards(addresses)

        if not shards:
            raise RuntimeError('NO_WS_SHARDS')

        counters={
            k:0 for k in (
                'acks','connections','notifications',
                'priced_events','reconnects',
                'rate_limit_disconnects','queue_drops',
                'event_errors'
            )
        }
        counters.update(
            last_ws_error=None,
            lat=[],
            best=None
        )

        async def observe():
            queue=asyncio.Queue(maxsize=4096)
            stop=asyncio.Event()
            tasks=[
                asyncio.create_task(
                    p._worker(i,s,queue,counters,stop)
                )
                for i,s in enumerate(shards)
            ]
            started=time.monotonic()

            try:
                while time.monotonic()-started<seconds:
                    try:
                        ev=await asyncio.wait_for(
                            queue.get(),timeout=.2
                        )
                    except asyncio.TimeoutError:
                        continue

                    binding=state['preg'].get(
                        ev.get('address')
                    )
                    if binding is None:
                        continue

                    i,kind=binding
                    pair=pairs[i]

                    if str(pair.token) not in ready:
                        continue

                    try:
                        changed=p.m.pd.apply_account_event(
                            pair,kind,ev['address'],
                            ev['raw'],ev['slot'],
                            ev['received_ns']
                        )
                        if changed:
                            counters['priced_events']+=1
                            lane.submit(
                                str(pair.token),
                                rt.immutable_snapshot(pair),
                                ev['slot'],
                                ev['received_ns']
                            )
                    except Exception:
                        counters['event_errors']+=1

            finally:
                stop.set()
                for t in tasks:
                    t.cancel()
                await asyncio.gather(
                    *tasks,
                    return_exceptions=True
                )

        asyncio.run(observe())
        lane.close()

        report['notifications']=counters['notifications']
        report['priced_events']=counters['priced_events']
        report['ws_acks']=counters['acks']
        report['ws_reconnects']=counters['reconnects']
        report['shard_sizes']=[
            len(s) for s in shards
        ]

        if any(
            x['status']=='UNSIGNED_SIM_PASS_ECONOMICS_HOLD'
            for x in report['attempts']
        ):
            report['status']='UNSIGNED_SIM_EVIDENCE_ONLY'

        report['holds'] += [
            'ACTUAL_TRANSACTION_FEES_UNVERIFIED',
            'TRANSFER_FEES_AND_RESIDUE_UNVERIFIED',
            'M2P_NATIVE_EXECUTION_UNVERIFIED',
            'NO_REALIZED_PROFIT'
        ]

        if not ticket['sent']:
            report['holds'].append(
                'NO_QUALIFIED_PROTECTED_ATOMIC_SIMULATION'
            )

    except Exception as ex:
        report['holds'].append(
            'ENGINE_'+type(ex).__name__
            +':'+str(ex)[:100]
        )
    finally:
        if lane is not None:
            try:
                lane.close()
            except Exception:
                pass
        write_report(root,report)

    return 0

class Tests(unittest.TestCase):

    def setUp(self):
        self.pool=types.SimpleNamespace(
            active_id=-538,
            loaded_arrays={-8,-9},
            is_loaded=lambda b:b//70 in {-8,-9}
        )
        self.snap={'dlmm_state':self.pool}
        self.t={
            'arrays':[(-9,'a9'),(-8,'a8')],
            'swap_for_y':True
        }

    def fixture_m(self,disc=SWAP,extra=b''):
        ac=[
            {'pubkey':'DP'}
        ]+[
            {'pubkey':'fixed'} for _ in range(12)
        ]+[
            {'pubkey':'event'},
            {'pubkey':'DLMM'},
            {'pubkey':'WRONG'}
        ]
        return {
            'programId':'DLMM',
            'accounts':ac,
            'data':base64.b64encode(
                disc
                +struct.pack(
                    '<QQ',
                    2_189_127_680,
                    10_055_232
                )
                +extra
            ).decode()
        }

    def test_legacy_to_swap2(self):
        m,amount,minimum=normalize_swap2(
            self.fixture_m(),'DP','DLMM'
        )
        self.assertEqual(
            base64.b64decode(m['data'])[:8],
            SWAP2
        )
        self.assertEqual(
            len(base64.b64decode(m['data'])),
            28
        )
        self.assertEqual(
            m['accounts'][13]['pubkey'],
            MEMO
        )
        self.assertEqual(
            m['accounts'][15]['pubkey'],
            'DLMM'
        )
        self.assertEqual(
            (amount,minimum),
            (2_189_127_680,10_055_232)
        )

    def test_existing_swap2_preserved(self):
        m=self.fixture_m(SWAP2,bytes(4))
        m['accounts'].insert(
            13,
            {
                'pubkey':MEMO,
                'isSigner':False,
                'isWritable':False
            }
        )
        out,_,_=normalize_swap2(m,'DP','DLMM')
        self.assertEqual(out,m)

    def test_bad_swap_encoding_refused(self):
        with self.assertRaisesRegex(
            RuntimeError,'UNSUPPORTED_METEORA'
        ):
            normalize_swap2(
                self.fixture_m(b'12345678'),
                'DP','DLMM'
            )

    def test_bad_program_order_refused(self):
        m=self.fixture_m()
        m['accounts'][14]['pubkey']='WRONG'
        with self.assertRaisesRegex(
            RuntimeError,'LEGACY_SWAP_ACCOUNTS'
        ):
            normalize_swap2(m,'DP','DLMM')

    def test_canary(self):
        self.assertTrue(quote_ok({
            'direction':P2M,
            'start':CANARY,
            'local_net':1
        }))
        self.assertFalse(quote_ok({
            'direction':P2M,
            'start':CANARY+1,
            'local_net':1
        }))

    def test_negative_rejected(self):
        self.assertFalse(quote_ok({
            'direction':P2M,
            'start':CANARY,
            'local_net':-1
        }))

    def test_no_sign(self):
        with self.assertRaisesRegex(
            RuntimeError,'NO_SIGNING'
        ):
            deny()

    def test_bin_array(self):
        def q(pool,amount,swap_for_y,strict):
            pool.is_loaded(-538)
            return types.SimpleNamespace(
                complete=True,
                remaining_in=0,
                amount_out=amount
            )
        self.assertEqual(
            exact_replay(
                self.snap,self.t,5,True,
                q,lambda x:x//70
            ),
            (5,['a8'])
        )

    def test_fee_margin(self):
        with self.assertRaisesRegex(
            RuntimeError,'PROTECTED_MARGIN'
        ):
            protected_margin(
                CANARY+20_000,
                CANARY,FEE_BUFFER
            )
        self.assertEqual(
            protected_margin(
                CANARY+55_000,
                CANARY,FEE_BUFFER
            ),
            25_000
        )

    def test_full_rebind_legacy_with_pump_trailer(self):
        gross=2_197_000_000
        net=2_193_514_710

        class C:
            PUMP='PUMP'
            DLMM='DLMM'

        class Q:
            @staticmethod
            def candidate_instruction_sets(ps,m):
                return [('FULL',ps+[m])]

        class RT:
            q87=types.SimpleNamespace(
                c=C(),
                las=types.SimpleNamespace(q59=Q())
            )
            BUY_EXACT_QUOTE_IN_DISC=b'EXACTBUY'
            METEORA_TEMPLATES={
                't':{
                    'arrays':[(-8,'GOOD')],
                    'swap_for_y':True
                }
            }

            @staticmethod
            def rewrite_pump_buy_bounds(
                p,spend,minimum
            ):
                out=dict(p)
                old=base64.b64decode(p['data'])
                out['data']=base64.b64encode(
                    b'EXACTBUY'
                    +struct.pack(
                        '<QQ',spend,minimum
                    )
                    +old[24:]
                ).decode()
                return out

            @staticmethod
            def same_snapshot_route(
                wallet,snap,q
            ):
                p={
                    'programId':'PUMP',
                    'accounts':[
                        {'pubkey':'PP'}
                    ],
                    'data':base64.b64encode(
                        b'EXACTBUY'
                        +struct.pack(
                            '<QQ',CANARY,100
                        )
                        +b'\x01'
                    ).decode()
                }
                m=Tests().fixture_m()
                return dict(
                    pump_ix=p,
                    meteora_ix=m,
                    pump_ixs=[p],
                    pump_index=0
                )

        quote={
            'direction':P2M,
            'start':CANARY,
            'local_net':95_575,
            'pump_base_out_gross':gross,
            'pump_base_out_net':net,
            'mq':{
                'raw_out':10_095_575,
                'swap_for_y':True
            }
        }

        snap=dict(
            self.snap,
            token='t',
            pump_pool='PP',
            meteora={
                'address':'DP',
                'token_x':'t',
                'token_y':'WSOL'
            }
        )

        def sdk(pool,amount,swap_for_y,strict):
            pool.is_loaded(-538)
            return types.SimpleNamespace(
                complete=True,
                remaining_in=0,
                amount_out=(
                    10_095_575
                    if amount==net
                    else 10_075_100
                )
            )

        instructions,bounds=build_bound(
            RT(),'user',snap,quote,
            sdk,lambda x:x//70
        )

        self.assertEqual(
            bounds['token_input_difference'],
            4_387_030
        )
        self.assertEqual(
            bounds['native_bin_arrays'],
            ['GOOD']
        )
        self.assertEqual(
            bounds['protected_margin_after_fee_reserve'],
            25_232
        )
        self.assertEqual(
            instructions[-1]['accounts'][-1]['pubkey'],
            'GOOD'
        )
        self.assertEqual(
            base64.b64decode(
                instructions[0]['data']
            )[-1],
            1
        )
        self.assertEqual(
            len(base64.b64decode(
                instructions[-1]['data']
            )),
            28
        )

    def test_report_readonly(self):
        r=report_base('x')
        self.assertFalse(r['signing'])
        self.assertFalse(r['profit_certified'])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument(
        '--test',action='store_true'
    )
    args=ap.parse_args()

    if args.test:
        result=unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(
                Tests
            )
        )
        return 0 if result.wasSuccessful() else 1

    dest=Path.cwd()/TARGET

    if not dest.parent.is_dir():
        print(
            '[HOLD] CANONICAL_EXECUTOR_PACKAGE_MISSING'
        )
        return 2

    if Path(__file__).resolve()!=dest.resolve():
        shutil.copyfile(
            Path(__file__),
            dest
        )

    print('[PASS]',VERSION,dest)
    print(
        '[MODE] SAME_SCANNER; LEGACY_TO_SWAP2; '
        'NATIVE_INPUT_REPRICE; MAX_ONE_SIM'
    )
    print(
        '[SIGNING] FALSE [BROADCAST] FALSE '
        '[ALT_MUTATION] FALSE'
    )
    return 0

if __name__=='__main__':
    raise SystemExit(main())
