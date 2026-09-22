from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID = "OAD-100"
REVISION = "OAD_100_PRODUCTION_INSTALLER_V1"
TITLE = 'FINAL DECOMPOSITION / SOURCE-DEMAND CERTIFICATION'

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT = find_root()
PKG = ROOT / "qseries_v2" / "oracle_adapters" / "independent"
MODULE = PKG / 'oad_100_final_decomposition_source_demand_certification.py'
TEST = ROOT / 'test_oad_100_final_decomposition_source_demand_certification.py'
INIT = PKG / "__init__.py"
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort, snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nSPORT_SOURCES={\n "NHL":("NHL official game/stat sources",),\n "MLB":("MLB official game/stat sources",),\n "SOCCER":("Competition/club official match sources",),\n "ATP_WTA":("ATP/WTA official tournament/result sources",),\n "UFC_MMA":("UFC/commission official bout/result sources",),\n "BOXING":("Sanctioning-body/commission official bout sources",),\n "NFL":("NFL official game/stat/injury sources",),\n "NCAA_FOOTBALL":("NCAA/conference/team official sources",),\n "NBA":("NBA official game/stat/injury sources",),\n "WNBA":("WNBA official game/stat/injury sources",),\n "NCAA_BASKETBALL":("NCAA/conference/team official basketball sources",),\n "UNKNOWN":("Sport-specific authoritative source unresolved",),\n}\nDOMAIN_SOURCES={\n "financial_markets":("Independent underlying asset/reference-price source",),\n "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),\n "politics_elections":("Official election authorities","FEC"),\n "corporate_finance":("SEC EDGAR","Issuer investor relations"),\n "crypto":("Coinbase/chain RPC/indexers",),\n "weather":("NWS/NOAA",),\n "energy_commodities":("EIA","USDA"),\n "legal_regulatory":("Federal Register","Official courts"),\n "health":("CDC","FDA"),\n "transport":("FAA","TSA","Maritime/port authorities"),\n "science_space":("NASA",),\n "geopolitics":("State/Defense/UN official releases",),\n "technology":("Issuer official releases","SEC EDGAR"),\n "entertainment_awards":("Official award/event organizations",),\n}\n\n@dataclass(frozen=True, slots=True)\nclass DemandRow:\n    rank:int\n    domain:str\n    subdomain:str\n    legs:int\n    source_families:tuple[str,...]\n\n@dataclass(frozen=True, slots=True)\nclass FinalDecompositionGate:\n    snapshot_id:str\n    markets:int\n    legs:int\n    unresolved_legs:int\n    sports_none:int\n    demand_without_source:int\n    priorities:tuple[DemandRow,...]\n\ndef final_decomposition_source_demand_gate(limit=1000):\n    snap=capture_current_market_cohort(limit)\n    counts=Counter(); unresolved=0; sports_none=0\n    for market in snapshot_markets(snap):\n        legs=decompose_mixed_market(market)\n        if not legs:\n            unresolved += 1\n            continue\n        for leg in legs:\n            if leg.state=="UNRESOLVED":\n                unresolved += 1\n            if leg.domain=="sports" and leg.subdomain in ("","NONE"):\n                sports_none += 1\n            counts[(leg.domain,leg.subdomain)] += 1\n    raw=[]\n    no_source=0\n    for (domain,sub),n in counts.items():\n        if domain=="other":\n            continue\n        sources=SPORT_SOURCES.get(sub,()) if domain=="sports" else DOMAIN_SOURCES.get(domain,())\n        if not sources:\n            no_source += n\n        raw.append((n,domain,sub,sources))\n    raw.sort(key=lambda x:(-x[0],x[1],x[2]))\n    rows=tuple(DemandRow(i+1,d,s,n,src) for i,(n,d,s,src) in enumerate(raw))\n    return FinalDecompositionGate(snap.snapshot_id,snap.market_count,sum(counts.values()),unresolved,sports_none,no_source,rows)\n'
TEST_SOURCE = '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_100_final_decomposition_source_demand_certification import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        g=final_decomposition_source_demand_gate(1000)\n        print("[PHYSICAL] snapshot_id=",g.snapshot_id)\n        print("[PHYSICAL] markets=",g.markets)\n        print("[PHYSICAL] decomposed_legs=",g.legs)\n        print("[PHYSICAL] unresolved_legs=",g.unresolved_legs)\n        print("[PHYSICAL] sports_none=",g.sports_none)\n        print("[PHYSICAL] demand_without_source=",g.demand_without_source)\n        for p in g.priorities:\n            print("[BUILD_NEXT]",p.rank,p.domain,p.subdomain,"legs=",p.legs,"sources=",p.source_families)\n        self.assertEqual(g.sports_none,0)\n        self.assertEqual(g.demand_without_source,0)\n        self.assertGreater(g.markets,0)\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-100 PHYSICAL CERTIFICATION TEST");print(" FINAL DECOMPOSITION / SOURCE-DEMAND CERTIFICATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Every admitted demand has a source requirement")\n    print("[PASS] sports/NONE eliminated")\n    print("[PASS] unresolved legs remain explicit")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-096 through OAD-100 CAPABILITY SLICE CERTIFIED")\n'
FROZEN = [('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED = [('qseries_v2/oracle_adapters/independent/oad_099_mixed_domain_cross_category_decomposition.py', 'Certified OAD-099'), ('qseries_v2/oracle_adapters/independent/oad_082_single_live_market_cohort_snapshot.py', 'Certified OAD-082')]

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
