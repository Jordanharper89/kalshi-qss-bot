from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

REVISION="OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_FULL_AUDIT_V1"

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/"oad_postgresql_unknown_sports_family_full_audit.py"
TEST=ROOT/"test_oad_postgresql_unknown_sports_family_full_audit.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='\nfrom __future__ import annotations\n\nimport csv\nimport json\nimport re\nfrom collections import Counter, defaultdict\nfrom contextlib import contextmanager\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (\n    build_existing_canonical_router,\n)\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nSPORT_PATTERNS={\n    "baseball":(\n        r"\\bmlb\\b",r"\\bbaseball\\b",r"\\binnings?\\b",r"\\bhome runs?\\b",\n        r"\\brbis?\\b",r"\\bpitcher\\b",r"\\bstrikeouts?\\b",\n    ),\n    "hockey":(\n        r"\\bnhl\\b",r"\\bhockey\\b",r"\\bpuck\\b",r"\\bpower play\\b",\n    ),\n    "basketball":(\n        r"\\bnba\\b",r"\\bwnba\\b",r"\\bncaa basketball\\b",r"\\bbasketball\\b",\n        r"\\brebounds?\\b",r"\\bassists?\\b",\n    ),\n    "football":(\n        r"\\bnfl\\b",r"\\bncaa football\\b",r"\\bfootball\\b",r"\\btouchdowns?\\b",\n        r"\\bpassing yards?\\b",r"\\brushing yards?\\b",\n    ),\n    "soccer":(\n        r"\\bsoccer\\b",r"\\bpremier league\\b",r"\\bchampions league\\b",\n        r"\\bla liga\\b",r"\\bserie a\\b",r"\\bbundesliga\\b",r"\\bligue 1\\b",\n        r"\\bmls\\b",r"\\buefa\\b",r"\\bfifa\\b",\n    ),\n    "tennis":(\n        r"\\batp\\b",r"\\bwta\\b",r"\\btennis\\b",r"\\bwimbledon\\b",\n        r"\\bus open\\b",r"\\baustralian open\\b",r"\\bfrench open\\b",\n    ),\n    "combat":(\n        r"\\bufc\\b",r"\\bmma\\b",r"\\bboxing\\b",r"\\bknockout\\b",\n        r"\\bsubmission\\b",r"\\bko/tko\\b",\n    ),\n    "golf":(\n        r"\\bpga\\b",r"\\blpga\\b",r"\\bgolf\\b",r"\\bmasters\\b",\n    ),\n    "esports":(\n        r"\\besports?\\b",r"\\bleague of legends\\b",r"\\bcounter[- ]strike\\b",\n        r"\\bvalorant\\b",r"\\bdota\\b",\n    ),\n}\n\nIDENTITY_NAMES=("ticker","market_ticker","event_ticker","series_ticker","title","subtitle","name","question","description")\nPAYLOAD_NAMES=("payload","raw_payload","source_payload","data","metadata","observation_payload")\n\ndef _safe_ident(name):\n    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",name):\n        raise ValueError("unsafe SQL identifier")\n    return \'"\'+name+\'"\'\n\ndef _backend(root):\n    router=build_existing_canonical_router(Path(root).resolve())\n    backend=getattr(router,"_persistence_backend",None)\n    if backend is None:\n        raise RuntimeError("existing PostgreSQL persistence backend unavailable")\n    return backend\n\ndef _pool_from_backend(backend):\n    for name in ("_pool","pool","_connection_pool","connection_pool"):\n        obj=getattr(backend,name,None)\n        if obj is not None and callable(getattr(obj,"connection",None)):\n            return obj\n    for value in vars(backend).values():\n        if callable(getattr(value,"connection",None)):\n            return value\n    raise RuntimeError(\n        "PostgreSQL connection pool not exposed by existing backend; "\n        "no direct SQL was attempted"\n    )\n\n@contextmanager\ndef _readonly_connection(root):\n    backend=_backend(root)\n    pool=_pool_from_backend(backend)\n    with pool.connection() as conn:\n        old_autocommit=getattr(conn,"autocommit",None)\n        try:\n            if old_autocommit is not None:\n                conn.autocommit=False\n            with conn.cursor() as cur:\n                cur.execute("BEGIN READ ONLY")\n            yield conn\n            conn.rollback()\n        except Exception:\n            conn.rollback()\n            raise\n        finally:\n            if old_autocommit is not None:\n                conn.autocommit=old_autocommit\n\ndef _schema(conn):\n    sql="""\n    SELECT table_schema, table_name, column_name, data_type\n    FROM information_schema.columns\n    WHERE table_schema NOT IN (\'pg_catalog\',\'information_schema\')\n    ORDER BY table_schema, table_name, ordinal_position\n    """\n    with conn.cursor() as cur:\n        cur.execute(sql)\n        rows=cur.fetchall()\n    tables=defaultdict(list)\n    for schema,table,column,dtype in rows:\n        tables[(schema,table)].append((column,dtype))\n    return tables\n\ndef _candidate_tables(tables):\n    result=[]\n    for (schema,table),cols in tables.items():\n        names={c for c,_ in cols}\n        identity=[c for c in IDENTITY_NAMES if c in names]\n        payload=[c for c in PAYLOAD_NAMES if c in names]\n        if identity or payload:\n            result.append((schema,table,identity,payload,tuple(c for c,_ in cols)))\n    return result\n\ndef _text(v):\n    if v is None: return ""\n    if isinstance(v,(dict,list,tuple)):\n        return json.dumps(v,sort_keys=True,default=str)\n    return str(v)\n\ndef _classify(text):\n    hits=[]\n    low=text.lower()\n    for family,patterns in SPORT_PATTERNS.items():\n        score=sum(1 for p in patterns if re.search(p,low,re.I))\n        if score:\n            hits.append((family,score))\n    hits.sort(key=lambda x:(-x[1],x[0]))\n    if not hits:\n        return "UNKNOWN","NO_EXPLICIT_FAMILY_SIGNAL"\n    if len(hits)>1 and hits[0][1]==hits[1][1]:\n        return "UNKNOWN","CONFLICTING_FAMILY_SIGNAL:"+",".join(x[0] for x in hits if x[1]==hits[0][1])\n    return hits[0][0],"EXPLICIT_POSTGRES_TEXT_SIGNAL"\n\ndef _fetch_table(conn,schema,table,identity,payload,limit):\n    selected=[]\n    for c in identity+payload:\n        if c not in selected:\n            selected.append(c)\n    if not selected:\n        return []\n    cols=", ".join(_safe_ident(c) for c in selected)\n    sql=f"SELECT {cols} FROM {_safe_ident(schema)}.{_safe_ident(table)} LIMIT %s"\n    with conn.cursor() as cur:\n        cur.execute(sql,(int(limit),))\n        rows=cur.fetchall()\n    return [dict(zip(selected,row)) for row in rows]\n\ndef run_postgresql_unknown_sports_family_audit(root=None,row_limit_per_table=200000):\n    root=Path(root or Path.cwd()).resolve()\n    report={\n        "read_only":True,\n        "execution_authority":False,\n        "probability_enabled":False,\n        "tables":[],\n        "family_counts":{},\n        "reason_counts":{},\n        "assignments":[],\n        "unknown_examples":[],\n    }\n    family=Counter(); reasons=Counter()\n    dedup=set()\n\n    with _readonly_connection(root) as conn:\n        tables=_schema(conn)\n        candidates=_candidate_tables(tables)\n        report["candidate_table_count"]=len(candidates)\n\n        for schema,table,identity,payload,allcols in candidates:\n            rows=_fetch_table(conn,schema,table,identity,payload,row_limit_per_table)\n            table_rec={\n                "schema":schema,\n                "table":table,\n                "identity_columns":identity,\n                "payload_columns":payload,\n                "rows_read":len(rows),\n            }\n            report["tables"].append(table_rec)\n\n            for row in rows:\n                joined=" | ".join(_text(row.get(c)) for c in identity+payload if row.get(c) is not None)\n                if not joined.strip():\n                    continue\n\n                # Keep only rows with a sports signal or market-style identity.\n                sports_hint=bool(re.search(\n                    r"\\b(sport|mlb|nhl|nba|wnba|nfl|soccer|tennis|atp|wta|ufc|mma|golf|pga|esport|goal|inning|touchdown|rebounds?)\\b",\n                    joined,re.I\n                ))\n                if not sports_hint:\n                    continue\n\n                fam,reason=_classify(joined)\n                key=(schema,table,joined[:1000])\n                if key in dedup:\n                    continue\n                dedup.add(key)\n                family[fam]+=1; reasons[reason]+=1\n\n                rec={\n                    "schema":schema,\n                    "table":table,\n                    "family":fam,\n                    "reason":reason,\n                    "identity":{c:_text(row.get(c))[:1000] for c in identity if row.get(c) is not None},\n                }\n                if fam=="UNKNOWN":\n                    if len(report["unknown_examples"])<200:\n                        report["unknown_examples"].append(rec)\n                else:\n                    report["assignments"].append(rec)\n\n    report["family_counts"]=dict(family.most_common())\n    report["reason_counts"]=dict(reasons.most_common())\n\n    json_path=root/"OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_FULL_AUDIT.json"\n    csv_path=root/"OAD_POSTGRESQL_UNKNOWN_SPORTS_FAMILY_ASSIGNMENTS.csv"\n    json_path.write_text(json.dumps(report,indent=2,sort_keys=True,default=str),encoding="utf-8")\n\n    with csv_path.open("w",encoding="utf-8",newline="") as f:\n        w=csv.writer(f)\n        w.writerow(["family","reason","schema","table","identity"])\n        for rec in report["assignments"]:\n            w.writerow([\n                rec["family"],rec["reason"],rec["schema"],rec["table"],\n                json.dumps(rec["identity"],sort_keys=True),\n            ])\n\n    return report,json_path,csv_path\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_postgresql_unknown_sports_family_full_audit import (\n    run_postgresql_unknown_sports_family_audit,\n)\n\nclass T(unittest.TestCase):\n    def test_physical_postgresql_audit(self):\n        report,json_path,csv_path=run_postgresql_unknown_sports_family_audit()\n        print("[POSTGRES] candidate_table_count=",report["candidate_table_count"])\n        for t in report["tables"]:\n            print(\n                "[POSTGRES_TABLE]",\n                f\'{t["schema"]}.{t["table"]}\',\n                "rows_read=",t["rows_read"],\n                "identity_columns=",t["identity_columns"],\n                "payload_columns=",t["payload_columns"],\n            )\n        print("[FAMILY_COUNTS]",report["family_counts"])\n        print("[REASON_COUNTS]",report["reason_counts"])\n        for family,count in report["family_counts"].items():\n            print("[FAMILY]",family,"rows=",count)\n        for i,rec in enumerate(report["unknown_examples"][:50],1):\n            print("[STILL_UNKNOWN]",i,rec)\n        print("[REPORT]",json_path)\n        print("[CSV]",csv_path)\n\n        self.assertTrue(report["read_only"])\n        self.assertFalse(report["execution_authority"])\n        self.assertFalse(report["probability_enabled"])\n        self.assertGreater(report["candidate_table_count"],0)\n\nif __name__=="__main__":\n    print("="*108)\n    print(" OAD POSTGRESQL UNKNOWN SPORTS FAMILY FULL AUDIT")\n    print(" READ-ONLY PRODUCTION DATABASE FAMILY IDENTIFICATION")\n    print("="*108)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] PostgreSQL inspected through existing production backend")\n    print("[PASS] transaction forced READ ONLY")\n    print("[PASS] family assignments written separately from production state")\n    print("[PASS] no classifier or PostgreSQL row modified")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] POSTGRESQL UNKNOWN SPORTS FAMILY AUDIT COMPLETE")\n'

REQUIRED=[
    ("qseries_v2/oracle_production_hardening/oph_007_physical_single_postgresql_writer_runtime.py","Existing PostgreSQL production router"),
    ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
    ("qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py","Recertified OAD-104"),
    ("qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py","Recertified OAD-105"),
    ("qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py","Recertified OAD-106"),
]

FROZEN=[
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
    print(" OAD POSTGRESQL UNKNOWN SPORTS FAMILY AUDIT INSTALLER")
    print(" READ-ONLY FULL DATABASE FAMILY IDENTIFICATION")
    print("="*108)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")

    hashes={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}

    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export="from .oad_postgresql_unknown_sports_family_full_audit import *"
        if export not in lines:
            lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in hashes.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Protected production file changed: "+p.name)

        print("[PASS] Diagnostic module installed")
        print("[PASS] Diagnostic test installed")
        print("[PASS] OAD-104/OAD-105/OAD-106 protected read-only")
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] PostgreSQL audit uses BEGIN READ ONLY")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] POSTGRESQL UNKNOWN SPORTS FAMILY AUDIT INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] Diagnostic files restored")
        raise

if __name__=="__main__":
    main()
