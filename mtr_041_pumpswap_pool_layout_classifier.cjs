const fs=require("fs"),{Connection,PublicKey}=require("@solana/web3.js");
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const c=new Connection(RPC,"confirmed");
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const KNOWN=[
 "8oo1APyu3UEGAQZVTVmw5Szjg5x9NT7Rw5c2GCta48Wj",
 "12x41vhkRjSzL85qyAez3FrGxgUfJQqwv9FtVksgUb9"
];
function hex(b,n=8){return b.subarray(0,n).toString("hex")}
function pk(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function main(){
 console.log("[MTR-041] START");
 console.log("[SCOPE] genuine PumpSwap pool layout classification; no signing; no sending");
 const anchors=[];
 for(const s of KNOWN){
  const k=new PublicKey(s),a=await c.getAccountInfo(k,"confirmed");
  if(!a)throw new Error(`KNOWN_POOL_MISSING ${s}`);
  if(!a.owner.equals(PUMP))throw new Error(`KNOWN_POOL_WRONG_OWNER ${s} owner=${a.owner.toBase58()}`);
  const b=Buffer.from(a.data),x={pool:s,size:b.length,discriminator:hex(b),
   offset9:pk(b,9),offset41:pk(b,41),lamports:a.lamports};
  anchors.push(x);
  console.log(`[ANCHOR] pool=${s} size=${x.size} disc=${x.discriminator} off9=${x.offset9} off41=${x.offset41}`);
 }
 const sizes=[...new Set(anchors.map(x=>x.size))],discs=[...new Set(anchors.map(x=>x.discriminator))];
 console.log(`[ANCHOR_SIZE_COUNT] ${sizes.length} sizes=${sizes.join(",")}`);
 console.log(`[ANCHOR_DISCRIMINATOR_COUNT] ${discs.length} discs=${discs.join(",")}`);
 if(sizes.length!==1||discs.length!==1)throw new Error("KNOWN_POOLS_DO_NOT_SHARE_LAYOUT_CLASS");
 const size=sizes[0],disc=discs[0];
 console.log(`[CLASSIFY] querying PumpSwap dataSize=${size}`);
 const rows=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64",
  dataSlice:{offset:0,length:73},filters:[{dataSize:size}]});
 let discMatch=0,layoutMatch=0;const sample=[];
 for(const r of rows){const d=Array.isArray(r.account.data)?r.account.data[0]:r.account.data,b=Buffer.from(d,"base64");
  if(hex(b)!==disc)continue;discMatch++;const base=pk(b,9),quote=pk(b,41);
  if(!base||!quote||base===quote)continue;layoutMatch++;
  if(sample.length<25)sample.push({pool:r.pubkey.toBase58(),base_mint:base,quote_mint:quote})}
 const out={schema:"MTR-041",execution_authority:false,signing:false,sending:false,
  anchor_pools:anchors,pool_account_size:size,pool_discriminator_hex:disc,
  same_size_accounts:rows.length,discriminator_matches:discMatch,layout_matches:layoutMatch,sample};
 fs.writeFileSync("mtr_041_pool_layout.json",JSON.stringify(out,null,2));
 console.log(`[SAME_SIZE_ACCOUNT_COUNT] ${rows.length}`);
 console.log(`[DISCRIMINATOR_MATCH_COUNT] ${discMatch}`);
 console.log(`[LAYOUT_MATCH_COUNT] ${layoutMatch}`);
 for(const x of sample)console.log(`[POOL_SAMPLE] pool=${x.pool} base=${x.base_mint} quote=${x.quote_mint}`);
 console.log(layoutMatch&&layoutMatch===discMatch?"[RESULT] PUMPSWAP_POOL_CLASS_PHYSICALLY_IDENTIFIED":"[RESULT] POOL_CLASS_REQUIRES_FURTHER_RESOLUTION");
 console.log("[OUTPUT] mtr_041_pool_layout.json");console.log("[MTR-041] COMPLETE");
}
main().catch(e=>{console.error("[MTR-041] FAIL");console.error(e?.stack||e);process.exit(1)});