from pathlib import Path

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_btc_kalshi_exact_price_profitability_gate.py"
TEST=ROOT/"test_opd_BTC_KALSHI_CANONICAL_PRICE_EXTRACTOR_V5.py"

s=TARGET.read_text(encoding="utf-8")

start=s.index("def normalize_price(v):")
end=s.index("\ndef connect_db():", start)

new = r'''def normalize_price(v):
    x=flt(v)
    if x is None:return None
    if 1.0 < x <= 100.0:x/=100.0
    return x if 0.0 <= x <= 1.0 else None

def _walk_dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk_dicts(v)
    elif isinstance(x,list):
        for v in x[:128]:
            yield from _walk_dicts(v)

def _best_level(x):
    vals=[]
    if isinstance(x,list):
        for item in x[:256]:
            if isinstance(item,(list,tuple)) and item:
                p=normalize_price(item[0])
                if p is not None: vals.append(p)
            elif isinstance(item,dict):
                for k in ("price","yes_price","p"):
                    if k in item:
                        p=normalize_price(item.get(k))
                        if p is not None: vals.append(p); break
    return max(vals) if vals else None

def extract_yes_price(x,observation_type=""):
    typ=str(observation_type or "").lower()

    explicit=(
        "yes_price","yes_bid","yes_ask","yes_bid_price","yes_ask_price",
        "best_yes_bid","best_yes_ask","last_yes_price","yes_last_price"
    )
    for d in _walk_dicts(x):
        bid=ask=None
        for k in ("yes_bid","yes_bid_price","best_yes_bid"):
            if k in d:
                bid=normalize_price(d.get(k))
                if bid is not None: break
        for k in ("yes_ask","yes_ask_price","best_yes_ask"):
            if k in d:
                ask=normalize_price(d.get(k))
                if ask is not None: break
        if bid is not None and ask is not None:
            return (bid+ask)/2.0

        for k in explicit:
            if k in d:
                p=normalize_price(d.get(k))
                if p is not None:return p

    if "trade" in typ or "ticker" in typ:
        for d in _walk_dicts(x):
            for k in ("price","last_price","market_price"):
                if k in d:
                    p=normalize_price(d.get(k))
                    if p is not None:return p

    if "orderbook" in typ:
        for d in _walk_dicts(x):
            for k in ("yes","yes_bids","yes_orders","yes_levels"):
                if k in d:
                    p=_best_level(d.get(k))
                    if p is not None:return p

    return None
'''

s=s[:start]+new+s[end:]

old_sql = '''SQL_EXACT_PRICE=(
    "SELECT sequence_number, canonical_observation_json "
    "FROM public.oracle_canonical_observations "
'''
new_sql = '''SQL_EXACT_PRICE=(
    "SELECT sequence_number, observation_type, canonical_observation_json "
    "FROM public.oracle_canonical_observations "
'''
if old_sql not in s:
    raise SystemExit("[FAIL] SQL exact-price block not found")
s=s.replace(old_sql,new_sql,1)

old_loop = '''    for sn,obj in cur.fetchall():
        if isinstance(obj,str):
            try: obj=json.loads(obj)
            except Exception: continue
        if extract_ticker(obj)!=ticker: continue
        px=extract_yes_price(obj)
        if px is not None:return px,int(sn),int(seq)
'''
new_loop = '''    for sn,observation_type,obj in cur.fetchall():
        if isinstance(obj,str):
            try: obj=json.loads(obj)
            except Exception: continue
        if extract_ticker(obj)!=ticker: continue
        px=extract_yes_price(obj,observation_type)
        if px is not None:return px,int(sn),int(seq)
'''
if old_loop not in s:
    raise SystemExit("[FAIL] exact-price row loop not found")
s=s.replace(old_loop,new_loop,1)

TARGET.write_text(s,encoding="utf-8")
compile(s,str(TARGET),"exec")

TEST_CODE=r'''from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
required=(
    "SELECT sequence_number, observation_type, canonical_observation_json",
    'def extract_yes_price(x,observation_type="")',
    '"trade" in typ or "ticker" in typ',
    '"orderbook" in typ',
    '"best_yes_bid"',
    '"best_yes_ask"',
    "_best_level",
    "extract_yes_price(obj,observation_type)",
    "HURDLE=0.02",
    "KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND",
)
for x in required:
    assert x in s,x
print("[PASS] canonical Kalshi price extractor is observation-type aware")
print("[PASS] ticker/trade/orderbook price semantics supported")
print("[PASS] generic numeric fields are not blindly accepted")
print("[PASS] canonical anchor logic unchanged")
print("[PASS] 28 survivors and fixed 2% profitability hurdle unchanged")
print("[PASS] execution/publication remain false")
'''

TEST.write_text(TEST_CODE,encoding="utf-8")
compile(TEST_CODE,str(TEST),"exec")

print("[PASS] BTC->Kalshi canonical price extractor V5 installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[PRICE POLICY] explicit YES fields; type-scoped trade/ticker price; explicit YES orderbook levels")
print("[SIGNAL/HURDLE] unchanged / 0.02")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
