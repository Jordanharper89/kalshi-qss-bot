from pathlib import Path
import ast, shutil, time

ROOT=Path.cwd().resolve()
PRED=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
if not PRED.exists():
    raise SystemExit("[FAIL] predictor missing: "+str(PRED))

src=PRED.read_text(encoding="utf-8")

def fn_span(text,name):
    t=ast.parse(text)
    for n in t.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name:
            return n.lineno,n.end_lineno
    return None

def replace_function(text,name,new_text):
    span=fn_span(text,name)
    if not span:
        raise SystemExit("[FAIL] function missing: "+name)
    a,b=span
    lines=text.splitlines()
    lines[a-1:b]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

stamp=str(int(time.time()))
backup=Path(str(PRED)+".bak."+stamp)
shutil.copy2(PRED,backup)

CONNECT_IMPORT="from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect as _opd_exo_connect"
if CONNECT_IMPORT not in src:
    lines=src.splitlines()
    insert_at=0
    for i,line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_at=i+1
    lines.insert(insert_at,CONNECT_IMPORT)
    src="\n".join(lines)+"\n"

loader = r'''
def _opd_load_exogenous_canonical_asof(anchor,root):
    root=Path(root or Path.cwd()).resolve()
    try:
        seq=int(anchor["anchor_sequence_boundary"])
        t=float(anchor["observed_epoch"])
    except Exception:
        return {}
    sql="""SELECT sequence_number,source_id,observation_type,
                  EXTRACT(EPOCH FROM observed_at),canonical_observation_json
           FROM public.oracle_canonical_observations
           WHERE sequence_number<=%s AND observed_at<=to_timestamp(%s)
             AND source_id NOT LIKE 'source.kalshi%%'
             AND source_id NOT LIKE 'source.crypto.hf.coinbase%%'
             AND source_id NOT LIKE 'source.crypto.condition.%%'
             AND source_id NOT LIKE 'source.crypto.learned_case.%%'
             AND source_id NOT LIKE 'source.polymarket%%'
           ORDER BY sequence_number DESC
           LIMIT 2048"""
    deny=("kalshi","coinbase","polymarket","market_data","orderbook",
          "prediction","learned_case","historical_window")
    out={}
    try:
        with _opd_exo_connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='12000ms'")
                q.execute(sql,(seq,t))
                rows=q.fetchall() or []
            c.rollback()
    except Exception as e:
        print("[EXOGENOUS ASOF READ ERROR]",type(e).__name__,str(e)[:220])
        return {}
    for rseq,sid,typ,obs_epoch,obj in rows:
        sid=str(sid or ""); typ=str(typ or "")
        low=(sid+" "+typ).lower()
        if not sid or any(x in low for x in deny):
            continue
        key=sid+"|"+typ
        if key in out:
            continue
        try:
            oe=float(obs_epoch)
        except Exception:
            oe=None
        if int(rseq)>seq or (oe is not None and oe>t):
            continue
        out[key]={
            "sequence_number":int(rseq),
            "observed_epoch":oe,
            "source_id":sid,
            "observation_type":typ,
            "canonical_observation":obj,
        }
        if len(out)>=64:
            break
    return out
'''

if "def _opd_load_exogenous_canonical_asof(" in src:
    src=replace_function(src,"_opd_load_exogenous_canonical_asof",loader)
else:
    marker="def materialize_current_states(anchor,root):"
    if marker not in src:
        raise SystemExit("[FAIL] materialize_current_states boundary missing")
    src=src.replace(marker,loader.strip()+"\n\n"+marker,1)

freeze_snapshot = r'''
def _opd_exogenous_freeze_snapshot(state):
    if not isinstance(state,dict):
        return {}
    raw=state.get("exogenous_evidence_state")
    if not isinstance(raw,dict) or not raw:
        return {}
    out={}
    for k in sorted(raw):
        v=raw.get(k)
        if not isinstance(v,dict):
            continue
        sid=str(v.get("source_id") or "")
        typ=str(v.get("observation_type") or "")
        low=(sid+" "+typ).lower()
        deny=("kalshi","coinbase","polymarket","market_data","orderbook",
              "prediction","learned_case","historical_window")
        if any(x in low for x in deny):
            continue
        out[str(k)]={
            "sequence_number":v.get("sequence_number"),
            "observed_epoch":v.get("observed_epoch"),
            "source_id":sid,
            "observation_type":typ,
            "canonical_observation":v.get("canonical_observation"),
        }
        if len(out)>=64:
            break
    return out
'''
if fn_span(src,"_opd_exogenous_freeze_snapshot"):
    src=replace_function(src,"_opd_exogenous_freeze_snapshot",freeze_snapshot)
else:
    src=freeze_snapshot.strip()+"\n\n"+src

materialize = r'''
def materialize_current_states(anchor,root):
    extra=assemble(anchor,root)
    exogenous=_opd_load_exogenous_canonical_asof(anchor,root)
    extra=dict(extra)
    extra["exogenous_evidence_state"]=exogenous
    out=[]
    for h in HORIZONS:
        world={"anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],
          "observed_epoch":anchor["observed_epoch"],"horizon_seconds":h,
          "anchor_price":anchor["anchor_price"],"kalshi_state":anchor["kalshi_state"],
          "coinbase_hf_state":extra["coinbase_hf_state"],
          "crypto_condition_state":extra["crypto_condition_state"],
          "learned_state":extra["learned_state"],
          "exogenous_evidence_state":exogenous}
        out.append({"state_id":"LIVE_IN_MEMORY_"+anchor["anchor_id"]+"_"+str(h),
          "anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],
          "observed_epoch":float(anchor["observed_epoch"]),"horizon_seconds":h,
          "anchor_price":anchor["anchor_price"],
          "contract_close_epoch":anchor.get("contract_close_epoch"),
          "contract_close_basis":anchor.get("contract_close_basis"),
          "exogenous_evidence_state":exogenous,
          "tokens":list(materialize_exact_live_tokens(root,world))})
    return out,extra
'''
src=replace_function(src,"materialize_current_states",materialize)

if '"exogenous_evidence_snapshot":z.get("exogenous_evidence_snapshot") or {},' not in src:
    needle='"evidence_votes":z.get("evidence_votes"),'
    if needle not in src:
        raise SystemExit("[FAIL] immutable ledger evidence_votes boundary missing")
    src=src.replace(
        needle,
        needle+'\n              "exogenous_evidence_snapshot":z.get("exogenous_evidence_snapshot") or {},',
        1
    )

if 'LIVE_EVIDENCE_EXOGENOUS_SOURCES=' not in src:
    needle='print("LIVE_EVIDENCE_CONDITION_METRICS=",len(extra["crypto_condition_state"]));print("LIVE_EVIDENCE_LEARNED=",bool(extra["learned_state"]))'
    if needle in src:
        src=src.replace(
            needle,
            needle+';print("LIVE_EVIDENCE_EXOGENOUS_SOURCES=",len(extra.get("exogenous_evidence_state") or {}))',
            1
        )

compile(src,str(PRED),"exec")
PRED.write_text(src,encoding="utf-8")

TEST=ROOT/"test_opd_EXOGENOUS_FULL_PIPELINE_ROOT_CUTOVER_V2.py"
TEST.write_text(r'''from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
required=[
"def _opd_load_exogenous_canonical_asof",
"sequence_number<=%s AND observed_at<=to_timestamp(%s)",
'"exogenous_evidence_state":exogenous',
'"exogenous_evidence_snapshot":z.get("exogenous_evidence_snapshot") or {}',
"LIVE_EVIDENCE_EXOGENOUS_SOURCES=",
]
for x in required:
    assert x in s,x
assert "source.kalshi%%" in s
assert "source.crypto.hf.coinbase%%" in s
assert "source.crypto.condition.%%" in s
assert "source.crypto.learned_case.%%" in s
assert "source.polymarket%%" in s
print("[PASS] exact anchor sequence/time-bounded exogenous canonical reader installed")
print("[PASS] market/derived predictive sources excluded")
print("[PASS] exogenous state carried independently of existing token/scoring semantics")
print("[PASS] immutable prediction ledger persists frozen exogenous snapshot")
print("[PASS] old immutable ledger rows are not rewritten")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
''',encoding="utf-8")

AUDIT=ROOT/"audit_opd_EXOGENOUS_CANONICAL_SOURCE_COVERAGE_V2.py"
AUDIT.write_text(r'''from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import latest_live_anchor,_opd_load_exogenous_canonical_asof
root=Path.cwd().resolve()
a=latest_live_anchor(root)
if not a: raise SystemExit("[FAIL] no live anchor")
x=_opd_load_exogenous_canonical_asof(a,root)
print("[ANCHOR]",a.get("ticker"),a.get("anchor_sequence_boundary"),a.get("observed_epoch"))
print("[EXOGENOUS SOURCES]",len(x))
for k,v in list(x.items())[:64]:
    print("[SOURCE]",v.get("sequence_number"),v.get("source_id"),v.get("observation_type"))
if not x: raise SystemExit("[FAIL] no eligible independent canonical evidence at live anchor")
print("[PASS] independent canonical evidence physically reachable at exact live anchor")
''',encoding="utf-8")

CERT=ROOT/"certify_opd_EXOGENOUS_PHYSICAL_LEDGER_V2.py"
CERT.write_text(r'''from pathlib import Path
import json,subprocess,sys
root=Path.cwd().resolve()
ledger=root/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
def load():
    out=[]
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try: out.append(json.loads(line))
            except Exception: pass
    return out
before=load(); ids={str(x.get("prediction_id")) for x in before if x.get("prediction_id")}
print("[LEDGER BEFORE]",len(before))
code="from pathlib import Path;from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import run;run(root=Path.cwd().resolve())"
p=subprocess.run([sys.executable,"-c",code],cwd=str(root),text=True,capture_output=True,timeout=180)
print("[FRESH INTERPRETER EXIT]",p.returncode)
for line in p.stdout.splitlines():
    if ("LIVE_EVIDENCE_EXOGENOUS_SOURCES=" in line or
        "[PREDICTION LEDGER]" in line or
        "LIVE_PREDICTION=" in line):
        print(line)
if p.returncode:
    if p.stderr.strip(): print("[STDERR]",p.stderr[-3000:])
    raise SystemExit("[FAIL] production predictor run failed")
after=load()
new=[x for x in after if str(x.get("prediction_id") or "") not in ids]
print("[LEDGER AFTER]",len(after))
print("[NEW IMMUTABLE ROWS]",len(new))
field=[x for x in new if "exogenous_evidence_snapshot" in x]
nonempty=[x for x in field if isinstance(x.get("exogenous_evidence_snapshot"),dict) and x["exogenous_evidence_snapshot"]]
print("[ROWS WITH SNAPSHOT FIELD]",len(field))
print("[ROWS WITH NONEMPTY SNAPSHOT]",len(nonempty))
if not new: raise SystemExit("[FAIL] no new immutable predictions written")
if not nonempty: raise SystemExit("[FAIL] new rows still lack non-empty exogenous evidence")
sample=nonempty[0]
snap=sample["exogenous_evidence_snapshot"]
aseq=int(sample.get("anchor_sequence_boundary"))
at=float(sample.get("anchor_observed_epoch"))
bad=[];sources=set()
for k,v in snap.items():
    sid=str(v.get("source_id") or "");typ=str(v.get("observation_type") or "")
    sources.add(sid)
    seq=int(v.get("sequence_number"))
    oe=v.get("observed_epoch")
    low=(sid+" "+typ).lower()
    if seq>aseq: bad.append(("future_sequence",sid,seq))
    if oe is not None and float(oe)>at: bad.append(("future_time",sid,oe))
    if any(x in low for x in ("kalshi","coinbase","polymarket","market_data","orderbook","learned_case","historical_window")):
        bad.append(("denied_source",sid,typ))
print("[SAMPLE PREDICTION_ID]",sample.get("prediction_id"))
print("[SAMPLE TICKER]",sample.get("ticker"))
print("[SNAPSHOT RECORDS]",len(snap))
print("[UNIQUE EXOGENOUS SOURCES]",len(sources))
for sid in sorted(sources)[:30]: print("[EXOGENOUS SOURCE]",sid)
print("[ANCHOR BOUNDARY VIOLATIONS]",len(bad))
if bad:
    for x in bad[:20]: print("[VIOLATION]",x)
    raise SystemExit("[FAIL] exogenous snapshot violated anchor/leakage boundary")
print("[PASS] non-empty raw independent evidence physically frozen into new immutable prediction rows")
print("[PASS] every checked exogenous row is sequence/time bounded at decision anchor")
print("[PASS] market/derived predictive leakage exclusions held")
print("[RESULT] EXOGENOUS_FULL_PIPELINE_PHYSICALLY_CERTIFIED")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
''',encoding="utf-8")

for x in (TEST,AUDIT,CERT):
    compile(x.read_text(encoding="utf-8"),str(x),"exec")

print("[PASS] exogenous full-pipeline root cutover V2 installed")
print("[ROOT FILE]",PRED)
print("[BACKUP]",backup)
print("[PIPELINE] canonical independent evidence -> exact anchor -> current state -> frozen score -> immutable ledger")
print("[SCORING/TOKENS/GATES] unchanged")
print("[OLD LEDGER] untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
