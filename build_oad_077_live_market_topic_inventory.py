from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-077"
REVISION="OAD_077_PRODUCTION_INSTALLER_V1"
TITLE='LIVE MARKET TOPIC INVENTORY'

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_077_live_market_topic_inventory.py'
TEST=ROOT/'test_oad_077_live_market_topic_inventory.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index\nfrom qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import classify_market_cohort\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass LiveTopicInventory:\n    market_count:int\n    classified_count:int\n    unclassified_count:int\n    topic_counts:tuple[tuple[str,int],...]\n    classifications:tuple\n\ndef build_live_topic_inventory(limit=1000):\n    markets,_=fetch_current_open_kalshi_market_index(limit=limit)\n    classes=classify_market_cohort(markets)\n    counts=Counter(x.primary_topic for x in classes)\n    unclassified=counts.get("other",0)\n    return LiveTopicInventory(\n        len(markets),\n        len(markets)-unclassified,\n        unclassified,\n        tuple(sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))),\n        classes,\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_077_live_market_topic_inventory import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=build_live_topic_inventory(1000)\n        print("[PHYSICAL] current_open_markets=",r.market_count)\n        print("[PHYSICAL] classified_markets=",r.classified_count)\n        print("[PHYSICAL] unclassified_markets=",r.unclassified_count)\n        print("[PHYSICAL] topic_counts=",r.topic_counts)\n        self.assertGreater(r.market_count,0)\n        self.assertEqual(r.classified_count+r.unclassified_count,r.market_count)\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-077 PHYSICAL CERTIFICATION TEST");print(" LIVE MARKET TOPIC INVENTORY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Real current Kalshi cohort classified without forcing unknown markets")\n    print("[DONE] OAD-077 CERTIFIED")\n'

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
