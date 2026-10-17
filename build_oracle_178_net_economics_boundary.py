
"""ORACLE178 complete installer: packet-linked preliminary economic screen."""
import argparse, ast
from build_oracle_173_rpc_backoff_boundary import install_block, TARGET

MARK='# ORACLE178_NET_ECONOMICS_BOUNDARY'
BLOCK='''# ORACLE178_NET_ECONOMICS_BOUNDARY
_ORACLE178_PREVIOUS_SIM=simulate_current

def _oracle178_evaluate(compiled,sim):
    if not isinstance(compiled,dict) or not isinstance(sim,dict):
        return {'status':'HOLD_INVALID_INPUT','screen_pass':False}
    if sim.get('oracle177_signed_sim_pass') is not True:
        return {'status':'HOLD_SIGNED_SIM_NOT_PASSED','screen_pass':False}
    if sim.get('oracle177_message_sha256')!=compiled.get('oracle176_packet_hash'):
        return {'status':'HOLD_PACKET_SIM_IDENTITY_MISMATCH','screen_pass':False}
    projected=compiled.get('oracle176_route_net')
    if type(projected) is not int or projected<=0:
        return {'status':'HOLD_EXECUTABLE_RETURN_UNPROVEN','screen_pass':False}
    # Never guess a complete bound for network, priority, rent or token fees.
    max_total_fees=compiled.get('oracle178_max_total_fees_lamports')
    if type(max_total_fees) is not int or max_total_fees<0:
        return {'status':'HOLD_TOTAL_FEE_BOUND_NOT_PROVEN','screen_pass':False}
    expected=projected-max_total_fees
    screen=expected>=10_000
    return {
        'status':'PRELIMINARY_SCREEN_PASS' if screen else 'HOLD_BELOW_NET_FLOOR',
        'screen_pass':screen,
        'expected_net_lamports':expected,
        'gross_lamports':projected,
        'max_total_fees_lamports':max_total_fees
    }

def simulate_current(compiled,user):
    import json as _json
    from pathlib import Path as _Path
    sim=_ORACLE178_PREVIOUS_SIM(compiled,user)
    result=_oracle178_evaluate(compiled,sim)
    digest=compiled.get('oracle176_packet_hash') if isinstance(compiled,dict) else None
    row={'build':'ORACLE178','message_sha256':digest,
         'status':result['status'],
         'preliminary_screen_pass':result['screen_pass'],
         'realized_profit_certified':False,
         'execution_authorized':False,
         'broadcast':False}
    for field in ('expected_net_lamports','gross_lamports','max_total_fees_lamports'):
        if field in result:row[field]=result[field]
    path=_Path('runtime_state/oracle/oracle_live_execution/ORACLE178_NET_ECONOMICS.jsonl')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:
        f.write(_json.dumps(row,sort_keys=True)+'\\n')
    print('[ORACLE178_ECON] %s realized_certified=FALSE broadcast=FALSE' %
          result['status'],flush=True)
    if isinstance(sim,dict):
        sim=dict(sim)
        sim['oracle178_preliminary_screen_pass']=result['screen_pass']
        sim['oracle178_realized_profit_certified']=False
    return sim
'''

def test():
    ast.parse(BLOCK)
    env={'simulate_current':lambda c,u:{'oracle177_signed_sim_pass':True}}
    exec(BLOCK,env)
    evaluate=env['_oracle178_evaluate']
    digest='a'*64
    compiled={'oracle176_packet_hash':digest,'oracle176_route_net':80_000}
    sim={'oracle177_signed_sim_pass':True,'oracle177_message_sha256':digest}
    assert not evaluate(compiled,sim)['screen_pass']
    compiled['oracle178_max_total_fees_lamports']=30_000
    assert evaluate(compiled,sim)['screen_pass']
    compiled['oracle178_max_total_fees_lamports']=71_000
    assert not evaluate(compiled,sim)['screen_pass']
    sim['oracle177_message_sha256']='different'
    assert not evaluate(compiled,sim)['screen_pass']
    assert "'realized_profit_certified':False" in BLOCK
    print('[TEST PASS] ORACLE178 net economics, missing-fee HOLD, no false profit')

def install():
    install_block('ORACLE178',MARK,BLOCK,
                  ('ORACLE177_SIGNED_SIM_TRUTH',))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    a=p.parse_args()
    test() if a.test else install()
