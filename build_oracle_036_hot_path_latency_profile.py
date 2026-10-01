from pathlib import Path
import ast

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_036_hot_path_latency_profile.py"
TEST=ROOT/"test_oracle_036_hot_path_latency_profile.py"
RUN=ROOT/"run_oracle_036_hot_path_latency_profile.py"

MODULE_SOURCE='\nfrom __future__ import annotations\nimport json,math\nfrom pathlib import Path\nfrom qseries_v2.oracle_execution import oracle_034_positive_only_paper_attack_lane as q34\nfrom qseries_v2.oracle_execution import oracle_035_positive_opportunity_lifecycle as q35\n\nEXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nREAL_MONEY_MOVED=False\nREPORT=Path("runtime_state/oracle/oracle_live_execution/oracle_036_hot_path_latency_profile.json")\n\ndef pct(vals,p):\n    vals=sorted(float(x) for x in vals)\n    if not vals:return None\n    i=(len(vals)-1)*float(p)\n    lo=int(math.floor(i));hi=int(math.ceil(i))\n    if lo==hi:return vals[lo]\n    return vals[lo]+(vals[hi]-vals[lo])*(i-lo)\n\ndef summarize(rows):\n    attacked=[x for x in rows if x.get("status")!="NONPOSITIVE_NOT_ATTACKED"]\n    c=[x["compose_ms"] for x in attacked if x.get("compose_ms") is not None]\n    s=[x["simulation_lane_ms"] for x in attacked if x.get("simulation_lane_ms") is not None]\n    t=[x["attack_total_ms"] for x in attacked if x.get("attack_total_ms") is not None]\n    return {\n        "attacks":len(attacked),\n        "compose_ms":{"p50":pct(c,.50),"p95":pct(c,.95),"p99":pct(c,.99)},\n        "simulation_lane_ms":{"p50":pct(s,.50),"p95":pct(s,.95),"p99":pct(s,.99)},\n        "attack_total_ms":{"p50":pct(t,.50),"p95":pct(t,.95),"p99":pct(t,.99)},\n    }\n\ndef run(seconds=300.0):\n    q34.ATTACK_ROWS.clear()\n    rc=q35.run(seconds=seconds)\n    summary=summarize(list(q34.ATTACK_ROWS))\n    REPORT.parent.mkdir(parents=True,exist_ok=True)\n    REPORT.write_text(json.dumps({\n        "oracle_build":"ORACLE-036",\n        "summary":summary,\n        "attack_rows":q34.ATTACK_ROWS,\n        "execution_authority":False,\n        "paper_only":True,\n    },indent=2,sort_keys=True),encoding="utf-8")\n    print("[ORACLE036_COMPLETE] attacks=%d total_p50_ms=%s total_p95_ms=%s total_p99_ms=%s"%(\n        summary["attacks"],\n        summary["attack_total_ms"]["p50"],\n        summary["attack_total_ms"]["p95"],\n        summary["attack_total_ms"]["p99"],\n    ),flush=True)\n    print("[REPORT] %s"%REPORT,flush=True)\n    return rc\n'

TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_execution import oracle_036_hot_path_latency_profile as q36\n\nclass T(unittest.TestCase):\n    def test_percentile(self):\n        self.assertEqual(q36.pct([1,2,3],.5),2.0)\n\n    def test_summary(self):\n        s=q36.summarize([\n            {"compose_ms":2,"simulation_lane_ms":8,"attack_total_ms":10},\n            {"compose_ms":4,"simulation_lane_ms":16,"attack_total_ms":20},\n        ])\n        self.assertEqual(s["attacks"],2)\n        self.assertEqual(s["attack_total_ms"]["p50"],15.0)\n\n    def test_safety(self):\n        self.assertFalse(q36.EXECUTION_AUTHORITY)\n        self.assertTrue(q36.PAPER_ONLY)\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

RUN_SOURCE='\nimport argparse\nfrom qseries_v2.oracle_execution.oracle_036_hot_path_latency_profile import run\nif __name__=="__main__":\n    p=argparse.ArgumentParser()\n    p.add_argument("--seconds",type=float,default=300.0)\n    a=p.parse_args()\n    raise SystemExit(run(seconds=a.seconds))\n'

ast.parse(MODULE_SOURCE)
ast.parse(TEST_SOURCE)
ast.parse(RUN_SOURCE)

MOD.write_text(MODULE_SOURCE.lstrip(),encoding="utf-8")
TEST.write_text(TEST_SOURCE.lstrip(),encoding="utf-8")
RUN.write_text(RUN_SOURCE.lstrip(),encoding="utf-8")

print('[PASS] ORACLE-036 hot-path latency profile installed')
print('[MEASURE] compose/simulation/total attack latency percentiles')
print('[BROADCAST] disabled')