from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-084"
REVISION="OAD_084_PRODUCTION_INSTALLER_V1"
TITLE='HIERARCHICAL SOURCE-DEMAND MAP'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
WRITES=[('qseries_v2/oracle_adapters/independent/oad_084_hierarchical_source_demand_map.py', '\nfrom __future__ import annotations\nfrom collections import Counter,defaultdict\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import classify_snapshot\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nEXISTING_FAMILIES={\n "weather":("NWS/NOAA",),\n "legal_regulatory":("Federal Register",),\n "geological":("USGS",),\n}\nMISSING_FAMILIES={\n "sports":("Official league/team feeds",),\n "crypto":("Coinbase/chain RPC/indexers",),\n "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),\n "politics_elections":("Official election authorities","FEC"),\n "corporate_finance":("SEC EDGAR","Issuer investor relations"),\n "energy_commodities":("EIA","USDA"),\n "legal_regulatory":("CourtListener/official courts",),\n "health":("CDC","FDA"),\n "transport":("FAA","TSA","Maritime/port authorities"),\n "science_space":("NASA",),\n "geopolitics":("State/Defense/UN official releases",),\n "entertainment_awards":("Official award/event organizations",),\n "technology":("Issuer official releases","SEC EDGAR"),\n}\n\n@dataclass(frozen=True,slots=True)\nclass SourceDemand:\n    topic:str\n    live_markets:int\n    existing_families:tuple[str,...]\n    missing_families:tuple[str,...]\n    state:str\n\ndef source_demand_from_snapshot(snapshot):\n    rows,counts=classify_snapshot(snapshot)\n    out=[]\n    for topic,count in counts:\n        if topic=="other":\n            out.append(SourceDemand(topic,count,(),(),"UNMAPPED"))\n            continue\n        existing=EXISTING_FAMILIES.get(topic,())\n        missing=MISSING_FAMILIES.get(topic,())\n        state="NOT_COVERED" if missing else ("COVERED" if existing else "UNMAPPED")\n        out.append(SourceDemand(topic,count,existing,missing,state))\n    return tuple(sorted(out,key=lambda x:(-x.live_markets,x.topic)))\n'), ('test_oad_084_hierarchical_source_demand_map.py', '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort\nfrom qseries_v2.oracle_adapters.independent.oad_084_hierarchical_source_demand_map import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        s=capture_current_market_cohort(1000)\n        rows=source_demand_from_snapshot(s)\n        print("[PHYSICAL] snapshot_id=",s.snapshot_id)\n        print("[PHYSICAL] source_demand_topics=",len(rows))\n        for x in rows:\n            print("[DEMAND]",x.topic,"markets=",x.live_markets,"state=",x.state,"existing=",x.existing_families,"missing=",x.missing_families)\n        self.assertGreater(len(rows),0)\n        self.assertTrue(all(x.state in ("COVERED","NOT_COVERED","UNMAPPED") for x in rows))\n        self.assertTrue(all(not (x.topic=="other" and x.state=="COVERED") for x in rows))\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-084 PHYSICAL CERTIFICATION TEST");print(" HIERARCHICAL SOURCE-DEMAND MAP");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Source demand derived from classified live-market topics")\n    print("[PASS] Unmapped demand cannot report covered")\n    print("[DONE] OAD-084 CERTIFIED")\n')]
FROZEN_DEPS=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED_DEPS=[('qseries_v2/oracle_adapters/independent/oad_083_deep_unresolved_market_classification.py', 'Certified OAD-083')]

def write_exact(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main():
    print("="*88)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*88)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    for rel,label in REQUIRED_DEPS:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")

    frozen={}
    for rel,label in FROZEN_DEPS:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        frozen[p]=hashlib.sha256(p.read_bytes()).hexdigest()

    targets=[ROOT/rel for rel,_ in WRITES]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}

    try:
        for rel,source in WRITES:
            p=ROOT/rel
            write_exact(p, source)
            print("[PASS] Wrote:",rel)

        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
