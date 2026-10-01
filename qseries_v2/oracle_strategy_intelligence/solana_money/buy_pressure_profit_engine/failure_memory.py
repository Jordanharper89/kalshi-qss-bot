from __future__ import annotations
import time
from pathlib import Path
from .persistence import read_json,write_json

WSOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
FORBIDDEN_ASSETS={WSOL,USDC}

# Frozen from the user's QSB-024B forward run. These ten repeat-traded
# tokens were net-negative over >=3 closes and together accounted for
# roughly -$8.64 in the supplied loss log. They are not eligible for the
# next forward trial.
LEGACY_NEGATIVE_TOKENS={'BcgpyBwFuVDgNivYmBUJAGpjfL3yWVqCmmSSUfDVpump', '2A6MxU3bJ6EziBH4g3wH1Q8N9JNGZNarx4W1TJegadot', '9TdmrDoTNUCzHuuhMfdfDbATg6tTgenNHFpUCvAMpump', 'GFcaDvCXpgfsMMd9ciMd7YvgdqRsne29nVoj5ThQpump', 'EVKGLpY3xNqp7fsCtVTv5G177FCShVrr7ryoU2k1Wyc5', '7hMgPAo2NLwJN7rrRs9pBKaF8otoLzfQLunjmr2hpump', 'CgMTyUGeUhz7qsbxr46Uw2vjkEXioWEtJUoMcpgUpump', '4cDrSbA9mofmbMoupzyWxoygN3BTxqNfyBN583bepump', '7GUnr7krtQhJwd6ASY2VUprd9t4c64zcgCsjdmZepump', '5a1CvpaxMtXN3bnWERo5WUo34tdQKUGSrFWd5DW73Qsx'}

FAILURE_AUDIT={
    "source":"QSB-024B user forward log 2026-09-24",
    "incremental_closed":85,
    "incremental_wins":11,
    "incremental_losses":74,
    "incremental_net_usdc":-9.6613,
    "repeat_after_first_loss_trades":49,
    "repeat_after_first_loss_losses":42,
    "repeat_after_first_loss_wins":7,
    "repeat_after_first_loss_net_usdc":-7.862318,
    "invalid_quote_asset_closes":12,
    "invalid_quote_asset_net_usdc":0.247874,
    "stale_max_hold_closes":40,
    "stale_max_hold_net_usdc":-5.242973,
    "raw_score_pnl_correlation_valid_matched":0.027367294600308026,
}

class FailureMemory:
    def __init__(self,path:Path,clock=time.time):
        self.path=Path(path);self.clock=clock
        self.data=read_json(self.path,{"tokens":{},"invalid":{}})
    def blocked(self,token,market=""):
        if token in FORBIDDEN_ASSETS:return True,"FORBIDDEN_QUOTE_ASSET"
        if token in LEGACY_NEGATIVE_TOKENS:return True,"LEGACY_REPEAT_LOSER"
        d=self.data.get("tokens",{}).get(token)
        if d and float(d.get("blocked_until") or 0)>self.clock():
            return True,"LOSS_QUARANTINE"
        return False,""
    def record_loss(self,token,market,pnl,reason,signal=None):
        d=self.data.setdefault("tokens",{}).setdefault(token,{"losses":0,"net":0.0})
        d["losses"]=int(d.get("losses") or 0)+1
        d["net"]=float(d.get("net") or 0)+float(pnl)
        d["last_market"]=market;d["last_reason"]=reason;d["last_signal"]=signal or {}
        # One loss is enough to stop repeatedly paying friction into the same
        # failed setup. Two losses escalate to a full-day quarantine.
        hours=24 if d["losses"]>=2 else 6
        d["blocked_until"]=self.clock()+hours*3600
        self.save()
    def record_invalid(self,token,why):
        self.data.setdefault("invalid",{})[str(token)]={"why":why,"time":self.clock()}
        self.save()
    def save(self):
        return write_json(self.path,self.data)
