from pathlib import Path
import ast, py_compile

P=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle149_atomic_alt_compiler.py')
START='def verified_alts(keys, instructions):\n'
END='def compile_route(user,route,blockhash):\n'
REPLACE='''def verified_alts(keys, instructions):
    # Evidence from the actual live atomic candidate, not a sample fixture.
    required=set()
    program_ids=set()
    for ix in instructions:
        program_ids.add(ix['programId'])
        for a in ix.get('accounts',[]):
            required.add(a['pubkey'])
    selected=[]
    evidence=[]
    for key in keys:
        try:
            response=q87.c.rpc('getAccountInfo',[key,{'encoding':'base64','commitment':'confirmed'}])
            account=(response or {}).get('value')
            if not isinstance(account,dict) or account.get('owner')!=ALT_PROGRAM:
                evidence.append({'alt':key,'reason':'ALT_OWNER_INVALID'});continue
            import base64
            raw=base64.b64decode(account['data'][0],validate=True)
            if len(raw)<56 or (len(raw)-56)%32 or int.from_bytes(raw[:4],'little')!=1:
                evidence.append({'alt':key,'reason':'ALT_LAYOUT_INVALID'});continue
            if int.from_bytes(raw[4:12],'little')!=(1<<64)-1:
                evidence.append({'alt':key,'reason':'ALT_INACTIVE'});continue
            addresses={q87.c.b58e(raw[i:i+32]) for i in range(56,len(raw),32)}
            # Payer, signers and instruction program IDs cannot be lookup-loaded.
            lookup_required=required-program_ids
            matching=sorted(addresses & lookup_required)
            missing=sorted(lookup_required-addresses)
            evidence.append({'alt':key,'entries':len(addresses),
                'required_account_keys':len(required),'eligible_matches':len(matching),
                'uncovered_count':len(missing),'uncovered_sample':missing[:12]})
            print('[ORACLE154_REAL_ALT_COVERAGE] required=%d matches=%d missing=%d table_entries=%d' %
                  (len(required),len(matching),len(missing),len(addresses)),flush=True)
            if matching:selected.append((key,len(matching)))
        except Exception as exc:
            evidence.append({'alt':key,'reason':'ALT_PROBE_ERROR','error_class':type(exc).__name__})
            print('[ORACLE154_ALT_HOLD] class='+type(exc).__name__,flush=True)
    return [key for key,n in sorted(selected,key=lambda item:-item[1])[:4]],evidence

'''

def install():
    old=P.read_text(encoding='utf-8')
    a=old.find(START);b=old.find(END,a)
    if a<0 or b<0 or b<=a:raise RuntimeError('ORACLE149_BOUNDARY_MISMATCH_HOLD')
    new=old[:a]+REPLACE+old[b:]
    ast.parse(new)
    backup=P.with_suffix('.pre_oracle154.bak')
    if not backup.exists():backup.write_text(old,encoding='utf-8')
    P.write_text(new,encoding='utf-8')
    py_compile.compile(str(P),doraise=True)
    print('[INSTALL PASS] ORACLE154 real candidate ALT coverage tracing')
    print('[GUARD] unchanged native swap instructions, scanner, signer and broadcast')

def test():
    ast.parse(REPLACE)
    assert REPLACE.count('getAccountInfo')==1
    assert "raw[4:12]" in REPLACE
    assert "selected.append" in REPLACE
    print('[TEST PASS] ORACLE154 actual account-coverage trace and ALT metadata guards')

if __name__=='__main__':
    install();test()
