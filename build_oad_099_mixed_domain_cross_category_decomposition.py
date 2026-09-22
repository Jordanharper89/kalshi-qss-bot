from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID = "OAD-099"
REVISION = "OAD_099_PRODUCTION_INSTALLER_V1"
TITLE = 'MIXED-DOMAIN CROSS-CATEGORY DECOMPOSITION'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / 'oad_099_mixed_domain_cross_category_decomposition.py'
TEST = ROOT / 'test_oad_099_mixed_domain_cross_category_decomposition.py'
INIT = PKG / "__init__.py"
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\nfrom qseries_v2.oracle_adapters.independent.oad_097_cross_category_leg_parser import split_cross_category_legs\nfrom qseries_v2.oracle_adapters.independent.oad_098_structured_sports_entity_type_recognition import recognize_sports_entity_type\nfrom qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import expanded_domain_classify\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass DecomposedLeg:\n    parent_ticker:str\n    leg_index:int\n    polarity:str\n    text:str\n    domain:str\n    subdomain:str\n    state:str\n\ndef _non_sports_override(text):\n    low=text.lower()\n    if "target price:" in low or re.search(r"\\$\\s*\\d",text):\n        return "financial_price"\n    return ""\n\ndef decompose_mixed_market(market):\n    rows=split_cross_category_legs(market)\n    out=[]\n    for leg in rows:\n        override=_non_sports_override(leg.text)\n        if override:\n            out.append(DecomposedLeg(leg.parent_ticker,leg.leg_index,leg.polarity,leg.text,"financial_markets",override,"RESOLVED"))\n            continue\n        entity=recognize_sports_entity_type(leg.text)\n        if leg.domain=="sports" or entity.entity_type!="UNRESOLVED":\n            sub=leg.league if leg.league not in ("NONE","") else "UNKNOWN"\n            out.append(DecomposedLeg(leg.parent_ticker,leg.leg_index,leg.polarity,leg.text,"sports",sub,"RESOLVED" if sub!="UNKNOWN" else "UNRESOLVED"))\n            continue\n        synthetic=dict(market);synthetic["title"]=leg.text;synthetic["yes_sub_title"]="";synthetic["no_sub_title"]=""\n        d=expanded_domain_classify(synthetic)\n        out.append(DecomposedLeg(leg.parent_ticker,leg.leg_index,leg.polarity,leg.text,d.domain,"", "RESOLVED" if d.domain!="other" else "UNRESOLVED"))\n    return tuple(out)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import *\n\nclass T(unittest.TestCase):\n    def test_mixed(self):\n        rows=decompose_mixed_market({"ticker":"KXMVECROSSCATEGORY-X","title":"yes Novak Djokovic,no Target Price: $100"})\n        self.assertEqual(len(rows),2)\n        self.assertEqual(rows[0].domain,"sports")\n        self.assertEqual(rows[1].domain,"financial_markets")\n    def test_no_sports_none(self):\n        rows=decompose_mixed_market({"ticker":"X","title":"yes Novak Djokovic"})\n        self.assertFalse(any(x.domain=="sports" and x.subdomain=="NONE" for x in rows))\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-099 CERTIFICATION TEST");print(" MIXED-DOMAIN CROSS-CATEGORY DECOMPOSITION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Mixed bundles preserve independent leg domains")\n    print("[DONE] OAD-099 CERTIFIED")\n'
FROZEN = [('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED = [('qseries_v2/oracle_adapters/independent/oad_098_structured_sports_entity_type_recognition.py', 'Certified OAD-098')]

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
