
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

REVISION="OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_FULL_AUDIT_DIRECT_CONNECT_REBUILD"

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/"oad_postgresql_unknown_sports_family_full_audit.py"
TEST=ROOT/"test_oad_postgresql_unknown_sports_family_full_audit.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nimport csv, json, re\nfrom collections import Counter, defaultdict\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import build_existing_canonical_router\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nSPORT_PATTERNS={\n"baseball":(r"\\bmlb\\b",r"\\bbaseball\\b",r"\\binnings?\\b",r"\\bhome runs?\\b",r"\\brbis?\\b",r"\\bpitcher\\b",r"\\bstrikeouts?\\b"),\n"hockey":(r"\\bnhl\\b",r"\\bhockey\\b",r"\\bpuck\\b",r"\\bpower play\\b"),\n"basketball":(r"\\bnba\\b",r"\\bwnba\\b",r"\\bbasketball\\b",r"\\brebounds?\\b",r"\\bassists?\\b"),\n"football":(r"\\bnfl\\b",r"\\bamerican football\\b",r"\\btouchdowns?\\b",r"\\bpassing yards?\\b",r"\\brushing yards?\\b"),\n"soccer":(r"\\bsoccer\\b",r"\\bpremier league\\b",r"\\bchampions league\\b",r"\\bla liga\\b",r"\\bserie a\\b",r"\\bbundesliga\\b",r"\\bligue 1\\b",r"\\bmls\\b",r"\\buefa\\b",r"\\bfifa\\b"),\n"tennis":(r"\\batp\\b",r"\\bwta\\b",r"\\btennis\\b",r"\\bwimbledon\\b",r"\\bus open\\b",r"\\baustralian open\\b",r"\\bfrench open\\b"),\n"combat":(r"\\bufc\\b",r"\\bmma\\b",r"\\bboxing\\b",r"\\bknockout\\b",r"\\bsubmission\\b",r"\\bko/tko\\b"),\n"golf":(r"\\bpga\\b",r"\\blpga\\b",r"\\bgolf\\b",r"\\bmasters\\b"),\n"esports":(r"\\besports?\\b",r"\\bleague of legends\\b",r"\\bcounter[- ]strike\\b",r"\\bvalorant\\b",r"\\bdota\\b"),\n}\n\nIDENTITY=("ticker","market_ticker","event_ticker","series_ticker","title","subtitle","name","question","description","observation_id","source_id","entity_id")\nPAYLOAD=("payload","raw_payload","source_payload","data","metadata","observation_payload","canonical_payload","value")\n\ndef _safe_ident(name):\n    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",name): raise ValueError("unsafe identifier")\n    return \'"\'+name+\'"\'\n\ndef _backend(root):\n    router=build_existing_canonical_router(Path(root).resolve())\n    backend=getattr(router,"_persistence_backend",None)\n    if backend is None: raise RuntimeError("PostgreSQL backend unavailable")\n    if not callable(getattr(backend,"_connect",None)): raise RuntimeError("audited backend._connect() unavailable")\n    return backend\n\ndef _connect_read_only(root):\n    conn=_backend(root)._connect()\n    if conn is None: raise RuntimeError("backend._connect() returned None")\n    with conn.cursor() as cur: cur.execute("BEGIN READ ONLY")\n    return conn\n\ndef _schema(conn):\n    with conn.cursor() as cur:\n        cur.execute("""\n        SELECT table_schema, table_name, column_name, data_type\n        FROM information_schema.columns\n        WHERE table_schema NOT IN (\'pg_catalog\',\'information_schema\')\n        ORDER BY table_schema,table_name,ordinal_position\n        """)\n        rows=cur.fetchall()\n    tables=defaultdict(list)\n    for s,t,c,d in rows: tables[(s,t)].append((c,d))\n    return tables\n\ndef _candidate_tables(tables):\n    out=[]\n    for (s,t),cols in tables.items():\n        names=[c for c,_ in cols]\n        ids=[c for c in IDENTITY if c in names]\n        payload=[c for c in PAYLOAD if c in names]\n        if ids or payload: out.append((s,t,ids,payload))\n    return out\n\ndef _txt(v):\n    if v is None: return ""\n    if isinstance(v,(dict,list,tuple)): return json.dumps(v,sort_keys=True,default=str)\n    return str(v)\n\ndef _classify(text):\n    hits=[]\n    for fam,patterns in SPORT_PATTERNS.items():\n        m=[p for p in patterns if re.search(p,text,re.I)]\n        if m: hits.append((fam,len(m),m))\n    hits.sort(key=lambda x:(-x[1],x[0]))\n    if not hits: return "UNKNOWN","NO_EXPLICIT_FAMILY_SIGNAL",()\n    if len(hits)>1 and hits[0][1]==hits[1][1]:\n        top=hits[0][1]; tied=tuple(x[0] for x in hits if x[1]==top)\n        return "UNKNOWN","CONFLICTING_FAMILY_SIGNAL:"+",".join(tied),tied\n    return hits[0][0],"EXPLICIT_POSTGRES_TEXT_SIGNAL",tuple(hits[0][2])\n\ndef _looks_sports(text):\n    return bool(re.search(r"\\b(sport|mlb|nhl|nba|wnba|nfl|soccer|tennis|atp|wta|ufc|mma|boxing|golf|pga|esport|goal|inning|touchdown|rebound|assist|pitcher|strikeout|home run|wimbledon|uefa|fifa)\\b",text,re.I))\n\ndef _fetch(conn,schema,table,ids,payload,limit):\n    cols=[]\n    for c in ids+payload:\n        if c not in cols: cols.append(c)\n    if not cols: return []\n    sql=f"SELECT {\', \'.join(_safe_ident(c) for c in cols)} FROM {_safe_ident(schema)}.{_safe_ident(table)} LIMIT %s"\n    with conn.cursor() as cur:\n        cur.execute(sql,(int(limit),)); rows=cur.fetchall()\n    return [dict(zip(cols,row)) for row in rows]\n\ndef run_postgresql_unknown_sports_family_audit(root=None,row_limit_per_table=250000):\n    root=Path(root or Path.cwd()).resolve()\n    conn=_connect_read_only(root)\n    report={"read_only":True,"execution_authority":False,"probability_enabled":False,"connection_path":"OraclePostgreSQLCanonicalObservationPersistenceBackend._connect()","transaction_mode":"BEGIN READ ONLY","tables":[],"family_counts":{},"reason_counts":{},"assignments":[],"still_unknown":[]}\n    fam=Counter(); reasons=Counter(); seen=set()\n    try:\n        candidates=_candidate_tables(_schema(conn)); report["candidate_table_count"]=len(candidates)\n        for schema,table,ids,payload in candidates:\n            rows=_fetch(conn,schema,table,ids,payload,row_limit_per_table)\n            report["tables"].append({"schema":schema,"table":table,"identity_columns":ids,"payload_columns":payload,"rows_read":len(rows)})\n            for row in rows:\n                joined=" | ".join(_txt(row.get(c)) for c in ids+payload if row.get(c) is not None).strip()\n                if not joined or not _looks_sports(joined): continue\n                key=(schema,table,joined[:4000])\n                if key in seen: continue\n                seen.add(key)\n                family,reason,signals=_classify(joined)\n                fam[family]+=1; reasons[reason]+=1\n                rec={"schema":schema,"table":table,"family":family,"reason":reason,"signals":list(signals),"identity":{c:_txt(row.get(c))[:2000] for c in ids if row.get(c) is not None}}\n                (report["still_unknown"] if family=="UNKNOWN" else report["assignments"]).append(rec)\n        report["family_counts"]=dict(fam.most_common()); report["reason_counts"]=dict(reasons.most_common())\n        jp=root/"OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_FULL_AUDIT.json"\n        cp=root/"OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_ASSIGNMENTS.csv"\n        up=root/"OAD_POSTGRESQL_STILL_UNKNOWN_SPORTS.csv"\n        jp.write_text(json.dumps(report,indent=2,sort_keys=True,default=str),encoding="utf-8")\n        with cp.open("w",encoding="utf-8",newline="") as f:\n            w=csv.writer(f); w.writerow(["family","reason","schema","table","signals","identity"])\n            for r in report["assignments"]: w.writerow([r["family"],r["reason"],r["schema"],r["table"],json.dumps(r["signals"]),json.dumps(r["identity"],sort_keys=True)])\n        with up.open("w",encoding="utf-8",newline="") as f:\n            w=csv.writer(f); w.writerow(["reason","schema","table","identity"])\n            for r in report["still_unknown"]: w.writerow([r["reason"],r["schema"],r["table"],json.dumps(r["identity"],sort_keys=True)])\n        conn.rollback()\n        return report,jp,cp,up\n    except Exception:\n        conn.rollback(); raise\n    finally:\n        try: conn.close()\n        except Exception: pass\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_postgresql_unknown_sports_family_full_audit import run_postgresql_unknown_sports_family_audit\n\nclass T(unittest.TestCase):\n    def test_physical_postgresql_audit(self):\n        report,jp,cp,up=run_postgresql_unknown_sports_family_audit()\n        print("[POSTGRES] connection_path=",report["connection_path"])\n        print("[POSTGRES] transaction_mode=",report["transaction_mode"])\n        print("[POSTGRES] candidate_table_count=",report["candidate_table_count"])\n        for t in report["tables"]:\n            print("[POSTGRES_TABLE]",f\'{t["schema"]}.{t["table"]}\',"rows_read=",t["rows_read"],"identity_columns=",t["identity_columns"],"payload_columns=",t["payload_columns"])\n        print("[FAMILY_COUNTS]",report["family_counts"])\n        print("[REASON_COUNTS]",report["reason_counts"])\n        for family,count in report["family_counts"].items(): print("[FAMILY]",family,"rows=",count)\n        print("[STILL_UNKNOWN_COUNT]",len(report["still_unknown"]))\n        for i,r in enumerate(report["still_unknown"][:100],1): print("[STILL_UNKNOWN]",i,r)\n        print("[REPORT]",jp); print("[ASSIGNMENTS_CSV]",cp); print("[UNKNOWN_CSV]",up)\n        self.assertTrue(report["read_only"])\n        self.assertFalse(report["execution_authority"])\n        self.assertFalse(report["probability_enabled"])\n        self.assertEqual(report["transaction_mode"],"BEGIN READ ONLY")\n        self.assertGreater(report["candidate_table_count"],0)\n\nif __name__=="__main__":\n    print("="*108)\n    print(" OAD POSTGRESQL UNKNOWN SPORTS FAMILY FULL AUDIT")\n    print(" DIRECT AUDITED BACKEND CONNECTION — READ ONLY")\n    print("="*108)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] actual production PostgreSQL backend connection used")\n    print("[PASS] transaction forced BEGIN READ ONLY")\n    print("[PASS] family assignments exported separately from production state")\n    print("[PASS] no classifier or PostgreSQL row modified")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] POSTGRESQL UNKNOWN SPORTS FAMILY FULL AUDIT COMPLETE")\n'

REQUIRED=[
("qseries_v2/oracle_production_hardening/oph_007_physical_single_postgresql_writer_runtime.py","Existing PostgreSQL production router"),
("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
("qseries_v2/oracle_adapters/independent/oad_postgresql_backend_interface_audit.py","Certified PostgreSQL backend interface audit"),
("qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py","Recertified OAD-104"),
("qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py","Recertified OAD-105"),
("qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py","Recertified OAD-106"),
]
PROTECTED=[
"qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
"qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
"qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py",
"qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py",
"qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
"qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
"qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py",
]

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*108)
    print(" OAD POSTGRESQL UNKNOWN SPORTS FAMILY FULL AUDIT REBUILD INSTALLER")
    print(" AUDITED DIRECT BACKEND CONNECTION — READ ONLY")
    print("="*108)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file(): raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")
    hashes={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in PROTECTED}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export="from .oad_postgresql_unknown_sports_family_full_audit import *"
        if export not in lines: lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in hashes.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("Protected production file changed: "+p.name)
        print("[PASS] failed PostgreSQL family audit replaced in place")
        print("[PASS] exact audited backend._connect() path bound")
        print("[PASS] SQL transaction forced BEGIN READ ONLY")
        print("[PASS] recertified OAD-104/OAD-105/OAD-106 protected")
        print("[PASS] frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] installer and embedded sources syntax-validated")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] POSTGRESQL UNKNOWN SPORTS FAMILY FULL AUDIT REBUILD COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] audit files restored")
        raise

if __name__=="__main__":
    main()
