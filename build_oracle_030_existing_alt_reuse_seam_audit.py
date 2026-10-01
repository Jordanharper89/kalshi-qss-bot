from pathlib import Path
import ast

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_030_existing_alt_reuse_seam_audit.py"
TEST=ROOT/"test_oracle_030_existing_alt_reuse_seam_audit.py"
RUN=ROOT/"run_oracle_030_existing_alt_reuse_seam_audit.py"

MODULE_SOURCE='\nfrom __future__ import annotations\nimport inspect, json\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q59\nfrom qseries_v2.solana_live_execution import qarb_097_official_meteora_sdk_executor as q97\n\nEXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nREAL_MONEY_MOVED=False\n\ndef _interesting_functions(mod):\n    rows=[]\n    for name,obj in inspect.getmembers(mod, inspect.isfunction):\n        try:\n            src=inspect.getsource(obj)\n        except Exception:\n            src=""\n        low=(name+"\\n"+src).lower()\n        if any(k in low for k in ("lookup","address table","alt","compile_v0","compile_signed","versioned")):\n            rows.append({\n                "name":name,\n                "signature":str(inspect.signature(obj)),\n                "mentions_alt":"alt" in low or "lookup" in low,\n                "mentions_compile":"compile" in low,\n                "mentions_send":"sendtransaction" in low,\n                "source_head":"\\n".join(src.splitlines()[:30]),\n            })\n    return rows\n\ndef run(root=None):\n    root=Path(root or Path.cwd())\n    q59_src=inspect.getsource(q59)\n    q97_src=inspect.getsource(q97)\n\n    out={\n        "oracle_build":"ORACLE-030",\n        "q59_has_compile_compact":callable(getattr(q59,"compile_compact",None)),\n        "q59_has_recent_alt_lookup":callable(getattr(q59,"recent_mriya_alt_keys",None)),\n        "q59_candidate_has_wrap_swap_close":"WRAP_SWAP_CLOSE" in q59_src,\n        "q97_functions":_interesting_functions(q97),\n        "q97_has_create_lookup_table":"createLookupTable" in q97_src or "create_lookup_table" in q97_src,\n        "q97_mentions_existing_alt":"existing" in q97_src.lower() and "alt" in q97_src.lower(),\n        "execution_authority":False,\n        "paper_only":True,\n        "real_money_moved":False,\n    }\n\n    p=root/"runtime_state/oracle/oracle_live_execution/oracle_030_existing_alt_reuse_seam_audit.json"\n    p.parent.mkdir(parents=True,exist_ok=True)\n    p.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")\n\n    print("[ORACLE-030] EXISTING ALT REUSE SEAM AUDIT")\n    print("[Q59] compile_compact=%s recent_alt_lookup=%s wrap_swap_close=%s"%(\n        out["q59_has_compile_compact"],\n        out["q59_has_recent_alt_lookup"],\n        out["q59_candidate_has_wrap_swap_close"],\n    ))\n    print("[Q97] existing_alt=%s create_lookup_table=%s candidates=%d"%(\n        out["q97_mentions_existing_alt"],\n        out["q97_has_create_lookup_table"],\n        len(out["q97_functions"]),\n    ))\n    for row in out["q97_functions"]:\n        print("[Q97_SEAM] name=%s sig=%s alt=%s compile=%s send=%s"%(\n            row["name"],row["signature"],row["mentions_alt"],row["mentions_compile"],row["mentions_send"]\n        ))\n    print("[REPORT] %s"%p)\n    print("[BROADCAST] disabled")\n    return 0\n\nif __name__=="__main__":\n    raise SystemExit(run())\n'
TEST_SOURCE='\nimport inspect, unittest\nfrom qseries_v2.oracle_execution import oracle_030_existing_alt_reuse_seam_audit as q30\n\nclass T(unittest.TestCase):\n    def test_safety(self):\n        self.assertFalse(q30.EXECUTION_AUTHORITY)\n        self.assertTrue(q30.PAPER_ONLY)\n        self.assertFalse(q30.REAL_MONEY_MOVED)\n\n    def test_exact_sources(self):\n        src=inspect.getsource(q30)\n        self.assertIn("qsb059_gav_reverse_atomic",src)\n        self.assertIn("qarb_097_official_meteora_sdk_executor",src)\n\n    def test_no_broadcast(self):\n        self.assertNotIn("sendTransaction(",inspect.getsource(q30))\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'
RUN_SOURCE='\nfrom qseries_v2.oracle_execution.oracle_030_existing_alt_reuse_seam_audit import run\nif __name__=="__main__":\n    raise SystemExit(run())\n'

ast.parse(MODULE_SOURCE)
ast.parse(TEST_SOURCE)
ast.parse(RUN_SOURCE)

MOD.write_text(MODULE_SOURCE.lstrip(),encoding="utf-8")
TEST.write_text(TEST_SOURCE.lstrip(),encoding="utf-8")
RUN.write_text(RUN_SOURCE.lstrip(),encoding="utf-8")

print("[PASS] ORACLE-030 existing ALT reuse seam audit installed")
print("[SOURCE] QSB-059 current atomic composer + QARB-097 certified existing ALT path")
print("[GOAL] pin exact reusable compiler/ALT seam before packet-size cutover")
print("[BROADCAST] disabled")
