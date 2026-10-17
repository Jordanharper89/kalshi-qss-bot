"""FULL INSTALLER: read-only ORACLE-322 rotation contract extractor.
No scanner modification, new sockets, RPC calls, or execution capability.
"""
from __future__ import annotations
import argparse, ast, hashlib, os, re, sys, tempfile
from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
DEST=PKG/'final_boss_scanner_rotation_contract.py'
ORIGINAL=ROOT/'build_oracle_322_scanner_isolated_discovery.py'
REPORT=ROOT/'runtime_state/oracle/final_boss_dual/scanner_rotation_source_excerpt.txt'
REFERENCE_SHA='60c9a4d8acc4259a01f37c64332caea6139e49a84a719ada7e7fe4ec17bab57b'

def digest(raw):
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def embedded_source(raw):
    tree=ast.parse(raw)
    found=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            val=node.value
            if isinstance(val,ast.Constant) and isinstance(val.value,str) and len(val.value)>1000:
                names=[n.id for n in getattr(node,'targets',[]) if isinstance(n,ast.Name)]
                if isinstance(getattr(node,'target',None),ast.Name):names.append(node.target.id)
                if any(k in name.upper() for name in names for k in ('SOURCE','SCRIPT','CONTENT','SCANNER')):
                    found.append(val.value)
    if len(found)!=1:
        raise RuntimeError('HOLD_AMBIGUOUS_EMBEDDED_SCANNER_SOURCE_COUNT_'+str(len(found)))
    return found[0]

def redact(line):
    if re.search(r'(?i)api.?key|secret|private.?key|seed.?phrase|mnemonic|password|authorization|bearer|token\s*=',line):
        return '[SOURCE_LINE_SUPPRESSED_CREDENTIAL_PATTERN]'
    line=re.sub(r'(?i)(https?://|wss?://)[^\s"\']+','[URL_REDACTED]',line)
    line=re.sub(r'(?<![A-Za-z0-9])[1-9A-HJ-NP-Za-km-z]{65,}(?![A-Za-z0-9])','[LONG_KEY_REDACTED]',line)
    return line[:260]

def inspect(raw):
    s=embedded_source(raw)
    src=ast.parse(s)
    lines=s.splitlines()
    focus=('select_rows','stage_discovery','discovery','heartbeat')
    required=[]
    for n in ast.walk(src):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in focus:
            required.append((n.name,n.lineno,n.end_lineno))
    if len({x[0] for x in required})!=len(focus):
        raise RuntimeError('HOLD_SCANNER_FUNCTION_CONTRACT_CHANGED')
    spans=[(1,min(len(lines),60))]
    for name,start,end in required:
        spans.append((max(1,start-5),min(len(lines),end+5)))
    for idx,line in enumerate(lines,1):
        if any(word in line.lower() for word in ('subscribe','unsubscribe','create_task','websocket','scanner.lock','discovery_staged','source_attached')):
            spans.append((max(1,idx-4),min(len(lines),idx+5)))
    chosen=set()
    for a,b in spans:
        chosen.update(range(a,b+1))
    out=['[ORACLE322_ROTATION_SOURCE_CONTRACT]',
         'installer_sha256='+digest(raw),
         'expected_installer_sha256='+REFERENCE_SHA,
         'source_sha256='+digest(s),
         'embedded_source_lines='+str(len(lines)),
         'source_matches_previous_audit='+str(digest(raw)==REFERENCE_SHA),
         'focused_functions='+str(sorted(required)),
         'subscription_calls='+str([(i,line.strip()[:80]) for i,line in enumerate(lines,1)
             if re.search(r'accountSubscribe|accountUnsubscribe|programSubscribe|programUnsubscribe',line)]),
         'source_excerpt_begin']
    for i in sorted(chosen):
        out.append(f'{i:04d} {redact(lines[i-1])}')
    out.append('source_excerpt_end')
    return '\n'.join(out)+'\n'

def atomic_write(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',dir=path.parent,encoding='utf-8',delete=False,suffix='.tmp',newline='\n') as f:
        temp=Path(f.name)
        f.write(body)
    os.replace(temp,path)

def install():
    data=Path(__file__).read_bytes()
    DEST.parent.mkdir(parents=True,exist_ok=True)
    if DEST.exists():
        if DEST.read_bytes()!=data:
            raise RuntimeError('HOLD_EXISTING_CONTRACT_MODULE_DIFFERS')
        print('[PASS] ROTATION_CONTRACT_ALREADY_INSTALLED')
        return
    with tempfile.NamedTemporaryFile('wb',dir=DEST.parent,delete=False,suffix='.tmp') as f:
        f.write(data)
        temp=Path(f.name)
    os.replace(temp,DEST)
    print('[INSTALLED]',DEST.relative_to(ROOT))

def audit():
    if not ORIGINAL.is_file():
        raise RuntimeError('HOLD_ORACLE322_INSTALLER_MISSING')
    raw=ORIGINAL.read_text(encoding='utf-8-sig')
    result=inspect(raw)
    atomic_write(REPORT,result)
    print('[SCANNER_ROTATION_SOURCE]', 'MATCHED' if digest(raw)==REFERENCE_SHA else 'DRIFT_DETECTED')
    print('[EXCERPT_LINES]',len(result.splitlines()))
    print('[REPORT]',REPORT.relative_to(ROOT))
    print('[MODE] READ_ONLY; SCANNER_FROZEN; NO_KEY_USE; NO_SIGNING; NO_BROADCAST')

def test():
    fixture='''def select_rows(x):return x\ndef stage_discovery(x):return x\ndef discovery(x):return x\ndef heartbeat(x):return x\n# accountSubscribe\n'''
    raw='SOURCE='+repr(fixture*80)
    doc=inspect(raw)
    assert 'focused_functions' in doc
    assert 'source_excerpt_begin' in doc
    assert 'accountSubscribe' in doc
    assert redact("api-key='private'")== '[SOURCE_LINE_SUPPRESSED_CREDENTIAL_PATTERN]'
    assert redact('wss://example')=='[URL_REDACTED]'
    print('[PASS] ROTATION_CONTRACT isolated AST, scoped excerpt, credential redaction, no scanner writes')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--test',action='store_true')
    parser.add_argument('--install',action='store_true')
    parser.add_argument('--audit',action='store_true')
    args=parser.parse_args()
    if not any((args.test,args.install,args.audit)):
        parser.error('select --test, --install, or --audit')
    if args.test:test()
    if args.install:install()
    if args.audit:audit()

if __name__=='__main__':main()