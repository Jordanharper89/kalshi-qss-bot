from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_038_formula_token_lineage_gate.py";TEST=ROOT/"test_opd_038_formula_token_lineage_gate.py"
MOD.write_text(r"""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";freeze=json.loads((rt/"opd_031_prospective_candidate_freeze.json").read_text())
    required=sorted({t for c in freeze["candidates"] for t in c["formula"]});sources=[rt/"opd_017_discovery_feature_primitives.jsonl",rt/"opd_021_holdout_feature_primitives.jsonl"]
    found=Counter();examples=defaultdict(list)
    for p in sources:
        if not p.exists():continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                x=json.loads(line);hit=set(x.get("tokens",[])).intersection(required)
                for t in hit:
                    found[t]+=1
                    if len(examples[t])<3:examples[t].append({"ticker":x.get("ticker"),"horizon_seconds":x.get("horizon_seconds"),"anchor_id":x.get("anchor_id"),"asset":x.get("asset")})
    missing=[t for t in required if not found[t]]
    if missing:raise RuntimeError("FROZEN_FORMULA_TOKEN_LINEAGE_MISSING:"+repr(missing))
    lineages=[{"token":t,"historical_occurrences":found[t],"examples":examples[t]} for t in required]
    s={"schema_version":"OPD-038","required_tokens":required,"token_lineages":lineages,"all_tokens_physically_observed":True,
       "live_token_semantics_may_not_be_reinvented":True,"exact_opd017_rules_required":True,"execution_authority":False}
    out=rt/"opd_038_formula_token_lineage_gate.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_038_formula_token_lineage_gate import build
s,p=build(Path.cwd());assert p.exists() and s["all_tokens_physically_observed"] and s["exact_opd017_rules_required"]
print("[FILE]",p);print("[REQUIRED_TOKENS]",s["required_tokens"]);print("[TOKEN_LINEAGES]",s["token_lineages"]);print("[PASS] every frozen formula token traced to physical OPD-017/021 observations");print("[PASS] OPD-038 formula-token lineage gate certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-038 installer complete")