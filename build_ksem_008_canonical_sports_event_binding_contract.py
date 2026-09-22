
from pathlib import Path
import json
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
SEL=PKG/"state/ksem007_exact_callable_binding_selection.json"
MOD=PKG/"canonical_event_binding.py"
STATE=PKG/"state/ksem008_canonical_event_binding_contract.json"
TEST=ROOT/"test_ksem_008_canonical_sports_event_binding_contract.py"
CODE='from dataclasses import dataclass\nfrom typing import Tuple\n\n@dataclass(frozen=True)\nclass CanonicalEventBinding:\n    ticker:str\n    league:str\n    market_entities:Tuple[str,...]\n    canonical_event_id:str|None\n    canonical_home:str|None\n    canonical_away:str|None\n    status:str\n    reasons:Tuple[str,...]\n    execution_authority:bool=False\n\ndef bind_exact(ticker,league,market_entities,*,canonical_event_id=None,canonical_home=None,canonical_away=None,ambiguity=()):\n    ents=tuple(str(x).strip() for x in market_entities if str(x).strip())\n    amb=tuple(str(x) for x in ambiguity)\n    if amb:\n        return CanonicalEventBinding(str(ticker),str(league),ents,None,None,None,"AMBIGUOUS",amb,False)\n    if not (ticker and league and ents and canonical_event_id and canonical_home and canonical_away):\n        return CanonicalEventBinding(str(ticker),str(league),ents,None,None,None,"UNBOUND",("INSUFFICIENT_EXACT_IDENTITY",),False)\n    normalized={x.casefold() for x in ents}\n    teams={str(canonical_home).casefold(),str(canonical_away).casefold()}\n    if not normalized.issubset(teams):\n        return CanonicalEventBinding(str(ticker),str(league),ents,None,None,None,"REJECTED",("ENTITY_MISMATCH",),False)\n    return CanonicalEventBinding(str(ticker),str(league),ents,str(canonical_event_id),str(canonical_home),str(canonical_away),"BOUND",(),False)\n'
def main():
    print("="*118); print(" KSEM-008 CANONICAL SPORTS EVENT BINDING CONTRACT"); print("="*118)
    if not SEL.exists(): raise SystemExit("[FAIL] missing KSEM-007")
    MOD.write_text(CODE,encoding="utf-8"); compile(CODE,str(MOD),"exec")
    STATE.write_text(json.dumps({"binding_states":["BOUND","UNBOUND","AMBIGUOUS","REJECTED"],"silent_guessing":False,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.canonical_event_binding import bind_exact\nx=bind_exact('KX','NFL',('Texans','Chiefs'),canonical_event_id='evt1',canonical_home='Chiefs',canonical_away='Texans')\nassert x.status=='BOUND'\ny=bind_exact('KX','NFL',('Texans',),ambiguity=('MULTIPLE_EVENTS',))\nassert y.status=='AMBIGUOUS'\nz=bind_exact('KX','NFL',('Texans','Bills'),canonical_event_id='evt1',canonical_home='Chiefs',canonical_away='Texans')\nassert z.status=='REJECTED'\nprint('[PASS] canonical event binding requires exact identity')\nprint('[PASS] KSEM-008 certified')\n",encoding="utf-8")
    print("[WRITE]",MOD.relative_to(ROOT)); print("[WRITE]",TEST.name)
if __name__=="__main__": main()
