from pathlib import Path
T=Path("mtr_054_pumpswap_unit_contract_probe.cjs")
J=r"""const {Connection,PublicKey,SystemProgram}=require("@solana/web3.js"),P=require("@pump-fun/pump-swap-sdk"),BN=require("bn.js");
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const POOL="QaZ2H7SPE6kZ6HENkTmHcuf3sh5YPjta2XRZrCB1gEo",c=new Connection(RPC,"confirmed");
const v=x=>x&&x.toString?x.toString():String(x);
(async()=>{
 console.log("[MTR-054] START");console.log("[SCOPE] PumpSwap live state unit/decimal contract only; no signing; no sending");
 const on=new P.OnlinePumpAmmSdk(c),s=await on.swapSolanaState(new PublicKey(POOL),SystemProgram.programId);
 const bm=s.baseMint.toBase58(),qm=s.quoteMint.toBase58();
 const [bi,qi]=await c.getMultipleAccountsInfo([s.baseMint,s.quoteMint]);
 const dec=b=>b&&b.data&&b.data.length>44?b.data[44]:null;
 console.log(`[MINTS] base=${bm} quote=${qm}`);
 console.log(`[DECIMALS] base=${dec(bi)} quote=${dec(qi)}`);
 console.log(`[RESERVES] poolBaseAmount=${v(s.poolBaseAmount)} poolQuoteAmount=${v(s.poolQuoteAmount)} virtualQuoteReserves=${v(s.pool.virtualQuoteReserves)}`);
 console.log(`[BASE_SUPPLY] ${v(s.baseMintAccount&&s.baseMintAccount.supply)}`);
 for(const n of ["1000000","10000000","100000000","1000000000"]){
  const q=new BN(n),a={quote:q,slippage:0,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,virtualQuoteReserves:s.pool.virtualQuoteReserves,globalConfig:s.globalConfig,baseMintAccount:s.baseMintAccount,baseMint:s.baseMint,coinCreator:s.pool.coinCreator,creator:s.pool.creator,feeConfig:s.feeConfig,quoteMint:s.pool.quoteMint,isMayhemMode:s.pool.isMayhemMode,creatorFeeBps:s.pool.creatorFeeBps};
  const z=P.buyQuoteInput(a);console.log(`[BUY_PROBE] quote_raw=${n} base_raw=${v(z.base)} max_quote=${v(z.maxQuote)}`);
 }
 console.log("[RESULT] PUMPSWAP_UNIT_CONTRACT_PHYSICALLY_CAPTURED");console.log("[NEXT_GATE] CORRECT_TOKEN_DECIMAL_NORMALIZED_ROUNDTRIP");console.log("[MTR-054] COMPLETE");
})().catch(e=>{console.error("[MTR-054] FAIL");console.error(e.stack||e);process.exit(1)});
"""
T.write_text(J,encoding="utf-8")
print(f"[BUILD] wrote {T}")
print("[BUILD] PumpSwap mint-decimal/reserve/input-unit physical probe")
print("[SCOPE] no private key; no signing; no sending; canonical executor untouched")
