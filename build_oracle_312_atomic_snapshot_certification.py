"""ORACLE-312: native route packet certification and deterministic snapshot replay.
No wallet secrets, signing or broadcast. A fixture never certifies live profitability.
Uses the existing on-chain ALT resolver + canonical compiler, not invented account trimming.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, os, pathlib, tempfile, time, unittest
from unittest.mock import patch

OUT=pathlib.Path('runtime_state/oracle/oracle_live_execution/ORACLE312_ATOMIC_SNAPSHOT_CERTIFICATION.json')
LIMIT=1232
CANARY=10_000_000
DIRECTIONS={'PUMP_TO_METEORA','METEORA_TO_PUMP'}
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'

def disarm():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('ORACLE312_KEYLESS_DISARMED_ONLY')

def checked_route(j):
    if not isinstance(j,dict):raise ValueError('ROUTE_NOT_OBJECT')
    direction=j.get('direction')
    if direction not in DIRECTIONS:raise ValueError('INVALID_DIRECTION')
    if int(j.get('start_lamports',-1))!=CANARY:raise ValueError('NOT_EXACT_010_SOL')
    if int(j.get('snapshot_slot',0))<=0:raise ValueError('SNAPSHOT_SLOT_REQUIRED')
    if int(j.get('gross_lamports',0))<=0:raise ValueError('NO_POSITIVE_SNAPSHOT')
    ixs=j.get('instructions')
    if not isinstance(ixs,list) or not ixs:raise ValueError('NATIVE_INSTRUCTIONS_REQUIRED')
    if not isinstance(j.get('payer'),str) or not j['payer']:raise ValueError('PUBLIC_PAYER_REQUIRED')
    if not isinstance(j.get('blockhash'),str) or not j['blockhash']:raise ValueError('RECENT_BLOCKHASH_REQUIRED')
    counts={PUMP:0,DLMM:0};positions=[]
    for ix in ixs:
        p=ix.get('programId')
        if p in counts:counts[p]+=1;positions.append(p)
        if not isinstance(ix.get('accounts'),list) or not isinstance(ix.get('data'),str):raise ValueError('BAD_IX_FORMAT')
        base64.b64decode(ix['data'],validate=True)
        for a in ix['accounts']:
            if not all(x in a for x in ('pubkey','isSigner','isWritable')):raise ValueError('BAD_ACCOUNT_META')
    if counts[PUMP]!=1 or counts[DLMM]!=1:raise ValueError('TWO_NATIVE_SWAP_IX_REQUIRED')
    expected=[PUMP,DLMM] if direction=='PUMP_TO_METEORA' else [DLMM,PUMP]
    if positions!=expected:raise ValueError('SWAP_LEG_ORDER_WRONG')
    alts=j.get('alt_addresses',[])
    if not isinstance(alts,list) or not all(isinstance(x,str) for x in alts):raise ValueError('ALT_LIST_INVALID')
    if len(alts)!=len(set(alts)):raise ValueError('DUPLICATE_ALTS')
    return True

def snapshot_replay(j):
    """Math-only fixture: no funds move and no guarantee any pool could fill."""
    start=int(j['start_lamports']);gross=int(j['gross_lamports'])
    estimated_fee=int(j.get('fee_scenario_lamports',250000))
    return {'start_lamports':start,'gross_lamports':gross,'fee_scenario_lamports':estimated_fee,
            'scenario_net_lamports':gross-estimated_fee,
            'scenario_only':True,'onchain_simulation':False,'execution_proven':False}

def packet(j,compiler=None):
    """Physically compile through canonical native compiler; ALT data comes from RPC."""
    disarm();checked_route(j)
    if compiler is None and j.get('alt_addresses'):
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
        compiler=c.compile_v0
    begun=time.monotonic_ns();out={'direction':j['direction'],'slot':int(j['snapshot_slot']),
        'token':j.get('token'),'size_sol':.010,'alt_count':len(j.get('alt_addresses',[])),
        'signing':False,'broadcast':False,'onchain_simulation':False,'execution_admission':False,
        'snapshot':snapshot_replay(j)}
    if not j.get('alt_addresses'):
        out['gate']='HOLD_NO_POPULATED_ALT';return out
    try:
        msg,raw=compiler(j['payer'],j['instructions'],j['alt_addresses'],j['blockhash'])
        out['serialized_bytes']=len(raw)
        out['compile_ms']=round((time.monotonic_ns()-begun)/1e6,3)
        out['message_sha256']=hashlib.sha256(msg).hexdigest()
        out['gate']=('HOLD_PACKET_OVER_1232' if len(raw)>LIMIT else 'UNSIGNED_PACKET_READY_NEEDS_SIGNED_SIM_FRESH_NET')
    except Exception as e:
        # Do not print raw RPC errors: they might embed the RPC URL credential.
        err=str(e);out['gate']='HOLD_COMPILE_'+('PACKET_OVER_1232' if 'ATOMIC_TX_TOO_LARGE' in err else type(e).__name__.upper())
        if 'ATOMIC_TX_TOO_LARGE' in err:
            try:out['serialized_bytes']=int(err.rsplit(':',1)[1])
            except ValueError:pass
        out['compile_ms']=round((time.monotonic_ns()-begun)/1e6,3)
    return out

def alt_probe(j):
    disarm();checked_route(j)
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
    alts=j.get('alt_addresses',[])
    if not alts:return {'gate':'HOLD_NO_ALT','alt_count':0}
    begin=time.monotonic_ns()
    try:
        resolved=c.alt_accounts(alts)
        missing=[a for a in alts if not resolved.get(a)]
        # ALT coverage on a specific route must include non-signer addresses; signers are never ALT eligible.
        elig=set()
        for ix in j['instructions']:
            for a in ix['accounts']:
                if not a['isSigner'] and a['pubkey']!=j['payer'] and a['pubkey']!=ix['programId']:
                    elig.add(a['pubkey'])
        covered=set()
        for arr in resolved.values():
            for b in arr:covered.add(c.b58e(b))
        coverage=sorted(elig & covered)
        return {'gate':'HOLD_ALT_INCOMPLETE' if missing or not coverage else 'ALT_ADDRESSES_RESOLVED',
                'alt_count':len(alts),'alt_unavailable_count':len(missing),
                'eligible_non_signer_count':len(elig),'covered_non_signer_count':len(coverage),
                'probe_ms':round((time.monotonic_ns()-begin)/1e6,3),'execution_certified':False}
    except Exception as e:
        return {'gate':'HOLD_ALT_RPC_'+type(e).__name__,'execution_certified':False}

def demo():
    """A *synthetic* positive quote: intentionally no instructions and no executable contract."""
    return {'build':'ORACLE312','kind':'SYNTHETIC_MATH_DEMONSTRATION','start_lamports':CANARY,
            'gross_lamports':650000,'fee_scenario_lamports':250000,
            'scenario_net_lamports':400000,'real_quote':False,'onchain_simulation':False,
            'executable':False,'gate':'HOLD_SYNTHETIC_DATA_CANNOT_EXECUTE'}

class T(unittest.TestCase):
    def setUp(self):
        wsol='So11111111111111111111111111111111111111112'
        self.c=type('C',(),{'PUMP':PUMP,'DLMM':DLMM,'WSOL':wsol,'TOKEN':'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'})
        c=self.c; ix=lambda p:{'programId':p,'accounts':[{'pubkey':c.WSOL,'isSigner':False,'isWritable':True}], 'data':base64.b64encode(b'12345678').decode()}
        self.j={'direction':'PUMP_TO_METEORA','start_lamports':CANARY,'gross_lamports':650000,
           'snapshot_slot':12345,'payer':c.WSOL,'blockhash':c.WSOL,
           'instructions':[ix(c.PUMP),ix(c.DLMM)],'alt_addresses':[c.TOKEN]}
    def test_both_direction_order(self):
        checked_route(self.j)
        rev=dict(self.j,direction='METEORA_TO_PUMP',instructions=list(reversed(self.j['instructions'])))
        checked_route(rev)
        with self.assertRaisesRegex(ValueError,'ORDER'):checked_route(dict(self.j,direction='METEORA_TO_PUMP'))
    def test_canary_and_positive(self):
        with self.assertRaisesRegex(ValueError,'010_SOL'):checked_route(dict(self.j,start_lamports=5_000_000))
        with self.assertRaisesRegex(ValueError,'POSITIVE'):checked_route(dict(self.j,gross_lamports=0))
    def test_packet(self):
        result=packet(self.j,compiler=lambda *a:(b'xyz',b'0'*1100))
        self.assertEqual(result['serialized_bytes'],1100)
        self.assertFalse(result['execution_admission'])
        over=packet(self.j,compiler=lambda *a:(b'xyz',b'0'*1299))
        self.assertEqual(over['gate'],'HOLD_PACKET_OVER_1232')
    def test_synthetic_never_admitted(self):
        self.assertFalse(demo()['executable'])
        self.assertTrue(snapshot_replay(self.j)['scenario_only'])
    def test_no_alts(self):
        self.assertEqual(packet(dict(self.j,alt_addresses=[]))['gate'],'HOLD_NO_POPULATED_ALT')
    def test_disarm(self):
        with patch.dict(os.environ,{'QSB_SOLANA_PRIVATE_KEY':'example','QSB_LIVE_ARM':'NO'}):
            with self.assertRaisesRegex(RuntimeError,'KEYLESS'):packet(self.j)

def main():
    p=argparse.ArgumentParser(description='ORACLE312 read-only snapshot and native packet certification')
    p.add_argument('--test',action='store_true');p.add_argument('--demo',action='store_true');p.add_argument('--route-json');p.add_argument('--alt-probe',action='store_true');p.add_argument('--audit',action='store_true')
    a=p.parse_args()
    if a.test:
        unittest.main(argv=['oracle312','-v'],exit=False);return
    if a.demo:print('[ORACLE312_DEMO]',json.dumps(demo(),sort_keys=True));return
    if a.audit:
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
        print('[ORACLE312_AUDIT]',json.dumps({'p2m_callable':callable(getattr(rt,'same_snapshot_route',None)),
          'native_v0_compiler':callable(getattr(q87.c,'compile_v0',None)),
          'alt_aware_candidate_compiler':callable(getattr(q87,'compile_candidate',None)),
          'm2p_certified':False,'signed_simulation_certified':False,'broadcast':False},sort_keys=True));return
    if not a.route_json:p.error('Use --test, --demo, --audit or --route-json PATH')
    disarm();j=json.loads(pathlib.Path(a.route_json).read_text(encoding='utf-8'))
    result=alt_probe(j) if a.alt_probe else packet(j)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2),encoding='utf-8')
    print('[ORACLE312_RESULT]',json.dumps(result,sort_keys=True))
    print('[REPORT]',OUT)
if __name__=='__main__':main()
