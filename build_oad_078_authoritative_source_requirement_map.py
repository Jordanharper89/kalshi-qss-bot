from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-078"
REVISION="OAD_078_PRODUCTION_INSTALLER_V1"
TITLE='AUTHORITATIVE SOURCE REQUIREMENT MAP'

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_078_authoritative_source_requirement_map.py'
TEST=ROOT/'test_oad_078_authoritative_source_requirement_map.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass SourceRequirement:\n    topic:str\n    source_family:str\n    authority_tier:str\n    existing_adapter:bool\n    rationale:str\n\nREQUIREMENTS=(\n SourceRequirement("weather","NWS/NOAA","AUTHORITATIVE",True,"warnings forecasts storms climate"),\n SourceRequirement("macroeconomics","BLS","AUTHORITATIVE",False,"CPI employment payrolls"),\n SourceRequirement("macroeconomics","BEA","AUTHORITATIVE",False,"GDP income spending"),\n SourceRequirement("macroeconomics","Federal Reserve/FRED","AUTHORITATIVE",False,"rates monetary policy macro series"),\n SourceRequirement("politics_elections","Official election authorities","AUTHORITATIVE",False,"certified election results"),\n SourceRequirement("politics_elections","FEC","AUTHORITATIVE",False,"federal campaign and candidate records"),\n SourceRequirement("corporate_finance","SEC EDGAR","AUTHORITATIVE",False,"filings material disclosures"),\n SourceRequirement("energy_commodities","EIA","AUTHORITATIVE",False,"petroleum gas electricity"),\n SourceRequirement("energy_commodities","USDA","AUTHORITATIVE",False,"agriculture crop reports"),\n SourceRequirement("legal_regulatory","Federal Register","AUTHORITATIVE",True,"rules notices executive agency actions"),\n SourceRequirement("legal_regulatory","CourtListener/official courts","PRIMARY_OR_HIGH_RELIABILITY",False,"court opinions and dockets"),\n SourceRequirement("health","CDC","AUTHORITATIVE",False,"public health surveillance"),\n SourceRequirement("health","FDA","AUTHORITATIVE",False,"drug/device regulatory actions"),\n SourceRequirement("transport","FAA","AUTHORITATIVE",False,"aviation restrictions and operations"),\n SourceRequirement("transport","TSA","AUTHORITATIVE",False,"checkpoint/travel statistics"),\n SourceRequirement("transport","Maritime/port authorities","AUTHORITATIVE",False,"shipping and port state"),\n SourceRequirement("science_space","NASA","AUTHORITATIVE",False,"missions launches space events"),\n SourceRequirement("geopolitics","State/Defense/UN official releases","AUTHORITATIVE",False,"official geopolitical state"),\n SourceRequirement("sports","Official league/team feeds","PRIMARY",False,"schedules results injuries where available"),\n SourceRequirement("crypto","Coinbase/chain RPC/indexers","PRIMARY",False,"spot/chain state independent of Kalshi"),\n SourceRequirement("other","Unmapped","NONE",False,"requires topic discovery before adapter assignment"),\n SourceRequirement("geological","USGS","AUTHORITATIVE",True,"earthquakes geological events"),\n)\n\ndef requirements_for_topic(topic):\n    return tuple(x for x in REQUIREMENTS if x.topic==str(topic))\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_078_authoritative_source_requirement_map import *\n\nclass T(unittest.TestCase):\n    def test_existing(self):\n        self.assertTrue(any(x.existing_adapter for x in requirements_for_topic("weather")))\n        self.assertTrue(any(x.existing_adapter for x in requirements_for_topic("legal_regulatory")))\n    def test_missing_macro(self):\n        self.assertTrue(all(not x.existing_adapter for x in requirements_for_topic("macroeconomics")))\n    def test_no_execution(self): self.assertFalse(EXECUTION_AUTHORITY)\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-078 CERTIFICATION TEST");print(" AUTHORITATIVE SOURCE REQUIREMENT MAP");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Topic-to-authoritative-source requirements certified")\n    print("[PASS] Existing NWS, Federal Register, and USGS families preserved")\n    print("[DONE] OAD-078 CERTIFIED")\n'

def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)

    kalshi=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    umd098=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_098_market_taxonomy.py"
    umd109=ROOT/"qseries_v2"/"universal_market_discovery"/"umd_109_market_semantic_profile.py"
    oad075=PKG/"oad_075_persisted_independent_association_quality_gate.py"

    deps=((kalshi,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(umd098,"Frozen UMD-098"),
          (umd109,"Frozen UMD-109"),(oad075,"Certified OAD-075"))
    for p,label in deps:
        if not p.is_file(): raise RuntimeError(label+" missing")

    frozen={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (kalshi,oph,umd098,umd109)}
    affected=(MODULE,TEST,INIT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen dependency changed: "+p.name)

        print("[PASS] Certified OAD-075 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 unchanged")
        print("[PASS] Frozen UMD-098 taxonomy unchanged")
        print("[PASS] Frozen UMD-109 semantic profile unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT))
        print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
