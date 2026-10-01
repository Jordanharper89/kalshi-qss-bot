from pathlib import Path
import py_compile

ROOT=Path.cwd()
MOD=ROOT/'qseries_v2/oracle_strategy_intelligence/solana_money/qsb059_gav_reverse_atomic.py'
if not MOD.is_file():
    raise SystemExit('[FAIL] QSB-059B module missing')

s=MOD.read_text(encoding='utf-8')

old='    n=min(len(arr),max(3,int(quote_result.get("bins_crossed") or 1)+2))\n    chosen=arr[:n] if swap_for_y else list(reversed(arr))[:n]\n'
new='    crossed=max(1,int(quote_result.get("bins_crossed") or 1))\n    n=min(len(arr),max(1,(crossed+69)//70))\n    chosen=arr[:n] if swap_for_y else list(reversed(arr))[:n]\n'
if old not in s:
    raise SystemExit('[FAIL] QSB-059B DLMM array boundary missing')
s=s.replace(old,new,1)

anchor='def compose_reverse_atomic(user,token,pump_pool,meteora_pool,start_sol):\n'
helper='''MRIYA_WALLET="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"\nCOMPUTE_BUDGET="ComputeBudget111111111111111111111111111111"\nMEMO_PROGRAMS={\n    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",\n    "Memo1UhkJRfHyvLMcVucJwxXeuD728EqVDDwQDxFMNo",\n}\n\ndef recent_mriya_alt_keys(limit=24):\n    out=[];seen=set()\n    try:\n        sigs=c.rpc("getSignaturesForAddress",[MRIYA_WALLET,{"limit":int(limit),"commitment":"processed"}]) or []\n    except Exception:\n        return []\n    for row in sigs:\n        sig=row.get("signature")\n        if not sig or row.get("err") is not None:\n            continue\n        try:\n            tx=c.rpc("getTransaction",[sig,{"encoding":"json","commitment":"processed","maxSupportedTransactionVersion":0}])\n        except Exception:\n            continue\n        msg=(((tx or {}).get("transaction") or {}).get("message") or {})\n        for lk in msg.get("addressTableLookups") or []:\n            k=lk.get("accountKey")\n            if k and k not in seen:\n                seen.add(k);out.append(k)\n        if len(out)>=16:\n            break\n    return out\n\ndef compact_ixs(ixs):\n    import base64\n    result=[];compute={}\n    for ix in ixs:\n        pid=ix.get("programId")\n        if pid in MEMO_PROGRAMS:\n            continue\n        if pid==COMPUTE_BUDGET:\n            try:\n                raw=base64.b64decode(ix.get("data") or "")\n                tag=raw[0] if raw else -1\n            except Exception:\n                tag=-1\n            compute[tag]=ix\n            continue\n        result.append(ix)\n    return [compute[k] for k in sorted(compute)] + result\n\ndef compile_compact(user,ixs,base_alts,blockhash):\n    attempts=[]\n    alt_sets=[\n        list(dict.fromkeys(base_alts)),\n        list(dict.fromkeys(list(base_alts)+recent_mriya_alt_keys())),\n    ]\n    last=None\n    for idx,alts in enumerate(alt_sets,1):\n        try:\n            msg,raw=c.compile_v0(user,compact_ixs(ixs),alts,blockhash)\n            print("[TX_SIZE] attempt=%d bytes=%d alts=%d"%(idx,len(raw),len(alts)),flush=True)\n            return msg,raw,alts\n        except RuntimeError as e:\n            last=e\n            if not str(e).startswith("ATOMIC_TX_TOO_LARGE:"):\n                raise\n            size=int(str(e).split(":")[-1])\n            attempts.append({"attempt":idx,"size":size,"alts":len(alts)})\n            print("[TX_SIZE] attempt=%d bytes=%d TOO_LARGE alts=%d"%(idx,size,len(alts)),flush=True)\n    raise RuntimeError("ATOMIC_TX_TOO_LARGE_AFTER_COMPACTION:"+str(attempts)+" last="+str(last))\n\n'''
if 'def recent_mriya_alt_keys(' not in s:
    if anchor not in s:
        raise SystemExit('[FAIL] compose boundary missing')
    s=s.replace(anchor,helper+anchor,1)

old_compile='    msg,unsigned=c.compile_v0(user,x["instructions"],x["alts"],bh)\n'
new_compile='    msg,unsigned,used_alts=compile_compact(user,x["instructions"],x["alts"],bh)\n'
if old_compile not in s:
    raise SystemExit('[FAIL] QSB-059B compile boundary missing')
s=s.replace(old_compile,new_compile,1)

s=s.replace('[QSB-059] GAV PUMP->METEORA NATIVE ATOMIC COMPOSER','[QSB-059C] GAV PUMP->METEORA ATOMIC SIZE-COMPACT COMPOSER',1)
s=s.replace('"revision":"QSB_059_GAV_REVERSE_ATOMIC_COMPOSER_V1"','"revision":"QSB_059C_GAV_REVERSE_ATOMIC_SIZE_COMPACT_V1"',1)

MOD.write_text(s,encoding='utf-8')
py_compile.compile(str(MOD),doraise=True)

TEST=ROOT/'test_qsb_059c_atomic_size_compaction.py'
TEST.write_text('''import base64,unittest\nfrom qseries_v2.oracle_strategy_intelligence.solana_money import qsb059_gav_reverse_atomic as q\n\nclass T(unittest.TestCase):\n    def test_exact_array_width_not_three_minimum(self):\n        with open(q.__file__,encoding="utf-8") as f: src=f.read()\n        self.assertIn("(crossed+69)//70",src)\n        self.assertNotIn("max(3,int(quote_result.get",src)\n        print("[PASS] narrow DLMM quote no longer forces 3 bin-array accounts")\n\n    def test_compact_drops_memo_and_dedupes_compute(self):\n        def ix(pid,data):\n            return {"programId":pid,"accounts":[],"data":base64.b64encode(data).decode()}\n        memo=next(iter(q.MEMO_PROGRAMS))\n        rows=[ix(memo,b"x"),ix(q.COMPUTE_BUDGET,b"\\x02aaa"),ix("SWAP",b"x"),ix(q.COMPUTE_BUDGET,b"\\x02bbb")]\n        out=q.compact_ixs(rows)\n        self.assertEqual(sum(1 for x in out if x["programId"]==q.COMPUTE_BUDGET),1)\n        self.assertEqual(sum(1 for x in out if x["programId"] in q.MEMO_PROGRAMS),0)\n        self.assertTrue(any(x["programId"]=="SWAP" for x in out))\n        print("[PASS] memo removed and duplicate compute-budget instructions compacted")\n\n    def test_alt_retry_after_1414(self):\n        old_compile=q.c.compile_v0; old_alts=q.recent_mriya_alt_keys\n        calls=[]\n        def fake_compile(user,ixs,alts,bh):\n            calls.append(list(alts))\n            if "MRIYA_ALT" not in alts:\n                raise RuntimeError("ATOMIC_TX_TOO_LARGE:1414")\n            return b"msg",b"x"*1200\n        q.c.compile_v0=fake_compile; q.recent_mriya_alt_keys=lambda:["MRIYA_ALT"]\n        try:\n            msg,raw,alts=q.compile_compact("U",[],["PUMP_ALT"],"BH")\n            self.assertEqual(len(raw),1200); self.assertIn("MRIYA_ALT",alts); self.assertEqual(len(calls),2)\n        finally:\n            q.c.compile_v0=old_compile; q.recent_mriya_alt_keys=old_alts\n        print("[PASS] 1414-byte failure retries using recent Mriya ALTs")\n\n    def test_no_broadcast(self):\n        with open(q.__file__,encoding="utf-8") as f: src=f.read()\n        self.assertNotIn("c.send(raw)",src)\n        print("[PASS] QSB-059C still simulation-only")\n\nif __name__=="__main__": unittest.main(verbosity=2)\n''',encoding='utf-8')
py_compile.compile(str(TEST),doraise=True)

RUN=ROOT/'run_qsb_059c_atomic_size_compaction.py'
RUN.write_text('from qseries_v2.oracle_strategy_intelligence.solana_money.qsb059_gav_reverse_atomic import run\nrun()\n',encoding='utf-8')
py_compile.compile(str(RUN),doraise=True)

print('[PASS] QSB-059C atomic size compaction installed')
print('[FIX] removes forced 3-array DLMM overhead')
print('[FIX] memo removed; duplicate compute-budget instructions compacted')
print('[FIX] retries v0 compile with recent Mriya lookup tables')
print('[TARGET] repair ATOMIC_TX_TOO_LARGE:1414')
print('[MODE] simulation only; execution_authority=FALSE')
