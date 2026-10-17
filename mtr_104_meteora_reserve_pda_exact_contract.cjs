const fs=require("fs");
const path=require("path");

console.log("[MTR-104] START");
console.log("[SCOPE] exact Meteora reserve-PDA + pair field contract; local only");

const entry=require.resolve("@meteora-ag/dlmm");
let d=path.dirname(entry),root=null;

while(true){
 const pj=path.join(d,"package.json");
 if(fs.existsSync(pj)){
  try{
   const j=JSON.parse(fs.readFileSync(pj,"utf8"));
   if(j.name==="@meteora-ag/dlmm"){root=d;break}
  }catch{}
 }
 const up=path.dirname(d);
 if(up===d)break;
 d=up;
}
if(!root)throw Error("METEORA_ROOT_NOT_FOUND");

const src=path.join(root,"dist","index.js");
if(!fs.existsSync(src))throw Error("METEORA_INDEX_NOT_FOUND");

const lines=fs.readFileSync(src,"utf8").split(/\r?\n/);

function emit(a,b,label){
 console.log(`\n[${label}]`);
 for(let i=a;i<=b;i++) console.log(`[L${i}] ${lines[i-1]}`);
}

emit(10572,10588,"DERIVE_RESERVE_EXACT");
emit(10450,10530,"PAIR_DERIVATION_CONTEXT");

const text=fs.readFileSync(src,"utf8");
const keys=["reserveX","reserveY","tokenXMint","tokenYMint"];
const hits=[];

for(const k of keys){
 let from=0,count=0;
 while(count<20){
  const i=text.indexOf(k,from);
  if(i<0)break;
  const ln=text.slice(0,i).split("\n").length;
  hits.push({term:k,line:ln});
  from=i+k.length;
  count++;
 }
}

console.log("\n[FIELD_HITS]");
for(const h of hits.slice(0,80))
 console.log(`[FIELD] ${h.term} line=${h.line}`);

fs.writeFileSync("mtr_104_meteora_reserve_pda_exact_contract.json",
 JSON.stringify({
  sdk_root:root,
  source:src,
  reserve_function:lines.slice(10571,10588),
  pair_context:lines.slice(10449,10530),
  field_hits:hits
 },null,2));

console.log("\n[RESULT] METEORA_RESERVE_PDA_EXACT_CONTRACT_CAPTURED");
console.log("[OUTPUT] mtr_104_meteora_reserve_pda_exact_contract.json");
console.log("[RPC] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-104] COMPLETE");
