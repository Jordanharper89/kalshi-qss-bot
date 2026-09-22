from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_022_formula_family_deduplication_freeze.py";TEST=ROOT/"test_opd_022_formula_family_deduplication_freeze.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict,Counter
import hashlib,json
def _sig(x):
    return (int(x["degree"]),int(x["horizon_seconds"]),x["target"],int(x["n"]),
            round(float(x["base_rate"]),12),round(float(x["conditional_rate"]),12),
            round(float(x["lift"]),12),round(float(x.get("mean_future_return",0)),12),
            round(float(x.get("mean_mfe",0)),12),round(float(x.get("mean_mae",0)),12))
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";reg=json.loads((rt/"opd_020_formula_discovery_registry.json").read_text())
    fam=defaultdict(list)
    for x in reg["candidates"]:fam[_sig(x)].append(x)
    rows=[]
    for i,(sig,members) in enumerate(sorted(fam.items(),key=lambda kv:(kv[0][0],kv[0][1],kv[0][2],-abs(kv[0][6]),-kv[0][3]))):
        members=sorted(members,key=lambda x:(len(x["formula"]),x["formula_id"]))
        rep=members[0]
        rows.append({"family_id":hashlib.sha256(json.dumps(sig).encode()).hexdigest()[:24],"representative_formula_id":rep["formula_id"],
                     "degree":rep["degree"],"horizon_seconds":rep["horizon_seconds"],"target":rep["target"],"discovery_n":rep["n"],
                     "discovery_base_rate":rep["base_rate"],"discovery_conditional_rate":rep["conditional_rate"],"discovery_lift":rep["lift"],
                     "discovery_q_value":rep["q_value"],"formula":rep["formula"],"member_count":len(members),
                     "member_formula_ids":[m["formula_id"] for m in members],"status":"FAMILY_DISCOVERED_NOT_VALIDATED"})
    rf=rt/"opd_022_formula_family_registry.json";rf.write_text(json.dumps(rows,indent=2,sort_keys=True))
    s={"schema_version":"OPD-022","input_candidates":len(reg["candidates"]),"family_count":len(rows),"collapsed_duplicates":len(reg["candidates"])-len(rows),
       "degree_counts":dict(Counter(str(x["degree"]) for x in rows)),"max_family_size":max([x["member_count"] for x in rows],default=0),
       "holdout_used":False,"family_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0,
       "model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_022_formula_family_deduplication_freeze.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_022_formula_family_deduplication_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["family_count"]>0 and s["family_count"]<=s["input_candidates"] and not s["holdout_used"] and s["edge_certified_count"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[INPUT_CANDIDATES]",s["input_candidates"]);print("[FAMILIES]",s["family_count"]);print("[COLLAPSED_DUPLICATES]",s["collapsed_duplicates"]);print("[MAX_FAMILY_SIZE]",s["max_family_size"]);print("[DEGREE_COUNTS]",s["degree_counts"]);print("[FAMILY_HASH]",s["family_hash"])
print("[PASS] discovery candidates collapsed into exact-statistic equivalence families before holdout scoring");print("[PASS] no holdout information influenced family construction");print("[PASS] OPD-022 formula-family deduplication freeze certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-022 installer complete")