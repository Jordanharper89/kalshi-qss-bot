from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))

def put(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*118)
    print(' OSN-057 MLB UNIFIED SPORTS BOUNDARY RECONCILIATION INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    put('qseries_v2/oracle_source_network/certification/mlb_unified_boundary_reconciliation.py','\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nROOT=Path.cwd()\nPROVIDER_DIR=ROOT/"qseries_v2/oracle_source_network/providers"\nACQ_DIR=ROOT/"qseries_v2/oracle_source_network/acquisition"\n\n@dataclass(frozen=True)\nclass MLBReconciliation:\n    provider_files:tuple\n    acquisition_files:tuple\n    canonical_contract_present:bool\n    admitted_boundary:bool\n    reason:str\n    execution_authority:bool=False\n\ndef _matching(directory):\n    out=[]\n    if directory.exists():\n        for p in directory.glob("*.py"):\n            try:\n                text=p.read_text(encoding="utf-8",errors="ignore").lower()\n            except OSError:\n                continue\n            if "mlb" in text and ("statsapi" in text or "major league baseball" in text or "mlb" in p.name.lower()):\n                out.append(str(p.relative_to(ROOT)))\n    return tuple(sorted(out))\n\ndef reconcile():\n    providers=_matching(PROVIDER_DIR)\n    acquisitions=_matching(ACQ_DIR)\n    canon=(ROOT/"qseries_v2/oracle_source_network/canonical/sports_event_v2.py").exists()\n    admitted=bool(providers and acquisitions and canon)\n    return MLBReconciliation(\n        providers,acquisitions,canon,admitted,\n        "existing MLB OSN provider/acquisition pavement discovered and reusable"\n        if admitted else\n        "MLB OSN provider/acquisition pavement not both physically located; no synthetic admission",\n    )\n')
    put('test_osn_057_mlb_unified_sports_boundary_reconciliation.py','\nfrom qseries_v2.oracle_source_network.certification.mlb_unified_boundary_reconciliation import reconcile\nr=reconcile()\nprint("[MLB_RECONCILIATION]",r)\nassert r.execution_authority is False\nassert r.canonical_contract_present is True\nif r.admitted_boundary:\n    print("[PASS] existing MLB OSN provider + acquisition pavement located")\nelse:\n    print("[HOLD] MLB remains outside unified admission until both existing OSN paths are located")\nprint("[PASS] OSN-057 MLB reconciliation truth gate certified")\n')
    print('[PASS] shallow OSN-only MLB pavement discovery installed')
    print('[PASS] no duplicate MLB adapter created')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
