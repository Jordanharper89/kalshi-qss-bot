from __future__ import annotations
import ast, hashlib, os, subprocess, sys
from pathlib import Path

BUILD_ID = "OAD-059"
TITLE = "USGS AUTHORITATIVE EVENT ADAPTER"
REVISION = "OAD_059_PRODUCTION_INSTALLER_V1"

def locate_repository():
    candidates = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    seen = set()
    for base in tuple(candidates):
        candidates += list(base.parents)
    for base in candidates:
        for c in (base, base / "kalshi-qss-bot"):
            try: c = c.resolve()
            except OSError: continue
            if c in seen: continue
            seen.add(c)
            if (c / "qseries_v2").is_dir():
                return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
MODULE = ROOT / r"qseries_v2/oracle_adapters/independent/oad_059_usgs_event_adapter.py"
TEST = ROOT / r"test_oad_059_usgs_authoritative_event_adapter.py"
INIT = ROOT / r"qseries_v2/oracle_adapters/independent/__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\nimport json, urllib.request\nfrom datetime import datetime, timezone\nfrom .oad_056_independent_source_provenance import build_independent_observation\nOAD_059_BUILD_ID="OAD-059"; OAD_059_REVISION="OAD_059_USGS_EVENT_ADAPTER_V1"\nREAD_ONLY=True; EXECUTION_AUTHORITY=False\nENDPOINT="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"\ndef acquire_usgs_events(limit=20, timeout=20):\n    req=urllib.request.Request(ENDPOINT,headers={"User-Agent":"QSeries-Oracle/1.0 read-only"})\n    with urllib.request.urlopen(req,timeout=timeout) as r: data=json.load(r)\n    rows=[]\n    for f in data.get("features",[])[:limit]:\n        p=f.get("properties") or {}\n        ms=p.get("time"); observed=(datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat() if isinstance(ms,(int,float)) else datetime.now(timezone.utc).isoformat())\n        rows.append(build_independent_observation(source_id="usgs.gov",source_class="authoritative_real_world",\n            observation_type="earthquake_event",subject=p.get("title") or p.get("place") or "USGS event",observed_at=observed,\n            source_url=p.get("url") or f.get("id") or ENDPOINT,payload={"magnitude":p.get("mag"),"place":p.get("place"),\n            "status":p.get("status"),"tsunami":p.get("tsunami"),"coordinates":(f.get("geometry") or {}).get("coordinates")}))\n    return tuple(rows)\ndef verify_oad_059_usgs_event_adapter():\n    rows=acquire_usgs_events(limit=3)\n    return isinstance(rows,tuple) and all(x.source_id=="usgs.gov" and not x.execution_authority for x in rows)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_059_usgs_event_adapter import *\nclass T(unittest.TestCase):\n    def test_physical_usgs(self):\n        rows=acquire_usgs_events(limit=3)\n        self.assertIsInstance(rows,tuple)\n        for x in rows: self.assertEqual(x.source_id,"usgs.gov")\nif __name__=="__main__":\n    print("="*72); print(" OAD-059 PHYSICAL CERTIFICATION TEST"); print(" USGS AUTHORITATIVE EVENT ACQUISITION"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Physical USGS event feed read completed")\n    print("[DONE] OAD-059 CERTIFIED")\n'

def write_exact(path, text):
    text = textwrap_dedent(text).lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def textwrap_dedent(s):
    import textwrap
    return textwrap.dedent(s)

def main():
    print("="*72)
    print(" OAD-059 INSTALLER")
    print(" USGS AUTHORITATIVE EVENT ADAPTER")
    print("="*72)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)

    kalshi_freeze = ROOT / "qseries_v2" / "oracle_adapters" / "kalshi" / "oad_055_kalshi_production_freeze.py"
    if not kalshi_freeze.is_file():
        raise RuntimeError("Frozen Kalshi OAD-055 boundary missing")
    frozen_hash = hashlib.sha256(kalshi_freeze.read_bytes()).hexdigest()

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from ." + MODULE.stem + " import *"
        if export not in current.splitlines():
            write_exact(INIT, current.rstrip() + ("\n" if current.strip() else "") + export + "\n")
        if hashlib.sha256(kalshi_freeze.read_bytes()).hexdigest() != frozen_hash:
            raise RuntimeError("Frozen Kalshi OAD-055 boundary changed")
        print("[PASS] Frozen Kalshi OAD-055 boundary unchanged")
        print("[PASS] Wrote:", MODULE.relative_to(ROOT))
        print("[PASS] Wrote:", TEST.name)
        print("[PASS] Read-only / execution_authority=False preserved")
        print("[DONE] OAD-059 INSTALLATION COMPLETE")
    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(old)
        print("[ROLLBACK] OAD-059 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
