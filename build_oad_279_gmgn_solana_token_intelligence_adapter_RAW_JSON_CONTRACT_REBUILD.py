from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED_FILENAME='build_oad_279_gmgn_solana_token_intelligence_adapter_RAW_JSON_CONTRACT_REBUILD.py'
MODULE_NAME='oad_279_gmgn_solana_token_intelligence_adapter.py'
TEST_NAME='test_oad_279_gmgn_solana_token_intelligence_adapter.py'
MODULE_SOURCE=r'''
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json, subprocess
from .oad_277_gmgn_production_admission_boundary import require_gmgn_admission
from .oad_278_gmgn_solana_trending_live_adapter import _decode_gmgn_bytes, acquire_gmgn_solana_trending
READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
@dataclass(frozen=True, slots=True)
class GMGNTokenIntelligenceObservation:
    source_id:str; provider:str; source_class:str; observation_type:str; token_address:str; observed_at:datetime; payload:dict; execution_authority:bool=False

def _parse_raw_json(stdout_bytes):
    text=_decode_gmgn_bytes(stdout_bytes).strip()
    if not text: raise RuntimeError('GMGN command returned empty stdout')
    try: return json.loads(text)
    except json.JSONDecodeError:
        s=text.find('{'); e=text.rfind('}')
        if s>=0 and e>s: return json.loads(text[s:e+1])
        raise RuntimeError('GMGN command output was not valid JSON')

def _run_raw(cli_path,args,timeout_seconds):
    p=subprocess.run([cli_path,*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=float(timeout_seconds),check=False)
    out=_decode_gmgn_bytes(p.stdout); err=_decode_gmgn_bytes(p.stderr)
    if p.returncode!=0: raise RuntimeError('GMGN command failed (returncode='+str(p.returncode)+'): '+(err or out).strip()[:1000])
    data=_parse_raw_json(p.stdout)
    if isinstance(data,dict) and 'code' in data and str(data.get('code')) not in ('0','200'):
        raise RuntimeError('GMGN API returned non-success envelope: code='+repr(data.get('code'))+' message='+repr(data.get('message'))+' error='+repr(data.get('error')))
    return data

def _token_resource(data):
    if isinstance(data,dict) and 'code' in data and 'data' in data: return data.get('data')
    return data

def _validate_token_resource(section,token,data):
    r=_token_resource(data)
    if r is None or not isinstance(r,(dict,list)): raise RuntimeError('GMGN '+section+' returned unsupported resource')
    if isinstance(r,dict):
        returned=str(r.get('address') or r.get('token_address') or r.get('token') or '').strip()
        if returned and returned!=token: raise RuntimeError('GMGN '+section+' token identity mismatch: '+returned+' != '+token)
    return data

def acquire_gmgn_solana_token_intelligence(token_address,timeout_seconds=30.0):
    token=str(token_address).strip()
    if not token: raise ValueError('token_address required')
    a=require_gmgn_admission()
    info=_validate_token_resource('info',token,_run_raw(a.cli_path,['token','info','--chain','sol','--address',token,'--raw'],timeout_seconds))
    security=_validate_token_resource('security',token,_run_raw(a.cli_path,['token','security','--chain','sol','--address',token,'--raw'],timeout_seconds))
    pool=_validate_token_resource('pool',token,_run_raw(a.cli_path,['token','pool','--chain','sol','--address',token,'--raw'],timeout_seconds))
    return GMGNTokenIntelligenceObservation('source.gmgn.solana.token.'+token,'gmgn','token_intelligence','gmgn_solana_token_intelligence',token,datetime.now(timezone.utc),{'chain':'sol','info':info,'security':security,'pool':pool},False)

def acquire_current_gmgn_solana_token_intelligence(timeout_seconds=30.0,candidate_limit=5):
    trending=acquire_gmgn_solana_trending(interval='1h',limit=max(1,int(candidate_limit)),timeout_seconds=timeout_seconds)
    rank=(((trending.payload.get('raw') or {}).get('data') or {}).get('rank') or [])
    if not rank: raise RuntimeError('GMGN trending returned no token candidates')
    errors=[]
    for row in rank:
        token=str(row.get('address') or '').strip()
        if not token: continue
        try: return acquire_gmgn_solana_token_intelligence(token,timeout_seconds=timeout_seconds)
        except Exception as exc: errors.append(token+': '+str(exc))
    raise RuntimeError('No current GMGN trending token completed info/security/pool acquisition. Candidate failures: '+' | '.join(errors[:5]))
'''
TEST_SOURCE=r'''
import unittest
from qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter import *
class T(unittest.TestCase):
    def test_direct_resource_shape(self):
        d={'address':'TEST','symbol':'T'}; self.assertIs(_token_resource(d),d)
    def test_envelope_shape(self):
        d={'code':0,'message':'success','data':{'address':'TEST'}}; self.assertEqual(_token_resource(d)['address'],'TEST')
    def test_physical_current_token_intelligence(self):
        r=acquire_current_gmgn_solana_token_intelligence(timeout_seconds=30.0,candidate_limit=5)
        print('[PHYSICAL] token=',r.token_address); print('[PHYSICAL] provider=',r.provider)
        for section in ('info','security','pool'):
            d=r.payload[section]; rr=_token_resource(d); print('[PHYSICAL]',section,'raw_type=',type(d).__name__,'resource_type=',type(rr).__name__); self.assertIsInstance(rr,(dict,list))
        self.assertEqual(r.provider,'gmgn'); self.assertEqual(r.payload['chain'],'sol'); self.assertFalse(r.execution_authority)
    def test_safety(self):
        self.assertFalse(PROBABILITY_ENABLED); self.assertFalse(DIRECTION_ENABLED); self.assertFalse(PUBLICATION_ALLOWED); self.assertFalse(EXECUTION_AUTHORITY)
if __name__=='__main__':
    print('='*120); print(' OAD-279 PHYSICAL CERTIFICATION TEST'); print(' GMGN SOLANA TOKEN INTELLIGENCE — RAW JSON CONTRACT'); print('='*120)
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print('[PASS] GMGN direct-resource raw JSON contract certified'); print('[PASS] GMGN envelope raw JSON contract certified'); print('[PASS] live token info/security/pool intelligence certified'); print('[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE'); print('[DONE] OAD-279 PHYSICALLY CERTIFIED')
'''
def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/'qseries_v2').is_dir(): return p
    raise RuntimeError('Q Series repository root not found')
def write_checked(path,source):
    s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True); t=path.with_suffix(path.suffix+'.tmp'); t.write_text(s,encoding='utf-8',newline='\n'); os.replace(t,path)
def main():
    if Path(__file__).name!=EXPECTED_FILENAME: raise RuntimeError('installer identity mismatch')
    root=locate_root(); pkg=root/'qseries_v2'/'oracle_adapters'/'independent'; module=pkg/MODULE_NAME; test=root/TEST_NAME; init=pkg/'__init__.py'
    print('='*120); print(' OAD-279 GMGN SOLANA TOKEN INTELLIGENCE — RAW JSON CONTRACT REBUILD'); print('='*120); print('[ROOT]',root)
    for rel,sym in ((pkg/'oad_277_gmgn_production_admission_boundary.py','require_gmgn_admission'),(pkg/'oad_278_gmgn_solana_trending_live_adapter.py','acquire_gmgn_solana_trending')):
        if not rel.is_file() or ('def '+sym+'(') not in rel.read_text(encoding='utf-8'): raise RuntimeError('dependency missing: '+str(rel)+' -> '+sym)
        print('[PASS] exact dependency verified:',rel.relative_to(root))
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE); write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding='utf-8').splitlines() if init.exists() else []; exp='from .'+module.stem+' import *'
        if exp not in lines: lines.append(exp)
        write_checked(init,'\n'.join(x for x in lines if x.strip())+'\n')
        print('[PASS] rebuilt existing OAD-279 production boundary in place'); print('[PASS] incorrect universal code==0 assumption retired'); print('[PASS] successful direct-resource --raw JSON accepted'); print('[PASS] envelope responses still validated when present'); print('[PASS] bounded fallback across current GMGN trending candidates'); print('[PASS] GMGN remains observation-only'); print('[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE'); print('[DONE] OAD-279 RAW JSON CONTRACT REBUILD INSTALLATION COMPLETE')
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print('[ROLLBACK] OAD-279 affected files restored'); raise
if __name__=='__main__': main()
