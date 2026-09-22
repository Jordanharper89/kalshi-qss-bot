from pathlib import Path
import json,time,ast
R=Path.cwd(); D=R/"runtime"/"predictive_data"; D.mkdir(parents=True,exist_ok=True)
hb=D/"opd_044_worker_heartbeat.json"; launcher=R/"run_oracle_LIVE.py"
if not hb.is_file(): raise RuntimeError("OPD-044 heartbeat missing: run unified Oracle runtime first")
x=json.loads(hb.read_text(encoding="utf-8"))
required={"cycles","state","execution_authority","probability_enabled","direction_enabled","publication_allowed","updated_epoch"}
miss=required-set(x)
if miss: raise RuntimeError("OPD-044 heartbeat missing fields: "+repr(sorted(miss)))
if x["state"]!="HEALTHY": raise RuntimeError("predictive child heartbeat not HEALTHY: "+repr(x.get("error")))
if any(x[k] is not False for k in ("execution_authority","probability_enabled","direction_enabled","publication_allowed")): raise RuntimeError("predictive safety lock violated")
age=time.time()-float(x["updated_epoch"])
if age>15: raise RuntimeError(f"predictive heartbeat stale age={age:.1f}s; unified runtime must be running")
tree=ast.parse(launcher.read_text(encoding="utf-8")); children=None
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets): children=ast.literal_eval(n.value)
if not children or children.get("predictive_prospective")!="run_opd_prospective_continuous_child.py": raise RuntimeError("predictive_prospective not native unified child")
report={"schema_version":"OPD-046","heartbeat_cycles":x["cycles"],"heartbeat_age_seconds":age,"native_child":True,"state":"HEALTHY","execution_authority":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False}
(D/"opd_046_sustained_live_prospective_advancement_gate.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
(R/"test_opd_046_sustained_live_prospective_advancement_gate.py").write_text("from pathlib import Path\nimport json\nx=json.loads(Path('runtime/predictive_data/opd_046_sustained_live_prospective_advancement_gate.json').read_text())\nassert x['native_child'] and x['state']=='HEALTHY'\nassert all(x[k] is False for k in ('execution_authority','probability_enabled','direction_enabled','publication_allowed'))\nprint('[CYCLES]',x['heartbeat_cycles'])\nprint('[PASS] OPD-046 live prospective native-child advancement gate certified')\n",encoding="utf-8")
print("[CYCLES]",x["cycles"]); print("[HEARTBEAT_AGE_SECONDS]",round(age,3)); print("[PASS] OPD-046 installer complete")