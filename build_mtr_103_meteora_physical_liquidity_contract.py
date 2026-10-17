from pathlib import Path

p=Path("mtr_103_meteora_physical_liquidity_contract.cjs")
p.write_text(r'''const fs=require("fs");
const path=require("path");

console.log("[MTR-103] START");
console.log("[SCOPE] installed Meteora DLMM physical-liquidity contract; local only");

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
if(!root)throw Error("METEORA_SDK_ROOT_NOT_FOUND");

console.log(`[ENTRYPOINT] ${entry}`);
console.log(`[SDK_ROOT] ${root}`);

function walk(dir,out=[]){
 for(const e of fs.readdirSync(dir,{withFileTypes:true})){
  const q=path.join(dir,e.name);
  if(e.isDirectory()&&e.name!=="node_modules")walk(q,out);
  else if(e.isFile()&&/\.(js|cjs|mjs|ts|d\.ts)$/.test(e.name))out.push(q);
 }
 return out;
}

const terms=/reserveX|reserveY|tokenX|tokenY|getTokenAccountBalance|getMultipleAccountsInfo|lbPair|tokenXMint|tokenYMint/i;
const files=walk(root),hits=[];

for(const f of files){
 let s;
 try{s=fs.readFileSync(f,"utf8")}catch{continue}
 if(!terms.test(s))continue;

 const lines=s.split(/\r?\n/),found=[];
 for(let i=0;i<lines.length;i++){
  if(terms.test(lines[i]))
   found.push({line:i+1,text:lines[i].trim().slice(0,280)});
 }
 if(!found.length)continue;

 hits.push({file:path.relative(root,f),found:found.slice(0,120)});
 console.log(`\n[FILE] ${path.relative(root,f)}`);
 for(const h of found.slice(0,60))
  console.log(`[L${h.line}] ${h.text}`);
}

fs.writeFileSync("mtr_103_meteora_physical_liquidity_contract.json",
 JSON.stringify({
  entrypoint:entry,
  sdk_root:root,
  files_scanned:files.length,
  hit_files:hits.length,
  hits
 },null,2));

console.log(`\n[SUMMARY] files=${files.length} hit_files=${hits.length}`);
console.log(hits.length?
 "[RESULT] METEORA_PHYSICAL_LIQUIDITY_CONTRACT_CAPTURED":
 "[RESULT] METEORA_PHYSICAL_LIQUIDITY_CONTRACT_NOT_FOUND");
console.log("[OUTPUT] mtr_103_meteora_physical_liquidity_contract.json");
console.log("[RPC] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-103] COMPLETE");
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] Meteora DLMM physical-liquidity contract capture")
print("[SCOPE] installed source only; no RPC; no pricing; no signing")