
from dataclasses import dataclass
from pathlib import Path

ROOT=Path.cwd()
PROVIDER_DIR=ROOT/"qseries_v2/oracle_source_network/providers"
ACQ_DIR=ROOT/"qseries_v2/oracle_source_network/acquisition"

@dataclass(frozen=True)
class MLBReconciliation:
    provider_files:tuple
    acquisition_files:tuple
    canonical_contract_present:bool
    admitted_boundary:bool
    reason:str
    execution_authority:bool=False

def _matching(directory):
    out=[]
    if directory.exists():
        for p in directory.glob("*.py"):
            try:
                text=p.read_text(encoding="utf-8",errors="ignore").lower()
            except OSError:
                continue
            if "mlb" in text and ("statsapi" in text or "major league baseball" in text or "mlb" in p.name.lower()):
                out.append(str(p.relative_to(ROOT)))
    return tuple(sorted(out))

def reconcile():
    providers=_matching(PROVIDER_DIR)
    acquisitions=_matching(ACQ_DIR)
    canon=(ROOT/"qseries_v2/oracle_source_network/canonical/sports_event_v2.py").exists()
    admitted=bool(providers and acquisitions and canon)
    return MLBReconciliation(
        providers,acquisitions,canon,admitted,
        "existing MLB OSN provider/acquisition pavement discovered and reusable"
        if admitted else
        "MLB OSN provider/acquisition pavement not both physically located; no synthetic admission",
    )
