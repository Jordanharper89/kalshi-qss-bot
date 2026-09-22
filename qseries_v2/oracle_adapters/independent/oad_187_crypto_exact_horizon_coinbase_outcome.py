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
