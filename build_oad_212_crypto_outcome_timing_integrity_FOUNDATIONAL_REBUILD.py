from __future__ import annotations
import ast,os,subprocess,sys,textwrap
from pathlib import Path
REVISION='OAD_212_CRYPTO_OUTCOME_TIMING_INTEGRITY_FOUNDATIONAL_REBUILD'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for x in (b,*b.parents):
            if (x/'qseries_v2').is_dir(): return x
    raise RuntimeError('Q Series repository root not found')
def write(path,src):
    src=textwrap.dedent(src).lstrip();ast.parse(src,filename=str(path));tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(src,encoding='utf-8',newline='\n');os.replace(tmp,path)
def run(r,t):
    z=subprocess.run([sys.executable,str(t)],cwd=str(r));
    if z.returncode: raise RuntimeError('Certification test failed: '+t.name)
M187=r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json
from urllib.request import Request,urlopen
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation,verify_outcome_observation
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
PRODUCTS={'BTC':'BTC-USD','ETH':'ETH-USD','SOL':'SOL-USD'}
SAMPLING_METHOD='coinbase_1m_candle_open_at_or_after_maturity';MAX_FINALIZATION_OFFSET_SECONDS=120
@dataclass(frozen=True,slots=True)
class CryptoExactHorizonOutcome:
    experience_id:str;asset:str;horizon_seconds:int;matures_at:str;candle_start:str;start_price:float;outcome_price:float;return_fraction:float;return_percent:float;source_ref:str;source_hash:str;outcome_observation:object;exact_interval:bool;sampling_method:str;realized_horizon_seconds:int;timing_offset_seconds:int;read_only:bool=True;probability_enabled:bool=False;direction_enabled:bool=False;execution_authority:bool=False
def _utc(v):
    if isinstance(v,datetime): return v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)
    x=datetime.fromisoformat(str(v).replace('Z','+00:00'));return x.astimezone(timezone.utc) if x.tzinfo else x.replace(tzinfo=timezone.utc)
def experience_start_spot_price(e):
    for row in tuple(e.condition_vector):
        if len(row)>=3 and str(row[0])=='coinbase' and str(row[1])=='spot_price': return float(row[2])
    raise RuntimeError('persisted experience has no Coinbase spot_price')
def select_first_candle_at_or_after(rows,matures_at):
    target=_utc(matures_at);c=[]
    for row in tuple(rows):
        if isinstance(row,(list,tuple)) and len(row)>=6:
            t=datetime.fromtimestamp(int(row[0]),tz=timezone.utc)
            if t>=target:c.append((t,row))
    if not c: raise RuntimeError('no Coinbase one-minute candle at/after maturity')
    return min(c,key=lambda x:x[0])[1]
def _coinbase_candles(product,start,end,timeout_seconds=20.0,opener=None):
    from urllib.parse import urlencode
    qs=urlencode({'granularity':60,'start':_utc(start).isoformat().replace('+00:00','Z'),'end':_utc(end).isoformat().replace('+00:00','Z')})
    req=Request(f'https://api.exchange.coinbase.com/products/{product}/candles?{qs}',headers={'User-Agent':'QSeries-Oracle/1.0','Accept':'application/json'})
    with (opener or urlopen)(req,timeout=float(timeout_seconds)) as resp:data=json.loads(resp.read().decode('utf-8'))
    if not isinstance(data,list):raise RuntimeError('Coinbase candles response is not a list')
    return tuple(data)
def acquire_exact_coinbase_outcome(experience,horizon_seconds=60,timeout_seconds=20.0,opener=None):
    asset=str(experience.asset).upper();product=PRODUCTS.get(asset)
    if not product:raise RuntimeError('unsupported crypto asset for Coinbase outcome: '+asset)
    snap=_utc(experience.snapshot_at);requested=int(horizon_seconds)
    if requested<1:raise ValueError('horizon_seconds must be positive')
    maturity=snap+timedelta(seconds=requested)
    candle=select_first_candle_at_or_after(_coinbase_candles(product,maturity-timedelta(minutes=2),maturity+timedelta(minutes=4),timeout_seconds,opener),maturity)
    sample=datetime.fromtimestamp(int(candle[0]),tz=timezone.utc);offset=int((sample-maturity).total_seconds())
    if offset<0:raise RuntimeError('Coinbase sample precedes maturity')
    if offset>MAX_FINALIZATION_OFFSET_SECONDS:raise RuntimeError(f'Coinbase maturity sample outside certified timing window: offset_seconds={offset}')
    # Coinbase candle: [time,low,high,open,close,volume]. OPEN is price at candle_start.
    end=float(candle[3]);start=experience_start_spot_price(experience)
    if start<=0:raise RuntimeError('experience start price must be positive')
    ret=(end-start)/start;realized=int((sample-snap).total_seconds());exact=offset==0
    typ=f'coinbase_spot_return_{requested}s_'+('exact_interval' if exact else 'bounded_finalization')
    ref=f'coinbase:{product}:candle_open:{int(candle[0])}'
    body={'product':product,'candle_start':sample.isoformat(),'open':end,'sampling_method':SAMPLING_METHOD,'requested_horizon_seconds':requested,'realized_horizon_seconds':realized,'timing_offset_seconds':offset}
    h=sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest();oo=build_outcome_observation(asset,typ,ret,sample.isoformat(),ref,h)
    if not verify_outcome_observation(oo):raise RuntimeError('OCL-003 outcome verification failed')
    return CryptoExactHorizonOutcome(str(experience.experience_id),asset,requested,maturity.isoformat(),sample.isoformat(),start,end,ret,ret*100,ref,h,oo,exact,SAMPLING_METHOD,realized,offset,True,False,False,False)
"""
M188=r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
PRODUCER='oracle.crypto_verified_learning';PRIORITY=20;SOURCE_PREFIX='source.crypto.learned_case.'
@dataclass(frozen=True,slots=True)
class LearnedCasePersistence: cases:int;already_present:int;committed_new:int;exact_readback:int;observation_ids:tuple;execution_authority:bool=False
def canonicalize_verified_learned_case(e,o,acquisition_batch_id='oad188.crypto-learned-case'):
    event=assemble_learning_event(e.asset,e.evidence_hash,e.lineage_hash,o.outcome_observation)
    if not verify_learning_event(event):raise RuntimeError('invalid OCL LearningEvent')
    method=str(getattr(o,'sampling_method',''));realized=int(getattr(o,'realized_horizon_seconds',o.horizon_seconds));offset=int(getattr(o,'timing_offset_seconds',realized-int(o.horizon_seconds)));exact=bool(getattr(o,'exact_interval',False))
    if not method:raise RuntimeError('verified learned case requires certified timing sampling method')
    if offset<0 or (exact and offset!=0):raise RuntimeError('invalid learned-case timing lineage')
    payload={'experience_id':e.experience_id,'asset':e.asset,'snapshot_at':e.snapshot_at,'condition_vector':e.condition_vector,'temporal_vector':e.temporal_vector,'evidence_hash':e.evidence_hash,'condition_hash':e.condition_hash,'experience_hash':e.experience_hash,'lineage_hash':e.lineage_hash,'horizon_seconds':int(o.horizon_seconds),'requested_horizon_seconds':int(o.horizon_seconds),'realized_horizon_seconds':realized,'timing_offset_seconds':offset,'sampling_method':method,'timing_schema_version':'OAD-212','timing_certified':True,'matures_at':o.matures_at,'outcome_observed_at':o.candle_start,'start_price':o.start_price,'outcome_price':o.outcome_price,'return_fraction':o.return_fraction,'return_percent':o.return_percent,'outcome_hash':o.outcome_observation.outcome_hash,'learning_event_id':event.event_id,'learning_event_hash':event.event_hash,'outcome_type':event.outcome_type,'exact_interval':exact,'probability':None,'direction':None}
    raw=RawSourceObservation.create(source_observation_id=f'{e.experience_id}:{event.event_hash}',observed_at=datetime.fromisoformat(str(o.candle_start).replace('Z','+00:00')),observation_type='crypto_verified_learned_case',payload=payload,provenance={'producer':PRODUCER,'source_ref':o.source_ref,'source_hash':o.source_hash,'read_only':True,'timing_certified':True})
    return CanonicalObservation.create(source_id=f'{SOURCE_PREFIX}{str(e.asset).lower()}',raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)
def persist_verified_learned_cases(pairs,root=None,timeout_seconds=120.0):
    root=Path(root or Path.cwd()).resolve();canonical=tuple(canonicalize_verified_learned_case(e,o) for e,o in tuple(pairs));backend=_backend(root);missing=[];existing=0
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None:missing.append(x)
        else:existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root);ev=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)));accepted=tuple(x for x in ev if getattr(x,'accepted',False) is True)
        if len(accepted)!=len(missing):raise RuntimeError('learned-case single-writer commit mismatch')
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical);rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()
    if len(rows)!=len(ids):raise RuntimeError('learned-case exact readback mismatch')
    return LearnedCasePersistence(len(ids),existing,committed,len(rows),ids,False)
"""
TEST=r"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_187_crypto_exact_horizon_coinbase_outcome as a
from qseries_v2.oracle_adapters.independent import oad_188_crypto_verified_learned_case_postgresql_persistence as b
class T(unittest.TestCase):
 def e(self):return SimpleNamespace(experience_id='e1',asset='BTC',snapshot_at='2026-08-31T10:00:00+00:00',condition_vector=(('coinbase','spot_price',100.0,'OBSERVED'),),temporal_vector=(),evidence_hash='a'*64,condition_hash='b'*64,experience_hash='c'*64,lineage_hash='d'*64)
 def test_open_and_truth(self):
  with patch.object(a,'_coinbase_candles',return_value=((1788170460,90,110,101,109,1),)):
   x=a.acquire_exact_coinbase_outcome(self.e(),60)
  print('[PRICE]',x.outcome_price,'[OFFSET]',x.timing_offset_seconds);self.assertEqual(x.outcome_price,101.0);self.assertTrue(x.exact_interval)
 def test_late_not_exact(self):
  with patch.object(a,'_coinbase_candles',return_value=((1788170520,90,110,102,109,1),)):
   x=a.acquire_exact_coinbase_outcome(self.e(),60)
  c=b.canonicalize_verified_learned_case(self.e(),x);p=dict(c.payload);print('[REALIZED]',p['realized_horizon_seconds'],'[EXACT]',p['exact_interval']);self.assertFalse(p['exact_interval']);self.assertEqual(p['timing_offset_seconds'],60);self.assertIsNone(p['probability']);self.assertFalse(c.execution_allowed)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-212 truthful timing integrity certified')
"""
def main():
 r=root();pkg=r/'qseries_v2'/'oracle_adapters'/'independent';targets=[pkg/'oad_187_crypto_exact_horizon_coinbase_outcome.py',pkg/'oad_188_crypto_verified_learned_case_postgresql_persistence.py',r/'test_oad_212_crypto_outcome_timing_integrity.py'];deps=[pkg/'oad_182_crypto_persisted_experience_exact_readback.py',r/'qseries_v2/oracle_continuous_learner/ocl_003_outcome_observation.py',r/'qseries_v2/oracle_continuous_learner/ocl_004_learning_event.py']
 print('='*112);print(' OAD-212 CRYPTO OUTCOME TIMING INTEGRITY FOUNDATIONAL REBUILD');print('='*112);print('[BOOT]',REVISION);print('[ROOT]',r)
 for d in deps:
  if not d.is_file():raise RuntimeError('Required dependency missing: '+str(d))
  print('[PASS] dependency verified:',d.relative_to(r))
 old={x:(x.read_bytes() if x.exists() else None) for x in targets}
 try:
  write(targets[0],M187);write(targets[1],M188);write(targets[2],TEST);run(r,targets[2]);print('[PASS] OAD-187/OAD-188 foundational timing path repaired');print('[PASS] probability=FALSE direction=FALSE execution=FALSE');print('[DONE] OAD-212 INSTALLATION COMPLETE')
 except Exception:
  for x,v in old.items():
   if v is None:
    if x.exists():x.unlink()
   else:x.write_bytes(v)
  print('[ROLLBACK] OAD-212 rolled back');raise
if __name__=='__main__':main()
