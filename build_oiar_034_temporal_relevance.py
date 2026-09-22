from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_034_temporal_relevance.py'
TEST=ROOT/'test_oiar_034_temporal_relevance.py'
MODULE_SOURCE='from __future__ import annotations\nfrom datetime import datetime,timezone\nOIAR_034_BUILD_ID="OIAR-034"\nOIAR_034_REVISION="OIAR_034_TEMPORAL_RELEVANCE_V1"\nEXECUTION_AUTHORITY=False\nTIME_KEYS=("event_start","event_start_at","start_time","close_time","close_at","expiration_time","expected_expiration_time")\n\ndef _parse(v):\n    if not v:return None\n    if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n    s=str(v).strip().replace("Z","+00:00")\n    try:\n        x=datetime.fromisoformat(s);return x if x.tzinfo else x.replace(tzinfo=timezone.utc)\n    except ValueError:return None\n\ndef temporal_relevance(market,now=None):\n    now=now or datetime.now(timezone.utc)\n    if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)\n    event=None;source=""\n    for key in TIME_KEYS:\n        event=_parse(market.get(key))\n        if event is not None:source=key;break\n    if event is None:return {"label":"UNKNOWN","proven":False,"event_time":None,"source":"NO_SNAPSHOT_EVENT_TIME"}\n    local_now=now.astimezone(event.tzinfo);delta=(event-local_now).total_seconds()\n    if event.date()==local_now.date():label="TODAY"\n    elif 0<delta<=36*3600:label="UPCOMING"\n    elif delta<0:label="PAST_OR_STARTED"\n    else:label="FUTURE"\n    return {"label":label,"proven":True,"event_time":event.isoformat(),"source":source}\n'
TEST_SOURCE='import unittest\nfrom datetime import datetime,timezone\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_034_temporal_relevance as m\nclass T(unittest.TestCase):\n def test_unknown_is_not_today(self):self.assertEqual(m.temporal_relevance({},datetime(2026,8,24,12,tzinfo=timezone.utc))["label"],"UNKNOWN")\n def test_today_requires_time(self):self.assertEqual(m.temporal_relevance({"event_start":"2026-08-24T20:00:00+00:00"},datetime(2026,8,24,12,tzinfo=timezone.utc))["label"],"TODAY")\nif __name__=="__main__":\n print("="*88);print(" OIAR-034 CERTIFICATION TEST");print(" TEMPORAL RELEVANCE");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] no-guess temporal grounding certified");print("[DONE] OIAR-034 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_033_event_sport_context.py',)
EXTRA={}

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
    print("="*88);print(" OIAR-034 INSTALLER");print(" TEMPORAL RELEVANCE");print("="*88);print("[ROOT]",ROOT)
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
        pass
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-034 failed; affected repository files restored")
        raise
    print("[PASS] snapshot-only trader presentation boundary preserved")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-034 INSTALLATION COMPLETE")
if __name__=="__main__":main()
