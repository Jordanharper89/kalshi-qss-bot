from pathlib import Path
import ast

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_037_positive_paper_attack_certification.py"
TEST=ROOT/"test_oracle_037_positive_paper_attack_certification.py"
RUN=ROOT/"run_oracle_037_positive_paper_attack_certification.py"

MODULE_SOURCE='\nfrom __future__ import annotations\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_execution import oracle_036_hot_path_latency_profile as q36\nfrom qseries_v2.oracle_execution import oracle_035_positive_opportunity_lifecycle as q35\n\nEXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nREAL_MONEY_MOVED=False\nREPORT=Path("runtime_state/oracle/oracle_live_execution/oracle_037_positive_paper_attack_certification.json")\n\ndef certify():\n    lat={}\n    life={}\n    if q36.REPORT.is_file():\n        lat=json.loads(q36.REPORT.read_text(encoding="utf-8"))\n    if q35.REPORT.is_file():\n        life=json.loads(q35.REPORT.read_text(encoding="utf-8"))\n\n    attacks=list(lat.get("attack_rows") or [])\n    measured=[\n        x for x in attacks\n        if any(\n            isinstance(a,dict) and a.get("net_sim_pnl_lamports") is not None\n            for a in ((x.get("winner"),) if x.get("winner") else ())\n        )\n    ]\n    profitable=[x for x in attacks if x.get("profitable")]\n    episodes=list(life.get("episodes") or [])\n    consecutive=[x for x in episodes if int(x.get("consecutive_positive_updates") or 0)>=2]\n\n    status=(\n        "PASS_MEASURED_EXECUTABLE_ECONOMICS"\n        if measured\n        else "HOLD_NO_MEASURED_EXECUTABLE_ECONOMICS"\n    )\n    out={\n        "oracle_build":"ORACLE-037",\n        "status":status,\n        "attacks":len(attacks),\n        "measured_executable_economics":len(measured),\n        "profitable_after_fee":len(profitable),\n        "positive_episodes":len(episodes),\n        "consecutive_positive_episodes":len(consecutive),\n        "latency_summary":lat.get("summary"),\n        "execution_authority":False,\n        "paper_only":True,\n        "real_money_moved":False,\n    }\n    REPORT.parent.mkdir(parents=True,exist_ok=True)\n    REPORT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")\n    return out\n\ndef run(seconds=300.0):\n    rc=q36.run(seconds=seconds)\n    out=certify()\n    print("[ORACLE037_COMPLETE] status=%s attacks=%d measured=%d profitable=%d episodes=%d consecutive=%d"%(\n        out["status"],out["attacks"],out["measured_executable_economics"],\n        out["profitable_after_fee"],out["positive_episodes"],\n        out["consecutive_positive_episodes"],\n    ),flush=True)\n    print("[REPORT] %s"%REPORT,flush=True)\n    print("[BROADCAST] disabled",flush=True)\n    return rc\n'

TEST_SOURCE='\nimport json,tempfile,unittest\nfrom pathlib import Path\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_execution import oracle_037_positive_paper_attack_certification as q37\n\nclass T(unittest.TestCase):\n    def test_safety(self):\n        self.assertFalse(q37.EXECUTION_AUTHORITY)\n        self.assertTrue(q37.PAPER_ONLY)\n        self.assertFalse(q37.REAL_MONEY_MOVED)\n\n    def test_hold_without_measurement(self):\n        with tempfile.TemporaryDirectory() as d:\n            lp=Path(d)/"lat.json";ep=Path(d)/"life.json";rp=Path(d)/"r.json"\n            lp.write_text(json.dumps({"attack_rows":[],"summary":{}}),encoding="utf-8")\n            ep.write_text(json.dumps({"episodes":[]}),encoding="utf-8")\n            with patch.object(q37.q36,"REPORT",lp),patch.object(q37.q35,"REPORT",ep),patch.object(q37,"REPORT",rp):\n                x=q37.certify()\n            self.assertEqual(x["status"],"HOLD_NO_MEASURED_EXECUTABLE_ECONOMICS")\n\nif __name__=="__main__":\n    unittest.main(verbosity=2)\n'

RUN_SOURCE='\nimport argparse\nfrom qseries_v2.oracle_execution.oracle_037_positive_paper_attack_certification import run\nif __name__=="__main__":\n    p=argparse.ArgumentParser()\n    p.add_argument("--seconds",type=float,default=300.0)\n    a=p.parse_args()\n    raise SystemExit(run(seconds=a.seconds))\n'

ast.parse(MODULE_SOURCE)
ast.parse(TEST_SOURCE)
ast.parse(RUN_SOURCE)

MOD.write_text(MODULE_SOURCE.lstrip(),encoding="utf-8")
TEST.write_text(TEST_SOURCE.lstrip(),encoding="utf-8")
RUN.write_text(RUN_SOURCE.lstrip(),encoding="utf-8")

print('[PASS] ORACLE-037 positive paper attack certification installed')
print('[CERTIFY] measured executable economics + lifecycle + latency')
print('[BROADCAST] disabled')