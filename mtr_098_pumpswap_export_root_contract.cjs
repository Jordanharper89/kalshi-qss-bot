const fs=require("fs");
const path=require("path");

function walk(root,out=[]){
 for(const e of fs.readdirSync(root,{withFileTypes:true})){
  const p=path.join(root,e.name);
  if(e.isDirectory() && e.name!=="node_modules") walk(p,out);
  else if(e.isFile() && /\.(js|cjs|mjs|ts|json)$/.test(e.name)) out.push(p);
 }
 return out;
}
function findRoot(start){
 let d=path.dirname(start);
 while(true){
  const pj=path.join(d,"package.json");
  if(fs.existsSync(pj)){
   try{
    const j=JSON.parse(fs.readFileSync(pj,"utf8"));
    if(j.name==="@pump-fun/pump-swap-sdk") return d;
   }catch{}
  }
  const up=path.dirname(d);
  if(up===d)break;
  d=up;
 }
 throw Error("PUMPSWAP_PACKAGE_ROOT_NOT_FOUND");
}

console.log("[MTR-098] START");
console.log("[SCOPE] exported-entrypoint PumpSwap SDK contract capture; local only");

const entry=require.resolve("@pump-fun/pump-swap-sdk");
const root=findRoot(entry);
console.log(`[ENTRYPOINT] ${entry}`);
console.log(`[SDK_ROOT] ${root}`);

const files=walk(root),hits=[];
const terms=/poolBaseAmount|poolQuoteAmount|baseTokenAccount|quoteTokenAccount|virtualQuoteReserves|swapSolanaState|fetchPool|poolAccount/i;

for(const f of files){
 let s;
 try{s=fs.readFileSync(f,"utf8")}catch{continue}
 if(!terms.test(s))continue;

 const found=[];
 const lines=s.split(/\r?\n/);
 for(let i=0;i<lines.length;i++){
  if(terms.test(lines[i]))
   found.push({line:i+1,text:lines[i].trim().slice(0,260)});
 }
 if(!found.length)continue;

 hits.push({file:path.relative(root,f),found:found.slice(0,100)});
 console.log(`\n[FILE] ${path.relative(root,f)}`);
 for(const h of found.slice(0,50))
  console.log(`[L${h.line}] ${h.text}`);
}

const pkg=require("@pump-fun/pump-swap-sdk");
console.log("\n[EXPORT_KEYS]");
console.log(Object.keys(pkg).sort().join(","));

for(const k of ["PumpAmmSdk","OnlinePumpAmmSdk","PUMP_AMM_SDK"]){
 const x=pkg[k];
 console.log(`[EXPORT] ${k} type=${typeof x}`);
 if(x&&x.prototype)
  console.log(`[METHODS] ${k} ${Object.getOwnPropertyNames(x.prototype).sort().join(",")}`);
}

fs.writeFileSync("mtr_098_pumpswap_export_root_contract.json",
 JSON.stringify({
  entrypoint:entry,
  sdk_root:root,
  files_scanned:files.length,
  hit_files:hits.length,
  hits,
  exports:Object.keys(pkg).sort()
 },null,2));

console.log(`\n[SUMMARY] files=${files.length} hit_files=${hits.length}`);
console.log(hits.length?
 "[RESULT] PUMPSWAP_POOL_CONTRACT_CAPTURED":
 "[RESULT] PUMPSWAP_POOL_CONTRACT_NOT_FOUND");
console.log("[OUTPUT] mtr_098_pumpswap_export_root_contract.json");
console.log("[RPC] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-098] COMPLETE");
