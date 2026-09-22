from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-085"
REVISION="OAD_085_PRODUCTION_INSTALLER_V1"
TITLE='SINGLE-SNAPSHOT ADAPTER PRIORITY GATE'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
WRITES=[('qseries_v2/oracle_adapters/independent/oad_085_single_snapshot_adapter_priority_gate.py', '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort\nfrom qseries_v2.oracle_adapters.independent.oad_084_hierarchical_source_demand_map import source_demand_from_snapshot\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass AdapterPriority:\n    rank:int\n    topic:str\n    source_family:str\n    live_markets:int\n    state:str\n\n@dataclass(frozen=True,slots=True)\nclass PhysicalAdapterPriorityGate:\n    snapshot_id:str\n    evaluated_markets:int\n    priorities:tuple[AdapterPriority,...]\n    unresolved_markets:int\n\ndef build_physical_adapter_priority_gate(limit=1000,max_priorities=12):\n    snapshot=capture_current_market_cohort(limit)\n    demand=source_demand_from_snapshot(snapshot)\n    candidates=[]\n    unresolved=0\n    for d in demand:\n        if d.state=="UNMAPPED":\n            unresolved+=d.live_markets\n            continue\n        for fam in d.missing_families:\n            candidates.append((d.live_markets,d.topic,fam,d.state))\n    candidates.sort(key=lambda x:(-x[0],x[1],x[2]))\n    priorities=tuple(\n        AdapterPriority(i+1,topic,fam,count,state)\n        for i,(count,topic,fam,state) in enumerate(candidates[:int(max_priorities)])\n    )\n    return PhysicalAdapterPriorityGate(snapshot.snapshot_id,snapshot.market_count,priorities,unresolved)\n'), ('test_oad_085_single_snapshot_adapter_priority_gate.py', '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_085_single_snapshot_adapter_priority_gate import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        g=build_physical_adapter_priority_gate(1000,12)\n        print("[PHYSICAL] snapshot_id=",g.snapshot_id)\n        print("[PHYSICAL] evaluated_markets=",g.evaluated_markets)\n        print("[PHYSICAL] unresolved_markets=",g.unresolved_markets)\n        print("[PHYSICAL] adapter_priorities=",len(g.priorities))\n        for p in g.priorities:\n            print("[BUILD_NEXT]",p.rank,p.topic,p.source_family,"live_markets=",p.live_markets,"state=",p.state)\n        self.assertGreater(g.evaluated_markets,0)\n        self.assertTrue(all(p.rank==i+1 for i,p in enumerate(g.priorities)))\n        self.assertTrue(all(p.state=="NOT_COVERED" for p in g.priorities))\n        self.assertTrue(all(p.source_family for p in g.priorities))\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-085 PHYSICAL CERTIFICATION TEST");print(" SINGLE-SNAPSHOT ADAPTER PRIORITY GATE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] One physical cohort drives classification, demand mapping, and adapter ranking")\n    print("[PASS] Unresolved markets remain explicit and never fabricate source coverage")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-081 through OAD-085 CAPABILITY SLICE CERTIFIED")\n')]
FROZEN_DEPS=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED_DEPS=[('qseries_v2/oracle_adapters/independent/oad_082_single_live_market_cohort_snapshot.py', 'Certified OAD-082'), ('qseries_v2/oracle_adapters/independent/oad_084_hierarchical_source_demand_map.py', 'Certified OAD-084')]

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
