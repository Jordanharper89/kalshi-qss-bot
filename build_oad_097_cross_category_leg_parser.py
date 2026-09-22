from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID = "OAD-097"
REVISION = "OAD_097_PRODUCTION_INSTALLER_V1"
TITLE = 'CROSS-CATEGORY LEG PARSER'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / 'oad_097_cross_category_leg_parser.py'
TEST = ROOT / 'test_oad_097_cross_category_leg_parser.py'
INIT = PKG / "__init__.py"
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\nfrom qseries_v2.oracle_adapters.independent.oad_096_atomic_sports_admission_boundary import atomic_sports_admission\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass CrossCategoryLeg:\n    parent_ticker:str\n    leg_index:int\n    polarity:str\n    text:str\n    domain:str\n    sport:str\n    league:str\n    state:str\n\ndef _title(market):\n    return str(market.get("title","") or "").strip()\n\ndef split_cross_category_legs(market):\n    ticker=str(market.get("ticker",""))\n    title=_title(market)\n    if not title:\n        return ()\n    pieces=[x.strip() for x in re.split(r",(?=\\s*(?:yes|no)\\b)", title, flags=re.I) if x.strip()]\n    if len(pieces)==1 and not re.match(r"^(yes|no)\\b", pieces[0], re.I):\n        pieces=[pieces[0]]\n    out=[]\n    for i,piece in enumerate(pieces,1):\n        m=re.match(r"^(yes|no)\\s+(.*)$",piece,re.I)\n        polarity=m.group(1).lower() if m else "unspecified"\n        text=m.group(2).strip() if m else piece\n        synthetic=dict(market)\n        synthetic["title"]=text\n        synthetic["yes_sub_title"]=""\n        synthetic["no_sub_title"]=""\n        admission=atomic_sports_admission(synthetic)\n        out.append(CrossCategoryLeg(ticker,i,polarity,text,admission.admitted_domain,admission.sport,admission.league,admission.state))\n    return tuple(out)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_097_cross_category_leg_parser import *\n\nclass T(unittest.TestCase):\n    def test_multiple_legs(self):\n        rows=split_cross_category_legs({"ticker":"KXMVECROSSCATEGORY-X","title":"yes Bayern Munich,yes Over 41.5 points scored,no Target Price: $100"})\n        self.assertEqual(len(rows),3)\n        self.assertEqual(rows[0].polarity,"yes")\n        self.assertEqual(rows[2].polarity,"no")\n    def test_preserves_parent(self):\n        rows=split_cross_category_legs({"ticker":"ABC","title":"yes Team A,yes Team B"})\n        self.assertTrue(all(x.parent_ticker=="ABC" for x in rows))\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-097 CERTIFICATION TEST");print(" CROSS-CATEGORY LEG PARSER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Cross-category bundles decomposed into immutable individual legs")\n    print("[DONE] OAD-097 CERTIFIED")\n'
FROZEN = [('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED = [('qseries_v2/oracle_adapters/independent/oad_096_atomic_sports_admission_boundary.py', 'Certified OAD-096')]

def write(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("=" * 88)
    print(" " + BUILD_ID + " INSTALLER")
    print(" " + TITLE)
    print("=" * 88)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", ROOT)
    for rel, label in REQUIRED:
        if not (ROOT / rel).is_file():
            raise RuntimeError(label + " missing")
        print("[PASS]", label, "verified")
    frozen = {ROOT / rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel, _ in FROZEN}
    old = {p: (p.read_bytes() if p.exists() else None) for p in (MODULE, TEST, INIT)}
    try:
        write(MODULE, MODULE_SOURCE)
        write(TEST, TEST_SOURCE)
        lines = INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export = "from ." + MODULE.stem + " import *"
        if export not in lines:
            lines.append(export)
        write(INIT, "\n".join(x for x in lines if x.strip()) + "\n")
        for p, h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest() != h:
                raise RuntimeError("Frozen dependency changed: " + p.name)
        print("[PASS] Wrote:", MODULE.relative_to(ROOT))
        print("[PASS] Wrote:", TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] " + BUILD_ID + " INSTALLATION COMPLETE")
    except Exception:
        for p, data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__ == "__main__":
    main()
