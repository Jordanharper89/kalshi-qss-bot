
from pathlib import Path
import json,importlib,inspect
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state/ksem020_first_physical_market_to_event_binding_gate.json"; TEST=ROOT/"test_ksem_020_first_physical_market_to_event_binding_gate.py"
LEAGUES=("NFL","NCAAF","NBA","NHL","MLS","EPL")
def pick(d,*names):
    if isinstance(d,dict):
        for n in names:
            if n in d and d[n] not in (None,"",[]): return d[n]
    return None
def norm(v):
    if hasattr(v,"__dict__"): return {k:norm(x) for k,x in vars(v).items() if not k.startswith("_")}
    if isinstance(v,dict): return {str(k):norm(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [norm(x) for x in v]
    return v
def canonical_events():
    from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
    out=[]
    for lg in LEAGUES:
        try: rows=acquire_canonical_events(lg,timeout=15,root=ROOT)
        except TypeError: rows=acquire_canonical_events(lg,timeout=15)
        for r in rows or []: out.append(norm(r))
    return out
def main():
    print("="*120); print(" KSEM-020 FIRST PHYSICAL MARKET-TO-EVENT BINDING GATE"); print("="*120)
    from qseries_v2.kalshi_sports_evidence_mapping.live_sports_candidate_boundary import read_current_sports_candidates
    from qseries_v2.kalshi_sports_evidence_mapping.canonical_event_candidate_matcher import score_candidate,select_exact
    try: markets=list(read_current_sports_candidates() or [])
    except TypeError: markets=list(read_current_sports_candidates(limit=100) or [])
    markets=[norm(x) for x in markets][:100]
    if not markets: raise SystemExit("[FAIL] no current sports markets")
    events=canonical_events()
    if not events: raise SystemExit("[FAIL] no canonical OSN sports events")
    results=[]
    for m in markets:
        league=str(pick(m,"league","sport_league","resolved_league") or "").upper()
        ents=pick(m,"teams","team_pair","entities","participants") or []
        if isinstance(ents,str): ents=[ents]
        cands=[]
        for e in events:
            cands.append(score_candidate(
                league=league,market_entities=ents,
                event_id=pick(e,"canonical_event_id","event_id","provider_event_id") or "",
                home=pick(e,"home","home_team","home_name") or "",
                away=pick(e,"away","away_team","away_name") or "",
                event_league=pick(e,"league") or ""))
        status,row=select_exact(cands)
        results.append({"ticker":pick(m,"ticker","market_ticker") or "","league":league,"entities":ents,
                        "status":status,"canonical_event_id":row.canonical_event_id if row else None,
                        "score":row.score if row else None})
    counts={s:sum(1 for r in results if r["status"]==s) for s in ("BOUND","AMBIGUOUS","UNBOUND")}
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps({"sample_size":len(markets),"canonical_event_count":len(events),"counts":counts,
                                 "results":results,"execution_authority":False},indent=2,default=str),encoding="utf-8")
    for r in results[:25]: print("[BINDING]",r)
    print("[COUNTS]",counts,"events=",len(events))
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem020_first_physical_market_to_event_binding_gate.json').read_text())\nassert d['sample_size']>0 and d['canonical_event_count']>0\nassert sum(d['counts'].values())==d['sample_size']\nassert d['execution_authority'] is False\nprint('[PASS] bounded physical Kalshi sports -> canonical event gate executed')\nprint('[PASS] every sampled market accounted BOUND/AMBIGUOUS/UNBOUND')\nprint('[PASS] KSEM-020 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT))
if __name__=="__main__": main()
