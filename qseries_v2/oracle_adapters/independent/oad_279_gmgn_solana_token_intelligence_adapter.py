from __future__ import annotations
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
