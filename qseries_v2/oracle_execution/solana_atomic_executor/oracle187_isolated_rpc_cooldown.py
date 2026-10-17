"""Bounded RPC 429 retries, isolated ORACLE186 only; NO broadcast."""
import argparse, json, os, random, time, urllib.error, urllib.request
from urllib.parse import urlsplit
from . import oracle186_direct_route_truth as q186

class RpcGate:
    def __init__(self,original,endpoint,sleep=time.sleep):
        self.original=original
        self.endpoint=urlsplit(endpoint)
        self.sleep=sleep
        self.throttles=0
        self.attempts=0
        self.next_allowed=0.0

    def method(self,request):
        try:
            raw=request.data
            obj=json.loads(raw)
            return obj.get('method') if isinstance(obj,dict) else None
        except (TypeError,ValueError,AttributeError):
            return None

    def __call__(self,request,*args,**kwargs):
        url=request.full_url if hasattr(request,'full_url') else str(request)
        dest=urlsplit(url)
        if (dest.scheme,dest.netloc,dest.path)!=(self.endpoint.scheme,self.endpoint.netloc,self.endpoint.path):
            return self.original(request,*args,**kwargs)
        method=self.method(request)
        if not isinstance(method,str):
            raise RuntimeError('ORACLE187_NON_JSON_RPC_BLOCKED')
        low=method.lower()
        if low.startswith('send') or low in ('requestairdrop','simulatebundle','sendbundle'):
            raise RuntimeError('ORACLE187_BROADCAST_FORBIDDEN')

        for attempt in range(1,4):
            wait=max(0,self.next_allowed-time.monotonic())
            if wait:self.sleep(wait)
            self.attempts+=1
            try:
                return self.original(request,*args,**kwargs)
            except urllib.error.HTTPError as exc:
                if exc.code!=429:raise
                self.throttles+=1
                if self.throttles>5 or attempt==3:
                    print('[ORACLE187_RATE_LIMIT_HOLD] method=%s total_429=%d' %
                          (method,self.throttles),flush=True)
                    raise RuntimeError('ORACLE187_RPC_429_BUDGET_EXHAUSTED') from None
                hint=exc.headers.get('Retry-After') if exc.headers else None
                try:seconds=float(hint)
                except (TypeError,ValueError):seconds=2**attempt
                seconds=max(1.0,min(30.0,seconds+random.uniform(0,0.5)))
                self.next_allowed=time.monotonic()+seconds
                print('[ORACLE187_429_COOLDOWN] method=%s retry=%d delay_s=%.1f' %
                      (method,attempt,seconds),flush=True)

def run():
    if os.getenv('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ORACLE187_ARMED_REFUSED')
    url=os.getenv('SOLANA_RPC_URL','')
    if not url.startswith('https://'):
        raise RuntimeError('ORACLE187_RPC_URL_MISSING')
    orig=urllib.request.urlopen
    gate=RpcGate(orig,url)
    urllib.request.urlopen=gate
    try:
        q186.run(max_pairs=4)
    finally:
        urllib.request.urlopen=orig
        print('[ORACLE187_SUMMARY] rpc_attempts=%d throttles=%d broadcast=FALSE' %
              (gate.attempts,gate.throttles),flush=True)

def test():
    from urllib.request import Request
    from email.message import Message
    fake='https://test.invalid/rpc?api-key=NOT_PRINTED'
    counts=[]
    def responder(req,*args,**kw):
        counts.append(True)
        if len(counts)==1:
            raise urllib.error.HTTPError(fake,429,'rate limit',Message(),None)
        return {'ok':True}

    req=Request(fake,data=b'{"jsonrpc":"2.0","method":"getAccountInfo","params":[]}')
    gate=RpcGate(responder,fake,sleep=lambda x:None)
    assert gate(req)=={'ok':True} and gate.throttles==1
    assert gate.method(req)=='getAccountInfo'
    forbidden=Request(fake,data=b'{"method":"sendTransaction","params":[]}')
    try:gate(forbidden)
    except RuntimeError as exc:
        assert str(exc)=='ORACLE187_BROADCAST_FORBIDDEN'
    else:
        raise AssertionError('send escaped gate')
    assert len(counts)==2
    print('[TEST PASS] ORACLE187 preserves method case, bounded 429, send forbidden')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    test() if a.test else run() if a.run else p.error('use --test or --run')
