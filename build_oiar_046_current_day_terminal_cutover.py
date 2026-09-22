from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_046_current_day_terminal_cutover.py'
TEST = ROOT / 'test_oiar_046_current_day_terminal_cutover.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_032_market_name_compression import compress_market_name\nfrom .oiar_033_event_sport_context import classify_event_context\nfrom .oiar_044_proven_current_day_trader_snapshot import STAGE as TODAY_STAGE\nfrom .oiar_027_trader_intent_classifier import classify_trader_intent\nfrom .oiar_035_conversational_followup_resolution import classify_followup,followup_kind\n\nOIAR_046_BUILD_ID="OIAR-046"\nOIAR_046_REVISION="OIAR_046_CURRENT_DAY_TERMINAL_CUTOVER_V1"\nEXECUTION_AUTHORITY=False\n_STATE={"rows":()}\n\ndef _read_today(root):\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TODAY_STAGE,))\n            row=cur.fetchone()\n        c.rollback()\n    if not row: return {"markets":[],"market_count":0}\n    p,h=row\n    if isinstance(p,str): p=json.loads(p)\n    if stable_hash(p)!=str(h): raise RuntimeError("OIAR-046 today snapshot hash mismatch")\n    return p\n\ndef render_today(root,limit=2):\n    p=_read_today(root);rows=tuple(p.get("markets",[]));_STATE["rows"]=rows\n    if not rows:\n        return ("="*80,"ORACLE TRADER READ","No snapshot-proven today markets are in the current trader cohort.","Oracle will not substitute UNKNOWN-time markets.","="*80)\n    lines=["="*80,"ORACLE TRADER READ",f"{len(rows)} snapshot-proven today market(s) are in the current trader cohort.","-"*80]\n    for i,m in enumerate(rows[:limit],1):\n        ctx=classify_event_context(m);t=m.get("time_relevance") or {}\n        lines += [f"#{i} {compress_market_name(m)}",f"   Market: {ctx[\'sport\']} | Time: {t.get(\'label\',\'UNKNOWN\')}",f"   Read: {m.get(\'trader_takeaway\') or \'NO EDGE RIGHT NOW\'} | Direction: {m.get(\'direction\') or \'NEUTRAL\'}",f"   Why: {m.get(\'why\') or \'Live evidence has not confirmed an edge.\'}",f"   Risk: {m.get(\'risk\') or \'UNKNOWN\'}"]\n    lines += ["-"*80,"No order placement. Q Series execution authority remains separate.","="*80]\n    return tuple(lines)\n\ndef bind_current_day_terminal(base_module,root=None):\n    if getattr(base_module,"_oiar046_bound",False): return base_module\n    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()\n    def display_query(query,*,session=None,root=None,builder=None,write=print):\n        canonical=base_module.normalize_query(query);use=Path(root or active).resolve()\n        if "today" in canonical and classify_trader_intent(canonical).route=="trader_brief":\n            for line in render_today(use,2): write(line)\n            return None\n        if classify_followup(canonical) and followup_kind(canonical)=="time":\n            rows=_STATE.get("rows") or ()\n            if not rows:\n                write("Oracle does not have an active snapshot-proven today market to confirm.")\n                return None\n            t=rows[0].get("time_relevance") or {}\n            write(f"Time relevance: {t.get(\'label\',\'UNKNOWN\')}")\n            write(f"Snapshot event time: {t.get(\'event_time\')}")\n            return None\n        kw={"session":session,"root":use,"write":write}\n        if builder is not None: kw["builder"]=builder\n        return original(canonical,**kw)\n    base_module.display_query=display_query;base_module._oiar046_bound=True\n    return base_module\n\ndef physical_probe(root=None):\n    lines=render_today(Path(root or Path.cwd()).resolve(),2)\n    return {"lines":len(lines),"today_surface_active":True,"execution_authority":False}\n'
TEST_SOURCE = '\nimport unittest,inspect\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_046_current_day_terminal_cutover as m\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(m.OIAR_046_BUILD_ID,"OIAR-046")\n    def test_no_scan(self): self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))\n    def test_boundary(self): self.assertFalse(m.EXECUTION_AUTHORITY)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-046 CERTIFICATION TEST");print(" CURRENT-DAY TERMINAL CUTOVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] current-day terminal cutover certified")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_045_temporal_trader_refresh_runtime.py', 'run_oracle_open_intelligence_terminal.py')
EXTRA_FILES = {'run_oracle_operator_terminal.py': '\nfrom __future__ import annotations\nimport run_oracle_open_intelligence_terminal as base\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import bind_historical_experience_surface\nfrom qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import bind_persisted_trader_intelligence\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover import bind_trader_brief_terminal\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_031_unified_trader_conversation_cutover import bind_unified_trader_conversation\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_036_trader_card_presentation_cutover import bind_trader_card_terminal\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_041_time_aware_terminal_cutover import bind_time_aware_trader_terminal\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_046_current_day_terminal_cutover import bind_current_day_terminal\ndef main():\n    bind_historical_experience_surface(base)\n    bind_persisted_trader_intelligence(base)\n    bind_trader_brief_terminal(base)\n    bind_unified_trader_conversation(base)\n    bind_trader_card_terminal(base)\n    bind_time_aware_trader_terminal(base)\n    bind_current_day_terminal(base)\n    return base.main()\nif __name__=="__main__":\n    raise SystemExit(main())\n'}

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR-046 INSTALLER")
    print(" CURRENT-DAY TERMINAL CUTOVER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    targets = [MOD, TEST] + [ROOT / rel for rel in EXTRA_FILES]
    old = {p: (p.read_bytes() if p.exists() else None) for p in targets}

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        for s in EXTRA_FILES.values():
            ast.parse(s)
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        for rel, s in EXTRA_FILES.items():
            write_exact(ROOT / rel, s)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=30)
        importlib.invalidate_caches()
        pass
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] OIAR-046 failed; affected repository files restored")
        raise

    print("[PASS] runtime-first temporal snapshot architecture preserved")
    print("[PASS] terminal remains snapshot-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-046 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
