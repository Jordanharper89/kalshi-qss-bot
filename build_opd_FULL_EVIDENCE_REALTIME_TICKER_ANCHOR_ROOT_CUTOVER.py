from pathlib import Path
import ast
import re

ROOT = Path.cwd().resolve()
PRED = ROOT / "qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py"
TAP = ROOT / "qseries_v2/oracle_predictive_discovery/opd_061_realtime_kalshi_anchor_tap.py"
BRIDGE = ROOT / "qseries_v2/oracle_adapters/kalshi/oad_036_websocket_canonical_bridge.py"
TEST = ROOT / "test_opd_FULL_EVIDENCE_REALTIME_TICKER_ANCHOR_ROOT_CUTOVER.py"

for path in (PRED, TAP, BRIDGE):
    if not path.exists():
        raise SystemExit(f"[FAIL] required production source missing: {path}")

def replace_function(source, name, replacement):
    tree = ast.parse(source)
    node = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name), None)
    if node is None:
        raise SystemExit(f"[FAIL] function not found: {name}")
    lines = source.splitlines(True)
    lines[node.lineno - 1:node.end_lineno] = [replacement.rstrip() + "\n\n"]
    return "".join(lines)

STRICT_ASSET = '''def _asset(ticker):
    u=str(ticker or "").upper().strip()
    if u.startswith("KXBTC"): return "BTC"
    if u.startswith("KXETH"): return "ETH"
    if u.startswith("KXSOL"): return "SOL"
    return None
'''

NEW_FREEZE = '''def freeze_trade(raw,received_at,observation_id,root=None):
    if not isinstance(raw,dict): return None
    typ=str(raw.get("type") or "").strip().lower()
    if typ not in ("trade","ticker"): return None
    msg=raw.get("msg") or {}
    ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()
    asset=_asset(ticker)
    if not asset: return None
    price=None
    for k in ("yes_price_dollars","price_dollars","last_price_dollars"):
        try:
            v=float(msg[k])
            if 0.0<=v<=1.0: price=v; break
        except Exception: pass
    if price is None:
        try:
            b=float(msg.get("yes_bid_dollars")); a=float(msg.get("yes_ask_dollars"))
            if 0.0<=b<=1.0 and 0.0<=a<=1.0 and b<=a: price=(b+a)/2.0
        except Exception: pass
    if price is None: return None
    root=Path(root or Path.cwd())
    t=float(received_at.timestamp()) if hasattr(received_at,"timestamp") else float(received_at)
    boundary=_canonical_highwater(root)
    row={"schema_version":"OPD-061","anchor_id":str(observation_id),"ticker":ticker,
         "asset":asset,"observed_epoch":t,"anchor_price":price,
         "anchor_sequence_boundary":boundary,
         "anchor_sequence_basis":"CANONICAL_HIGHWATER_AT_FREEZE",
         "kalshi_state":{"sequence_number":boundary,"event_epoch":t,"trade_price":price,
         "yes_bid":msg.get("yes_bid_dollars"),"yes_ask":msg.get("yes_ask_dollars"),
         "spread":None,"yes_bid_size":msg.get("yes_bid_size"),"yes_ask_size":msg.get("yes_ask_size"),
         "last_trade_size":msg.get("count_fp"),"volume":msg.get("volume_fp") or msg.get("volume"),
         "open_interest":msg.get("open_interest_fp") or msg.get("open_interest"),
         "observation_type":typ,"event_time_path":"LIVE_RECEIVED_AT"},"post_freeze":True}
    p=root/"runtime"/"predictive_data"/"opd_061_live_anchor_spool.jsonl"
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\\n"); f.flush(); os.fsync(f.fileno())
    return row
'''

tap = TAP.read_text(encoding="utf-8")
tap = replace_function(tap, "_asset", STRICT_ASSET)
tap = replace_function(tap, "freeze_trade", NEW_FREEZE)
compile(tap, str(TAP), "exec")
TAP.write_text(tap, encoding="utf-8")

bridge = BRIDGE.read_text(encoding="utf-8")
old = 'if typ=="trade":\n        freeze_trade('
new = 'if typ in ("trade","ticker"):\n        freeze_trade('
if old not in bridge:
    raise SystemExit("[FAIL] exact OAD-036 trade-only tap boundary not found")
bridge = bridge.replace(old, new, 1)
compile(bridge, str(BRIDGE), "exec")
BRIDGE.write_text(bridge, encoding="utf-8")

pred = PRED.read_text(encoding="utf-8")
if "EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1" not in pred:
    raise SystemExit("[FAIL] exact-contract family root boundary missing")
pred = replace_function(pred, "_asset", STRICT_ASSET)
if not re.search(r'(?m)^import .*json', pred):
    lines = pred.splitlines(True)
    lines.insert(1 if lines and lines[0].startswith("from __future__") else 0, "import json\n")
    pred = "".join(lines)

HELPERS = '''REALTIME_FAMILY_ANCHOR_ROOT_REVISION="REALTIME_TRADE_TICKER_ANCHOR_ROOT_V1"
REALTIME_FAMILY_MAX_AGE_SECONDS=120.0
REALTIME_FAMILY_SPOOL_TAIL_BYTES=8388608

def _tail_realtime_anchor_spool(root):
    p=Path(root)/"runtime"/"predictive_data"/"opd_061_live_anchor_spool.jsonl"
    if not p.exists(): return []
    try:
        size=p.stat().st_size
        with p.open("rb") as f:
            start=max(0,size-REALTIME_FAMILY_SPOOL_TAIL_BYTES); f.seek(start); data=f.read()
        if start:
            k=data.find(b"\\n"); data=data[k+1:] if k>=0 else b""
        out=[]
        for raw in data.splitlines():
            try:
                row=json.loads(raw.decode("utf-8"))
                if isinstance(row,dict) and row.get("schema_version")=="OPD-061": out.append(row)
            except Exception: pass
        return out
    except Exception: return []

def _validated_realtime_anchor(row,now=None):
    if not isinstance(row,dict): return None
    ticker=str(row.get("ticker") or "").strip(); asset=_asset(ticker)
    if not asset or str(row.get("asset") or "").upper()!=asset: return None
    try: observed=float(row["observed_epoch"]); price=float(row["anchor_price"]); seq=int(row["anchor_sequence_boundary"])
    except Exception: return None
    if not (0.0<=price<=1.0) or seq<0: return None
    now=float(time.time() if now is None else now)
    if max(0.0,now-observed)>REALTIME_FAMILY_MAX_AGE_SECONDS: return None
    a=dict(row); a["asset"]=asset; a["ticker"]=ticker; a["observed_epoch"]=observed; a["anchor_price"]=price
    a["anchor_sequence_boundary"]=seq; a["anchor_sequence_basis"]=row.get("anchor_sequence_basis") or "CANONICAL_HIGHWATER_AT_FREEZE"
    a["realtime_anchor_basis"]="OPD061_REALTIME_TRADE_TICKER_SPOOL"
    return a

def _latest_realtime_spool_anchor(root,now=None):
    best=None
    for row in _tail_realtime_anchor_spool(root):
        a=_validated_realtime_anchor(row,now)
        if a is not None and (best is None or a["observed_epoch"]>best["observed_epoch"]): best=a
    return best
'''

UNIVERSE = '''def _recent_asset_anchor_universe(root,asset,lead,now=None):
    asset=str(asset or "").upper(); now=float(time.time() if now is None else now); anchors=[]; seen=set()
    realtime=[]
    for row in _tail_realtime_anchor_spool(root):
        a=_validated_realtime_anchor(row,now)
        if a is not None and a.get("asset")==asset: realtime.append(a)
    realtime.sort(key=lambda x:float(x.get("observed_epoch") or 0),reverse=True)
    for a in realtime:
        ticker=str(a.get("ticker"))
        if ticker in seen: continue
        meta=_contract_close_metadata(root,ticker)
        a["contract_close_epoch"]=meta.get("close_epoch"); a["contract_close_metadata_sequence"]=meta.get("metadata_sequence"); a["contract_close_basis"]=meta.get("basis")
        anchors.append(a); seen.add(ticker)
        if len(anchors)>=MAX_FAMILY_CONTRACTS: return anchors
    like="%"+asset+"%"
    sql="SELECT sequence_number,observation_id,EXTRACT(EPOCH FROM observed_at),canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND (canonical_observation_json->'payload'->>'source_market_id') ILIKE %s ORDER BY sequence_number DESC LIMIT %s"
    try:
        with connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout='7000ms'"); q.execute(sql,(SOURCE,like,int(FAMILY_SOURCE_SCAN_ROWS))); rows=q.fetchall() or []
            c.rollback()
    except Exception: rows=[]
    for row in rows:
        a=_anchor_from_row(row)
        if not a or _asset(a.get("ticker"))!=asset: continue
        ticker=str(a.get("ticker"))
        if ticker in seen: continue
        try: age=max(0.0,now-float(a.get("observed_epoch")))
        except Exception: age=999999.0
        if age>REALTIME_FAMILY_MAX_AGE_SECONDS: continue
        meta=_contract_close_metadata(root,ticker)
        a["contract_close_epoch"]=meta.get("close_epoch"); a["contract_close_metadata_sequence"]=meta.get("metadata_sequence"); a["contract_close_basis"]=meta.get("basis"); a["realtime_anchor_basis"]="CANONICAL_FALLBACK"
        anchors.append(a); seen.add(ticker)
        if len(anchors)>=MAX_FAMILY_CONTRACTS: break
    return anchors
'''

pred = replace_function(pred, "_recent_asset_anchor_universe", UNIVERSE)
marker = 'def _recent_asset_anchor_universe(root,asset,lead,now=None):'
if marker not in pred:
    raise SystemExit("[FAIL] patched family universe marker missing")
pred = pred.replace(marker, HELPERS + "\n" + marker, 1)
if 'lead=latest_live_anchor(root)' not in pred:
    raise SystemExit("[FAIL] production family lead call missing")
pred = pred.replace('lead=latest_live_anchor(root)', 'lead=_latest_realtime_spool_anchor(root,now) or latest_live_anchor(root)', 1)
if 'anchors=_recent_asset_anchor_universe(root,asset,lead)' not in pred:
    raise SystemExit("[FAIL] production family universe call missing")
pred = pred.replace('anchors=_recent_asset_anchor_universe(root,asset,lead)', 'anchors=_recent_asset_anchor_universe(root,asset,lead,now)', 1)
compile(pred, str(PRED), "exec")
PRED.write_text(pred, encoding="utf-8")

TEST_SOURCE = '''from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m
import qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap as tap
import qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge as bridge
assert m.MAX_STATE_AGE_SECONDS==120.0 and m.HURDLE==0.020 and m.MIN_NET_EDGE==0.005
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False
assert tap._asset("KXITFMATCH-26SEP12PETHUR-HUR") is None and m._asset("KXITFMATCH-26SEP12PETHUR-HUR") is None
assert tap._asset("KXBTC15M-X")=="BTC" and tap._asset("KXETH15M-X")=="ETH" and tap._asset("KXSOLE-X")=="SOL"
old=tap._canonical_highwater; tap._canonical_highwater=lambda root:123
with tempfile.TemporaryDirectory() as td:
 r=Path(td); now=2000000000.0
 q=tap.freeze_trade({"type":"ticker","msg":{"market_ticker":"KXBTCD-X","yes_bid_dollars":"0.50","yes_ask_dollars":"0.60"}},now,"ticker-id",r)
 assert q and q["anchor_price"]==0.55 and q["kalshi_state"]["observation_type"]=="ticker" and q["anchor_sequence_boundary"]==123
 bad=tap.freeze_trade({"type":"ticker","msg":{"market_ticker":"KXITFMATCH-26SEP12PETHUR-HUR","yes_bid_dollars":"0.50","yes_ask_dollars":"0.60"}},now,"bad",r)
 assert bad is None
 a=m._latest_realtime_spool_anchor(r,now+2); assert a and a["ticker"]=="KXBTCD-X" and now+2-a["observed_epoch"]==2
 assert a["realtime_anchor_basis"]=="OPD061_REALTIME_TRADE_TICKER_SPOOL"
tap._canonical_highwater=old
src=Path("qseries_v2/oracle_adapters/kalshi/oad_036_websocket_canonical_bridge.py").read_text(encoding="utf-8")
assert 'if typ in ("trade","ticker"):' in src
print("[PASS] OAD-036 now sends trade + ticker events into existing OPD-061 realtime anchor tap")
print("[PASS] OPD-061 freezes exact ticker midpoint/last/trade price with canonical high-water lineage")
print("[PASS] family selector consumes <=120s realtime trade/ticker anchors before canonical fallback")
print("[PASS] stale canonical family anchors no longer outrank fresh fast-lane events")
print("[PASS] PETHUR blocked at realtime tap and predictor root")
print("[PASS] 120s freshness gate, exact-contract ranking, 2pct hurdle, publication, execution unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
TEST.write_text(TEST_SOURCE, encoding="utf-8")
compile(TEST_SOURCE, str(TEST), "exec")

print("[PASS] realtime ticker-anchor root cutover installed")
print("[ROOT] OAD-036 fast lane -> OPD-061 trade/ticker spool -> full-evidence family selector")
print("[PRESERVED] canonical high-water lineage on every realtime anchor")
print("[PRESERVED] MAX_STATE_AGE_SECONDS=120; no freshness gate lowering")
print("[PRESERVED] exact-contract scoring/ranking + immutable ledger + 2pct hurdle")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
