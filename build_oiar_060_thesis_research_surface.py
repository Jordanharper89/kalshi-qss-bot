from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_060_thesis_research_surface.py'
TEST = ROOT / 'test_oiar_060_thesis_research_surface.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom pathlib import Path\nfrom .oiar_059_thesis_calibration_readiness import read_latest_thesis_calibration_readiness\n\nOIAR_060_BUILD_ID="OIAR-060"\nTOKENS=("why do you like","build a thesis","what is the thesis","thesis for","why is this strong","evidence for")\n\ndef is_thesis_query(q):\n    n=" ".join(str(q or "").lower().split())\n    return any(t in n for t in TOKENS)\n\ndef render_thesis_surface(root=None,limit=5):\n    x=read_latest_thesis_calibration_readiness(root)\n    if not x:raise RuntimeError("OIAR-060 requires OIAR-059 snapshot")\n    rows=x.get("markets",[])[:max(1,min(int(limit),10))]\n    lines=["="*80,"ORACLE THESIS RESEARCH","EVIDENCE COMBINATION | CALIBRATION-GATED | READ ONLY","-"*80]\n    for i,r in enumerate(rows,1):\n        lines += [\n            f"#{i} {r.get(\'title\') or r.get(\'market_id\')}",\n            f"   Market: {r.get(\'market_id\')}",\n            f"   Direction: {str(r.get(\'direction\',\'neutral\')).upper()}",\n            f"   Thesis: {r.get(\'thesis_statement\')}",\n            f"   Calibration: {r.get(\'calibration_status\')} ({r.get(\'settled_outcomes\',0)}/{r.get(\'minimum_outcomes_required\',30)} settled outcomes)",\n            "   Probability: UNAVAILABLE" if r.get("empirical_rate") is None else f"   Historical rate: {r[\'empirical_rate\']}",\n            "   Trader take: Research only; no execution authority.",\n            ""\n        ]\n    lines += ["Oracle will not invent a probability until settled-outcome calibration exists.",\n              "No order placement. Q Series execution authority remains separate.","="*80]\n    return tuple(lines)\n\ndef physical_probe(root=None):\n    lines=render_thesis_surface(root,5)\n    return {"lines":len(lines),"header":lines[1],"execution_authority":False}\n'
TEST_SOURCE = 'import inspect,unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_060_thesis_research_surface as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_060_BUILD_ID,"OIAR-060")\n    def test_queries(self):\n        self.assertTrue(m.is_thesis_query("what is the thesis for this market?"))\n        self.assertTrue(m.is_thesis_query("why do you like this?"))\n    def test_no_canonical_scan(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))\n    def test_surface(self):\n        x=m.render_thesis_surface();self.assertTrue(any("Probability: UNAVAILABLE" in s for s in x))\nif __name__=="__main__":\n    print("="*88);print(" OIAR-060 CERTIFICATION TEST");print(" THESIS RESEARCH SURFACE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] calibration-gated thesis surface certified");print("[DONE] OIAR-060 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_059_thesis_calibration_readiness.py',)

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OIAR-060 INSTALLER")
    print(" THESIS RESEARCH SURFACE")
    print("="*88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError("Required proven upstream missing: " + rel)

    old_mod = MOD.read_bytes() if MOD.exists() else None
    old_test = TEST.read_bytes() if TEST.exists() else None

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        importlib.invalidate_caches()

        m = importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_060_thesis_research_surface")
        started = time.monotonic()
        x = m.physical_probe(ROOT)
        print("[PHYSICAL]", x, "elapsed_seconds=", round(time.monotonic()-started, 3))

        if x["lines"]<=0: raise RuntimeError("OIAR-060 rendered zero lines")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True, timeout=120)

    except Exception:
        restore(MOD, old_mod)
        restore(TEST, old_test)
        print("[ROLLBACK] OIAR-060 failed; affected files restored")
        raise

    print("[PASS] snapshot-only intelligence path preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-060 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
