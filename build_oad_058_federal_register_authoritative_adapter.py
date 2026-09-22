from __future__ import annotations
import ast, hashlib, os, subprocess, sys
from pathlib import Path

BUILD_ID = "OAD-058"
TITLE = "FEDERAL REGISTER AUTHORITATIVE ADAPTER"
REVISION = "OAD_058_PRODUCTION_INSTALLER_V1"

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
MODULE = ROOT / r"qseries_v2/oracle_adapters/independent/oad_058_federal_register_adapter.py"
TEST = ROOT / r"test_oad_058_federal_register_authoritative_adapter.py"
INIT = ROOT / r"qseries_v2/oracle_adapters/independent/__init__.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\nimport json, urllib.parse, urllib.request\nfrom datetime import datetime, timezone\nfrom .oad_056_independent_source_provenance import build_independent_observation\nOAD_058_BUILD_ID="OAD-058"; OAD_058_REVISION="OAD_058_FEDERAL_REGISTER_ADAPTER_V1"\nREAD_ONLY=True; EXECUTION_AUTHORITY=False\nBASE="https://www.federalregister.gov/api/v1/documents.json"\ndef acquire_federal_register_documents(limit=20, timeout=20):\n    url=BASE+"?"+urllib.parse.urlencode({"per_page":max(1,min(int(limit),100)),"order":"newest"})\n    req=urllib.request.Request(url,headers={"User-Agent":"QSeries-Oracle/1.0 read-only"})\n    with urllib.request.urlopen(req,timeout=timeout) as r: data=json.load(r)\n    rows=[]\n    for d in data.get("results",[])[:limit]:\n        rows.append(build_independent_observation(source_id="federalregister.gov",source_class="authoritative_real_world",\n            observation_type="federal_register_document",subject=d.get("title") or "Federal Register document",\n            observed_at=(d.get("publication_date") or datetime.now(timezone.utc).date().isoformat())+"T00:00:00Z",\n            source_url=d.get("html_url") or d.get("pdf_url") or BASE,payload={"document_number":d.get("document_number"),\n            "type":d.get("type"),"agencies":[a.get("name") for a in d.get("agencies",[]) if isinstance(a,dict)],\n            "abstract":d.get("abstract")}))\n    return tuple(rows)\ndef verify_oad_058_federal_register_adapter():\n    rows=acquire_federal_register_documents(limit=3)\n    return len(rows)>0 and all(x.source_id=="federalregister.gov" and not x.execution_authority for x in rows)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_058_federal_register_adapter import *\nclass T(unittest.TestCase):\n    def test_physical_federal_register(self):\n        rows=acquire_federal_register_documents(limit=3)\n        self.assertGreater(len(rows),0)\n        self.assertTrue(all(x.source_id=="federalregister.gov" for x in rows))\nif __name__=="__main__":\n    print("="*72); print(" OAD-058 PHYSICAL CERTIFICATION TEST"); print(" FEDERAL REGISTER AUTHORITATIVE ACQUISITION"); print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Physical Federal Register API observations acquired")\n    print("[DONE] OAD-058 CERTIFIED")\n'

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
    print(" OAD-058 INSTALLER")
    print(" FEDERAL REGISTER AUTHORITATIVE ADAPTER")
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
        print("[DONE] OAD-058 INSTALLATION COMPLETE")
    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(old)
        print("[ROLLBACK] OAD-058 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
