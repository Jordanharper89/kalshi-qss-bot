from pathlib import Path
import py_compile

ROOT=Path.cwd()
MOD=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/engine.py"
if not MOD.is_file():
    raise SystemExit("[FAIL] QARB-001 clean bot missing")

s=MOD.read_text(encoding="utf-8")

anchor='_hot_cache={"at":0.0,"rows":[]}\n'
if '_cross_cache=' not in s:
    if anchor not in s:
        raise SystemExit("[FAIL] QARB-001 hot-cache anchor missing")
    s=s.replace(
        anchor,
        anchor+'_cross_cache={"at":0.0,"rows":[]}\n'
               'CROSSLIST_TTL=float(os.getenv("QARB_CROSSLIST_TTL","20"))\n'
               'DISCOVERY_BUDGET=int(os.getenv("QARB_DISCOVERY_BUDGET","48"))\n',
        1
    )

start=s.find("def candidate_universe(root):")
end=s.find("\ndef exact_pool_ok(",start)
if start<0 or end<0:
    raise SystemExit("[FAIL] QARB-001 candidate_universe boundary missing")

s=s[:start]+'def raw_candidate_universe(root):\n    tape=tape_candidates(root)\n    by_token={t:p for t,p in tape}\n    out=[];seen=set()\n    for h in mriya_hot_tokens():\n        t=h["token"];p=by_token.get(t)\n        if p is None:\n            try:\n                p=c.canonical_pump_pool(t)\n            except Exception:\n                p=None\n        if p and t not in seen:\n            out.append({"token":t,"pump_pool":p,"source":"MRIYA_HOT","age":h["age"]})\n            seen.add(t)\n    for t,p in tape:\n        if t not in seen:\n            out.append({"token":t,"pump_pool":p,"source":"LIVE_TAPE","age":None})\n            seen.add(t)\n    return out[:DISCOVERY_BUDGET]\n\ndef candidate_universe(root):\n    now=time.time()\n    if now-_cross_cache["at"]<CROSSLIST_TTL and _cross_cache["rows"]:\n        return list(_cross_cache["rows"])[:MAX_TOKENS]\n\n    raw=raw_candidate_universe(root)\n    rows=[]\n    failures={}\n    for x in raw:\n        if len(rows)>=MAX_TOKENS:\n            break\n        t=x["token"];p=x["pump_pool"]\n\n        ok,why=exact_pool_ok(t,p)\n        if not ok:\n            failures[why]=failures.get(why,0)+1\n            continue\n\n        try:\n            meta=c.discover_dlmm(t)\n        except Exception as exc:\n            key="HTTP_429" if _is_429(exc) else ("NO_DLMM_PAIR" if str(exc)=="NO_DLMM_PAIR" else type(exc).__name__)\n            failures[key]=failures.get(key,0)+1\n            if key=="HTTP_429":\n                break\n            continue\n\n        if not isinstance(meta,dict) or not meta.get("address"):\n            failures["BAD_DLMM_META"]=failures.get("BAD_DLMM_META",0)+1\n            continue\n\n        tx=meta.get("token_x");ty=meta.get("token_y")\n        if WSOL not in (tx,ty):\n            failures["DLMM_NOT_WSOL_PAIR"]=failures.get("DLMM_NOT_WSOL_PAIR",0)+1\n            continue\n\n        y=dict(x)\n        y["meteora_pool"]=meta["address"]\n        y["crosslisted"]=True\n        rows.append(y)\n\n        try:\n            cache=getattr(c,"_DLMM_CACHE",None)\n            if isinstance(cache,dict):\n                cache[t]=meta\n        except Exception:\n            pass\n\n    _cross_cache["at"]=now\n    _cross_cache["rows"]=rows\n    print("[CROSSLIST_DISCOVERY] raw=%d exact_pairs=%d failures=%s"%(\n        len(raw),len(rows),json.dumps(failures,sort_keys=True)),flush=True)\n    return list(rows)[:MAX_TOKENS]\n'+s[end:]

s=s.replace(
    'print("[ARCH] hot tokens first -> exact Pump pool -> one snapshot -> local sizes -> top-only fresh revalidation",flush=True)',
    'print("[ARCH] hot tokens first -> exact Pump+DLMM crosslist cache -> one snapshot -> local sizes -> top-only fresh revalidation",flush=True)',
    1
)
s=s.replace(
    'print("[CANDIDATES] %d landing_cost=%.9f SOL"%(len(universe),landing/1e9),flush=True)',
    'print("[CANDIDATES] quoteable_crosslisted=%d landing_cost=%.9f SOL"%(len(universe),landing/1e9),flush=True)',
    1
)

MOD.write_text(s,encoding="utf-8")
py_compile.compile(str(MOD),doraise=True)

TEST=ROOT/"test_qarb_002b_live_crosslist_hot_cache_repair.py"
TEST.write_text('import time,unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine as e\n\nclass T(unittest.TestCase):\n    def setUp(self):\n        e._cross_cache={"at":0.0,"rows":[]}\n\n    def test_no_dlmm_removed_before_quote_budget(self):\n        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm\n        e.raw_candidate_universe=lambda root:[\n            {"token":"A","pump_pool":"PA","source":"LIVE_TAPE","age":None},\n            {"token":"B","pump_pool":"PB","source":"LIVE_TAPE","age":None},\n            {"token":"C","pump_pool":"PC","source":"LIVE_TAPE","age":None},\n        ]\n        e.exact_pool_ok=lambda t,p:(True,"OK")\n        def disc(t):\n            if t in ("A","B"):\n                raise RuntimeError("NO_DLMM_PAIR")\n            return {"address":"M","token_x":e.WSOL,"token_y":"C"}\n        e.c.discover_dlmm=disc\n        try:\n            rows=e.candidate_universe(".")\n        finally:\n            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc\n        self.assertEqual([x["token"] for x in rows],["C"])\n        print("[PASS] NO_DLMM_PAIR removed before quote budget")\n\n    def test_cache_prevents_repeat_discovery(self):\n        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm\n        calls={"n":0}\n        e.raw_candidate_universe=lambda root:[{"token":"T","pump_pool":"P","source":"LIVE_TAPE","age":None}]\n        e.exact_pool_ok=lambda t,p:(True,"OK")\n        def disc(t):\n            calls["n"]+=1\n            return {"address":"M","token_x":e.WSOL,"token_y":"T"}\n        e.c.discover_dlmm=disc\n        try:\n            a=e.candidate_universe(".")\n            b=e.candidate_universe(".")\n        finally:\n            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc\n        self.assertEqual(calls["n"],1)\n        self.assertEqual(a,b)\n        print("[PASS] crosslist cache prevents repeated discovery")\n\n    def test_exact_wsol_pair_only(self):\n        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm\n        e.raw_candidate_universe=lambda root:[\n            {"token":"T","pump_pool":"P","source":"LIVE_TAPE","age":None},\n            {"token":"X","pump_pool":"PX","source":"LIVE_TAPE","age":None},\n        ]\n        e.exact_pool_ok=lambda t,p:(True,"OK")\n        e.c.discover_dlmm=lambda t:(\n            {"address":"M1","token_x":e.WSOL,"token_y":"T"} if t=="T"\n            else {"address":"M2","token_x":"AAA","token_y":"BBB"}\n        )\n        try:\n            rows=e.candidate_universe(".")\n        finally:\n            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc\n        self.assertEqual(len(rows),1)\n        self.assertEqual(rows[0]["token"],"T")\n        print("[PASS] exact WSOL/token DLMM pair required")\n\n    def test_429_stops_fanout_without_crash(self):\n        import urllib.error\n        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm\n        e.raw_candidate_universe=lambda root:[\n            {"token":"A","pump_pool":"PA","source":"LIVE_TAPE","age":None},\n            {"token":"B","pump_pool":"PB","source":"LIVE_TAPE","age":None},\n        ]\n        e.exact_pool_ok=lambda t,p:(True,"OK")\n        e.c.discover_dlmm=lambda t:(_ for _ in ()).throw(urllib.error.HTTPError("u",429,"rate",{},None))\n        try:\n            rows=e.candidate_universe(".")\n        finally:\n            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc\n        self.assertEqual(rows,[])\n        print("[PASS] 429 halts discovery fanout cleanly")\n\n    def test_max_tokens_applies_after_crosslist(self):\n        old=e.MAX_TOKENS\n        try:\n            e.MAX_TOKENS=2\n            e._cross_cache={"at":time.time(),"rows":[\n                {"token":"A","pump_pool":"P","meteora_pool":"M","crosslisted":True},\n                {"token":"B","pump_pool":"P","meteora_pool":"M","crosslisted":True},\n                {"token":"C","pump_pool":"P","meteora_pool":"M","crosslisted":True},\n            ]}\n            rows=e.candidate_universe(".")\n        finally:\n            e.MAX_TOKENS=old\n        self.assertEqual(len(rows),2)\n        print("[PASS] quote budget applies after crosslist filtering")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/"run_qarb_002b_live_crosslist_hot_cache_repair.py"
RUN.write_text(
    "from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.engine import main\n"
    "if __name__=='__main__': main()\n",
    encoding="utf-8"
)
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QARB-002B crosslist hot-cache repair installed")
print("[FIX] broken QARB-002 installer retired")
print("[NEW] quote budget is spent only on exact PumpSwap + Meteora DLMM pairs")
print("[CACHE] short-lived exact crosslist cache")
print("[429] discovery fanout stops cleanly instead of crashing")
print("[MODE] scanner_only=True execution_authority=FALSE")
