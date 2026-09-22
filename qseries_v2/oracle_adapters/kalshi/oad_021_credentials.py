from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
import os

OAD_021_BUILD_ID="OAD-021"
OAD_021_REVISION="OAD_021_PHYSICAL_KALSHI_CREDENTIAL_AUTH_LOADER_V1"

ENV_KEY_CANDIDATES=("KALSHI_API_KEY_ID","KALSHI_API_KEY","KALSHI_KEY_ID")
ENV_PRIVATE_KEY_PATH_CANDIDATES=("KALSHI_PRIVATE_KEY_PATH","KALSHI_PRIVATE_KEY_FILE")
ENV_PRIVATE_KEY_PEM_CANDIDATES=("KALSHI_PRIVATE_KEY_PEM",)

@dataclass(frozen=True)
class KalshiCredentialConfig:
    api_key_id:str
    private_key_pem:str
    source:str
    secret_persisted_by_adapter:bool=False

def _parse_dotenv(path):
    out={}
    p=Path(path)
    if not p.is_file(): return out
    for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        k,v=s.split("=",1)
        out[k.strip()]=v.strip().strip('"').strip("'")
    return out

def load_kalshi_credentials(root=None,environ=None):
    env=dict(os.environ if environ is None else environ)
    root=Path(root or Path.cwd())
    dotenv=_parse_dotenv(root/".env")
    merged=dict(dotenv); merged.update({k:v for k,v in env.items() if v is not None})
    key_id=next((merged.get(k,"").strip() for k in ENV_KEY_CANDIDATES if merged.get(k,"").strip()),"")
    pem=next((merged.get(k,"").strip() for k in ENV_PRIVATE_KEY_PEM_CANDIDATES if merged.get(k,"").strip()),"")
    source="environment"
    if not pem:
        key_path=next((merged.get(k,"").strip() for k in ENV_PRIVATE_KEY_PATH_CANDIDATES if merged.get(k,"").strip()),"")
        if key_path:
            p=Path(key_path)
            if not p.is_absolute(): p=root/p
            if not p.is_file(): raise FileNotFoundError("Configured Kalshi private key file not found")
            pem=p.read_text(encoding="utf-8")
            source="private_key_file"
    if not key_id or "PRIVATE KEY" not in pem:
        raise RuntimeError("Kalshi API credentials not configured. Set KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PATH (or KALSHI_PRIVATE_KEY_PEM).")
    return KalshiCredentialConfig(key_id,pem,source,False)

def redact_credential_config(cfg):
    return MappingProxyType({"api_key_id_present":bool(cfg.api_key_id),"private_key_present":bool(cfg.private_key_pem),
        "source":cfg.source,"secret_persisted_by_adapter":False})

def verify_oad_021_physical_kalshi_credential_auth_loader():
    fake={"KALSHI_API_KEY_ID":"abc","KALSHI_PRIVATE_KEY_PEM":"-----BEGIN PRIVATE KEY-----\\nX\\n-----END PRIVATE KEY-----"}
    c=load_kalshi_credentials(root=".",environ=fake)
    r=redact_credential_config(c)
    return c.api_key_id=="abc" and r["private_key_present"] and not r["secret_persisted_by_adapter"]
