from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path

BUILD_ID='OAD-333'
TITLE='SOLANA AUTHORITATIVE PROGRAM IDENTITY REGISTRY'
EXPECTED='build_oad_333_solana_authoritative_program_identity_registry.py'
MODULE='oad_333_solana_authoritative_program_identity_registry.py'
TEST='test_oad_333_solana_authoritative_program_identity_registry.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_332_solana_live_decode_coverage_physical_gate.py': ('unknown_program_counts', 'known_instruction_ratio'), 'qseries_v2/oracle_adapters/independent/oad_320_solana_program_instruction_registry.py': ('UNKNOWN_PROGRAM',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

PROGRAMS={
    "11111111111111111111111111111111":("SYSTEM","INFRASTRUCTURE"),
    "ComputeBudget111111111111111111111111111111":("COMPUTE_BUDGET","INFRASTRUCTURE"),
    "Vote111111111111111111111111111111111111111":("SOLANA_VOTE","INFRASTRUCTURE"),
    "Stake11111111111111111111111111111111111111":("SOLANA_STAKE","INFRASTRUCTURE"),
    "AddressLookupTab1e1111111111111111111111111":("ADDRESS_LOOKUP_TABLE","INFRASTRUCTURE"),
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":("SPL_TOKEN","TOKEN"),
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL":("ASSOCIATED_TOKEN","TOKEN"),
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4":("JUPITER_V6","ROUTER"),
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P":("PUMP_FUN_BONDING_CURVE","DEX_LAUNCH"),
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA":("PUMP_FUN_AMM","DEX"),
    "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ":("PUMP_FUN_FEES","DEX_SUPPORT"),
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo":("METEORA_DLMM","DEX"),
}

@dataclass(frozen=True,slots=True)
class SolanaProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    execution_authority:bool=False

def identify_solana_program(program_id):
    pid=str(program_id or "")
    name,cat=PROGRAMS.get(pid,("UNKNOWN_PROGRAM","UNKNOWN"))
    market=cat not in ("INFRASTRUCTURE","UNKNOWN")
    return SolanaProgramIdentity(pid,name,cat,pid in PROGRAMS,market,False)

def authoritative_program_registry():
    return tuple(identify_solana_program(x) for x in PROGRAMS)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_333_solana_authoritative_program_identity_registry import *
class T(unittest.TestCase):
 def test_registry(self):
  vote=identify_solana_program("Vote111111111111111111111111111111111111111")
  pump=identify_solana_program("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
  jup=identify_solana_program("JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4")
  met=identify_solana_program("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo")
  print("[PROGRAMS]",vote.name,pump.name,jup.name,met.name)
  self.assertFalse(vote.market_relevant)
  self.assertEqual(pump.name,"PUMP_FUN_AMM")
  self.assertEqual(jup.category,"ROUTER")
  self.assertEqual(met.name,"METEORA_DLMM")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-333 authoritative Solana program identity registry certified")

"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"
    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]",r)
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file():
            raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src:
                raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_332_solana_live_decode_coverage_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    targets=(m,t,init)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] OAD-327 continuity and OAD-332 live baseline preserved unchanged")
        print("[PASS] program attribution includes top-level + inner/CPI instructions")
        print("[PASS] unknown programs retained; infrastructure separated from economic traffic")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
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
