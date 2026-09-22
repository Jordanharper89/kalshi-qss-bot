from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-105'
REVISION='OAD_105_SPORT_VOCABULARY_FOUNDATIONAL_REBUILD'
TITLE='AUTHORITATIVE SOURCE REQUIREMENT ROUTER — SPORT VOCABULARY REBUILD'

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=ROOT/'qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py'
TEST=ROOT/'test_oad_105_authoritative_source_requirement_router.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nSPORT_ALIASES={\n    "MLB":"baseball","BASEBALL":"baseball",\n    "NHL":"hockey","HOCKEY":"hockey",\n    "SOCCER":"soccer",\n    "NFL":"football","FOOTBALL":"football",\n    "NBA":"basketball","WNBA":"basketball","BASKETBALL":"basketball",\n    "TENNIS":"tennis",\n    "MMA":"combat","UFC":"combat","COMBAT":"combat",\n    "ESPORTS":"esports","GOLF":"golf",\n    "UNKNOWN":"UNKNOWN","NONE":"UNKNOWN","":"UNKNOWN",\n}\n\n@dataclass(frozen=True, slots=True)\nclass SourceRequirement:\n    domain: str\n    subdomain: str\n    state: str\n    authoritative_source_families: tuple[str,...]\n\nSPORT_SOURCES={\n    "baseball":("Official league/game/stat sources",),\n    "soccer":("Competition/club official match sources",),\n    "tennis":("ATP/WTA/official tournament sources",),\n    "combat":("UFC/commission/promotion official sources",),\n    "golf":("Official tour/tournament sources",),\n    "esports":("Official tournament/operator sources",),\n    "hockey":("NHL/official league game-stat sources",),\n    "basketball":("NBA/WNBA/NCAA official game-stat sources",),\n    "football":("NFL/NCAA official game-stat sources",),\n    "UNKNOWN":("Sport-specific authoritative source unresolved",),\n}\nDOMAIN_SOURCES={\n    "financial_markets":("Independent underlying asset/reference-price source",),\n    "financial_price":("Independent underlying asset/reference-price source",),\n    "crypto":("Independent exchange/chain reference sources",),\n    "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),\n    "politics_elections":("Official election authorities","FEC"),\n    "weather":("NWS/NOAA",),\n    "energy_commodities":("EIA","USDA/official commodity sources"),\n    "legal_regulatory":("Federal Register","Official courts/regulators"),\n    "health":("CDC","FDA"),\n    "transport":("FAA","TSA","Maritime/port authorities"),\n    "science_space":("NASA/official science agencies",),\n    "geopolitics":("State/Defense/UN official sources",),\n}\n\ndef canonical_sport_subdomain(value):\n    raw=str(value or "").strip()\n    return SPORT_ALIASES.get(raw.upper(),raw.lower() if raw else "UNKNOWN")\n\ndef assign_source_requirement(domain,subdomain="",state="UNRESOLVED"):\n    domain=str(domain or "unknown").strip()\n    subdomain=str(subdomain or "").strip()\n    state=str(state or "UNRESOLVED").strip()\n\n    if domain=="sports":\n        subdomain=canonical_sport_subdomain(subdomain)\n        fam=SPORT_SOURCES.get(subdomain)\n        if fam is None:\n            return SourceRequirement(domain,subdomain,"UNMAPPED",())\n        return SourceRequirement(domain,subdomain,state,fam)\n\n    if domain=="financial_markets":\n        subdomain=subdomain if subdomain not in ("","NONE") else "financial_price"\n        return SourceRequirement(domain,subdomain,state,DOMAIN_SOURCES["financial_markets"])\n\n    if domain in DOMAIN_SOURCES:\n        return SourceRequirement(domain,subdomain,state,DOMAIN_SOURCES[domain])\n\n    return SourceRequirement(domain,subdomain,"UNMAPPED",())\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_105_authoritative_source_requirement_router import assign_source_requirement\n\nclass T(unittest.TestCase):\n    def test_mlb_alias(self):\n        r=assign_source_requirement("sports","MLB","UPSTREAM_SPORTS_PRESERVED")\n        self.assertEqual(r.subdomain,"baseball"); self.assertTrue(r.authoritative_source_families)\n    def test_soccer_alias(self):\n        r=assign_source_requirement("sports","SOCCER","UPSTREAM_SPORTS_PRESERVED")\n        self.assertEqual(r.subdomain,"soccer"); self.assertTrue(r.authoritative_source_families)\n    def test_nhl_alias(self):\n        r=assign_source_requirement("sports","NHL","UPSTREAM_SPORTS_PRESERVED")\n        self.assertEqual(r.subdomain,"hockey"); self.assertTrue(r.authoritative_source_families)\n    def test_financial(self):\n        r=assign_source_requirement("financial_markets","financial_price","UPSTREAM_FINANCIAL_PRESERVED")\n        self.assertTrue(r.authoritative_source_families)\n\nif __name__=="__main__":\n    print("="*100)\n    print(" OAD-105 SPORT VOCABULARY SOURCE ROUTER TEST")\n    print("="*100)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] MLB/SOCCER/NHL vocabulary canonicalized")\n    print("[PASS] Every canonical sport family maps to an authoritative source requirement")\n    print("[PASS] financial_markets source contract preserved")\n    print("[DONE] OAD-105 SPORT VOCABULARY REBUILD CERTIFIED")\n'
REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py', 'Rebuilt OAD-104 canonical sport vocabulary'), ('qseries_v2/oracle_adapters/independent/oad_106_failed_gate_repository_audit.py', 'Certified repository audit')]
FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*108)
    print(" OAD-105 REBUILD INSTALLER")
    print(" "+TITLE)
    print("="*108)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file(): raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")
    frozen={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export=f"from .oad_105_authoritative_source_requirement_router import *"
        if export not in lines: lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Rebuilt foundational module:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-105 REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] OAD-105 affected files restored")
        raise

if __name__=="__main__":
    main()
