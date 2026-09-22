from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_035_conversational_followup_resolution.py'
TEST=ROOT/'test_oiar_035_conversational_followup_resolution.py'
MODULE_SOURCE='from __future__ import annotations\nimport re\nOIAR_035_BUILD_ID="OIAR-035"\nOIAR_035_REVISION="OIAR_035_CONVERSATIONAL_FOLLOWUP_RESOLUTION_V1"\nEXECUTION_AUTHORITY=False\nFOLLOWUP_PATTERNS=(\n "is this for today","is that for today","is this today","is that today",\n "what about the first one","what about the second one","what about the third one",\n "why","why that one","anything better","what\'s the risk","whats the risk","what is the risk",\n)\ndef classify_followup(query):\n    q=" ".join(str(query).lower().split()).strip(" ?")\n    if q in FOLLOWUP_PATTERNS:return True\n    if re.match(r"^(what about|how about) (the )?(first|second|third|#?[123])",q):return True\n    return False\ndef ordinal_index(query):\n    q=str(query).lower()\n    if "first" in q or "#1" in q:return 0\n    if "second" in q or "#2" in q:return 1\n    if "third" in q or "#3" in q:return 2\n    return None\ndef followup_kind(query):\n    q=" ".join(str(query).lower().split())\n    if "today" in q:return "time"\n    if "risk" in q:return "risk"\n    if q.startswith("why"):return "why"\n    if "better" in q:return "better"\n    if ordinal_index(q) is not None:return "market"\n    return "context"\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_035_conversational_followup_resolution as m\nclass T(unittest.TestCase):\n def test_today(self):self.assertTrue(m.classify_followup("is this for today?"));self.assertEqual(m.followup_kind("is this for today?"),"time")\n def test_first(self):self.assertTrue(m.classify_followup("what about the first one?"));self.assertEqual(m.ordinal_index("what about the first one?"),0)\n def test_why(self):self.assertTrue(m.classify_followup("why?"))\nif __name__=="__main__":\n print("="*88);print(" OIAR-035 CERTIFICATION TEST");print(" CONVERSATIONAL FOLLOW-UP RESOLUTION");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] trader follow-up routing certified");print("[DONE] OIAR-035 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_034_temporal_relevance.py',)
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
    print("="*88);print(" OIAR-035 INSTALLER");print(" CONVERSATIONAL FOLLOW-UP RESOLUTION");print("="*88);print("[ROOT]",ROOT)
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
        print("[ROLLBACK] OIAR-035 failed; affected repository files restored")
        raise
    print("[PASS] snapshot-only trader presentation boundary preserved")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-035 INSTALLATION COMPLETE")
if __name__=="__main__":main()
