"use strict";
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=process.cwd(),OUT=path.join(ROOT,'runtime_state/oracle/oracle_live_execution/ORACLE_118_SCANNER_INTEGRITY.json');
const SOL='So11111111111111111111111111111111111111112';
const VALID=/^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
const safe=(s)=>String(s||'').replace(/(api-key=)[^&\s]+/gi,'$1[REDACTED]').replace(/https?:\/\/[^\s]+/gi,'[URL_REDACTED]').slice(0,180);
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
function normalized(raw){let list=Array.isArray(raw)?raw:Array.isArray(raw?.rows)?raw.rows:Array.isArray(raw?.pairs)?raw.pairs:[];
 return list.map((r,i)=>({index:i,token:r.token||r.token_mint||r.base_mint,pump_pool:r.pump_pool||r.pump,meteora_pool:r.meteora_pool||r.dlmm,observed_unix:r.observed_unix||r.updated_unix||r.timestamp||null})).filter(r=>VALID.test(r.token||'')&&VALID.test(r.pump_pool||'')&&VALID.test(r.meteora_pool||'')&&r.token!==SOL);
}
function unique(rows){const seen=new Set();return rows.filter(r=>{const key=[r.token,r.pump_pool,r.meteora_pool].join(':');if(seen.has(key))return false;seen.add(key);return true})}
function freshness(row,now,maxAge){const ts=Number(row.observed_unix);return Number.isFinite(ts)&&ts>0&&ts<=now+30&&now-ts<=maxAge}
function inspectFile(file){const s=fs.statSync(file);if(!s.isFile()||s.size>25000000)return null;const raw=JSON.parse(fs.readFileSync(file,'utf8'));const rows=normalized(raw);return rows.length?{file:path.relative(ROOT,file),mtime_ms:s.mtimeMs,rows,sha256:hash(fs.readFileSync(file))}:null}
function findCandidates(){const roots=['runtime_state/oracle/oracle_live_execution','runtime_state/oracle/solana_atomic_executor'];let files=[];
 for(const base of roots){const dir=path.join(ROOT,base);if(!fs.existsSync(dir))continue;for(const item of fs.readdirSync(dir,{withFileTypes:true})){if(!item.isFile()||!item.name.endsWith('.json'))continue;const f=path.join(dir,item.name);try{const hit=inspectFile(f);if(hit)files.push(hit)}catch(e){}}}
 return files.sort((a,b)=>b.mtime_ms-a.mtime_ms);
}
function select(sources,now,maxAge){const out=[];for(const src of sources){for(const row of unique(src.rows)){if(!freshness(row,now,maxAge))continue;out.push({...row,source:src.file,source_sha256:src.sha256})}}
 return unique(out);
}
function report(){const now=Math.floor(Date.now()/1000),maxAge=Number(process.env.ORACLE118_MAX_AGE_SECONDS||90);if(!Number.isFinite(maxAge)||maxAge<1||maxAge>3600)throw Error('INVALID_MAX_AGE');
 const sources=findCandidates(),fresh=select(sources,now,maxAge);const registry=sources.find(x=>x.file.endsWith('multi_dlmm_pair_registry.json'));
 const output={revision:'ORACLE-118',status:fresh.length?'FRESH_CANDIDATES_UNVERIFIED_SCANNER_LINEAGE':'HOLD_NO_FRESH_VERIFIED_SCANNER_CANDIDATES',scanner_modified:false,signing:false,broadcast:false,execution_admitted:false,generated_unix:now,max_age_seconds:maxAge,source_count:sources.length,registry_count:registry?.rows.length||0,source_summaries:sources.map(x=>({file:x.file,rows:x.rows.length,sha256:x.sha256})),fresh_candidates:fresh.length,candidates:fresh.slice(0,40),next_gate:'PHYSICAL_SCANNER_OUTPUT_CONTRACT_AND_ATOMIC_SIMULATION'};
 fs.mkdirSync(path.dirname(OUT),{recursive:true});fs.writeFileSync(OUT,JSON.stringify(output,null,2));console.log('[ORACLE-118]',output.status,'sources='+sources.length,'fresh='+fresh.length);console.log('[SCANNER] UNCHANGED [SIGNING] FALSE [BROADCAST] FALSE');console.log('[REPORT]',OUT);
 if(fresh.length)console.log('[NOTICE] Candidate freshness does not prove scanner lineage, profitability, or execution readiness');
}
if(require.main===module){try{report()}catch(e){console.error('[HOLD]',safe(e));process.exitCode=1}}
module.exports={normalized,unique,freshness,select};

