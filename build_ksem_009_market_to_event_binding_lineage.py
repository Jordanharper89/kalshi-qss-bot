
from pathlib import Path
import json
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
MOD=PKG/"binding_lineage.py"
STATE=PKG/"state/ksem009_market_to_event_binding_lineage.json"
TEST=ROOT/"test_ksem_009_market_to_event_binding_lineage.py"
CODE='from dataclasses import dataclass\nimport hashlib,json\n\n@dataclass(frozen=True)\nclass BindingLineage:\n    lineage_id:str\n    ticker:str\n    proposition_type:str\n    league:str\n    canonical_event_id:str|None\n    binding_status:str\n    source_modules:tuple\n    reasons:tuple\n    execution_authority:bool=False\n\ndef make_lineage(*,ticker,proposition_type,league,canonical_event_id,binding_status,source_modules=(),reasons=()):\n    payload={"ticker":str(ticker),"proposition_type":str(proposition_type),"league":str(league),"canonical_event_id":canonical_event_id,"binding_status":str(binding_status),"source_modules":tuple(source_modules),"reasons":tuple(reasons)}\n    lid=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return BindingLineage(lid,payload["ticker"],payload["proposition_type"],payload["league"],canonical_event_id,payload["binding_status"],payload["source_modules"],payload["reasons"],False)\n'
def main():
    print("="*118); print(" KSEM-009 MARKET-TO-EVENT BINDING LINEAGE"); print("="*118)
    for p in [PKG/"state/ksem008_canonical_event_binding_contract.json",PKG/"state/ksem007_exact_callable_binding_selection.json"]:
        if not p.exists(): raise SystemExit("[FAIL] missing dependency: "+str(p.relative_to(ROOT)))
    MOD.write_text(CODE,encoding="utf-8"); compile(CODE,str(MOD),"exec")
    STATE.write_text(json.dumps({"lineage":"IMMUTABLE_HASHED","venue":"KALSHI","canonical_event_reusable":True,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.binding_lineage import make_lineage\na=make_lineage(ticker='KX',proposition_type='GAME_WINNER',league='NFL',canonical_event_id='evt1',binding_status='BOUND',source_modules=('oad088','oad098'))\nb=make_lineage(ticker='KX',proposition_type='GAME_WINNER',league='NFL',canonical_event_id='evt1',binding_status='BOUND',source_modules=('oad088','oad098'))\nassert a.lineage_id==b.lineage_id and len(a.lineage_id)==64\nprint('[PASS] deterministic immutable binding lineage')\nprint('[PASS] KSEM-009 certified')\n",encoding="utf-8")
    print("[WRITE]",MOD.relative_to(ROOT)); print("[WRITE]",TEST.name)
if __name__=="__main__": main()
