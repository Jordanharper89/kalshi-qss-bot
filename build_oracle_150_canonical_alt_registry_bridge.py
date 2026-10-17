from pathlib import Path
import ast,py_compile

TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle149_atomic_alt_compiler.py')
START='def alt_candidates():\n'
END='def verified_alts(keys, instructions):\n'
REPLACEMENT='''def alt_candidates():
    # Public address lookup table discovery only. NEVER scan key material.
    found=[]
    def accept(v):
        if isinstance(v,str) and _valid_key(v) and v not in found:
            found.append(v)
    if EXPLICIT.exists():
        data=json.loads(EXPLICIT.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or not isinstance(data.get('alt_keys'),list):
            raise RuntimeError('ALT_EXPLICIT_SCHEMA_INVALID')
        for value in data['alt_keys']:accept(value)
    locations=(
        Path('runtime_state/oracle/solana_atomic_executor'),
        ROOT,
        Path('runtime_state/qseries/qarb_execution_engineering'),
    )
    alt_names=('alt','lookup','address_table')
    field_names=('table','address','pubkey','key','alt','lookup','account')
    def scan(node,context='',depth=0):
        if depth>18:return
        if isinstance(node,dict):
            for k,v in node.items():
                name=str(k).lower()
                relevant=any(x in name for x in alt_names)
                if isinstance(v,str) and (relevant or (any(x in context for x in alt_names) and any(x in name for x in field_names))):
                    accept(v)
                elif isinstance(v,(list,dict)):
                    scan(v,name if relevant else context,depth+1)
        elif isinstance(node,list):
            for item in node:
                if isinstance(item,str) and any(x in context for x in alt_names):accept(item)
                elif isinstance(item,(dict,list)):scan(item,context,depth+1)
    for directory in locations:
        if not directory.exists():continue
        for path in sorted(directory.glob('*.json'))[:300]:
            if path in (REPORT,EXPLICIT) or not any(x in path.name.lower() for x in alt_names):continue
            try:
                if path.stat().st_size>2_000_000:continue
                scan(json.loads(path.read_text(encoding='utf-8')), 'alt_registry')
            except (ValueError,OSError,UnicodeError):continue
    return found[:64]

'''

def install():
    if not TARGET.is_file():raise RuntimeError('ORACLE149_MODULE_MISSING; install ORACLE149 first')
    old=TARGET.read_text(encoding='utf-8')
    a=old.find(START);b=old.find(END,a)
    if a<0 or b<0:raise RuntimeError('ORACLE149_DISCOVERY_BOUNDARY_CHANGED_HOLD')
    updated=old[:a]+REPLACEMENT+old[b:]
    ast.parse(updated)
    if old!=updated:
        backup=TARGET.with_suffix('.pre_oracle150.bak')
        if not backup.exists():backup.write_text(old,encoding='utf-8')
        TARGET.write_text(updated,encoding='utf-8')
    py_compile.compile(str(TARGET),doraise=True)
    print('[INSTALL PASS] ORACLE150 canonical ALT registry bridged into ORACLE149')
    print('[SCOPE] read-only public ALT discovery; no signing or broadcasting; scanner untouched')

if __name__=='__main__':install()
