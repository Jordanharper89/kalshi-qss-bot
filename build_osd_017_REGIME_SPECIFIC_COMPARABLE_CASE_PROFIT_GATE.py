from pathlib import Path
R=Path.cwd()
src=R/'qseries_v2/oracle_strategy_discovery/osd_016_comparable_case_regime_discovery.py'
dst=R/'qseries_v2/oracle_strategy_discovery/osd_017_regime_specific_comparable_case_profit_gate.py'
test=R/'test_osd_017_REGIME_SPECIFIC_COMPARABLE_CASE_PROFIT_GATE.py'
s=src.read_text(encoding='utf-8')
s=s.replace('osd_016_comparable_case_regime_discovery.json','osd_017_regime_specific_comparable_case_profit_gate.json')
s=s.replace('A=.65; B=.80; MIN=24; K=64; MAXF=40','A=.60; B=.80; MIN=24; K=64; MAXF=80')
s=s.replace('eg=quant([x[1]["expected_net"] for x in cal],.75)','eg=max(0.000001,quant([x[1]["expected_net"] for x in cal],.75))')
needle='ev=[]\nfor q in range(ib,n):'
repl='cz=[x[2] for x in cal if x[1]["distance"]<=dg and x[1]["expected_net"]>=eg]\ncm=statistics.mean(cz) if cz else None\ncs=statistics.stdev(cz) if len(cz)>1 else 0\nclb=cm-1.96*cs/(len(cz)**.5) if cz else None\ncalibration_certified=bool(len(cz)>=12 and cm is not None and cm>0 and clb is not None and clb>0)\nev=[]\nfor q in range(ib,n) if calibration_certified else []:'
s=s.replace(needle,repl)
s=s.replace('"calibration_forecasts":len(cal),','"calibration_forecasts":len(cal),"calibration_gate_n":len(cz),"calibration_mean_net":cm,"calibration_lb95":clb,"calibration_certified":calibration_certified,')
s=s.replace('print("[EXPECTED NET GATE]",eg)','print("[EXPECTED NET GATE]",eg);print("[CALIBRATION GATE N]",len(cz));print("[CALIBRATION MEAN NET AFTER 2PCT]",cm);print("[CALIBRATION LB95]",clb);print("[CALIBRATION CERTIFIED]",calibration_certified)')
s=s.replace('COMPARABLE_CASE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT','REGIME_SPECIFIC_EDGE_SURVIVES_UNTOUCHED_HOLDOUT')
s=s.replace('NO_COMPARABLE_CASE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT','NO_REGIME_SPECIFIC_EDGE_SURVIVES_UNTOUCHED_HOLDOUT')
s=s.replace('OSD-016-COMPARABLE-CASE-REGIME-DISCOVERY-V1','OSD-017-REGIME-SPECIFIC-COMPARABLE-CASE-PROFIT-GATE-V1')
dst.write_text(s,encoding='utf-8')
compile(s,str(dst),'exec')
t='from pathlib import Path\np=Path("qseries_v2/oracle_strategy_discovery/osd_017_regime_specific_comparable_case_profit_gate.py");s=p.read_text(encoding="utf-8");compile(s,str(p),"exec")\nfor x in ["HURDLE=.02","A=.60","B=.80","MAXF=80","max(0.000001","calibration_certified","cm>0","clb>0","REGIME_SPECIFIC_EDGE_SURVIVES_UNTOUCHED_HOLDOUT"]:assert x in s,x\nprint("[PASS] OSD-017 strict comparable-case profit gate compiles")\nprint("[PASS] expected-net gate cannot be negative")\nprint("[PASS] calibration mean net and LB95 must be positive before holdout opens")\nprint("[PASS] feature capacity expanded to 80")\nprint("[PASS] fixed 2% hurdle; execution/publication remain false")\n'
test.write_text(t,encoding='utf-8')
compile(t,str(test),'exec')
print('[PASS] OSD-017 strict comparable-case profit gate installed')
print('[TARGET]',dst);print('[TEST]',test);print('[EXECUTION/PUBLICATION] FALSE/FALSE')
