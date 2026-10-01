"""OOI-024 installer. Physical test is run separately by the operator."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
TEST = ROOT / 'test_ooi_024_existing_producer_runtime_contract.py'
TEST_SOURCE = r'''"""Static producer/launcher contract capture. No runtime activation or imports."""
import ast
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / 'OOI_024_EXISTING_PRODUCER_RUNTIME_CONTRACT.txt'
SLOP = ROOT / 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity'
TERMS = re.compile(r'slop_|solana_live_opportunity|buy_pressure', re.I)
ENTRY = ROOT / 'run_oracle_live.py'

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def source(path):
    raw = path.read_bytes()
    text = raw.decode('utf-8-sig')
    tree = ast.parse(text, filename=str(path))
    return text, tree, hashlib.sha256(raw).hexdigest()

def dependencies(path, tree):
    package = path.relative_to(ROOT).with_suffix('').parts[:-1]
    modules = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            modules.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            prefix = '.'.join(package[:len(package)-n.level+1]) if n.level else ''
            prefix = '.'.join(x for x in (prefix, n.module) if x)
            modules.add(prefix)
            modules.update(prefix+'.'+a.name for a in n.names if a.name != '*')
    out = []
    for module in sorted(modules):
        if not module.startswith('qseries_v2.'):
            continue
        path = ROOT / (module.replace('.', '/')+'.py')
        if path.is_file():
            out.append(path)
        else:
            package_init = ROOT / module.replace('.', '/') / '__init__.py'
            if package_init.is_file():
                out.append(package_init)
    return tuple(sorted(set(out)))

def capture():
    require(ENTRY.is_file() and SLOP.is_dir(), 'Save installer in repo root; existing launcher/SLOP sources required')
    data = {}
    edges = {}
    def add(path):
        if path not in data:
            require(len(data)<100, 'Source capture exceeded 100 files; no silent truncation')
            data[path] = source(path)
    add(ENTRY)
    # Include production-era SLOP sources, including numeric suffix replacements.
    producer_files=[]
    for path in sorted(SLOP.glob('slop_*.py')):
        match=re.match(r'slop_(\d+)',path.name)
        if match and int(match.group(1))>=25:
            add(path)
            producer_files.append(path)
    require(producer_files, 'Existing SLOP producer files not found')
    # Capture every repository module that statically references SLOP, without importing it.
    references=[]
    for path in sorted((ROOT/'qseries_v2').rglob('*.py')):
        if SLOP in path.parents or '__pycache__' in path.parts:
            continue
        text=path.read_text(encoding='utf-8-sig')
        if TERMS.search(text):
            add(path)
            references.append(path)
    # Resolve launcher dependencies two levels deep and direct producer dependencies.
    frontier=[ENTRY]
    for depth in range(2):
        following=[]
        for path in frontier:
            deps=dependencies(path,data[path][1])
            edges[path]=deps
            for dep in deps:
                if dep not in data:
                    add(dep)
                    following.append(dep)
        frontier=following
    for path in producer_files:
        deps=dependencies(path,data[path][1])
        edges[path]=deps
        for dep in deps:
            add(dep)
    lines=['OOI-024 EXISTING PRODUCER/RUNTIME CONTRACT',
           'SOURCE INSPECTION ONLY; execution_authority=FALSE',
           'No processes started, source ledgers changed, producer functions called, or launcher edited.',
           'Static references do not prove runtime activation or fresh production.',
           'Frozen thesis: BUY_PRESSURE / 60 seconds / +10% / -5% / 200 bps.',
           '', '[EXTERNAL_SLOP_REFERENCE_MODULES]']
    lines.extend(p.relative_to(ROOT).as_posix() for p in references)
    if not references:
        lines.append('NONE_FOUND_STATICALLY; dynamic wiring remains unresolved')
    lines.append('[DEPENDENCIES]')
    for path in sorted(edges):
        lines.append(path.relative_to(ROOT).as_posix()+' -> '+repr([p.relative_to(ROOT).as_posix() for p in edges[path]]))
    manifest={}
    for path in sorted(data):
        text,tree,sha=data[path]
        relative=path.relative_to(ROOT).as_posix()
        manifest[relative]=sha
        lines.extend(['', '[BEGIN_FILE] '+relative,'[SHA256] '+sha,text.rstrip(),'[END_FILE] '+relative])
    lines.extend(['','[FILE_COUNT] '+str(len(data)), '[END_OF_COMPLETE_REPORT]'])
    return '\n'.join(lines)+'\n',manifest

def main():
    first,manifest=capture()
    second,repeated=capture()
    require(first==second and manifest==repeated,'Source changed during capture; retry; no report written')
    raw=first.encode('utf-8')
    REPORT.write_bytes(raw)
    require(REPORT.read_bytes()==raw,'Report writeback mismatch')
    print('[PASS] OOI-024 static producer and launcher contracts captured')
    print('[FILES]',len(manifest))
    print('[BYTES]',len(raw))
    print('[SHA256]',hashlib.sha256(raw).hexdigest())
    print('[REPORT]',REPORT)
    print('[NEXT] Attach OOI_024_EXISTING_PRODUCER_RUNTIME_CONTRACT.txt directly')
    print('[HOLD] Producer health, fresh output and live admission remain unverified; execution_authority=FALSE')

if __name__=='__main__':
    main()
'''

def main():
    if not (ROOT / 'qseries_v2').is_dir():
        raise RuntimeError('Save installer into repository root')
    compile(TEST_SOURCE, str(TEST), 'exec')
    if TEST.exists() and TEST.read_text(encoding='utf-8') != TEST_SOURCE:
        raise RuntimeError('Existing test differs; refusing overwrite')
    if not TEST.exists():
        TEST.write_text(TEST_SOURCE,encoding='utf-8')
    print('[PASS] OOI-024 test installed; production sources unchanged')
    print('[NEXT] Run test_ooi_024_existing_producer_runtime_contract.py')

if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI-024: '+str(exc))
        sys.exit(1)
