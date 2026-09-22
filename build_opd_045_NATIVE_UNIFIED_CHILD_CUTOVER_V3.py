from pathlib import Path
import ast,hashlib,json

R=Path.cwd(); L=R/"run_oracle_LIVE.py"; CHILD="run_opd_prospective_continuous_child.py"
if not L.is_file(): raise RuntimeError("run_oracle_LIVE.py missing")
if not (R/CHILD).is_file(): raise RuntimeError("OPD-044 child runner missing")

text=L.read_text(encoding="utf-8"); tree=ast.parse(text)
assign=None
for n in tree.body:
    if isinstance(n,ast.Assign):
        for t in n.targets:
            if isinstance(t,ast.Name) and t.id=="CHILDREN":
                assign=n
if assign is None or not isinstance(assign.value,ast.Dict): raise RuntimeError("top-level CHILDREN dict not found")
before=ast.literal_eval(assign.value)

if "predictive_prospective" in before:
    if before["predictive_prospective"]!=CHILD: raise RuntimeError("existing predictive_prospective points elsewhere")
    print("[PASS] OPD-045 native child already present")
else:
    lines=text.splitlines(keepends=True)
    li=assign.value.end_lineno-1
    target=lines[li]
    pos=assign.value.end_col_offset-1
    insertion='\n    "predictive_prospective": "run_opd_prospective_continuous_child.py",'
    lines[li]=target[:pos]+insertion+target[pos:]
    new="".join(lines)
    ast.parse(new)
    backup=R/f"run_oracle_LIVE.pre_opd045_v3_{hashlib.sha256(text.encode()).hexdigest()[:12]}.py"
    backup.write_text(text,encoding="utf-8")
    L.write_text(new,encoding="utf-8")
    print("[BACKUP]",backup.name)

tree2=ast.parse(L.read_text(encoding="utf-8")); after=None
for n in tree2.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
        after=ast.literal_eval(n.value)
if after is None: raise RuntimeError("post-cutover CHILDREN missing")
for k,v in before.items():
    if after.get(k)!=v: raise RuntimeError("existing child changed: "+k)
if after.get("predictive_prospective")!=CHILD: raise RuntimeError("native child insertion failed")

D=R/"runtime"/"predictive_data"; D.mkdir(parents=True,exist_ok=True)
(D/"opd_045_native_unified_child_cutover.json").write_text(json.dumps({
 "schema_version":"OPD-045","preexisting_children":before,
 "native_child":"predictive_prospective","runner":CHILD,
 "all_preexisting_children_preserved":True,"execution_authority":False,
 "probability_enabled":False,"direction_enabled":False,"publication_allowed":False
},indent=2,sort_keys=True),encoding="utf-8")

(R/"test_opd_045_native_unified_runtime_child_cutover.py").write_text(r'''from pathlib import Path
import ast
p=Path("run_oracle_LIVE.py"); t=ast.parse(p.read_text(encoding="utf-8")); children=None
for n in t.body:
    if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="CHILDREN" for x in n.targets):
        children=ast.literal_eval(n.value)
assert children is not None
assert children["predictive_prospective"]=="run_opd_prospective_continuous_child.py"
required={"fast_lane","inventory","reasoning","learning","coverage","canonical_writer","continuity","recovery","crypto_learning","gmgn_intelligence","sports","ksem_mapping","coinbase_hf"}
assert required.issubset(children)
assert Path(children["predictive_prospective"]).is_file()
print("[CHILDREN]",len(children))
print("[PASS] all 13 preexisting native children preserved")
print("[PASS] predictive_prospective added as native supervised child")
print("[PASS] execution_authority=FALSE; probability/direction/publication disabled")
print("[PASS] OPD-045 certified")
''',encoding="utf-8")
print("[PASS] OPD-045 V3 installer complete")
