
"""ORACLE177 complete installer: enforce sigVerify and packet-linked simulation."""
import argparse, ast, re
from build_oracle_173_rpc_backoff_boundary import install_block, TARGET

MARK='# ORACLE177_SIGNED_SIM_TRUTH'

def rewrite_sigverify(source):
    tree=ast.parse(source)
    funcs=[x for x in tree.body if isinstance(x,ast.FunctionDef) and
           x.name=='simulate_current' and 'simulateTransaction' in
           (ast.get_source_segment(source,x) or '')]
    if len(funcs)!=1:
        raise RuntimeError('HOLD_ORACLE177_SIM_RPC_BOUNDARY_NOT_UNIQUE')
    f=funcs[0]
    lines=source.splitlines(keepends=True)
    body=''.join(lines[f.lineno-1:f.end_lineno])
    pattern=r'([\'\"]sigVerify[\'\"]\s*:\s*)(True|False)'
    matches=list(re.finditer(pattern,body))
    if len(matches)!=1:
        raise RuntimeError('HOLD_ORACLE177_SIGVERIFY_KEY_UNKNOWN')
    updated=re.sub(pattern,r'\g<1>True',body,count=1)
    changed=''.join(lines[:f.lineno-1])+updated+''.join(lines[f.end_lineno:])
    ast.parse(changed)
    return changed

BLOCK='''# ORACLE177_SIGNED_SIM_TRUTH
_ORACLE177_PREVIOUS_SIM=simulate_current

def simulate_current(compiled,user):
    import json as _json
    from pathlib import Path as _Path
    if not isinstance(compiled,dict) or compiled.get('oracle176_packet_verified') is not True:
        raise RuntimeError('ORACLE177_NATIVE_PACKET_NOT_CERTIFIED')
    digest=compiled.get('oracle176_packet_hash')
    if not isinstance(digest,str) or len(digest)!=64:
        raise RuntimeError('ORACLE177_PACKET_HASH_ABSENT')
    if compiled.get('oracle162_signature_verified') is not True:
        raise RuntimeError('ORACLE177_SIGNED_TX_REQUIRED')
    result=_ORACLE177_PREVIOUS_SIM(compiled,user)
    if not isinstance(result,dict):
        raise RuntimeError('ORACLE177_SIM_RESPONSE_NOT_MAPPING')
    err=result.get('err','MISSING_ERR')
    units=result.get('unitsConsumed')
    passed=(err is None and type(units) is int and units>=0)
    record={'build':'ORACLE177','message_sha256':digest,
            'signed_sim_success':passed,
            'units_consumed':units if type(units) is int else None,
            'error_type':type(err).__name__ if err is not None else None,
            'execution_authorized':False,'broadcast':False}
    path=_Path('runtime_state/oracle/oracle_live_execution/ORACLE177_SIGNED_SIM.jsonl')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:
        f.write(_json.dumps(record,sort_keys=True)+'\\n')
    updated=dict(result)
    updated['oracle177_signed_sim_pass']=passed
    updated['oracle177_message_sha256']=digest
    updated['oracle177_sim_units']=units if type(units) is int else None
    print('[ORACLE177_SIM_%s] units=%s digest=%s broadcast=FALSE' %
          ('PASS' if passed else 'HOLD',str(units),digest[:16]),flush=True)
    return updated
'''

def test():
    ast.parse(BLOCK)
    sample=('def simulate_current(c,u):\n'
            '    a=rpc("simulateTransaction",[{"sigVerify":False}])\n'
            '    return a\n')
    fixed=rewrite_sigverify(sample)
    assert '"sigVerify":True' in fixed
    assert rewrite_sigverify(fixed)==fixed
    for bad in ('def simulate_current(a,b):return {}\n',
                'def simulate_current(a,b):return rpc("simulateTransaction",[])\n'):
        try:rewrite_sigverify(bad)
        except RuntimeError:pass
        else:raise AssertionError('missing sigVerify accepted')
    assert 'ORACLE177_NATIVE_PACKET_NOT_CERTIFIED' in BLOCK
    print('[TEST PASS] ORACLE177 sigVerify, native packet binding, fail-closed sim truth')

def install():
    install_block('ORACLE177',MARK,BLOCK,
                  ('ORACLE176_COMPILED_V0_IDENTITY',),
                  rewrite=rewrite_sigverify)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    a=p.parse_args()
    test() if a.test else install()
