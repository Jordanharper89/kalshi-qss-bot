
"""ORACLE173 complete guarded installer: real blockhash RPC backoff, fail closed."""
import argparse, ast, os
from pathlib import Path

TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
MARK='# ORACLE173_BLOCKHASH_BACKOFF'
GUARDS=('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
        'CANARY_TRADE_LAMPORTS=50_000_000')

# Shared safe installer used by ORACLE174-178.
def install_block(stage, marker, block, required=(), rewrite=None):
    if not TARGET.is_file(): raise RuntimeError('HOLD_RUNTIME_NOT_FOUND')
    src=TARGET.read_text(encoding='utf-8')
    for token in GUARDS+tuple(required):
        if token not in src:
            raise RuntimeError('HOLD_%s_MISSING_%s'%(stage,token[:36]))
    if src.count(marker)==1:
        ast.parse(src)
        print('[INSTALL PASS]',stage,'already installed')
        return
    if marker in src: raise RuntimeError('HOLD_%s_PARTIAL_MARKER'%stage)
    if rewrite is not None:
        src=rewrite(src)
        ast.parse(src)
    tree=ast.parse(src)
    runs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run']
    if len(runs)!=1: raise RuntimeError('HOLD_%s_RUN_BOUNDARY_NOT_UNIQUE'%stage)
    lines=src.splitlines(keepends=True)
    offset=runs[0].lineno-1
    updated=''.join(lines[:offset])+block+'\n'+''.join(lines[offset:])
    ast.parse(updated)
    backup=TARGET.with_name('runtime.before_%s.py'%stage.lower())
    original=TARGET.read_text(encoding='utf-8')
    if backup.is_file() and backup.read_text(encoding='utf-8')!=original:
        raise RuntimeError('HOLD_%s_BACKUP_COLLISION'%stage)
    if not backup.exists(): backup.write_text(original,encoding='utf-8')
    temp=TARGET.with_name('runtime.%s.pending'%stage.lower())
    if temp.exists(): raise RuntimeError('HOLD_%s_PENDING_COLLISION'%stage)
    try:
        temp.write_text(updated,encoding='utf-8')
        ast.parse(temp.read_text(encoding='utf-8'))
        os.replace(temp,TARGET)
    finally:
        if temp.exists(): temp.unlink()
    print('[INSTALL PASS]',stage,'runtime boundary integrated; scanner unchanged; broadcast blocked')

BLOCK='''# ORACLE173_BLOCKHASH_BACKOFF
_ORACLE173_REFRESH=BlockhashCache.refresh

def _oracle173_refresh(self):
    import time as _time
    wait_until=getattr(self,'_oracle173_cooldown',0.0)
    if _time.monotonic()<wait_until:
        raise RuntimeError('ORACLE173_RPC_COOLDOWN_ACTIVE')
    try:
        value=_ORACLE173_REFRESH(self)
        self._oracle173_failures=0
        return value
    except Exception as exc:
        e=str(exc).lower()
        if '429' in e or 'too many requests' in e:
            import random as _random
            failures=min(6,1+getattr(self,'_oracle173_failures',0))
            self._oracle173_failures=failures
            delay=min(60.0,2.0**failures)+_random.uniform(0.0,1.0)
            self._oracle173_cooldown=_time.monotonic()+delay
            print('[ORACLE173_RPC_429] backoff_s=%.2f count=%d' %
                  (delay,failures),flush=True)
        raise

def _oracle173_loop(self):
    import time as _time
    while not self.stop:
        try: self.refresh()
        except Exception as exc:
            print('[ORACLE173_BLOCKHASH_HOLD] reason=%s' %
                  type(exc).__name__,flush=True)
        deadline=max(_time.monotonic()+10.0,
                     getattr(self,'_oracle173_cooldown',0.0))
        while not self.stop and _time.monotonic()<deadline:
            _time.sleep(min(0.2,max(0,deadline-_time.monotonic())))

def _oracle173_start(self):
    import time as _time
    import threading as _threading
    for attempt in range(1,6):
        try:
            self.refresh()
            break
        except Exception:
            if attempt==5: raise
            pause=max(0.5,getattr(self,'_oracle173_cooldown',0.0)-_time.monotonic())
            _time.sleep(min(pause,65.0))
    self.thread=_threading.Thread(target=self._loop,
        name='canonical-blockhash',daemon=True)
    self.thread.start()

BlockhashCache.refresh=_oracle173_refresh
BlockhashCache._loop=_oracle173_loop
BlockhashCache.start=_oracle173_start
'''

def test():
    ast.parse(BLOCK)
    assert 'sendTransaction' not in BLOCK
    assert '429' in BLOCK and '_oracle173_cooldown' in BLOCK
    env={}
    exec('class BlockhashCache:\n    def refresh(self):return 1\n'+BLOCK,env)
    c=env['BlockhashCache']()
    assert c.refresh()==1
    c._oracle173_cooldown=__import__('time').monotonic()+10
    try:
        c.refresh()
        raise AssertionError('cooldown bypass')
    except RuntimeError as e:
        assert 'COOLDOWN' in str(e)
    print('[TEST PASS] ORACLE173 blockhash 429 backoff and fail-closed cooldown')

def install():
    src=TARGET.read_text(encoding='utf-8') if TARGET.is_file() else ''
    if 'class BlockhashCache:' not in src or 'BLOCKHASH=BlockhashCache()' not in src:
        raise RuntimeError('HOLD_ORACLE173_BLOCKHASH_CLASS_DRIFT')
    install_block('ORACLE173',MARK,BLOCK,('class BlockhashCache:',))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    a=p.parse_args()
    test() if a.test else install()
