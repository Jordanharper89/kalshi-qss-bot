from pathlib import Path

p = Path("mtr_099_exact_pool_ata_derivation_contract.cjs")
p.write_text(r'''const fs=require("fs");
const path=require("path");

console.log("[MTR-099] START");
console.log("[SCOPE] exact installed PumpSwap pool ATA derivation contract; local only");

const entry=require.resolve("@pump-fun/pump-swap-sdk");
let d=path.dirname(entry),root=null;

while(true){
 const pj=path.join(d,"package.json");
 if(fs.existsSync(pj)){
  try{
   const j=JSON.parse(fs.readFileSync(pj,"utf8"));
   if(j.name==="@pump-fun/pump-swap-sdk"){root=d;break}
  }catch{}
 }
 const up=path.dirname(d);
 if(up===d)break;
 d=up;
}
if(!root)throw Error("SDK_ROOT_NOT_FOUND");

const src=path.join(root,"src","sdk","onlinePumpAmm.ts");
if(!fs.existsSync(src))throw Error("ONLINE_PUMP_AMM_SOURCE_NOT_FOUND");

const lines=fs.readFileSync(src,"utf8").split(/\r?\n/);

function emit(a,b,label){
 console.log(`\n[${label}]`);
 for(let i=a;i<=b;i++)
  console.log(`[L${i}] ${lines[i-1]}`);
}

emit(125,155,"POOL_ATA_DERIVATION");
emit(220,277,"SWAP_STATE_POOL_ACCOUNT_READ");
emit(300,312,"PHYSICAL_RESERVE_ASSIGNMENT");

const capture={
 source:src,
 pool_ata_derivation:lines.slice(124,155),
 swap_state_read:lines.slice(219,277),
 reserve_assignment:lines.slice(299,312)
};

fs.writeFileSync(
 "mtr_099_exact_pool_ata_derivation_contract.json",
 JSON.stringify(capture,null,2)
);

console.log("\n[RESULT] EXACT_POOL_ATA_DERIVATION_CAPTURED");
console.log("[OUTPUT] mtr_099_exact_pool_ata_derivation_contract.json");
console.log("[RPC] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-099] COMPLETE");
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] exact PumpSwap pool ATA derivation contract")
print("[SCOPE] local installed-source capture only; no RPC; no signing; no sending")