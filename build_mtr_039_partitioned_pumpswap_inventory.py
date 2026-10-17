from pathlib import Path
TARGET=Path("mtr_039_partitioned_pumpswap_inventory.cjs")
JS=r'''const fs=require("fs"),{Connection,PublicKey}=require("@solana/web3.js");
const M=require("@meteora-ag/dlmm"),DLMM=M.default||M.DLMM||M;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"),c=new Connection(RPC,"confirmed");
const A="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function b58(n){if(n===0)return"1";let s="";while(n){s=A[n%58]+s;n=Math.floor(n/58)}return s}
const key=v=>!v?null:typeof v==="string"?v:typeof v.toBase58==="function"?v.toBase58():v.address||null;
function pk(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function main(){
 console.log("[MTR-039] START");console.log("[SCOPE] 256 server-side shards; no signing; no sending; no executor");
 const mr=await DLMM.getLbPairs(c),rows=Array.isArray(mr)?mr:mr?.pairs||mr?.lbPairs||[],byMint=new Map();
 for(const r of rows){const a=r.account||r,p=key(r.publicKey||r.pubkey),x=key(a.tokenXMint||a.tokenX?.mint),y=key(a.tokenYMint||a.tokenY?.mint);
  if(!p||!x||!y)continue;const z={lb_pair:p,token_x:x,token_y:y};for(const m of[x,y]){if(!byMint.has(m))byMint.set(m,[]);byMint.get(m).push(z)}}
 console.log(`[METEORA_LBPAIR_COUNT] ${rows.length}`);console.log(`[METEORA_DISTINCT_MINT_COUNT] ${byMint.size}`);
 const state={schema:"MTR-039",execution_authority:false,signing:false,sending:false,completed_shards:[],pools:{},candidates:{}};
 if(fs.existsSync("mtr_039_checkpoint.json"))Object.assign(state,JSON.parse(fs.readFileSync("mtr_039_checkpoint.json","utf8")));
 for(let shard=0;shard<256;shard++){
  if(state.completed_shards.includes(shard)){console.log(`[SHARD ${shard}/255] checkpoint skip`);continue}
  const rows=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64",dataSlice:{offset:9,length:64},
   filters:[{memcmp:{offset:9,bytes:b58(shard)}}]});
  let valid=0,overlap=0;
  for(const r of rows){const raw=r.account.data,b64=Array.isArray(raw)?raw[0]:raw;if(typeof b64!=="string")continue;
   const b=Buffer.from(b64,"base64"),base=pk(b,0),quote=pk(b,32);if(!base||!quote||base===quote)continue;valid++;
   state.pools[r.pubkey.toBase58()]={base_mint:base,quote_mint:quote};
   const mm=byMint.get(base)||[];if(mm.length){overlap++;state.candidates[r.pubkey.toBase58()]={base_mint:base,quote_mint:quote,meteora_pairs:mm}}}
  state.completed_shards.push(shard);fs.writeFileSync("mtr_039_checkpoint.json",JSON.stringify(state,null,2));
  console.log(`[SHARD ${shard}/255] rpc=${rows.length} valid=${valid} overlap=${overlap} total_pools=${Object.keys(state.pools).length} total_overlap=${Object.keys(state.candidates).length}`);
 }
 const pools=Object.entries(state.pools),cand=Object.entries(state.candidates),qc=new Map();
 for(const[,p]of pools)qc.set(p.quote_mint,(qc.get(p.quote_mint)||0)+1);
 const out={...state,pool_count:pools.length,quote_mint_count:qc.size,quote_universe:[...qc].sort((a,b)=>b[1]-a[1]).map(([mint,pool_count])=>({mint,pool_count})),overlap_count:cand.length};
 fs.writeFileSync("mtr_039_inventory.json",JSON.stringify(out,null,2));
 console.log(`[PUMPSWAP_POOL_COUNT] ${pools.length}`);console.log(`[PUMPSWAP_QUOTE_MINT_COUNT] ${qc.size}`);console.log(`[CROSS_VENUE_OVERLAP_COUNT] ${cand.length}`);
 for(const[pool,x]of cand.slice(0,40))console.log(`[CANDIDATE] pump_pool=${pool} base=${x.base_mint} quote=${x.quote_mint} meteora_pairs=${x.meteora_pairs.length}`);
 console.log(cand.length?"[RESULT] PHYSICAL_PARTITIONED_INTERSECTION_FOUND":"[RESULT] NO_PARTITIONED_INTERSECTION");
 console.log(cand.length?"[NEXT_GATE] EXACT_BIDIRECTIONAL_QUOTE_PROOF":"[NEXT_GATE] REASSESS_CROSS_VENUE_INVENTORY");
 console.log("[OUTPUT] mtr_039_inventory.json");console.log("[MTR-039] COMPLETE");
}
main().catch(e=>{console.error("[MTR-039] FAIL");console.error(e?.stack||e);process.exit(1)});'''
TARGET.write_text(JS,encoding="utf-8")
print(f"[BUILD] wrote {TARGET}")
print("[BUILD] 256 server-side PumpSwap base-mint shards with persistent checkpoint")
print("[SCOPE] discovery only; no signing; no sending; canonical executor untouched")