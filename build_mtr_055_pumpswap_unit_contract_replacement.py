from pathlib import Path
T=Path("mtr_055_pumpswap_unit_contract_replacement.cjs")
J=r"""const {Connection,PublicKey,SystemProgram}=require("@solana/web3.js"),P=require("@pump-fun/pump-swap-sdk"),BN=require("bn.js");
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const POOL="QaZ2H7SPE6kZ6HENkTmHcuf3sh5YPjta2XRZrCB1gEo",c=new Connection(RPC,"confirmed"),V=x=>x==null?"NULL":x.toString();
(async()=>{
 console.log("[MTR-055] START");console.log("[SCOPE] corrected PumpSwap state/unit contract; no signing; no sending");
 const on=new P.OnlinePumpAmmSdk(c),s=await on.swapSolanaState(new PublicKey(POOL),SystemProgram.programId);
 console.log(`[STATE_KEYS] ${Object.keys(s).sort().join(",")}`);console.log(`[POOL_KEYS] ${Object.keys(s.pool||{}).sort().join(",")}`);
 const bm=s.pool.baseMint,qm=s.pool.quoteMint;if(!bm||!qm)throw Error("POOL_MINTS_NOT_FOUND");
 const [bi,qi]=await c.getMultipleAccountsInfo([bm,qm]),dec=i=>i&&i.data&&i.data.length>44?i.data[44]:null;
 console.log(`[MINTS] base=${bm.toBase58()} quote=${qm.toBase58()}`);console.log(`[DECIMALS] base=${dec(bi)} quote=${dec(qi)}`);
 console.log(`[RESERVES] poolBaseAmount=${V(s.poolBaseAmount)} poolQuoteAmount=${V(s.poolQuoteAmount)} virtualQuoteReserves=${V(s.pool.virtualQuoteReserves)}`);
 console.log(`[BASE_SUPPLY] ${V(s.baseMintAccount&&s.baseMintAccount.supply)}`);
 const common={slippage:0,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,virtualQuoteReserves:s.pool.virtualQuoteReserves,globalConfig:s.globalConfig,baseMintAccount:s.baseMintAccount,baseMint:bm,coinCreator:s.pool.coinCreator,creator:s.pool.creator,feeConfig:s.feeConfig,quoteMint:qm,isMayhemMode:s.pool.isMayhemMode,creatorFeeBps:s.pool.creatorFeeBps};
 for(const n of ["1000000","10000000","100000000","1000000000"]){const z=P.buyQuoteInput({...common,quote:new BN(n)});console.log(`[BUY_PROBE] quote_raw=${n} base_raw=${V(z.base)} max_quote=${V(z.maxQuote)}`)}
 console.log("[RESULT] PUMPSWAP_UNIT_CONTRACT_PHYSICALLY_CAPTURED");console.log("[NEXT_GATE] TOKEN-ORIENTATION_AND_DECIMAL_CORRECT_ROUNDTRIP");console.log("[MTR-055] COMPLETE");
})().catch(e=>{console.error("[MTR-055] FAIL");console.error(e.stack||e);process.exit(1)});
"""
T.write_text(J,encoding="utf-8")
print(f"[BUILD] wrote {T}")
print("[BUILD] full replacement for failed MTR-054 state-shape assumption")
print("[SCOPE] no private key; no signing; no sending; canonical executor untouched")
