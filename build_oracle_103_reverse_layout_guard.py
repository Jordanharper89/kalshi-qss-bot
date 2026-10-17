"""Complete guarded replacement installer for ORACLE090 legacy layout acceptance."""
from pathlib import Path
import ast

TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_089_reverse_mint_owner_binding.py')
OLD="if len(raw)!=24 or len(ac)!=15:"
NEW="if len(raw)!=24 or len(ac)<15:"

def install():
    if not TARGET.is_file(): raise RuntimeError('ORACLE089_TARGET_MISSING')
    source=TARGET.read_text(encoding='utf-8')
    if source.count(OLD)!=1: raise RuntimeError('ORACLE090_SOURCE_CONTRACT_MISMATCH_NO_WRITE')
    if "str(ac[14].get('pubkey') or '')!=DLMM" not in source: raise RuntimeError('ORACLE090_PROGRAM_SLOT_GUARD_MISSING')
    if "ac.insert(13,{'pubkey':MEMO" not in source: raise RuntimeError('ORACLE090_MEMO_INSERT_GUARD_MISSING')
    updated=source.replace(OLD,NEW)
    ast.parse(updated)
    assert updated.count(NEW)==1
    # This accepts trailing accounts ONLY when the exact required legacy program slot remains valid.
    # Never delete or reorder trailing metas; retain all subsequent mint and owner checks.
    backup=TARGET.with_suffix('.oracle103_backup')
    if backup.exists(): raise RuntimeError('ORACLE103_BACKUP_ALREADY_EXISTS_NO_WRITE')
    backup.write_text(source,encoding='utf-8')
    try:
        TARGET.write_text(updated,encoding='utf-8')
        compile(TARGET.read_text(encoding='utf-8'),str(TARGET),'exec')
    except Exception:
        TARGET.write_text(source,encoding='utf-8')
        raise
    print('[PASS] ORACLE103_REVERSE_LAYOUT_GUARD_INSTALLED')
    print('[SCOPE] Accept legacy 15+ metas only with verified DLMM program at index 14; preserve all trailing metas')
    print('[BOUNDARY] NO_SIGNING_NO_BROADCAST_NO_SCANNER_CHANGE')

def test():
    def valid(accounts,data):
        return len(data)==24 and len(accounts)>=15 and accounts[14]=='DLMM'
    assert valid(['x']*14+['DLMM'],b'x'*24)
    assert valid(['x']*14+['DLMM','extra'],b'x'*24)
    assert not valid(['x']*15+['DLMM'],b'x'*24)
    assert not valid(['x']*14+['DLMM'],b'x'*23)
    assert not valid(['x']*14,b'x'*24)
    ast.parse(Path(__file__).read_text(encoding='utf-8'))
    print('[PASS] ORACLE103_LAYOUT_GUARD_TESTS')

if __name__=='__main__':
    import sys
    test()
    if '--test' not in sys.argv: install()
