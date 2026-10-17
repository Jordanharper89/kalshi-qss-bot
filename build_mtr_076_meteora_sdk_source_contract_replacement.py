from pathlib import Path

target=Path("mtr_076_meteora_sdk_source_contract_replacement.cjs")
target.write_text(r'''const fs=require("fs");
const path=require("path");

console.log("[MTR-076] START");
console.log("[SCOPE] installed Meteora SDK source-contract inspection; local only");

const entry=require.resolve("@meteora-ag/dlmm");
console.log(`[RESOLVED_ENTRY] ${entry}`);

if(!fs.existsSync(entry))throw Error("RESOLVED_ENTRY_NOT_FOUND");
const src=fs.readFileSync(entry,"utf8");

console.log(`[SDK_FILE] ${entry}`);
console.log(`[SDK_BYTES] ${src.length}`);

let root=path.dirname(entry);
while(root!==path.dirname(root) &&
      !fs.existsSync(path.join(root,"package.json")))
 root=path.dirname(root);

const pkgFile=path.join(root,"package.json");
if(fs.existsSync(pkgFile)){
 const pkg=JSON.parse(fs.readFileSync(pkgFile,"utf8"));
 console.log(`[SDK_VERSION] ${pkg.version||"unknown"}`);
 console.log(`[PACKAGE_ROOT] ${root}`);
}else{
 console.log("[SDK_VERSION] package-json-not-found");
}

const terms=[
 "swapQuote(",
 "swapQuoteExactOut",
 "pairType",
 "functionType",
 "tokenMintXProgramFlag",
 "tokenMintYProgramFlag",
 "Swap2",
 "feeOnInput",
 "protocolShare"
];

for(const term of terms){
 let pos=0,count=0,shown=0;
 while((pos=src.indexOf(term,pos))!==-1){
  count++;
  if(shown<6){
   shown++;
   const a=Math.max(0,pos-500);
   const b=Math.min(src.length,pos+1100);
   console.log(`\n===== ${term} OCCURRENCE ${count} @ ${pos} =====`);
   console.log(src.slice(a,b));
  }
  pos+=term.length;
 }
 console.log(`\n[TERM_COUNT] ${term}=${count}`);
}

console.log("[RESULT] METEORA_INSTALLED_SOURCE_CONTRACT_CAPTURED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[NETWORK] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-076] COMPLETE");
''',encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] Meteora installed-source contract replacement")
print("[SCOPE] local files only; no RPC; no private key; no signing; no sending")