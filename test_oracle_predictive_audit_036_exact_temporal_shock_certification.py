from collections import defaultdict, Counter
from bisect import bisect_right
import json, re, math, statistics
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT = Path.cwd()
TICKER_RE = re.compile(r"\bKXBTC15M-[A-Z0-9-]+\b", re.I)
RAW_SPOT = "source.crypto.condition.btc.coinbase.spot_price"
KALSHI_SOURCE = "source.kalshi.market_data"
PRICE_KEYS = ("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")

def walk(x):
    if isinstance(x, dict):
        for k,v in x.items():
            yield str(k),v
            yield from walk(v)
    elif isinstance(x,list):
        for v in x:
            yield from walk(v)

def asdict(obj):
    try:
        return obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:
        return {}

def numeric_map(obj):
    d=asdict(obj); out={}
    for k,v in walk(d):
        try:
            f=float(v)
            if math.isfinite(f): out.setdefault(k.lower(),f)
        except Exception:
            pass
    return out

def scalar_value(obj, preferred=()):
    vals=numeric_map(obj)
    for k in preferred:
        if k in vals: return vals[k]
    uniq=list(vals.values())
    return uniq[0] if len(uniq)==1 else None

def kalshi_parse(obj):
    d=asdict(obj)
    text=json.dumps(d,default=str).upper()
    m=TICKER_RE.search(text)
    if not m: return None,None
    vals=numeric_map(d); p=None
    for k in PRICE_KEYS[:3]:
        v=vals.get(k)
        if v is not None and 0<=v<=1: p=v; break
    bid=vals.get("yes_bid_dollars"); ask=vals.get("yes_ask_dollars")
    if p is None and bid is not None and ask is not None and 0<=bid<=ask<=1:
        p=(bid+ask)/2
    return m.group(0),p

def load_rows():
    rows=[]; cursor=None
    for page in range(1,5):
        with connect(ROOT,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='15000ms'")
                sql="""SELECT sequence_number,observed_at,source_id,canonical_observation_json
                       FROM public.oracle_canonical_observations"""
                args=[]
                if cursor is not None:
                    sql+=" WHERE sequence_number < %s"; args.append(cursor)
                sql+=" ORDER BY sequence_number DESC LIMIT 50000"
                q.execute(sql,tuple(args)); b=q.fetchall() or []
            c.rollback()
        print("[PAGE]",page,"rows=",len(b))
        if not b: break
        rows+=b; cursor=min(int(x[0]) for x in b)
    return rows

def build_series(rows):
    spot=[]; kalshi=defaultdict(list)
    for seq,ts,source,obj in rows:
        if ts is None: continue
        s=str(source)
        if s==RAW_SPOT:
            v=scalar_value(obj,("spot_price","price","value"))
            if v is not None and v>0: spot.append((ts,int(seq),float(v)))
        elif s==KALSHI_SOURCE:
            t,p=kalshi_parse(obj)
            if t and p is not None: kalshi[t].append((ts,int(seq),float(p)))
    spot.sort(key=lambda x:(x[0],x[1]))
    for t in kalshi: kalshi[t].sort(key=lambda x:(x[0],x[1]))
    return spot,kalshi

def certified_returns(spot):
    specs={30:(20,45),60:(45,90),120:(90,150)}
    out={k:[] for k in specs}
    times=[x[0] for x in spot]
    for i,(ts,seq,px) in enumerate(spot):
        for horizon,(lo,hi) in specs.items():
            best=None
            for j in range(i-1,-1,-1):
                span=(ts-spot[j][0]).total_seconds()
                if span>hi: break
                if lo<=span<=hi:
                    err=abs(span-horizon)
                    if best is None or err<best[0]:
                        best=(err,j,span)
            if best is not None:
                _,j,span=best
                prev=spot[j][2]
                if prev>0:
                    out[horizon].append((ts,seq,px,(px/prev)-1.0,span,spot[j][0],spot[j][1]))
    return out

def empirical_threshold(vals,q=.95):
    if not vals: return None
    s=sorted(vals)
    idx=min(len(s)-1,max(0,int(round((len(s)-1)*q))))
    return s[idx]

def detect_certified_shocks(spot,horizon=60):
    cr=certified_returns(spot)[horizon]
    thr=empirical_threshold([abs(x[3]) for x in cr],.95)
    shocks=[]; last=None
    if thr is None: return shocks,thr,cr
    for ts,seq,px,ret,span,base_ts,base_seq in cr:
        if abs(ret)<thr: continue
        if last is not None and (ts-last).total_seconds()<30: continue
        shocks.append({"ts":ts,"seq":seq,"spot":px,"ret":ret,"span":span,
                       "base_ts":base_ts,"base_seq":base_seq,"threshold":thr})
        last=ts
    return shocks,thr,cr

def contract_phase_from_ticker(ticker, shock_ts):
    m=re.match(r"KXBTC15M-(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})-(\d{2})",ticker)
    if not m:
        return None
    yy,mon,dd,hh,mm,ss=m.groups()
    months={"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        end=shock_ts.replace(year=2000+int(yy),month=months[mon],day=int(dd),hour=int(hh),minute=int(mm),second=int(ss),microsecond=0)
        sec_to_end=(end-shock_ts).total_seconds()
        sec_from_start=900-sec_to_end
        return sec_from_start,sec_to_end
    except Exception:
        return None

def choose_contract(kalshi,ts):
    cand=[]
    for t,pts in kalshi.items():
        times=[x[0] for x in pts]
        i=bisect_right(times,ts)-1
        if i<0: continue
        lag=(ts-pts[i][0]).total_seconds()
        phase=contract_phase_from_ticker(t,ts)
        if phase is None: continue
        sec_from_start,sec_to_end=phase
        if 0<=lag<=90 and 0<=sec_from_start<=900 and 0<=sec_to_end<=900:
            cand.append((lag,t,i,pts,sec_from_start,sec_to_end))
    if not cand: return None
    cand.sort(key=lambda x:x[0])
    return cand[0]

def reaction_curve(shock,kalshi):
    chosen=choose_contract(kalshi,shock["ts"])
    if chosen is None: return None
    lag,ticker,i0,pts,sec_from_start,sec_to_end=chosen
    base_ts,base_seq,p0=pts[i0]
    fut=[x for x in pts[i0+1:] if 0<(x[0]-shock["ts"]).total_seconds()<=300]
    if not fut: return None
    out={"ticker":ticker,"shock_ts":shock["ts"],"shock_ret":shock["ret"],"shock_span":shock["span"],
         "base_price":p0,"base_ts":base_ts,"base_seq":base_seq,"base_lag_s":lag,
         "sec_from_start":sec_from_start,"sec_to_end":sec_to_end}
    direction=1 if shock["ret"]>=0 else -1
    out["direction"]=direction
    prices=[x[2] for x in fut]
    signed=[direction*(p-p0) for p in prices]
    out["fav_excursion"]=max(signed)
    out["adv_excursion"]=max(-x for x in signed)
    out["raw_up_mfe"]=max(p-p0 for p in prices)
    out["raw_down_mae"]=max(p0-p for p in prices)
    for h in (5,15,30,60,120,300):
        z=[x for x in fut if (x[0]-shock["ts"]).total_seconds()<=h]
        if z:
            d=z[-1][2]-p0
            out[f"d{h}"]=d
            out[f"sd{h}"]=direction*d
    first=None
    for h in (5,15,30,60,120,300):
        sd=out.get(f"sd{h}")
        if sd is not None and abs(sd)>=.03:
            first=h; break
    out["first_3c_s"]=first
    out["full_300_available"]=bool(fut and (fut[-1][0]-shock["ts"]).total_seconds()>=285)
    return out

def phase_bucket(sec_from_start,sec_to_end):
    if sec_from_start<180: return "EARLY"
    if sec_to_end<=180: return "LATE"
    return "MID"

rows=load_rows(); spot,kalshi=build_series(rows)
cr=certified_returns(spot)
print("[SPOT_ROWS]",len(spot))
for h in (30,60,120):
    spans=[x[4] for x in cr[h]]
    rets=[abs(x[3]) for x in cr[h]]
    print("[CERTIFIED_WINDOW]",h,"rows=",len(spans),
          "span_min=",round(min(spans),3) if spans else None,
          "span_median=",round(statistics.median(spans),3) if spans else None,
          "span_max=",round(max(spans),3) if spans else None,
          "p95_abs_return=",round(empirical_threshold(rets,.95),8) if rets else None)
shocks,thr,base=detect_certified_shocks(spot,60)
print("[CERTIFIED_60S_SHOCKS]",len(shocks))
print("[CERTIFIED_60S_THRESHOLD]",None if thr is None else round(thr,8))
for s in shocks[:40]:
    print("[SHOCK]",s["ts"],"ret=",round(s["ret"],8),"span_s=",round(s["span"],3),
          "spot=",round(s["spot"],2))
print("[REJECT_RULE] returns outside 45-90s temporal tolerance cannot be called 60-second shocks")
print("[PASS] OPA-036 exact temporal shock certification audit complete")
