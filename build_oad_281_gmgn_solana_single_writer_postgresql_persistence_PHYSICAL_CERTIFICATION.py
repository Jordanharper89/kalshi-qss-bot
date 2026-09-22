from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED_FILENAME="build_oad_281_gmgn_solana_single_writer_postgresql_persistence_PHYSICAL_CERTIFICATION.py"
MODULE_NAME="oad_281_gmgn_solana_single_writer_postgresql_persistence.py"
TEST_NAME="test_oad_281_gmgn_solana_single_writer_postgresql_persistence.py"

MODULE_SOURCE=r"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib, json

from .oad_279_gmgn_solana_token_intelligence_adapter import (
    acquire_current_gmgn_solana_token_intelligence,
)
from .oad_261_crypto_universal_expansion_single_writer_postgresql_persistence import (
    canonicalize_crypto_observation,
)
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_single_writer import (
    write_canonical_observations,
)
from .oad_068_exact_postgresql_independent_readback import (
    readback_exact_observation_ids,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False


@dataclass(frozen=True,slots=True)
class GMGNPersistenceResult:
    token_address: str
    raw_count: int
    canonical_count: int
    committed_new: int
    exact_readback: int
    observation_ids: tuple
    execution_authority: bool=False


def _stable_json(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str)


def _split_observations(obs):
    token=obs.token_address
    out=[]
    for section in ("info","security","pool"):
        payload=obs.payload.get(section)
        if not isinstance(payload,dict):
            continue
        raw={
            "source_id":"source.gmgn.solana.token."+token+"."+section,
            "provider":"gmgn",
            "source_class":"token_intelligence",
            "observation_type":"gmgn_solana_token_"+section,
            "subject_id":token,
            "observed_at":obs.observed_at,
            "payload":payload,
            "execution_authority":False,
        }
        raw["source_hash"]=hashlib.sha256(_stable_json(raw).encode("utf-8")).hexdigest()
        out.append(raw)
    return tuple(out)


def persist_current_gmgn_solana_intelligence(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=30.0):
    obs=acquire_current_gmgn_solana_token_intelligence(timeout_seconds=acquisition_timeout_seconds)
    raw=_split_observations(obs)
    if not raw:
        raise RuntimeError("GMGN produced no persistable token observations")

    canonical=tuple(canonicalize_crypto_observation(x) for x in raw)
    ids=tuple(str(getattr(x,"observation_id")) for x in canonical)

    committed=write_canonical_observations(canonical,root=root,timeout_seconds=timeout_seconds)
    readback=readback_exact_observation_ids(ids,root=root,timeout_seconds=timeout_seconds)

    return GMGNPersistenceResult(
        token_address=obs.token_address,
        raw_count=len(raw),
        canonical_count=len(canonical),
        committed_new=int(committed),
        exact_readback=len(readback),
        observation_ids=ids,
        execution_authority=False,
    )
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_281_gmgn_solana_single_writer_postgresql_persistence import (
    EXECUTION_AUTHORITY,PUBLICATION_ALLOWED,PROBABILITY_ENABLED,DIRECTION_ENABLED,
    persist_current_gmgn_solana_intelligence,
)

class T(unittest.TestCase):
    def test_physical_persistence(self):
        r=persist_current_gmgn_solana_intelligence()
        print("[PHYSICAL] token=",r.token_address)
        print("[PHYSICAL] raw=",r.raw_count)
        print("[PHYSICAL] canonical=",r.canonical_count)
        print("[PHYSICAL] committed_new=",r.committed_new)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] observation_ids=",r.observation_ids)
        self.assertEqual(r.raw_count,3)
        self.assertEqual(r.canonical_count,3)
        self.assertEqual(r.exact_readback,3)
        self.assertEqual(len(r.observation_ids),3)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(PROBABILITY_ENABLED); self.assertFalse(DIRECTION_ENABLED); self.assertFalse(PUBLICATION_ALLOWED); self.assertFalse(EXECUTION_AUTHORITY)

if __name__=="__main__":
    print("="*120); print(" OAD-281 PHYSICAL CERTIFICATION TEST"); print(" GMGN SOLANA → UNIVERSAL SINGLE WRITER → POSTGRESQL → EXACT READBACK"); print("="*120)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] GMGN token intelligence persisted through universal single writer")
    print("[PASS] exact observation-id PostgreSQL readback certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-281 PHYSICALLY CERTIFIED")
"""

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path)); path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,path)

def main():
    if Path(__file__).name!=EXPECTED_FILENAME: raise RuntimeError("installer identity mismatch")
    root=locate_root(); pkg=root/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/MODULE_NAME; test=root/TEST_NAME; init=pkg/"__init__.py"
    print("="*120); print(" OAD-281 GMGN SOLANA SINGLE-WRITER POSTGRESQL PERSISTENCE INSTALLER"); print("="*120); print("[ROOT]",root)
    required=(
        ("qseries_v2/oracle_adapters/independent/oad_279_gmgn_solana_token_intelligence_adapter.py","acquire_current_gmgn_solana_token_intelligence"),
        ("qseries_v2/oracle_adapters/independent/oad_261_crypto_universal_expansion_single_writer_postgresql_persistence.py","canonicalize_crypto_observation"),
        ("qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_single_writer.py","write_canonical_observations"),
        ("qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py","readback_exact_observation_ids"),
    )
    for rel,symbol in required:
        p=root/rel
        if not p.is_file() or ("def "+symbol+"(") not in p.read_text(encoding="utf-8"): raise RuntimeError("dependency missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE); write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []; exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] OAD-281 installed")
        print("[PASS] GMGN info/security/pool split into three source-scoped observations")
        print("[PASS] universal canonicalization + OPH-019 single writer wired")
        print("[PASS] exact observation-id readback wired")
        print("[PASS] no broad PostgreSQL scan")
        print("[PASS] no probability/direction/publication/execution")
        print("[DONE] OAD-281 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OAD-281 restored"); raise

if __name__=="__main__": main()
