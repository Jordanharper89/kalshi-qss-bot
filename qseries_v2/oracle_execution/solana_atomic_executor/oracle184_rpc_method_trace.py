"""Identify RPC -32601 method at the outbound request boundary. No broadcast."""
import argparse, json, os, re, subprocess, sys, urllib.request
from collections import Counter

METHOD=re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{1,79}$')

def extract_method(req):
    try:
        data=req.data if hasattr(req,'data') else None
        if not isinstance(data,(bytes,bytearray)) or len(data)>200000:
            return None
        doc=json.loads(data)
        name=doc.get('method') if isinstance(doc,dict) else None
        return name if isinstance(name,str) and METHOD.fullmatch(name) else None
    except (ValueError,TypeError,AttributeError):
        return None

def child():
    if os.getenv('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ORACLE184_LIVE_ARM_REFUSED')
    if not os.getenv('QSB_SOLANA_PRIVATE_KEY') or not os.getenv('SOLANA_RPC_URL'):
        raise RuntimeError('ORACLE184_CREDENTIALS_MISSING')

    real=urllib.request.urlopen
    calls=Counter()

    def traced(req,*args,**kwargs):
        name=extract_method(req)
        if name:
            if name.lower().startswith('send') or name.lower() in (
                'requestairdrop','simulatebundle'
            ):
                raise RuntimeError('ORACLE184_SEND_RPC_FORBIDDEN')
            calls[name]+=1
            print('[ORACLE184_RPC_CALL] method=%s count=%d' %
                  (name,calls[name]),flush=True)
        return real(req,*args,**kwargs)

    urllib.request.urlopen=traced

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle183_isolated_swap2_bootstrap as m
    )
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r

    old=r.q87.c.rpc

    def rpc_traced(method,*args,**kwargs):
        if str(method).lower().startswith('send'):
            raise RuntimeError('ORACLE184_SEND_RPC_FORBIDDEN')
        try:
            return old(method,*args,**kwargs)
        except Exception as exc:
            if '-32601' in str(exc):
                print('[ORACLE184_UNSUPPORTED_METHOD] method=%s' %
                      method,flush=True)
            raise

    r.q87.c.rpc=rpc_traced
    try:
        m.diagnostic(11)
    finally:
        r.q87.c.rpc=old
        urllib.request.urlopen=real
        print('[ORACLE184_RPC_SUMMARY] '+
              json.dumps(calls,sort_keys=True),flush=True)

def launch():
    import build_oracle_182_secure_windows_credentials as vault
    db=vault.api()
    h=vault.load(db,vault.HELIUS)
    s=vault.load(db,vault.SOLANA)
    if not h or not s:
        raise RuntimeError('ORACLE184_CREDENTIALS_NOT_STORED')

    env=os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY']=s
    env['SOLANA_RPC_URL']=(
        'https://mainnet.helius-rpc.com/?api-key='+
        vault.quote(h,safe='')
    )
    env['SOLANA_WS_URL']=(
        'wss://mainnet.helius-rpc.com/?api-key='+
        vault.quote(h,safe='')
    )
    env['QSB_LIVE_ARM']='NO'

    print('[ORACLE184_START] tracing RPC method names only; '
          'credentials hidden',flush=True)

    return subprocess.call([
        sys.executable,'-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.'
        'oracle184_rpc_method_trace','--child'
    ],env=env)

def test():
    class Request:
        data=b'{"jsonrpc":"2.0","method":"getMultipleAccounts","params":[]}'
    assert extract_method(Request())=='getMultipleAccounts'
    Request.data=b'{"method":"sendTransaction"}'
    assert extract_method(Request())=='sendTransaction'
    Request.data=b'{"method":"bad secret key"}'
    assert extract_method(Request()) is None
    print('[TEST PASS] ORACLE184 parses JSON-RPC method '
          'without exposing credentials')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true')
    g.add_argument('--run',action='store_true')
    g.add_argument('--child',action='store_true')
    a=p.parse_args()
    if a.test:
        test()
    elif a.run:
        sys.exit(launch())
    else:
        child()
