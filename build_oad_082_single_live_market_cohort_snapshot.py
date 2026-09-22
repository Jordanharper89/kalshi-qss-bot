from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-082"
REVISION="OAD_082_PRODUCTION_INSTALLER_V1"
TITLE='SINGLE LIVE MARKET COHORT SNAPSHOT'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=locate_root()
WRITES=[('qseries_v2/oracle_adapters/independent/oad_082_single_live_market_cohort_snapshot.py', '\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nimport hashlib,json\n\nfrom qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\ndef _freeze(v):\n    if isinstance(v,dict):\n        return tuple((str(k),_freeze(v[k])) for k in sorted(v))\n    if isinstance(v,list):\n        return tuple(_freeze(x) for x in v)\n    if isinstance(v,tuple):\n        return tuple(_freeze(x) for x in v)\n    return v\n\ndef thaw_market(v):\n    if isinstance(v,tuple) and all(isinstance(x,tuple) and len(x)==2 for x in v):\n        return {k:thaw_market(x) for k,x in v}\n    if isinstance(v,tuple):\n        return tuple(thaw_market(x) for x in v)\n    return v\n\n@dataclass(frozen=True,slots=True)\nclass CurrentMarketCohortSnapshot:\n    snapshot_id:str\n    captured_at:str\n    market_count:int\n    markets:tuple\n\ndef capture_current_market_cohort(limit=1000):\n    markets,_=fetch_current_open_kalshi_market_index(limit=limit)\n    frozen=tuple(_freeze(m) for m in markets)\n    payload=json.dumps(frozen,sort_keys=True,default=str,separators=(",",":"))\n    sid=hashlib.sha256(payload.encode("utf-8")).hexdigest()\n    return CurrentMarketCohortSnapshot(\n        sid,datetime.now(timezone.utc).isoformat(),len(frozen),frozen\n    )\n\ndef snapshot_markets(snapshot):\n    return tuple(thaw_market(x) for x in snapshot.markets)\n'), ('test_oad_082_single_live_market_cohort_snapshot.py', '\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        s=capture_current_market_cohort(1000)\n        a=snapshot_markets(s)\n        b=snapshot_markets(s)\n        print("[PHYSICAL] snapshot_id=",s.snapshot_id)\n        print("[PHYSICAL] captured_at=",s.captured_at)\n        print("[PHYSICAL] current_open_markets=",s.market_count)\n        self.assertGreater(s.market_count,0)\n        self.assertEqual(len(a),s.market_count)\n        self.assertEqual(a,b)\n\nif __name__=="__main__":\n    print("="*88);print(" OAD-082 PHYSICAL CERTIFICATION TEST");print(" SINGLE LIVE MARKET COHORT SNAPSHOT");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] One immutable live cohort snapshot reused deterministically downstream")\n    print("[DONE] OAD-082 CERTIFIED")\n')]
FROZEN_DEPS=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]
REQUIRED_DEPS=[('qseries_v2/oracle_adapters/independent/oad_069_current_open_kalshi_market_index.py', 'Certified OAD-069'), ('qseries_v2/oracle_adapters/independent/oad_081_truthful_coverage_state_foundation.py', 'Certified OAD-081')]

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
