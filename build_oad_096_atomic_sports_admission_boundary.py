from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID = "OAD-096"
REVISION = "OAD_096_PRODUCTION_INSTALLER_V1"
TITLE = 'ATOMIC SPORTS ADMISSION BOUNDARY'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / 'oad_096_atomic_sports_admission_boundary.py'
TEST = ROOT / 'test_oad_096_atomic_sports_admission_boundary.py'
INIT = PKG / "__init__.py"
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import expanded_domain_classify\nfrom qseries_v2.oracle_adapters.independent.oad_092_expanded_structural_sport_league_resolver import expanded_resolve_sport_league\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass AtomicSportsAdmission:\n    ticker:str\n    admitted_domain:str\n    sport:str\n    league:str\n    state:str\n    evidence:tuple[str,...]\n\ndef atomic_sports_admission(market):\n    domain = expanded_domain_classify(market)\n    ticker = str(market.get("ticker",""))\n    if domain.domain != "sports":\n        return AtomicSportsAdmission(ticker, domain.domain, "NONE", "NONE", "NOT_SPORTS", domain.evidence)\n    resolved = expanded_resolve_sport_league(market)\n    if resolved.league in ("", "NONE"):\n        return AtomicSportsAdmission(ticker, "sports", "sports_unresolved", "UNKNOWN", "UNRESOLVED", resolved.evidence)\n    if resolved.league == "UNKNOWN":\n        return AtomicSportsAdmission(ticker, "sports", "sports_unresolved", "UNKNOWN", "UNRESOLVED", resolved.evidence)\n    return AtomicSportsAdmission(ticker, "sports", resolved.sport, resolved.league, "RESOLVED", resolved.evidence)\n\ndef verify_no_sports_none(rows):\n    for row in rows:\n        if row.admitted_domain == "sports" and row.league in ("", "NONE"):\n            return False\n    return True\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_096_atomic_sports_admission_boundary import *\n\nclass T(unittest.TestCase):\n    def test_non_sport(self):\n        r=atomic_sports_admission({"ticker":"X","title":"Will CPI inflation exceed 3 percent?"})\n        self.assertNotEqual(r.admitted_domain,"sports")\n    def test_unknown_is_explicit(self):\n        r=atomic_sports_admission({"ticker":"X","title":"Over 41.5 points scored"})\n        self.assertFalse(r.admitted_domain=="sports" and r.league=="NONE")\n    def test_verifier(self):\n        self.assertTrue(verify_no_sports_none((AtomicSportsAdmission("X","sports","sports_unresolved","UNKNOWN","UNRESOLVED",()),)))\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-096 CERTIFICATION TEST");print(" ATOMIC SPORTS ADMISSION BOUNDARY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] sports/NONE state eliminated by atomic admission")\n    print("[DONE] OAD-096 CERTIFIED")\n'
FROZEN = [('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED = [('qseries_v2/oracle_adapters/independent/oad_095_single_snapshot_universal_source_demand_gate.py', 'Certified OAD-095')]

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
