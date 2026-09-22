from __future__ import annotations
import hashlib, json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
from .oracle_terminal_intelligence_answer_generation import (
    OracleTerminalIntelligenceAnswerGenerationReport,
    OracleTerminalIntelligenceAnswerInvariantError,
    verify_terminal_intelligence_answer_generation_report,
)
SCHEMA_VERSION = "OIT-043"
ENGINE_ID = "OIT-043"
POLICY_ID = "oracle.bounded-multi-turn-intelligence-session-context.v1"
MAX_SESSION_TURNS = 32
MAX_SESSION_LINES = 2048
class OracleBoundedMultiTurnSessionInvariantError(OracleTerminalIntelligenceAnswerInvariantError): pass
@dataclass(frozen=True)
class OracleIntelligenceConversationTurn:
    turn_index:int; query:str; answer_id:str; answer_hash:str; answer_line_count:int
    source_answer_report_hash:str; source_projection_report_hash:str
    evidence_linked:bool; read_only:bool; turn_hash:str
@dataclass(frozen=True)
class OracleBoundedMultiTurnSessionContext:
    session_id:str; turns:tuple[OracleIntelligenceConversationTurn,...]; turn_count:int
    total_answer_line_count:int; latest_turn_index:int; bounded_turn_count:bool
    bounded_line_count:bool; deterministic_ordering_applied:bool
    complete_lineage_preserved:bool; volatile_memory_only:bool
    persistent_memory_enabled:bool; learning_enabled:bool; session_active:bool
    read_only:bool; context_hash:str
@dataclass(frozen=True)
class OracleBoundedMultiTurnSessionUpdateReport:
    schema_version:str; engine_id:str; policy_id:str; status:str; repository_root:str
    prior_session_context_hash:str|None; source_answer_report_hash:str
    updated_session_context:OracleBoundedMultiTurnSessionContext
    turn_appended:bool; session_continuation_ready:bool; volatile_memory_only:bool
    persistent_memory_enabled:bool; learning_update_performed:bool
    analytics_execution_performed:bool; database_access_performed:bool
    runtime_artifact_created:bool; runtime_artifact_modified:bool
    networking_performed:bool; publication_allowed:bool
    action_authorization_allowed:bool; qseries_execution_allowed:bool
    read_only:bool; failure_reason:str|None; report_hash:str

def _canonical(v:Any)->Any:
    if hasattr(v,"__dataclass_fields__"): return _canonical(asdict(v))
    if isinstance(v,Mapping): return {str(k):_canonical(x) for k,x in sorted(v.items(),key=lambda p:str(p[0]))}
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    if v is None or isinstance(v,(str,int,float,bool)): return v
    raise OracleBoundedMultiTurnSessionInvariantError(f"unsupported session value type: {type(v)}")
def _stable_hash(v:Any)->str:
    return hashlib.sha256(json.dumps(_canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def verify_conversation_turn(t):
    b=asdict(t); s=b.pop("turn_hash")
    if _stable_hash(b)!=s: raise OracleBoundedMultiTurnSessionInvariantError("conversation turn hash mismatch")
    if t.turn_index<0 or not t.query or not t.answer_id or not t.answer_hash or t.answer_line_count<=0: raise OracleBoundedMultiTurnSessionInvariantError("conversation turn identity invalid")
    if not t.source_answer_report_hash or not t.source_projection_report_hash or not t.evidence_linked or not t.read_only: raise OracleBoundedMultiTurnSessionInvariantError("conversation turn lineage invalid")
    return True
def verify_multi_turn_session_context(c):
    b=asdict(c); s=b.pop("context_hash")
    if _stable_hash(b)!=s: raise OracleBoundedMultiTurnSessionInvariantError("session context hash mismatch")
    if c.turn_count!=len(c.turns) or c.total_answer_line_count!=sum(t.answer_line_count for t in c.turns): raise OracleBoundedMultiTurnSessionInvariantError("session counts mismatch")
    for i,t in enumerate(c.turns):
        verify_conversation_turn(t)
        if t.turn_index!=i: raise OracleBoundedMultiTurnSessionInvariantError("turn ordering mismatch")
    if c.latest_turn_index!=len(c.turns)-1: raise OracleBoundedMultiTurnSessionInvariantError("latest turn mismatch")
    if c.bounded_turn_count!=(c.turn_count<=MAX_SESSION_TURNS) or c.bounded_line_count!=(c.total_answer_line_count<=MAX_SESSION_LINES): raise OracleBoundedMultiTurnSessionInvariantError("session bounds mismatch")
    if not c.deterministic_ordering_applied or not c.complete_lineage_preserved or not c.volatile_memory_only or c.persistent_memory_enabled or c.learning_enabled or not c.read_only: raise OracleBoundedMultiTurnSessionInvariantError("session boundary invalid")
    expected=bool(c.turns and c.bounded_turn_count and c.bounded_line_count)
    if c.session_active!=expected: raise OracleBoundedMultiTurnSessionInvariantError("session active mismatch")
    return True
def append_answer_to_bounded_multi_turn_session(repository_root,*,answer_report,prior_session_context=None):
    root=Path(repository_root).resolve(); verify_terminal_intelligence_answer_generation_report(answer_report)
    if not answer_report.answer_generated: raise OracleBoundedMultiTurnSessionInvariantError("answer unavailable")
    prior=() if prior_session_context is None else prior_session_context.turns
    prior_hash=None if prior_session_context is None else prior_session_context.context_hash
    if prior_session_context is not None: verify_multi_turn_session_context(prior_session_context)
    a=answer_report.answer; tb={"turn_index":len(prior),"query":a.query,"answer_id":a.answer_id,"answer_hash":a.answer_hash,"answer_line_count":a.answer_line_count,"source_answer_report_hash":answer_report.report_hash,"source_projection_report_hash":a.source_projection_report_hash,"evidence_linked":a.all_claims_evidence_linked,"read_only":True}
    turn=OracleIntelligenceConversationTurn(**tb,turn_hash=_stable_hash(tb)); verify_conversation_turn(turn)
    turns=prior+(turn,); lines=sum(t.answer_line_count for t in turns)
    if len(turns)>MAX_SESSION_TURNS or lines>MAX_SESSION_LINES: raise OracleBoundedMultiTurnSessionInvariantError("session limit exceeded")
    sid=prior_session_context.session_id if prior_session_context else _stable_hash({"root":str(root),"first":answer_report.report_hash})[:24]
    cb={"session_id":sid,"turns":turns,"turn_count":len(turns),"total_answer_line_count":lines,"latest_turn_index":len(turns)-1,"bounded_turn_count":True,"bounded_line_count":True,"deterministic_ordering_applied":True,"complete_lineage_preserved":True,"volatile_memory_only":True,"persistent_memory_enabled":False,"learning_enabled":False,"session_active":True,"read_only":True}
    context=OracleBoundedMultiTurnSessionContext(**cb,context_hash=_stable_hash(cb)); verify_multi_turn_session_context(context)
    rb={"schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"policy_id":POLICY_ID,"status":"certified_read_only","repository_root":str(root),"prior_session_context_hash":prior_hash,"source_answer_report_hash":answer_report.report_hash,"updated_session_context":context,"turn_appended":True,"session_continuation_ready":True,"volatile_memory_only":True,"persistent_memory_enabled":False,"learning_update_performed":False,"analytics_execution_performed":False,"database_access_performed":False,"runtime_artifact_created":False,"runtime_artifact_modified":False,"networking_performed":False,"publication_allowed":False,"action_authorization_allowed":False,"qseries_execution_allowed":False,"read_only":True,"failure_reason":None}
    report=OracleBoundedMultiTurnSessionUpdateReport(**rb,report_hash=_stable_hash(rb)); verify_bounded_multi_turn_session_update_report(report); return report
def verify_bounded_multi_turn_session_update_report(r):
    b=asdict(r); s=b.pop("report_hash")
    if _stable_hash(b)!=s: raise OracleBoundedMultiTurnSessionInvariantError("update report hash mismatch")
    if r.schema_version!=SCHEMA_VERSION or r.policy_id!=POLICY_ID: raise OracleBoundedMultiTurnSessionInvariantError("update report identity mismatch")
    verify_multi_turn_session_context(r.updated_session_context)
    if not r.read_only or not r.volatile_memory_only or r.persistent_memory_enabled or r.learning_update_performed or r.analytics_execution_performed or r.database_access_performed or r.runtime_artifact_created or r.runtime_artifact_modified or r.networking_performed or r.publication_allowed or r.action_authorization_allowed or r.qseries_execution_allowed: raise OracleBoundedMultiTurnSessionInvariantError("forbidden multi-turn capability enabled")
    if r.session_continuation_ready!=bool(r.turn_appended and r.updated_session_context.session_active): raise OracleBoundedMultiTurnSessionInvariantError("continuation readiness mismatch")
    return True
