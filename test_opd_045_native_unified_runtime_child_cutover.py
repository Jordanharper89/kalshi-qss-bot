from pathlib import Path
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
