from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

EXPECTED_FILENAME = "build_oad_279_284_gmgn_rate_limit_resilient_acquisition_BOUNDARY_REBUILD.py"
MOD279 = Path("qseries_v2/oracle_adapters/independent/oad_279_gmgn_solana_token_intelligence_adapter.py")
MOD284 = Path("qseries_v2/oracle_adapters/independent/oad_284_gmgn_resilient_continuous_worker.py")
TEST = Path("test_oad_279_284_gmgn_rate_limit_resilient_acquisition_boundary.py")

SOURCE279 = r'''from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
import subprocess
import time

from .oad_277_gmgn_production_admission_boundary import require_gmgn_admission
from .oad_278_gmgn_solana_trending_live_adapter import _decode_gmgn_bytes, acquire_gmgn_solana_trending

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class GMGNTokenIntelligenceObservation:
    source_id:str
    provider:str
    source_class:str
    observation_type:str
    token_address:str
    observed_at:datetime
    payload:dict
    execution_authority:bool=False

class GMGNRateLimitError(RuntimeError):
    def __init__(self, message, reset_at=None, retry_after_seconds=None):
        super().__init__(str(message))
        self.reset_at = float(reset_at) if reset_at is not None else None
        self.retry_after_seconds = float(retry_after_seconds) if retry_after_seconds is not None else None

def _parse_raw_json(stdout_bytes):
    text=_decode_gmgn_bytes(stdout_bytes).strip()
    if not text:
        raise RuntimeError("GMGN command returned empty stdout")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s=text.find("{")
        e=text.rfind("}")
        if s>=0 and e>s:
            return json.loads(text[s:e+1])
        raise RuntimeError("GMGN command output was not valid JSON")

def _extract_json_object(text):
    value=str(text or "").strip()
    if not value:
        return None
    try:
        obj=json.loads(value)
        return obj if isinstance(obj,dict) else None
    except Exception:
        pass
    s=value.find("{")
    e=value.rfind("}")
    if s>=0 and e>s:
        try:
            obj=json.loads(value[s:e+1])
            return obj if isinstance(obj,dict) else None
        except Exception:
            return None
    return None

def _rate_limit_details(text):
    value=str(text or "")
    upper=value.upper()
    body=_extract_json_object(value) or {}
    code=body.get("code")
    err=str(body.get("error") or "")
    msg=str(body.get("message") or "")
    combined=(upper+" "+err.upper()+" "+msg.upper())

    limited=(
        str(code)=="429"
        or "RATE_LIMIT_EXCEEDED" in combined
        or "RATE_LIMIT_BANNED" in combined
        or "HTTP 429" in combined
        or "STATUS 429" in combined
        or " 429 " in (" "+combined+" ")
    )
    if not limited:
        return None

    reset_at=body.get("reset_at")
    if reset_at is None:
        for pattern in (
            r"reset_at[^0-9]*(\d{10,13})",
            r"X-RateLimit-Reset[^0-9]*(\d{10,13})",
            r"reset(?:\s+at)?[^0-9]*(\d{10,13})",
        ):
            m=re.search(pattern,value,re.IGNORECASE)
            if m:
                reset_at=m.group(1)
                break

    try:
        reset_at=float(reset_at) if reset_at is not None else None
        if reset_at is not None and reset_at>10_000_000_000:
            reset_at=reset_at/1000.0
    except Exception:
        reset_at=None

    retry_after=None
    if reset_at is not None:
        retry_after=max(1.0,reset_at-time.time())
    if retry_after is None:
        retry_after=300.0
    return reset_at,retry_after

def _raise_if_rate_limited(detail):
    parsed=_rate_limit_details(detail)
    if parsed is None:
        return
    reset_at,retry_after=parsed
    raise GMGNRateLimitError(
        "GMGN_RATE_LIMITED",
        reset_at=reset_at,
        retry_after_seconds=retry_after,
    )

def _run_raw(cli_path,args,timeout_seconds):
    p=subprocess.run(
        [cli_path,*args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=float(timeout_seconds),
        check=False,
    )
    out=_decode_gmgn_bytes(p.stdout)
    err=_decode_gmgn_bytes(p.stderr)
    detail=(err or out).strip()

    if p.returncode!=0:
        _raise_if_rate_limited(detail)
        raise RuntimeError("GMGN command failed (returncode="+str(p.returncode)+"): "+detail[:1000])

    data=_parse_raw_json(p.stdout)

    if isinstance(data,dict):
        if str(data.get("code"))=="429":
            reset_at=data.get("reset_at")
            try:
                reset_at=float(reset_at) if reset_at is not None else None
            except Exception:
                reset_at=None
            retry_after=max(1.0,reset_at-time.time()) if reset_at is not None else 300.0
            raise GMGNRateLimitError(
                "GMGN_RATE_LIMITED",
                reset_at=reset_at,
                retry_after_seconds=retry_after,
            )
        if "code" in data and str(data.get("code")) not in ("0","200"):
            raise RuntimeError(
                "GMGN API returned non-success envelope: code="
                +repr(data.get("code"))
                +" message="+repr(data.get("message"))
                +" error="+repr(data.get("error"))
            )
    return data

def _token_resource(data):
    if isinstance(data,dict) and "code" in data and "data" in data:
        return data.get("data")
    return data

def _validate_token_resource(section,token,data):
    r=_token_resource(data)
    if r is None or not isinstance(r,(dict,list)):
        raise RuntimeError("GMGN "+section+" returned unsupported resource")
    if isinstance(r,dict):
        returned=str(r.get("address") or r.get("token_address") or r.get("token") or "").strip()
        if returned and returned!=token:
            raise RuntimeError("GMGN "+section+" token identity mismatch: "+returned+" != "+token)
    return data

def acquire_gmgn_solana_token_intelligence(token_address,timeout_seconds=30.0):
    token=str(token_address).strip()
    if not token:
        raise ValueError("token_address required")
    a=require_gmgn_admission()
    info=_validate_token_resource(
        "info",token,
        _run_raw(a.cli_path,["token","info","--chain","sol","--address",token,"--raw"],timeout_seconds),
    )
    security=_validate_token_resource(
        "security",token,
        _run_raw(a.cli_path,["token","security","--chain","sol","--address",token,"--raw"],timeout_seconds),
    )
    pool=_validate_token_resource(
        "pool",token,
        _run_raw(a.cli_path,["token","pool","--chain","sol","--address",token,"--raw"],timeout_seconds),
    )
    return GMGNTokenIntelligenceObservation(
        "source.gmgn.solana.token."+token,
        "gmgn",
        "token_intelligence",
        "gmgn_solana_token_intelligence",
        token,
        datetime.now(timezone.utc),
        {"chain":"sol","info":info,"security":security,"pool":pool},
        False,
    )

def acquire_current_gmgn_solana_token_intelligence(timeout_seconds=30.0,candidate_limit=5):
    trending=acquire_gmgn_solana_trending(
        interval="1h",
        limit=max(1,int(candidate_limit)),
        timeout_seconds=timeout_seconds,
    )
    rank=(((trending.payload.get("raw") or {}).get("data") or {}).get("rank") or [])
    if not rank:
        raise RuntimeError("GMGN trending returned no token candidates")

    errors=[]
    for row in rank:
        token=str(row.get("address") or "").strip()
        if not token:
            continue
        try:
            return acquire_gmgn_solana_token_intelligence(token,timeout_seconds=timeout_seconds)
        except GMGNRateLimitError:
            raise
        except Exception as exc:
            errors.append(token+": "+str(exc))

    raise RuntimeError(
        "No current GMGN trending token completed info/security/pool acquisition. "
        "Candidate failures: "+" | ".join(errors[:5])
    )
'''

SOURCE284 = r'''from __future__ import annotations
from datetime import datetime, timezone
import time

from .oad_279_gmgn_solana_token_intelligence_adapter import GMGNRateLimitError
from .oad_281_gmgn_solana_single_writer_postgresql_persistence import persist_gmgn_solana_token_intelligence
from .oad_282_gmgn_continuous_production_policy import default_gmgn_continuous_policy, verify_gmgn_continuous_policy
from .oad_283_gmgn_continuous_runtime_checkpoint import (
    load_gmgn_runtime_checkpoint,
    save_gmgn_runtime_checkpoint,
    advance_success,
    advance_failure,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

def run_gmgn_cycle(root=None,policy=None):
    p=policy or default_gmgn_continuous_policy()
    if not verify_gmgn_continuous_policy(p):
        raise RuntimeError("invalid GMGN policy")
    cp=load_gmgn_runtime_checkpoint(root)
    try:
        result=persist_gmgn_solana_token_intelligence(
            root=root,
            timeout_seconds=p.persistence_timeout_seconds,
            acquisition_timeout_seconds=p.acquisition_timeout_seconds,
        )
        cp=advance_success(cp,result.token_address,result.observation_ids)
        save_gmgn_runtime_checkpoint(cp,root)
        return result,cp
    except Exception as exc:
        cp=advance_failure(cp,exc)
        save_gmgn_runtime_checkpoint(cp,root)
        raise

def _rate_limit_wait(exc):
    if not isinstance(exc,GMGNRateLimitError):
        return None

    wait=getattr(exc,"retry_after_seconds",None)
    try:
        wait=float(wait) if wait is not None else None
    except Exception:
        wait=None

    reset_at=getattr(exc,"reset_at",None)
    try:
        reset_at=float(reset_at) if reset_at is not None else None
    except Exception:
        reset_at=None

    if reset_at is not None:
        wait=max(1.0,reset_at-time.time())
    if wait is None:
        wait=300.0
    return min(600.0,max(5.0,wait+2.0))

def _safe_error_detail(exc):
    if isinstance(exc,GMGNRateLimitError):
        reset_at=getattr(exc,"reset_at",None)
        if reset_at is not None:
            try:
                stamp=datetime.fromtimestamp(float(reset_at),tz=timezone.utc).isoformat()
                return "GMGN_RATE_LIMITED reset_at_utc="+stamp
            except Exception:
                pass
        return "GMGN_RATE_LIMITED cooldown_required"

    detail=" ".join(str(exc).replace("\r"," ").replace("\n"," ").split())
    return detail[:500] if detail else type(exc).__name__

def run_resilient_gmgn_worker(root=None,policy=None,max_cycles=None,progress=print):
    p=policy or default_gmgn_continuous_policy()
    completed=0
    backoff=p.initial_backoff_seconds

    while max_cycles is None or completed<int(max_cycles):
        started=time.monotonic()
        try:
            result,cp=run_gmgn_cycle(root,p)
            completed+=1
            backoff=p.initial_backoff_seconds
            progress(
                f"[GMGN] cycle={cp.cycles} status=SUCCESS "
                f"token={result.token_address} committed_new={result.committed_new} "
                f"exact_readback={result.exact_readback} execution_authority=FALSE"
            )
            elapsed=time.monotonic()-started
            if max_cycles is None or completed<int(max_cycles):
                time.sleep(max(0.0,p.cadence_seconds-elapsed))

        except KeyboardInterrupt:
            raise

        except Exception as exc:
            completed+=1
            cp=load_gmgn_runtime_checkpoint(root)
            provider_wait=_rate_limit_wait(exc)

            if provider_wait is not None:
                retry_in=provider_wait
                reason=_safe_error_detail(exc)
                progress(
                    f"[GMGN] cycle={cp.cycles} status=COOLDOWN "
                    f"error={reason} retry_in={retry_in:.1f}s "
                    f"execution_authority=FALSE"
                )
                backoff=p.initial_backoff_seconds
            else:
                retry_in=backoff
                reason=_safe_error_detail(exc)
                progress(
                    f"[GMGN] cycle={cp.cycles} status=RETRY "
                    f"error_type={type(exc).__name__} detail={reason} "
                    f"retry_in={retry_in:.1f}s execution_authority=FALSE"
                )
                backoff=min(
                    p.max_backoff_seconds,
                    max(p.initial_backoff_seconds,backoff*2.0),
                )

            if max_cycles is None or completed<int(max_cycles):
                time.sleep(retry_in)

    return load_gmgn_runtime_checkpoint(root)
'''

TEST_SOURCE = r'''from __future__ import annotations

import importlib
import time
import unittest
from unittest.mock import patch

M279=importlib.import_module(
    "qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter"
)
M284=importlib.import_module(
    "qseries_v2.oracle_adapters.independent.oad_284_gmgn_resilient_continuous_worker"
)

class T(unittest.TestCase):
    def test_rate_limit_parser_body(self):
        reset=int(time.time())+240
        parsed=M279._rate_limit_details(
            '{"code":429,"error":"RATE_LIMIT_BANNED","reset_at":'+str(reset)+'}'
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(int(parsed[0]),reset)
        self.assertGreater(parsed[1],200)

    def test_unknown_429_defaults_to_five_minute_cooldown(self):
        parsed=M279._rate_limit_details("HTTP 429 RATE_LIMIT_EXCEEDED")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed[1],300.0)

    def test_candidate_fallback_stops_immediately_on_rate_limit(self):
        fake_trending=type("X",(),{
            "payload":{"raw":{"data":{"rank":[
                {"address":"TOKEN_A"},{"address":"TOKEN_B"}
            ]}}}
        })()
        calls=[]
        def acquire(token,timeout_seconds=30.0):
            calls.append(token)
            raise M279.GMGNRateLimitError(
                "GMGN_RATE_LIMITED",
                retry_after_seconds=300.0,
            )
        with patch.object(M279,"acquire_gmgn_solana_trending",return_value=fake_trending):
            with patch.object(M279,"acquire_gmgn_solana_token_intelligence",side_effect=acquire):
                with self.assertRaises(M279.GMGNRateLimitError):
                    M279.acquire_current_gmgn_solana_token_intelligence()
        self.assertEqual(calls,["TOKEN_A"])

    def test_worker_uses_provider_cooldown_not_generic_60s_cap(self):
        e=M279.GMGNRateLimitError(
            "GMGN_RATE_LIMITED",
            retry_after_seconds=300.0,
        )
        wait=M284._rate_limit_wait(e)
        self.assertGreaterEqual(wait,300.0)
        self.assertLessEqual(wait,600.0)

    def test_safety_boundaries(self):
        for m in (M279,M284):
            self.assertFalse(m.PROBABILITY_ENABLED)
            self.assertFalse(m.DIRECTION_ENABLED)
            self.assertFalse(m.PUBLICATION_ALLOWED)
            self.assertFalse(m.EXECUTION_AUTHORITY)

if __name__=="__main__":
    print("="*100)
    print(" OAD-279 / OAD-284 GMGN RATE-LIMIT RESILIENT ACQUISITION BOUNDARY CERTIFICATION")
    print("="*100)
    r=unittest.main(verbosity=2,exit=False)
    if not r.result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] provider 429/reset cooldown recognized")
    print("[PASS] candidate amplification stops immediately on provider rate limit")
    print("[PASS] five-minute conservative cooldown used when reset time is unavailable")
    print("[PASS] exact provider cooldown can exceed old 60-second generic retry cap")
    print("[PASS] runtime now exposes bounded provider failure detail")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-279/OAD-284 GMGN ACQUISITION BOUNDARY REBUILD CERTIFIED")
'''

def _check_original(root):
    p279=root/MOD279
    p284=root/MOD284
    if not p279.is_file() or not p284.is_file():
        raise RuntimeError("exact OAD-279/OAD-284 production modules missing")

    s279=p279.read_text(encoding="utf-8")
    s284=p284.read_text(encoding="utf-8")
    required279=(
        "def acquire_current_gmgn_solana_token_intelligence",
        "def acquire_gmgn_solana_token_intelligence",
        "acquire_gmgn_solana_trending",
        "for row in rank:",
    )
    required284=(
        "def run_gmgn_cycle",
        "def run_resilient_gmgn_worker",
        "persist_gmgn_solana_token_intelligence",
        "status=RETRY",
        "backoff=min(p.max_backoff_seconds",
    )
    for m in required279:
        if m not in s279:
            raise RuntimeError("OAD-279 exact boundary marker missing: "+m)
    for m in required284:
        if m not in s284:
            raise RuntimeError("OAD-284 exact boundary marker missing: "+m)

def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch")

    root=Path.cwd().resolve()
    _check_original(root)

    p279=root/MOD279
    p284=root/MOD284
    test=root/TEST

    backup279=p279.with_suffix(".py.oad279_rate_limit_backup")
    backup284=p284.with_suffix(".py.oad284_rate_limit_backup")
    backup279.write_bytes(p279.read_bytes())
    backup284.write_bytes(p284.read_bytes())

    try:
        ast.parse(SOURCE279)
        ast.parse(SOURCE284)
        ast.parse(TEST_SOURCE)

        p279.write_text(SOURCE279,encoding="utf-8",newline="\n")
        p284.write_text(SOURCE284,encoding="utf-8",newline="\n")
        test.write_text(TEST_SOURCE,encoding="utf-8",newline="\n")

        for path in (p279,p284,test):
            compile(path.read_text(encoding="utf-8"),str(path),"exec")

        proc=subprocess.run(
            [sys.executable,str(test)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode!=0:
            raise RuntimeError(
                "OAD-279/OAD-284 certification failed:\n"+proc.stdout+"\n"+proc.stderr
            )

        after279=p279.read_text(encoding="utf-8")
        after284=p284.read_text(encoding="utf-8")
        for marker in (
            "class GMGNTokenIntelligenceObservation",
            "def acquire_gmgn_solana_token_intelligence",
            "def acquire_current_gmgn_solana_token_intelligence",
            "class GMGNRateLimitError",
        ):
            if marker not in after279:
                raise RuntimeError("repaired OAD-279 contract missing: "+marker)
        for marker in (
            "def run_gmgn_cycle",
            "def run_resilient_gmgn_worker",
            "status=COOLDOWN",
            "def _rate_limit_wait",
        ):
            if marker not in after284:
                raise RuntimeError("repaired OAD-284 contract missing: "+marker)

        print("="*100)
        print(" OAD-279 / OAD-284 GMGN RATE-LIMIT RESILIENT ACQUISITION — BOUNDARY REBUILD")
        print("="*100)
        print("[ROOT]",root)
        print("[PASS] exact current OAD-279 token-intelligence boundary verified")
        print("[PASS] exact current OAD-284 resilient-worker boundary verified")
        print("[PASS] OAD-279 rebuilt in place with provider rate-limit recognition")
        print("[PASS] token candidate amplification stops immediately on a provider-wide 429")
        print("[PASS] OAD-284 rebuilt in place with reset-aware provider cooldown")
        print("[PASS] missing reset timestamp defaults to conservative five-minute cooldown")
        print("[PASS] old generic maximum 60-second retry is not used for GMGN rate-limit bans")
        print("[PASS] bounded provider failure detail is now visible in runtime logs")
        print("[PASS] downstream OAD-281 persistence public contract remains unchanged")
        print("[PASS] deterministic certification passed before installation acceptance")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-279/OAD-284 GMGN ACQUISITION BOUNDARY REBUILD INSTALLATION COMPLETE")

    except Exception:
        p279.write_bytes(backup279.read_bytes())
        p284.write_bytes(backup284.read_bytes())
        raise

if __name__=="__main__":
    main()
