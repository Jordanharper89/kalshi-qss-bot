from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-279"
REVISION="OAD_279_GMGN_SOLANA_TOKEN_INTELLIGENCE_ADAPTER_PHYSICAL_CERTIFICATION_V1"
EXPECTED_FILENAME="build_oad_279_gmgn_solana_token_intelligence_adapter_PHYSICAL_CERTIFICATION.py"
MODULE_NAME="oad_279_gmgn_solana_token_intelligence_adapter.py"
TEST_NAME="test_oad_279_gmgn_solana_token_intelligence_adapter.py"

MODULE_SOURCE=r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json, subprocess

from .oad_277_gmgn_production_admission_boundary import require_gmgn_admission
from .oad_278_gmgn_solana_trending_live_adapter import (
    _decode_gmgn_bytes,
    acquire_gmgn_solana_trending,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False


@dataclass(frozen=True, slots=True)
class GMGNTokenIntelligenceObservation:
    source_id: str
    provider: str
    source_class: str
    observation_type: str
    token_address: str
    observed_at: datetime
    payload: dict
    execution_authority: bool=False


def _run_raw(cli_path, args, timeout_seconds):
    p=subprocess.run(
        [cli_path,*args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=float(timeout_seconds),
        check=False,
    )
    out=_decode_gmgn_bytes(p.stdout)
    err=_decode_gmgn_bytes(p.stderr)
    if p.returncode!=0:
        raise RuntimeError("GMGN command failed: "+(err or out).strip()[:800])
    text=out.strip()
    try:
        data=json.loads(text)
    except json.JSONDecodeError:
        start=text.find("{"); end=text.rfind("}")
        if start<0 or end<=start:
            raise RuntimeError("GMGN command returned no valid JSON")
        data=json.loads(text[start:end+1])
    if not isinstance(data,dict) or data.get("code")!=0:
        raise RuntimeError("GMGN command returned non-success response")
    return data


def acquire_gmgn_solana_token_intelligence(token_address, timeout_seconds=30.0):
    token=str(token_address).strip()
    if not token:
        raise ValueError("token_address required")

    a=require_gmgn_admission()

    info=_run_raw(a.cli_path,["token","info","--chain","sol","--address",token,"--raw"],timeout_seconds)
    security=_run_raw(a.cli_path,["token","security","--chain","sol","--address",token,"--raw"],timeout_seconds)
    pool=_run_raw(a.cli_path,["token","pool","--chain","sol","--address",token,"--raw"],timeout_seconds)

    return GMGNTokenIntelligenceObservation(
        source_id="source.gmgn.solana.token."+token,
        provider="gmgn",
        source_class="token_intelligence",
        observation_type="gmgn_solana_token_intelligence",
        token_address=token,
        observed_at=datetime.now(timezone.utc),
        payload={"chain":"sol","info":info,"security":security,"pool":pool},
        execution_authority=False,
    )


def acquire_current_gmgn_solana_token_intelligence(timeout_seconds=30.0):
    trending=acquire_gmgn_solana_trending(interval="1h",limit=5,timeout_seconds=timeout_seconds)
    rank=((trending.payload.get("raw") or {}).get("data") or {}).get("rank") or []
    if not rank:
        raise RuntimeError("GMGN trending returned no token candidate")
    token=str(rank[0].get("address") or "").strip()
    if not token:
        raise RuntimeError("GMGN trending first token missing address")
    return acquire_gmgn_solana_token_intelligence(token,timeout_seconds=timeout_seconds)
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter import (
    EXECUTION_AUTHORITY,PUBLICATION_ALLOWED,PROBABILITY_ENABLED,DIRECTION_ENABLED,
    acquire_current_gmgn_solana_token_intelligence,
)

class T(unittest.TestCase):
    def test_physical_current_token_intelligence(self):
        r=acquire_current_gmgn_solana_token_intelligence()
        print("[PHYSICAL] token=",r.token_address)
        print("[PHYSICAL] provider=",r.provider)
        print("[PHYSICAL] sections=",tuple(r.payload.keys()))
        self.assertEqual(r.provider,"gmgn")
        self.assertTrue(r.token_address)
        self.assertEqual(r.payload.get("chain"),"sol")
        for key in ("info","security","pool"):
            self.assertIsInstance(r.payload.get(key),dict)
            self.assertEqual(r.payload[key].get("code"),0)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(PROBABILITY_ENABLED)
        self.assertFalse(DIRECTION_ENABLED)
        self.assertFalse(PUBLICATION_ALLOWED)
        self.assertFalse(EXECUTION_AUTHORITY)

if __name__=="__main__":
    print("="*120)
    print(" OAD-279 PHYSICAL CERTIFICATION TEST")
    print(" GMGN SOLANA TOKEN INTELLIGENCE")
    print("="*120)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] live GMGN token info/security/pool intelligence certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-279 PHYSICALLY CERTIFIED")
"""

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    s=textwrap.dedent(source).lstrip(); ast.parse(s,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,path)

def main():
    if Path(__file__).name!=EXPECTED_FILENAME: raise RuntimeError("installer identity mismatch")
    root=locate_root(); pkg=root/"qseries_v2"/"oracle_adapters"/"independent"; module=pkg/MODULE_NAME; test=root/TEST_NAME; init=pkg/"__init__.py"
    print("="*120); print(" OAD-279 GMGN SOLANA TOKEN INTELLIGENCE ADAPTER — PHYSICAL CERTIFICATION INSTALLER"); print("="*120); print("[BOOT] Revision:",REVISION); print("[ROOT]",root)
    for rel,symbol in (
        ("qseries_v2/oracle_adapters/independent/oad_277_gmgn_production_admission_boundary.py","require_gmgn_admission"),
        ("qseries_v2/oracle_adapters/independent/oad_278_gmgn_solana_trending_live_adapter.py","acquire_gmgn_solana_trending"),
    ):
        p=root/rel
        if not p.is_file() or ("def "+symbol+"(") not in p.read_text(encoding="utf-8"): raise RuntimeError("dependency missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE); write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] OAD-279 installed")
        print("[PASS] physical test selects a current live GMGN Solana token")
        print("[PASS] token info/security/pool acquisition wired")
        print("[PASS] GMGN remains observation-only")
        print("[DONE] OAD-279 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] OAD-279 restored")
        raise

if __name__=="__main__": main()
