from pathlib import Path

target = Path("mtr_075_meteora_sdk_pool_type_source_diagnosis.cjs")
target.write_text(r'''const fs=require("fs");
const path=require("path");

console.log("[MTR-075] START");
console.log("[SCOPE] installed Meteora SDK source-contract diagnosis; read-only");

const pkg=require.resolve("@meteora-ag/dlmm/package.json");
const root=path.dirname(pkg);
const candidates=[
 path.join(root,"dist","index.js"),
 path.join(root,"dist","index.cjs"),
 path.join(root,"dist","index.mjs")
];
const file=candidates.find(fs.existsSync);
if(!file)throw Error("METEORA_DIST_NOT_FOUND");

const src=fs.readFileSync(file,"utf8");
console.log(`[SDK_FILE] ${file}`);
console.log(`[SDK_BYTES] ${src.length}`);

const terms=[
 "swapQuote(",
 "swapQuoteExactOut",
 "pairType",
 "functionType",
 "tokenMintXProgramFlag",
 "tokenMintYProgramFlag",
 "Swap2",
 "swap2",
 "feeOnInput",
 "protocolShare"
];

for(const term of terms){
 let pos=0,count=0;
 while((pos=src.indexOf(term,pos))!==-1){
  count++;
  if(count<=8){
   const a=Math.max(0,pos-650),b=Math.min(src.length,pos+1300);
   console.log(`\n===== ${term} OCCURRENCE ${count} @ ${pos} =====`);
   console.log(src.slice(a,b));
  }
  pos+=term.length;
 }
 console.log(`\n[TERM_COUNT] ${term}=${count}`);
}

const version=require(pkg).version;
console.log(`[SDK_VERSION] ${version}`);
console.log("[RESULT] METEORA_INSTALLED_SOURCE_CONTRACT_CAPTURED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[NETWORK] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-075] COMPLETE");
''',encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] installed Meteora SDK pool-type/source diagnosis")
print("[SCOPE] local source only; no RPC; no private key; no signing; no sending")