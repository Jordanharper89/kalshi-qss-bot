from pathlib import Path
import py_compile,shutil

ROOT=Path.cwd()
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/mriya_python_paper_arb/crosslisted.py"
T=ROOT/"test_qsb_038e_identity_rows_repair.py"
if not P.is_file():
    raise SystemExit("[FAIL] QSB-038D crosslisted.py missing")

src=P.read_text(encoding="utf-8")
patches=[
('    resolved=resolve(Path(root))\n    ids=list((resolved or {}).get("rows") or (resolved or {}).get("identities") or [])\n    out=[]\n','    resolved=resolve(Path(root))\n    ids=list((resolved or {}).get("identity_rows") or (resolved or {}).get("rows") or (resolved or {}).get("identities") or [])\n    resolver_identity_rows=len(ids)\n    out=[]\n'),
('    out.sort(key=lambda z:z["activity"],reverse=True)\n    return {"router_rows":len(rows),"active_pools":len(active),"identities":out}\n','    out.sort(key=lambda z:z["activity"],reverse=True)\n    return {"router_rows":len(rows),"active_pools":len(active),\n            "resolver_identity_rows":resolver_identity_rows,\n            "active_overlap":len(out),"identities":out}\n'),
('    if not active:\n        return {"router_rows":len(rows),"active_pools":0,"identities":[]}\n','    if not active:\n        return {"router_rows":len(rows),"active_pools":0,\n                "resolver_identity_rows":0,"active_overlap":0,"identities":[]}\n'),
('    print("[LIVE_PUMPSWAP] router_rows=%d active_pools=%d exact_wsol_identities=%d"%(\n      pump["router_rows"],pump["active_pools"],len(pump["identities"])),flush=True)\n','    print("[LIVE_PUMPSWAP] router_rows=%d active_pools=%d resolver_identity_rows=%d active_wsol_overlap=%d"%(\n      pump["router_rows"],pump["active_pools"],pump.get("resolver_identity_rows",0),\n      pump.get("active_overlap",len(pump["identities"]))),flush=True)\n'),
]
for old,new in patches:
    if old not in src:
        raise SystemExit("[FAIL] exact QSB-038D repair target not found; refusing blind patch")
    src=src.replace(old,new,1)

B=ROOT/"runtime_state/qseries/qsb038e_backup/crosslisted.py"
B.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(P,B)
P.write_text(src,encoding="utf-8")
py_compile.compile(str(P),doraise=True)

T.write_text('import unittest,tempfile\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import core\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import crosslisted as x\n\nclass T(unittest.TestCase):\n    def test_certified_identity_rows_key_is_consumed(self):\n        fake_capture={"rows":[{"venue":"PUMP_SWAP","event":{"pool":"PP1"}}]}\n        fake_resolve={"identity_rows":[\n            {"venue":"PUMP_SWAP","identity_state":"EXACT","pool":"PP1",\n             "base_mint":"TOK","quote_mint":core.WSOL,\n             "base_decimals":6,"quote_decimals":9}]}\n        async def cap(seconds=5,max_rows=1600): return fake_capture\n        import types,sys\n        m1=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router")\n        m1.capture=cap\n        m2=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver")\n        m2.resolve=lambda root:fake_resolve\n        with tempfile.TemporaryDirectory() as td:\n            with patch.dict(sys.modules,{m1.__name__:m1,m2.__name__:m2}):\n                r=x.live_pumpswap_identities(td,1)\n        self.assertEqual(len(r["identities"]),1)\n        self.assertEqual(r["identities"][0]["token"],"TOK")\n        self.assertEqual(r["resolver_identity_rows"],1)\n        self.assertEqual(r["active_overlap"],1)\n        print("[PASS] certified USLS-047C identity_rows are now consumed")\n\n    def test_nonactive_identity_is_not_admitted(self):\n        fake_capture={"rows":[{"venue":"PUMP_SWAP","event":{"pool":"ACTIVE"}}]}\n        fake_resolve={"identity_rows":[\n            {"venue":"PUMP_SWAP","identity_state":"EXACT","pool":"OTHER",\n             "base_mint":"TOK","quote_mint":core.WSOL,\n             "base_decimals":6,"quote_decimals":9}]}\n        async def cap(seconds=5,max_rows=1600): return fake_capture\n        import types,sys\n        m1=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router");m1.capture=cap\n        m2=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver");m2.resolve=lambda root:fake_resolve\n        with tempfile.TemporaryDirectory() as td:\n            with patch.dict(sys.modules,{m1.__name__:m1,m2.__name__:m2}):\n                r=x.live_pumpswap_identities(td,1)\n        self.assertEqual(r["active_overlap"],0)\n        self.assertEqual(r["identities"],[])\n        print("[PASS] stale/nonactive pool identity cannot enter current intersection")\n\n    def test_diagnostic_fields_exist(self):\n        fake_capture={"rows":[]}\n        fake_resolve={"identity_rows":[]}\n        async def cap(seconds=5,max_rows=1600): return fake_capture\n        import types,sys\n        m1=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router");m1.capture=cap\n        m2=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver");m2.resolve=lambda root:fake_resolve\n        with tempfile.TemporaryDirectory() as td:\n            with patch.dict(sys.modules,{m1.__name__:m1,m2.__name__:m2}):\n                r=x.live_pumpswap_identities(td,1)\n        self.assertIn("resolver_identity_rows",r)\n        self.assertIn("active_overlap",r)\n        print("[PASS] zero-result diagnostics distinguish capture/resolver/overlap")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n',encoding="utf-8")
py_compile.compile(str(T),doraise=True)

print("[PASS] QSB-038E repaired QSB-038D identity handoff in place")
print("[ROOT_CAUSE] USLS-047C returns identity_rows; QSB-038D ignored that certified key")
print("[FIX] identity_rows -> active pool overlap -> WSOL identity -> Meteora intersection")
print("[DIAGNOSTIC] router_rows / active_pools / resolver_identity_rows / active_wsol_overlap")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
