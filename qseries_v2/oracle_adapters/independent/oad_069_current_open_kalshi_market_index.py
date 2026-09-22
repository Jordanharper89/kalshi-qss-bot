import re
from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
STOP={"the","and","for","with","will","what","when","from","this","that","yes","no","market"}
def _terms(m):
    text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title"))
    return tuple(sorted({w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9.-]{2,}",text) if w.lower() not in STOP}))
def fetch_current_open_kalshi_market_index(root=None,limit=1000,timeout_seconds=20):
    limit=max(1,min(int(limit),1000))
    cred=load_kalshi_credentials(root=Path(root or Path.cwd()).resolve())
    r=kalshi_rest_get(cred,"/markets",{"limit":limit,"status":"open"},timeout_seconds)
    if r.status_code!=200: raise RuntimeError("Kalshi current-market request failed")
    markets=tuple(r.body.get("markets",()))
    index={}
    for m in markets:
        ticker=str(m.get("ticker","")).strip()
        if ticker:index[ticker]=_terms(m)
    return markets,index
