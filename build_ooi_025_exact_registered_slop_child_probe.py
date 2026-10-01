"""OOI-025 complete installer; physical verification runs in operator CMD."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
TEST=ROOT/'test_ooi_025_exact_registered_slop_child_probe.py'
TEST_SOURCE = r'''"""Bounded registered-child source/ledger probe. Does not start another producer."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parent
REPORT=ROOT/'OOI_025_REGISTERED_SLOP_CHILD_PROBE.txt'
CHILD=ROOT/'run_slop_buy_pressure_live.py'
LAUNCHER=ROOT/'run_oracle_live.py'
STATE=ROOT/'runtime_state/solana_live_opportunity'

def now():
    return datetime.now(timezone.utc)

def read_source(path):
    raw=path.read_bytes()
    text=raw.decode('utf-8-sig')
    return text,ast.parse(text,filename=str(path)),hashlib.sha256(raw).hexdigest()

def dependencies(path,tree):
    package=path.relative_to(ROOT).with_suffix('').parts[:-1]
    modules=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):modules.update(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom):
            parent='.'.join(package[:len(package)-node.level+1]) if node.level else ''
            prefix='.'.join(x for x in (parent,node.module) if x)
            modules.add(prefix)
            modules.update(prefix+'.'+a.name for a in node.names if a.name!='*')
    paths=set()
    for module in modules:
        if not module.startswith('qseries_v2.'):
            continue
        path=ROOT/(module.replace('.','/')+'.py')
        if path.is_file():paths.add(path)
    return sorted(paths)

def ledger_sample():
    result={'observed_at':now().isoformat()}
    for filename,key in [('prospective_predictions.json','predictions'),('economic_resolutions.json','resolutions')]:
        path=STATE/filename
        if not path.is_file():
            result[filename]={'exists':False}
            continue
        # Retry concurrent source replacement; never overwrite it.
        for attempt in range(3):
            raw=path.read_bytes()
            try:
                doc=json.loads(raw.decode('utf-8-sig'))
                rows=doc[key]
                if not isinstance(rows,list):raise ValueError('Ledger rows must be a list')
                ids=[str(r['prediction_id']) for r in rows]
                if len(ids)!=len(set(ids)):raise ValueError('Duplicate ledger identity')
                fresh=[]
                if key=='predictions':
                    instant=now()
                    for row in rows:
                        frozen=datetime.fromisoformat(str(row['frozen_at']).replace('Z','+00:00'))
                        if frozen.tzinfo is None:raise ValueError('Naive prediction timestamp')
                        age=(instant-frozen.astimezone(timezone.utc)).total_seconds()
                        if 0<=age<60:fresh.append(str(row['prediction_id']))
                result[filename]={'exists':True,'sha256':hashlib.sha256(raw).hexdigest(),
                    'count':len(rows),'ids':sorted(ids),'fresh_ids':sorted(fresh),
                    'latest_frozen_at':max((str(r.get('frozen_at','')) for r in rows),default=None)}
                break
            except (json.JSONDecodeError,KeyError):
                if attempt==2:raise
                time.sleep(.1)
    predictions=result.get('prospective_predictions.json',{})
    resolutions=result.get('economic_resolutions.json',{})
    result['fresh_unresolved_ids']=sorted(set(predictions.get('fresh_ids',[]))-set(resolutions.get('ids',[])))
    return result

def main():
    if not CHILD.is_file() or not LAUNCHER.is_file():raise FileNotFoundError('Registered producer child or launcher missing')
    text,tree,sha=read_source(LAUNCHER)
    assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHILDREN' for t in n.targets)]
    if len(assignments)!=1:raise ValueError('Ambiguous launcher child contract')
    children=ast.literal_eval(assignments[0].value)
    if children.get('solana_buy_pressure')!=CHILD.name:raise ValueError('Actual launcher registration differs')
    print('[REGISTERED_CHILD]',CHILD.name,flush=True)
    sources={CHILD:read_source(CHILD)}
    frontier=[CHILD]
    for depth in range(3):
        following=[]
        for path in frontier:
            for dep in dependencies(path,sources[path][1]):
                if dep not in sources:
                    if len(sources)>=60:raise RuntimeError('More than 60 child dependencies; refusing silent truncation')
                    sources[dep]=read_source(dep);following.append(dep)
        frontier=following
        print('[SOURCE_PROGRESS] depth=%d files=%d'%(depth+1,len(sources)),flush=True)
    first=ledger_sample()
    print('[LEDGER_BASELINE]',json.dumps({k:{'count':v.get('count')} for k,v in first.items() if isinstance(v,dict)},sort_keys=True),flush=True)
    for elapsed in range(5,21,5):
        time.sleep(5)
        print('[OBSERVE] %d/20 seconds'%elapsed,flush=True)
    second=ledger_sample()
    new_ids=sorted(set(second.get('prospective_predictions.json',{}).get('ids',[]))-set(first.get('prospective_predictions.json',{}).get('ids',[])))
    lines=['OOI-025 EXACT REGISTERED CHILD CONTRACT AND BOUNDED LEDGER OBSERVATION',
        'execution_authority=FALSE; no producer started or production file edited',
        'Static registration/ledger changes do not prove process health; freshness is reported separately.',
        '[LAUNCHER_SHA256] '+sha,'[REGISTERED_CHILD] '+CHILD.name,
        '[BASELINE] '+json.dumps(first,sort_keys=True),'[AFTER_20_SECONDS] '+json.dumps(second,sort_keys=True),
        '[NEW_PREDICTION_IDS] '+repr(new_ids)]
    for path in sorted(sources):
        source,_,digest=sources[path]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise RuntimeError('Source changed during probe; retry')
        rel=path.relative_to(ROOT).as_posix()
        lines.extend(['','[BEGIN_FILE] '+rel,'[SHA256] '+digest,source.rstrip(),'[END_FILE] '+rel])
    lines.append('[END_OF_COMPLETE_REPORT]')
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('[PASS] OOI-025 exact child contract captured; bounded observation completed',flush=True)
    print('[NEW_PREDICTIONS]',len(new_ids),flush=True)
    print('[FRESH_UNRESOLVED]',len(second['fresh_unresolved_ids']),flush=True)
    if not new_ids:print('[HOLD] No new predictions observed in 20 seconds; producer health/cause unresolved',flush=True)
    print('[REPORT]',REPORT,flush=True)
    print('[NEXT] Attach OOI_025_REGISTERED_SLOP_CHILD_PROBE.txt directly',flush=True)

if __name__=='__main__':main()
'''

def main():
    if not (ROOT/'qseries_v2').is_dir():raise RuntimeError('Save installer in repository root')
    compile(TEST_SOURCE,str(TEST),'exec')
    if TEST.exists() and TEST.read_text(encoding='utf-8')!=TEST_SOURCE:raise RuntimeError('Existing test differs; refusing overwrite')
    if not TEST.exists():TEST.write_text(TEST_SOURCE,encoding='utf-8')
    print('[PASS] OOI-025 test installed; execution_authority=FALSE',flush=True)
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('[FAIL] OOI-025: '+str(exc),flush=True)
        sys.exit(1)
