from pathlib import Path

p = Path("mtr_097_pumpswap_pool_layout_contract.cjs")
p.write_text(r'''const fs=require("fs");
const path=require("path");

function walk(root,out=[]){
 for(const e of fs.readdirSync(root,{withFileTypes:true})){
  const p=path.join(root,e.name);
  if(e.isDirectory()) walk(p,out);
  else if(/\.(js|json|ts)$/.test(e.name)) out.push(p);
 }
 return out;
}

console.log("[MTR-097] START");
console.log("[SCOPE] installed PumpSwap SDK pool-layout contract capture; local only");

const root=path.dirname(require.resolve("@pump-fun/pump-swap-sdk/package.json"));
console.log(`[SDK_ROOT] ${root}`);

const files=walk(root);
const hits=[];

for(const f of files){
 let s;
 try{s=fs.readFileSync(f,"utf8")}catch{continue}
 if(!/poolBaseAmount|poolQuoteAmount|baseTokenAccount|quoteTokenAccount|virtualQuoteReserves|Pool/.test(s)) continue;

 const lines=s.split(/\r?\n/);
 const found=[];
 for(let i=0;i<lines.length;i++){
  if(/poolBaseAmount|poolQuoteAmount|baseTokenAccount|quoteTokenAccount|virtualQuoteReserves|account\.pool|fetchPool|poolAccount/i.test(lines[i])){
   found.push({
    line:i+1,
    text:lines[i].trim().slice(0,240)
   });
  }
 }

 if(found.length){
  hits.push({file:path.relative(root,f),found:found.slice(0,80)});
  console.log(`\n[FILE] ${path.relative(root,f)}`);
  for(const h of found.slice(0,40))
   console.log(`[L${h.line}] ${h.text}`);
 }
}

const pkg=require("@pump-fun/pump-swap-sdk");
console.log("\n[EXPORT_KEYS]");
console.log(Object.keys(pkg).sort().join(","));

for(const k of ["PumpAmmSdk","OnlinePumpAmmSdk","PUMP_AMM_SDK"]){
 const x=pkg[k];
 console.log(`[EXPORT] ${k} type=${typeof x}`);
 if(x && x.prototype)
  console.log(`[METHODS] ${k} ${Object.getOwnPropertyNames(x.prototype).sort().join(",")}`);
}

fs.writeFileSync("mtr_097_pumpswap_pool_layout_contract.json",
 JSON.stringify({sdk_root:root,hits,exports:Object.keys(pkg).sort()},null,2));

console.log(`\n[SUMMARY] files=${files.length} hit_files=${hits.length}`);
console.log("[RESULT] PUMPSWAP_POOL_LAYOUT_CONTRACT_CAPTURED");
console.log("[OUTPUT] mtr_097_pumpswap_pool_layout_contract.json");
console.log("[RPC] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-097] COMPLETE");
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] PumpSwap installed SDK pool-layout contract capture")
print("[SCOPE] local source inspection only; no RPC; no signing; no sending")