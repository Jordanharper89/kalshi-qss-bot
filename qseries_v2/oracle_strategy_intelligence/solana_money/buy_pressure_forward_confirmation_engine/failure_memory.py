from __future__ import annotations
import time
from pathlib import Path
from .persistence import read_json,write_json

WSOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
FORBIDDEN_ASSETS={WSOL,USDC}

LEGACY_NEGATIVE_TOKENS={
"4cDrSbA9mofmbMoupzyWxoygN3BTxqNfyBN583bepump","EVKGLpY3xNqp7fsCtVTv5G177FCShVrr7ryoU2k1Wyc5",
"9TdmrDoTNUCzHuuhMfdfDbATg6tTgenNHFpUCvAMpump","2A6MxU3bJ6EziBH4g3wH1Q8N9JNGZNarx4W1TJegadot",
"GFcaDvCXpgfsMMd9ciMd7YvgdqRsne29nVoj5ThQpump","7GUnr7krtQhJwd6ASY2VUprd9t4c64zcgCsjdmZepump",
"5a1CvpaxMtXN3bnWERo5WUo34tdQKUGSrFWd5DW73Qsx","7hMgPAo2NLwJN7rrRs9pBKaF8otoLzfQLunjmr2hpump",
"BcgpyBwFuVDgNivYmBUJAGpjfL3yWVqCmmSSUfDVpump","CgMTyUGeUhz7qsbxr46Uw2vjkEXioWEtJUoMcpgUpump",
# QSB-026 valid forward losses. The DATA_GAP_ABORT token is intentionally excluded.
"3znS89gifim2Hhhu8wjb2PfSgaCDdma187D5NMkDpump","FFNt4JythQsievkxudufGCfiHpEP8cef7r5QMunhpump",
"3K54D4aE9ewEEyo8ycJnuQFHqT3NnCq7PBtRpKhHCDME","5qfodizArUwfzWxnHqvaK45eVdzv1mj8L6QPY8gUpump",
}

class FailureMemory:
    def __init__(self,path:Path,clock=time.time):
        self.path=Path(path);self.clock=clock;self.data=read_json(self.path,{"tokens":{}})
    def blocked(self,token):
        if token in FORBIDDEN_ASSETS:return True,"FORBIDDEN_ASSET"
        if token in LEGACY_NEGATIVE_TOKENS:return True,"KNOWN_FAILED_SETUP_TOKEN"
        d=self.data.get("tokens",{}).get(token)
        if d and float(d.get("blocked_until") or 0)>self.clock():return True,"LOSS_QUARANTINE"
        return False,""
    def loss(self,token,pnl,reason,signal):
        d=self.data.setdefault("tokens",{}).setdefault(token,{"losses":0,"net":0.0})
        d["losses"]+=1;d["net"]+=float(pnl);d["last_reason"]=reason;d["last_signal"]=signal
        d["blocked_until"]=self.clock()+(24 if d["losses"]>=2 else 6)*3600
        return write_json(self.path,self.data)
