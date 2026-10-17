from pathlib import Path

target=Path("mtr_082_pump_sell_base_contract_capture.cjs")
target.write_text(r'''const fs=require("fs");

console.log("[MTR-082] START");
console.log("[SCOPE] installed Pump SDK sellBaseInput contract capture; local only");

const entry=require.resolve("@pump-fun/pump-swap-sdk");
const src=fs.readFileSync(entry,"utf8");

console.log(`[SDK_ENTRY] ${entry}`);
console.log(`[SDK_BYTES] ${src.length}`);

const terms=[
 "function sellBaseInput",
 "sellBaseInput({",
 "sellBaseInput(",
 "function sellQuoteInput",
 "function buyQuoteInput"
];

for(const term of terms){
 let pos=0,count=0;
 while((pos=src.indexOf(term,pos))!==-1){
  count++;
  if(count<=8){
   const a=Math.max(0,pos-900);
   const b=Math.min(src.length,pos+3000);
   console.log(`\n===== ${term} OCCURRENCE ${count} @ ${pos} =====`);
   console.log(src.slice(a,b));
  }
  pos+=term.length;
 }
 console.log(`\n[TERM_COUNT] ${term}=${count}`);
}

console.log("[RESULT] PUMP_SELL_BASE_CONTRACT_CAPTURED");
console.log("[NETWORK] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-082] COMPLETE");
''',encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] Pump sellBaseInput installed-source contract capture")
print("[SCOPE] local SDK only; no RPC; no private key; no signing; no sending")