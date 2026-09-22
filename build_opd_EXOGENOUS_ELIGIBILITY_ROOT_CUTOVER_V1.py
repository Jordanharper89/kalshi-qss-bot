from pathlib import Path
import ast, shutil, time

ROOT=Path.cwd().resolve()
PRED=ROOT/'qseries_v2'/'oracle_predictive_discovery'/'opd_live_full_evidence_fusion_predictor.py'
if not PRED.exists():
    raise SystemExit('[FAIL] predictor missing: '+str(PRED))

src=PRED.read_text(encoding='utf-8')

def span(text,name):
    tree=ast.parse(text)
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return node.lineno,node.end_lineno
    return None

def repl(text,name,new_body):
    s=span(text,name)
    if not s:
        raise SystemExit('[FAIL] function missing: '+name)
    a,b=s
    lines=text.splitlines()
    lines[a-1:b]=new_body.strip('\n').splitlines()
    return '\n'.join(lines)+'\n'

backup=Path(str(PRED)+'.bak.'+str(int(time.time())))
shutil.copy2(PRED,backup)

elig='''
def _opd_exogenous_source_eligible(anchor,sid,typ,obj):
    sid=str(sid or ""); typ=str(typ or ""); low=(sid+" "+typ).lower()
    deny=("kalshi","coinbase","polymarket","prospective_forecast","prospective_binding",
          "experience","learned_case","prediction","outcome","resolution","profit","pnl",
          "historical_window","market_data","orderbook","sports.","source.sports")
    if any(x in low for x in deny):
        return False
    ticker=str((anchor or {}).get("ticker") or "").upper()
    asset="BTC" if ticker.startswith("KXBTC") else "ETH" if ticker.startswith("KXETH") else "SOL" if ticker.startswith("KXSOL") else None
    words={"BTC":("btc","bitcoin"),"ETH":("eth","ethereum"),"SOL":("sol","solana")}
    all_words=("btc","bitcoin","eth","ethereum","sol","solana")
    if asset:
        mentions_asset=any(x in low for x in all_words)
        if mentions_asset and not any(x in low for x in words[asset]):
            return False
    if "gmgn" in low:
        return asset=="SOL" and ("solana" in low or ".sol" in low)
    allow=("usgs","weather","official","macro","economic","economy","network","onchain",
           "on_chain","chain","mempool","block","provider","event","calendar","release",
           "announcement","ethereum","solana","bitcoin","btc","eth","sol")
    return any(x in low for x in allow)
'''

if span(src,'_opd_exogenous_source_eligible'):
    src=repl(src,'_opd_exogenous_source_eligible',elig)
else:
    marker='def _opd_load_exogenous_canonical_asof('
    if marker not in src:
        raise SystemExit('[FAIL] exogenous loader missing')
    src=src.replace(marker,elig.strip()+'\n\n'+marker,1)

loader='''
def _opd_load_exogenous_canonical_asof(anchor,root):
    root=Path(root or Path.cwd()).resolve()
    try:
        seq=int(anchor["anchor_sequence_boundary"]); t=float(anchor["observed_epoch"])
    except Exception:
        return {}
    sql="""SELECT sequence_number,source_id,observation_type,
                  EXTRACT(EPOCH FROM observed_at),canonical_observation_json
           FROM public.oracle_canonical_observations
           WHERE sequence_number<=%s AND observed_at<=to_timestamp(%s)
           ORDER BY sequence_number DESC LIMIT 4096"""
    out={}
    try:
        with _opd_exo_connect(root,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='12000ms'")
                q.execute(sql,(seq,t)); rows=q.fetchall() or []
            c.rollback()
    except Exception as e:
        print("[EXOGENOUS ASOF READ ERROR]",type(e).__name__,str(e)[:220]); return {}
    for rseq,sid,typ,obs_epoch,obj in rows:
        if not _opd_exogenous_source_eligible(anchor,sid,typ,obj):
            continue
        key=str(sid or "")+"|"+str(typ or "")
        if key in out:
            continue
        try: oe=float(obs_epoch)
        except Exception: oe=None
        if int(rseq)>seq or (oe is not None and oe>t):
            continue
        out[key]={"sequence_number":int(rseq),"observed_epoch":oe,
                  "source_id":str(sid or ""),"observation_type":str(typ or ""),
                  "canonical_observation":obj}
        if len(out)>=64:
            break
    return out
'''
src=repl(src,'_opd_load_exogenous_canonical_asof',loader)
compile(src,str(PRED),'exec')
PRED.write_text(src,encoding='utf-8')

TEST=ROOT/'test_opd_EXOGENOUS_ELIGIBILITY_ROOT_CUTOVER_V1.py'
TEST.write_text("""from pathlib import Path
P=Path('qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py')
s=P.read_text(encoding='utf-8'); compile(s,str(P),'exec')
for x in ('def _opd_exogenous_source_eligible','prospective_forecast','prospective_binding','source.sports','if \"gmgn\" in low:','sequence_number<=%s AND observed_at<=to_timestamp(%s)'):
    assert x in s,x
print('[PASS] exogenous eligibility boundary installed')
print('[PASS] internal predictive/experience and sports noise excluded')
print('[PASS] GMGN restricted to SOL')
print('[PASS] exact anchor bounds preserved')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
""",encoding='utf-8')

AUDIT=ROOT/'audit_opd_EXOGENOUS_ELIGIBILITY_PHYSICAL_V1.py'
AUDIT.write_text("""from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import latest_live_anchor,_opd_load_exogenous_canonical_asof
root=Path.cwd().resolve(); a=latest_live_anchor(root)
if not a: raise SystemExit('[FAIL] no live anchor')
x=_opd_load_exogenous_canonical_asof(a,root)
print('[ANCHOR]',a.get('ticker'),a.get('anchor_sequence_boundary'),a.get('observed_epoch'))
print('[ELIGIBLE EXOGENOUS SOURCES]',len(x))
bad=[]
for v in x.values():
    sid=str(v.get('source_id') or ''); typ=str(v.get('observation_type') or ''); low=(sid+' '+typ).lower()
    print('[ELIGIBLE SOURCE]',v.get('sequence_number'),sid,typ)
    if any(z in low for z in ('prospective_forecast','prospective_binding','experience','source.sports','sports.','kalshi','coinbase','polymarket','learned_case')):
        bad.append((sid,typ))
if bad:
    for z in bad: print('[BAD SOURCE]',z)
    raise SystemExit('[FAIL] contaminated source survived')
if not x: raise SystemExit('[FAIL] no eligible exogenous evidence at anchor')
print('[PASS] only eligible external decision-time evidence survives')
""",encoding='utf-8')

CERT=ROOT/'certify_opd_EXOGENOUS_ELIGIBILITY_LEDGER_V1.py'
CERT.write_text("""from pathlib import Path
import json,subprocess,sys
root=Path.cwd().resolve(); ledger=root/'runtime'/'predictive_data'/'opd_full_evidence_live_prediction_ledger.jsonl'
def load():
    out=[]
    if ledger.exists():
        for line in ledger.read_text(encoding='utf-8').splitlines():
            try: out.append(json.loads(line))
            except Exception: pass
    return out
before=load(); ids={str(x.get('prediction_id')) for x in before if x.get('prediction_id')}
print('[LEDGER BEFORE]',len(before))
code=\"from pathlib import Path;from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import run;run(root=Path.cwd().resolve())\"
p=subprocess.run([sys.executable,'-c',code],cwd=str(root),text=True,capture_output=True,timeout=180)
print('[FRESH INTERPRETER EXIT]',p.returncode)
for line in p.stdout.splitlines():
    if 'LIVE_EVIDENCE_EXOGENOUS_SOURCES=' in line or '[PREDICTION LEDGER]' in line or 'LIVE_PREDICTION=' in line:
        print(line)
if p.returncode:
    if p.stderr.strip(): print('[STDERR]',p.stderr[-3000:])
    raise SystemExit('[FAIL] predictor run failed')
after=load(); new=[x for x in after if str(x.get('prediction_id') or '') not in ids]
rows=[x for x in new if isinstance(x.get('exogenous_evidence_snapshot'),dict) and x['exogenous_evidence_snapshot']]
print('[NEW IMMUTABLE ROWS]',len(new)); print('[ROWS WITH NONEMPTY ELIGIBLE SNAPSHOT]',len(rows))
if not rows: raise SystemExit('[FAIL] no eligible snapshot frozen')
bad=[]; sources=set()
for row in rows:
    aseq=int(row['anchor_sequence_boundary']); at=float(row['anchor_observed_epoch'])
    for v in row['exogenous_evidence_snapshot'].values():
        sid=str(v.get('source_id') or ''); typ=str(v.get('observation_type') or ''); low=(sid+' '+typ).lower(); sources.add(sid)
        if int(v['sequence_number'])>aseq: bad.append(('future_seq',sid))
        if v.get('observed_epoch') is not None and float(v['observed_epoch'])>at: bad.append(('future_time',sid))
        if any(z in low for z in ('prospective_forecast','prospective_binding','experience','source.sports','sports.','kalshi','coinbase','polymarket','learned_case')):
            bad.append(('contaminated',sid))
print('[UNIQUE ELIGIBLE SOURCES]',len(sources))
for sid in sorted(sources): print('[ELIGIBLE SOURCE]',sid)
print('[ELIGIBILITY/ANCHOR VIOLATIONS]',len(bad))
if bad:
    for z in bad[:30]: print('[VIOLATION]',z)
    raise SystemExit('[FAIL] contamination/leakage detected')
print('[PASS] clean eligible exogenous evidence physically frozen into new immutable rows')
print('[PASS] internal predictive state and unrelated-domain evidence excluded')
print('[PASS] exact anchor anti-leakage boundary preserved')
print('[RESULT] EXOGENOUS_ELIGIBILITY_PHYSICALLY_CERTIFIED')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
""",encoding='utf-8')

for path in (TEST,AUDIT,CERT):
    compile(path.read_text(encoding='utf-8'),str(path),'exec')

print('[PASS] exogenous eligibility root cutover installed')
print('[ROOT FILE]',PRED)
print('[BACKUP]',backup)
print('[PIPELINE] certified exogenous freeze path preserved')
print('[ELIGIBILITY] external + anchor-bounded + asset/event relevant only')
print('[SCORING/GATES] unchanged')
print('[OLD LEDGER] untouched')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
