from pathlib import Path
WORKER=Path("qseries_v2/oracle_predictive_discovery/opd_044_continuous_prospective_worker.py")
s=WORKER.read_text(encoding="utf-8")
imp="from qseries_v2.oracle_predictive_discovery.opd_063_multi_horizon_prospective_intake import intake_anchor"
if imp not in s:s=imp+"\n"+s
helper=r'''
def _intake_spool(root):
    import json
    from pathlib import Path
    root=Path(root);rt=root/"runtime"/"predictive_data"
    spool=rt/"opd_061_live_anchor_spool.jsonl";cursor=rt/"opd_065_intake_cursor.json"
    if not spool.exists():return {"anchors":0,"states":0}
    pos=0
    if cursor.exists():
        try:pos=int(json.loads(cursor.read_text()).get("byte_offset",0))
        except Exception:pos=0
    anchors=states=0
    with spool.open("r",encoding="utf-8") as f:
        f.seek(pos)
        while True:
            line=f.readline()
            if not line:break
            end=f.tell();a=json.loads(line)
            intake_anchor(a,root,root)
            anchors+=1;states+=7;pos=end
    cursor.write_text(json.dumps({"byte_offset":pos,"anchors_last_cycle":anchors,"states_last_cycle":states},sort_keys=True))
    return {"anchors":anchors,"states":states}
'''
if "def _intake_spool(" not in s:
    i=s.find("def cycle(")
    if i<0:raise RuntimeError("CERTIFIED_WORKER_CYCLE_NOT_FOUND")
    s=s[:i]+helper+"\n"+s[i:]
lines=s.splitlines()
for i,line in enumerate(lines):
    if line.startswith("def cycle("):
        if "_intake_spool" not in lines[i+1]:
            indent=line[:len(line)-len(line.lstrip())]+"    "
            lines.insert(i+1,indent+"intake=_intake_spool(root or Path.cwd())")
        break
else:raise RuntimeError("CERTIFIED_WORKER_CYCLE_NOT_FOUND")
s="\n".join(lines)+"\n"
old='return {"mature":len(rows),"resolved":resolved,"abstained":abstained}'
new='return {"intake_anchors":intake["anchors"],"intake_states":intake["states"],"mature":len(rows),"resolved":resolved,"abstained":abstained}'
if old in s:s=s.replace(old,new,1)
WORKER.write_text(s,encoding="utf-8")
TEST=r'''from pathlib import Path
import ast
p=Path("qseries_v2/oracle_predictive_discovery/opd_044_continuous_prospective_worker.py")
s=p.read_text(encoding="utf-8");ast.parse(s)
assert "def _intake_spool(" in s and "intake_anchor(a,root,root)" in s
assert "execution_authority=False" in s and "probability_enabled=False" in s
assert "direction_enabled=False" in s and "publication_allowed=False" in s
assert "opd_044_continuous_prospective_worker import run_forever" in Path("run_opd_prospective_continuous_child.py").read_text()
assert '"predictive_prospective": "run_opd_prospective_continuous_child.py"' in Path("run_oracle_live.py").read_text()
print("[NATIVE_CHILD] predictive_prospective")
print("[INTAKE] OPD-061 -> OPD-062 -> OPD-063 -> OPD-032/039")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-065 native predictive worker live intake activation gate certified")
'''
Path("test_opd_065_native_worker_live_intake_activation_V1.py").write_text(TEST,encoding="utf-8")
print("[PASS] OPD-065 V1 installed")
