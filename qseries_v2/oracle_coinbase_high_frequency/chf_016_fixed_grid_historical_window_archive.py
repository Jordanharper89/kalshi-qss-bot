import json,math
from datetime import datetime,timezone
from pathlib import Path
WINDOWS=(5,15,30,60); PRODUCTS=('BTC-USD','ETH-USD','SOL-USD')
GRID_SECONDS=5; BOUNDARY_STALENESS_S=5.0

def _ts(x):
    s=x.get('event_time') or x.get('observed_at') or x.get('received_at')
    if not s:return None
    try:return datetime.fromisoformat(str(s).replace('Z','+00:00')).timestamp()
    except:return None

def _product(x):
    return x.get('product_id') or (x.get('payload') or {}).get('product_id')

def _price(x):
    p=x.get('price') or (x.get('payload') or {}).get('price')
    try:return float(p)
    except:return None

def _load(path):
    out=[]
    if not path.exists():return out
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            x=json.loads(line); t=_ts(x); p=_product(x)
            if t is not None and p in PRODUCTS: out.append((t,x))
        except:pass
    return sorted(out,key=lambda z:z[0])

def archive(root=None):
    root=Path(root or Path.cwd()).resolve(); d=root/'runtime'/'coinbase_hf'; d.mkdir(parents=True,exist_ok=True)
    src=d/'canonical_events.jsonl'; dst=d/'historical_condition_windows.jsonl'; state=d/'historical_window_state.json'
    events=_load(src)
    if not events:return {'written':0,'total':0,'reason':'NO_CANONICAL_EVENTS'}
    last={}
    if state.exists():
        try:last=json.loads(state.read_text(encoding='utf-8')).get('last_anchor',{})
        except:last={}
    by={p:[] for p in PRODUCTS}
    for t,x in events:by[_product(x)].append((t,x))
    rows=[]
    for product,ev in by.items():
        if not ev:continue
        first,last_t=ev[0][0],ev[-1][0]
        start=max(first+60,float(last.get(product,0))+GRID_SECONDS)
        anchor=math.ceil(start/GRID_SECONDS)*GRID_SECONDS
        while anchor<=last_t:
            for h in WINDOWS:
                cutoff=anchor-h; prior=[z for z in ev if z[0]<=cutoff]
                if not prior:continue
                bt,bx=prior[-1]
                if cutoff-bt>BOUNDARY_STALENESS_S:continue
                inside=[z for z in ev if cutoff<z[0]<=anchor]
                seq=[(bt,bx)]+inside
                prices=[(_t,_price(_x)) for _t,_x in seq if _price(_x) is not None]
                if len(prices)<2:continue
                p0=prices[0][1]; p1=prices[-1][1]
                gaps=[seq[i][0]-seq[i-1][0] for i in range(1,len(seq))]
                rows.append({'schema_version':'CHF-016','product_id':product,'anchor_epoch':anchor,'anchor_time':datetime.fromtimestamp(anchor,timezone.utc).isoformat(),'window_seconds':h,'boundary_age_seconds':round(cutoff-bt,6),'event_count':len(seq),'max_event_gap_seconds':round(max(gaps) if gaps else 0,6),'open_price':p0,'close_price':p1,'return':None if not p0 else (p1/p0)-1,'full_horizon_complete':True,'past_only':True,'upstream_class':'RAW_EXTERNAL','derived_class':'ORACLE_DERIVED','probability_enabled':False,'direction_enabled':False,'publication_allowed':False,'execution_authority':False})
            last[product]=anchor; anchor+=GRID_SECONDS
    if rows:
        with dst.open('a',encoding='utf-8') as f:
            for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
    state.write_text(json.dumps({'last_anchor':last},sort_keys=True),encoding='utf-8')
    total=sum(1 for _ in dst.open(encoding='utf-8')) if dst.exists() else 0
    return {'written':len(rows),'total':total,'archive':str(dst),'state':str(state)}
