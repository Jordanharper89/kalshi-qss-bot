from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_036_trader_card_presentation_cutover.py'
TEST=ROOT/'test_oiar_036_trader_card_presentation_cutover.py'
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief\nfrom .oiar_027_trader_intent_classifier import classify_trader_intent\nfrom .oiar_028_relative_strength_semantics import rank_relative\nfrom .oiar_032_market_name_compression import compress_market_name\nfrom .oiar_033_event_sport_context import classify_event_context\nfrom .oiar_034_temporal_relevance import temporal_relevance\nfrom .oiar_035_conversational_followup_resolution import classify_followup,followup_kind,ordinal_index\nOIAR_036_BUILD_ID="OIAR-036"\nOIAR_036_REVISION="OIAR_036_TRADER_CARD_PRESENTATION_CUTOVER_V1"\nEXECUTION_AUTHORITY=False\n_STATE={"markets":(),"selected":0}\n\ndef _card(m,rank=1):\n    ctx=classify_event_context(m);tm=temporal_relevance(m)\n    return (\n      f"#{rank} {compress_market_name(m)}",\n      f"   Market: {ctx[\'sport\']} | Time: {tm[\'label\']}",\n      f"   Read: {m.get(\'trader_takeaway\') or \'NO EDGE RIGHT NOW\'} | Direction: {m.get(\'direction\') or \'NEUTRAL\'}",\n      f"   Why: {m.get(\'why\') or \'Live evidence has not confirmed an edge.\'}",\n      f"   Risk: {m.get(\'risk\') or \'UNKNOWN\'}",\n      f"   Trader take: {\'Worth watching.\' if str(m.get(\'setup_status\')) in (\'WORTH_WATCHING_NOW\',\'SETUP_FORMING\') else \'Watch only. Do not chase it.\'}",\n    )\n\ndef render_trader_cards(markets,limit=2):\n    ranked=rank_relative(markets);chosen=ranked[:max(1,min(int(limit),2))]\n    _STATE["markets"]=tuple(chosen);_STATE["selected"]=0\n    edge=any(str(x.get("setup_status") or "")=="WORTH_WATCHING_NOW" for x in chosen)\n    lead="Oracle has something worth watching." if edge else "Nothing clears Oracle\'s edge threshold right now."\n    lines=["="*80,"ORACLE TRADER READ",lead,"-"*80]\n    for i,m in enumerate(chosen,1):lines.extend(_card(m,i))\n    lines+=["-"*80,"No order placement. Q Series execution authority remains separate.","="*80]\n    return tuple(lines)\n\ndef render_followup(query):\n    markets=_STATE.get("markets") or ()\n    if not markets:return ("I do not have an active trader read to follow up on yet.",)\n    idx=ordinal_index(query)\n    if idx is not None and idx<len(markets):_STATE["selected"]=idx\n    m=markets[min(_STATE.get("selected",0),len(markets)-1)]\n    kind=followup_kind(query)\n    if kind=="time":\n        t=temporal_relevance(m)\n        if not t["proven"]:return ("Oracle cannot prove from this snapshot that this market is for today.","Time relevance: UNKNOWN")\n        return (f"Time relevance: {t[\'label\']}",f"Snapshot event time: {t[\'event_time\']}")\n    if kind=="why":return (f"Why: {m.get(\'why\') or \'Live evidence has not confirmed an edge.\'}",)\n    if kind=="risk":return (f"Risk: {m.get(\'risk\') or \'UNKNOWN\'}",)\n    return _card(m,_STATE.get("selected",0)+1)\n\ndef bind_trader_card_terminal(base_module,root=None):\n    if getattr(base_module,"_oiar036_bound",False):return base_module\n    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()\n    def display_query(query,*,session=None,root=None,builder=None,write=print):\n        canonical=base_module.normalize_query(query)\n        if classify_followup(canonical):\n            for line in render_followup(canonical):write(line)\n            return None\n        intent=classify_trader_intent(canonical)\n        if intent.route=="trader_brief":\n            x=read_fast_trader_brief(Path(root or active).resolve(),50)\n            for line in render_trader_cards(x.markets,2):write(line)\n            return None\n        kwargs={"session":session,"root":Path(root or active).resolve(),"write":write}\n        if builder is not None:kwargs["builder"]=builder\n        return original(canonical,**kwargs)\n    base_module.display_query=display_query;base_module._oiar036_bound=True\n    return base_module\n'
TEST_SOURCE='import unittest,inspect\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_036_trader_card_presentation_cutover as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_036_BUILD_ID,"OIAR-036")\n def test_no_scan(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))\n def test_readable(self):\n  rows=({"market_title":"yes Philadelphia,yes Cleveland,yes Boston,yes Milwaukee,yes Pittsburgh","market_id":"x","trader_takeaway":"NO EDGE RIGHT NOW","direction":"NEUTRAL","why":"Live evidence is weak.","risk":"MODERATE","setup_status":"NO_CONFIRMED_EDGE"},)\n  out=m.render_trader_cards(rows,2);text="\\n".join(out)\n  self.assertIn("Philadelphia + Cleveland",text);self.assertNotIn("yes Philadelphia,yes Cleveland",text)\n  follow="\\n".join(m.render_followup("is this for today?"));self.assertIn("cannot prove",follow)\nif __name__=="__main__":\n print("="*88);print(" OIAR-036 CERTIFICATION TEST");print(" TRADER CARD PRESENTATION CUTOVER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] readable trader-card and follow-up cutover certified");print("[DONE] OIAR-036 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_035_conversational_followup_resolution.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_031_unified_trader_conversation_cutover.py', 'run_oracle_open_intelligence_terminal.py')
EXTRA={'run_oracle_operator_terminal.py': 'from __future__ import annotations\nimport run_oracle_open_intelligence_terminal as base\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import bind_historical_experience_surface\nfrom qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import bind_persisted_trader_intelligence\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover import bind_trader_brief_terminal\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_031_unified_trader_conversation_cutover import bind_unified_trader_conversation\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_036_trader_card_presentation_cutover import bind_trader_card_terminal\ndef main():\n    bind_historical_experience_surface(base)\n    bind_persisted_trader_intelligence(base)\n    bind_trader_brief_terminal(base)\n    bind_unified_trader_conversation(base)\n    bind_trader_card_terminal(base)\n    return base.main()\nif __name__=="__main__":raise SystemExit(main())\n'}

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8")
    os.replace(t,p)

def restore(p,b):
    if b is None:
        if p.exists(): p.unlink()
    else:
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def main():
    print("="*88);print(" OIAR-036 INSTALLER");print(" TRADER CARD PRESENTATION CUTOVER");print("="*88);print("[ROOT]",ROOT)
    for rel in REQUIRED:
        p=ROOT/rel
        if not p.is_file():raise RuntimeError(f"Required upstream missing: {p}")
    targets=[MOD,TEST]+[ROOT/x for x in EXTRA]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD));ast.parse(TEST_SOURCE,filename=str(TEST))
        for s in EXTRA.values():ast.parse(s)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for rel,s in EXTRA.items():write_exact(ROOT/rel,s)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)
        importlib.invalidate_caches()
        base=importlib.import_module("run_oracle_open_intelligence_terminal")
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_036_trader_card_presentation_cutover")
        m.bind_trader_card_terminal(base,ROOT)
        for q in ("what are the plays for today?","anything worth watching?"):
            lines=[];started=time.monotonic();base.display_query(q,root=ROOT,write=lines.append);elapsed=time.monotonic()-started
            print(f"[PHYSICAL QUERY] {q!r} elapsed_seconds={elapsed:.4f}")
            if elapsed>=1.0:raise RuntimeError("OIAR-036 trader query exceeded 1 second")
            text="\n".join(str(x) for x in lines)
            if "Oracle Operator Decision Brief" in text:raise RuntimeError("OIAR-036 fell through to legacy decision brief")
            if "yes Philadelphia,yes" in text:raise RuntimeError("OIAR-036 raw contract title leaked to trader")
            for line in lines[:14]:print(line)
        lines=[];base.display_query("is this for today?",root=ROOT,write=lines.append)
        if any("Oracle Operator Decision Brief" in str(x) for x in lines):raise RuntimeError("OIAR-036 follow-up fell through to legacy decision brief")
        print("[PHYSICAL FOLLOW-UP]");[print(x) for x in lines]
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-036 failed; affected repository files restored")
        raise
    print("[PASS] snapshot-only trader presentation boundary preserved")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-036 INSTALLATION COMPLETE")
if __name__=="__main__":main()
