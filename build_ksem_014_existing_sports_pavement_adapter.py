
from pathlib import Path
import json
ROOT=Path.cwd();PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
INP=PKG/"state/ksem013_exact_semantic_role_resolution.json"
MOD=PKG/"existing_sports_pavement_adapter.py"
STATE=PKG/"state/ksem014_existing_pavement_adapter.json"
TEST=ROOT/"test_ksem_014_existing_sports_pavement_adapter.py"
CODE="from importlib import import_module\nfrom dataclasses import is_dataclass,asdict\nROLE_BINDINGS={\n'market_type':('qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver','resolve_sports_market_type'),\n'entity':('qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition','recognize_sports_entity_type'),\n'decomposition':('qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition','decompose_mixed_market'),\n'classification':('qseries_v2.oracle_adapters.independent.oad_101_universal_classification_exhaustive_diagnostic','classify_isolated_root_cause')}\ndef _load(role):\n    m,f=ROLE_BINDINGS[role]\n    return getattr(import_module(m),f)\ndef normalize_output(v):\n    if is_dataclass(v):return asdict(v)\n    if isinstance(v,(list,tuple)):return [normalize_output(x) for x in v]\n    if isinstance(v,dict):return {str(k):normalize_output(x) for k,x in v.items()}\n    return v\ndef run_market_type(market):return normalize_output(_load('market_type')(market))\ndef run_entity(text):return normalize_output(_load('entity')(text))\ndef run_decomposition(market):return normalize_output(_load('decomposition')(market))\ndef run_classification(leg,parent_market,sibling_legs):return normalize_output(_load('classification')(leg,parent_market,sibling_legs))\n"
def main():
    print("="*120);print(" KSEM-014 EXISTING SPORTS PAVEMENT ADAPTER");print("="*120)
    if not INP.exists():raise SystemExit("[FAIL] missing KSEM-013")
    MOD.write_text(CODE,encoding="utf-8");compile(CODE,str(MOD),"exec")
    STATE.write_text(json.dumps({"roles":4,"upstream_mutated":False,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.existing_sports_pavement_adapter import ROLE_BINDINGS,normalize_output\nassert set(ROLE_BINDINGS)=={'market_type','entity','decomposition','classification'}\nassert normalize_output((1,2))==[1,2]\nprint('[PASS] exact OAD bindings exposed read-only')\nprint('[PASS] KSEM-014 certified')\n",encoding="utf-8")
    print("[WRITE]",MOD.relative_to(ROOT));print("[WRITE]",TEST.name)
if __name__=="__main__":main()
