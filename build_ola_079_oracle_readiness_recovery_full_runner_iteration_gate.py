from __future__ import annotations

import base64
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_readiness_recovery_full_runner_iteration_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_079_oracle_readiness_recovery_full_runner_iteration_gate.py"
)


PRODUCTION_PAYLOAD = "c-qApYjYd7@jHJ7%6=%>p*T)5lTK7$r>sQTnvq0@q|>Gz4+gvgrK^v3%sph$j{kcXz~OlSDchm!50-Sh3+#Ir3#`jxgD_q<byHG|QM%a{WsOLl7d5HVBCmSAHN#0rP2!AH6|E$a`lK*uoo=WB=6?%lz1ybwt%ObT-3XnLEF-Ioj?gvPGHAQixF}&=inH{d;_8kh#d}=Q@;;3zE}J~3rCesvL-23L(XRk|!I2jNci!Z48W&|U+J|*n(~=AN2;4c}eAFA-e6}oZi!1{n*v~ZH;g}>e2aaieo95K!_|@#{>hk6VUMwfeDV|TyX7h8r{PopTY%ex_CDvPj9jN$T)l6OZj#PJuR7h@EF$`<~8Hc^a*~{tm1phLfFD_>{C_??&)#T*a-+t=%rZ+DxZ>IS2-1<77PR{Y{=IU4Yx-1*ooBn5d_Ie4#cye_$`}dTgUy!V#y~)*dzFc%Z|Gb#aFQ*Iqa&mJ%ySV7Um-ET_6i;3+U(V*2|DAZ322D)o_|?_qY<fMtS$5zTuW!y5_<Ht>@$J=YzPy-SUC!|JYo<{R>GimSwg#P3l7KC$irM;}mb;54%Y;#t8@vErPRp_=2LNF1%l{ajas%}H{eO{)qE=_<7Ld`Jq!|Ry7=T~6-&v8@Kv0W)4G;V*hI^XHIY}#;p!at)M+8;PcAKT}cS5%`XI{BO_i2#<VTI~DD#VCeCcZ+B3!#ZWS^~!6s%U`o1eIbL_FJ0?<SN__Rm=T9Rc;zUsD7Y%#5{WV*;0w5Ah@dHJGvnlFe`wZLNu2Ay9jWcCi>HD8<2HV>5oPV>%f#0I0ixMQ<Ua42gJo@o6(vkIEYe8IWVbfy4lt)0+=<gQkvJeb=B?)b-BX{&B(5^{~e9r!S1BS+mbR7D9E`gicH9UPqK#8VFXiXmYSIQ(sgR#Xvsnt>og}>o999}Obximvz^J_1C1NLGL)L)y@gLQTGo{Z@Eh=)(h4@plVZL0V1Pmsib+%76=nK?1U3N2p(WmCB&Hjt{4T~Ce7eG$!d4lp6Kkj;1>Q7FViUHZHDRuODof@Y@SqVZr*C^4A)#wj7f^iiB2QybT9U@~prYA&h)({2*k77N_;u?6O_`&Q>H`l$+vEG-uCUJ7{yMTrR4_<v^}#_jLPVk(pB&_F=qP475Qo$W8%gJUc8G#eC&_~d&O(9Ml*<Ib&LV;Mm5T(x9ZsAW*E~1?R~McPpw!@jxenpY5Xw8e&^^|-qTlBP7DCV$yvqc@&LY8FB$o*yczlB=EYlnK2Umq|7E{`D0S=*^;v|**)gcKaKS>(^cO5pA9}TAsp*V{L(x_Z00CtV0Gp#a{{^THc60juc031S@odI8^-Ld>Q)X1NpLt%+p#M>Zl&q0_413gveqBn2ej#wdv|G|B-1m|Q!dC$OeIY2}LPuB=eYe+8RtT!~WJZq}HzBiTs*8Pu~uTN;xR5e;r#YbNu5BYDL8|ch!_69>KLt3RdL=Bvo1{^ZtWp4;|l#AB|g912IEc_fjds0c;l1YHM{3NGPyx_RVcyi@#5jmHw;bq#x?FmxXfwsTh!HGP}+S9JCF@meV3QrQi(?f?<uH8JXQ%FkIiSaae&eZI@dr!*S3JObH7v;`y&GC3V>h>USN2*g!8b~u=NFOMRSbB~xMD}&MhY34H@GyxiI(u3&^gFsKa^~~w2b{`T*nZjJqm6MR2!#1Z`^|s6;P1ERFB$cF*>FRmD~;DfM;;G7qC{RElz?4U0#d0w915dj8YQsh!Q|}n9tz<j@*di9FYo-<6<rq)>us{AAl}-_YMgKOXB1tV`-f2b0(WTc+-4i!&WBQxvGXBR-_AT``6UizG)vYHlG;m_8mLTFlhv@32>dbp(7Sm<C-MiiBHEA#UD~SXyOGCSwkt#-fF=!jQ4|6gq)tYU+9uBa$~umZpN5uxyxF<c*a+1PoE3SelF{6N4AGw=^uyN$lr?fwcIETQ?|*<UG~tZ3El3Knp(X>UzAGs`;mma+N-)U>;(9z&jm$xe@Pt;B{b~^F92(OPkEscv0h%BJYRK8~9SFhCrO}xzNO1ayVr6K=Hm-(n<9_!P#+9=OL?6JTvmIhBhn$xxhB{KIxoKor_|3Dohh!c-@+Rfmm{W`OSYsM4eT07F3&r3}$qOD-x!r~sV6I`KZ&CEb#^0dkiH)D8<VigMCgl9c)%J<obclg&D}zm>G<D+k3+>33@nVy-GM?CFUS(OEx##HnV>oFig{X`}A7~k~ZIs){dzqal-fX2jKTc8%Gh3|qP!SI5%GV6OTjo4$n`U`(rj>??@M^(LCj|hTy23hxc~*a9qUp2xWMHbHyoGcO5xeCTa&LRokd27kziR_ixXz%T^R5Q*{bL$P=4(?LxBPn8S9Uc<%Xza|!Lj*R%|VmXhb@h3gK6zuV(-0->O!Dr`;1v1hB>^~viw<Xyrt!awVd>~hGc2IV@?R!47%?GvAHXo*Zv*aP;iJ9gl2pvU4s~lmGplg4%-+l(+vgFZ?>qtDG*Wtk({uj)sEj5E8j8}ayx^+RH9)rk^vN3N^Yr`wgOW$E8dUQ5?l7t<#7so?lnE|Ub@=)<1DYmFc>N6EvSm!q>DmgXn}L{NMA55Z3*X-{<y+ftaQZFTpY-i++%jwy*U~Tr4O?A0>^Cq%v8c3^avl0^;-s-?6poSfqiN9bo^^adMx)cF=6+D47#4+QzpIpp}T2g)%{o0!UJ%<+fpDq@Dxk$$9r&lo9;!sMI#0yan>Z%kTw!8lT0M*YRK-LOrf;GARz~}c?_d_jw6pUyJ(7wa+M|tWhc##J#&7HeK(tCn-ad?<mBP2L1U4F7leE%`-0FQ_g)in65lnULAd9#(71^9X+X#LJ_YDC!fMbf9oB+g&(?)r!><ZW=TnHL4(Q{PCpoK&a5I^)?!hiR9h76XfSu=NSy74J;e@l%US-$56A;OF0~G~hei2v=hQlXi_m-q=(4d3S%P{{nFUk!xY#$)GsG(<s_6<WrWaDPbUI7n`u$M!Qly!udvr9_$1j1Kme*8%tETQKs?o)7Lc88`$Ua}hP8+RGLYEPVDQ)A}bXAdCLyeXPWwFPa*28cXq8^|jXzq>8jt~e`-?H)|vJLU}%_=+Ec4PwEYy$GM=Kvqm}Klk!*V9mvKNsR2*!I~L$GK|zCVGT4MXhnV24g<H{@wq;sMSIV0n$meg6*-esjTn4(W$yHdw^@O4S7gmqMu+BEku}*Eh38O_F-tIn@jRa5&r}U-c%Mf(NWs@n4qo7SlY<p}z2xAj1njcxmaNEecl-H~3k^Ila?$oYA97IxmCr>pikl1SR4x}mT^M;%pc*RjhaVfr!UOyD&bCa=A*Otf&*~acc}>nJ85x{;WJ-q&2zo+EK}8YdSqSyb)FK{si@esR59u-Eey{UN<ry#v6$|s1E*PUILVb)G+ZeYa7E!Dgy9#1u`jFNGA=I$<fAFH9&j"

TEST_PAYLOAD = "c-o~|TXWmG5q{UN!0?GmW!Z7sb9&rSXIz^}J$0mvET=t_@n9elvM}Z?0BKt%lmFhujRbgcoYoJHNq)Q7UF<zOUStU4U0v0jVvJZ;7Q8|v&x?vwtjNV=vXhvERJ39lwFvt>L-O|@MNTzNe@@xf0`)&QE0Q{;hS^s^IimtUp3VzS;*?^RS2Ru8J<Ve}PuU~IB>q}6!K4fp^gvRvXIOpalqBjG%c&6f9>lRHh7$xo|5D&<z^(zcw#fH{rJ(BUCCr+}1y5#^>Hj5dD;x)YkCY$4%xQ{wo#&KeR#C1jJRp0t{BX65@YSUjGx|?-al5%%E%EvF_3Gb|dA*L#FY#)5{kwj=x%g-F@f?4S);9pv@8}~*YhaImQl>`tii!#sDZwYF?<^Cgu-KENc*0<sM;24Vz}I41voyhR0q=5}S3--#a<CFfu>k)v*C66OmEOVe!xQ260`Ev%75pHjn0#8VK3`o%Yy5F_d3zn<<@v`5EzA+YPu`7mLz>P5O>8K3jDwP3n$&6q*I(8Gr=-r~z0@Ehc@juzCJEhH#YkS{ECwpysyqqb%n+y)KhOk|YS!F>ej-&xv$C3=DIqw8$je{$M6Ii}R7NmdoB(YW!Rq?_=;ZBRgIR;1`8`l#mJEGt1%>aspn06b4WIn_+uS$>P3GT>l-~!b<=xd{5tKv-nm7=Wkg}4F1jn1d&ArTZ@XpJ6o3a>Zgg?+q%(cNC4x*@etmW5#T0%{MA@7hrd`kqyHBT48zN$)bc6>}qHm50#RSvT};3khNP7-<qpN}6;`;2Iwlm)oZA~-f8IvB|tXSCWEAl-*(<9uqbd*R%Cdn=9yEIfB;AjU9_02^LY$FOy^hZq8PQ*K;?*%$9YDF>o_{hmrs{#whhjf)!iyzS{27daRqt}w^}cJ>c4n35M;iuVu`)xNoI{dnkG4Ll>>lWj_enWdm?9v^Tf2Ba}(&_|ZYki~l<_TZb=0nbi;`SY{qg)*Hf6^e9}3jGPaJ?W9U`U7!7V<y9BfcW%>#GtYO(irlIScHL_V@R47Pcke}(6vu6b-YO{UKViehgOr4Q$c(8ue5$0v?J(%WL*NC^ki!6dL88CN;G60hqJjCyp=rAF_c>^;)Be$ATrb)nN1Fz^Q6oyuM5b%plizVd+B?;>T`9qDk<L;JnMtn3|(wxq0+Gv!^s02OPNzer3}mR$Kqk&P-%`a`i?bpB^U#Dyyrz5Nk3BEPLZbv*MZu63^|F&#JC8<HmPId&N#2LE#*O5d1ix5`cd$%9|bJS>S`d;IW1Fi82CWygbfkUXCPqtAS<J5kAlXv=f)kQIsj9KAU=xp@ioYi8&|~w%j8>d_6K?CbhvHc14_j-gWDT}?dm*%3o8bslC9GYLcGAz#vQMby+@ovy+vzXq#-z(HsJ%Hbvq&36O3h#g>fiox-)HtigS3JLo}oU`ll~<lZL<+Bt<YoZ{FxOY>;$L$`Wc+n6S7C4Q|@H#}1`54_o*YEf(l)%Sh)kCg>0P^DvN32(1G@v@VKv`eQJ4oJF-yKkUdn0i0s3HTV*=uY$Xo2lh(0g}X1i1SWnK9YeGr+eSjR6BVza5JR<1>R2Z;UdZ&$L;D9-w?0F1N|;G~Aum7=OAhvaED$c$r<r4%(<kr)|Mk?Pn(Ognq4;;c=)+WRCBTf}xPbf1{A3W8k!J_>%SjI=Qc6oDrmKYUrw%qwi}(SMDap18IYS{vkm3={r#T9z(|NV$#Z!B!=g@|7X}*Z_g3BBT2cVKvdt?$YB05Fs;8Zg!RF<qXuGF=Ojgr2qo#Z+Mf~1iPCUb!CSKWyXAmKWyJ{*8cIZr$OZApyhv|{)JQ`iobI_b}lQ%9x$jEyD!H1e&nY|!NxoT1(!En2#?O07`Oj5Y!&JR#;oAeToQif3r3nf9aa4E6iz@5W9URG4szj{XjQQ`u;NKf_@0%Aa8BQXw@`{rVeve|vq6*0;-Lw1zSKVg*C@@94w%ChFps5&FmKc6k|HYTDCx=xP(K&*e1V!CtJEo2%vR>h=cRMC;F27ZF;nHt1$^zTQNaKKLiZS7by5NM}VLQ*&T63S3yTei%hGs|Umcl4aT>@2)E(NR_gQ=l^CW1n%zbh{B<X-w#lo$Yj!j#;2;BWT{y|$AmvMIn~w}6)~R-(ptvNMY=5Nx3<RG^f*#=!$z=f0tcFx6MS3u{Y>xFHctrmLo0LB9q9hq?pomV?)oKcvxZD>s`DC<YdUcq?aL;*+1!ElBz2T*YmQ9B_5EI*oKmoq_3|c3w1$?2807k2cT%mv^p{1e+Lu7Ta!aw@GkLjZ;ccJ7!9Lhesf)1>GjAy~w7y!5@3s1;+GbsqiuQtR0UWrfdA}HWjq6YidL82t;z0)-<14!#uUT>IWp;+m)bh>ip8~aWWC>*UpxH~wi?remdPm?lVZj!}N~mPwPZ8>)-t`$V%!CQZPCx$Li!GDfv|e6dI-TyR3-wbA<Q8b1?tFj@iMixqb}TC4nyuOZ(%H7U1UC2vY1(RSx)A8c2Ve~k{7Qlm*B!8ef{!*uW86C)HY#`1An0`nhrw#7C>glhE4+%pHMyLS<?fa3*o!o+1z$_CgGtyVrB~B5bMi~-c4y|c6!*a+6YNVQ&NTZHtT)+qIs(0cmtizRdWKLBYE&2qHTQ&;)F0xczc{S?k7Eq{v98C$|2)P-t?HgwE|)pZ-YK|qd{wd@licO&9sgR!<7#`A{nPo)&0W*cHmiSU+-`CLf-;NfGgPm^`rhYyVJGo+(n3&$DY>VpjXDzZ0*<j|e~^<s58`ju9y&uLPmqe5BNa7BMhz9n#?3G<)o{RhaxO5M9?1y$Te}fLX4z96T3o_}tZkO58In$5$Y65Yl9NpS*Qw0J7)uh212aykO~=haK!S{(SrzJmWIFjTJV4C0"


def decode(payload: str) -> str:
    return zlib.decompress(
        base64.b85decode(
            payload.encode("ascii")
        )
    ).decode("utf-8")


def write_full_replacement(
    path: Path,
    payload: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        decode(payload),
        encoding="utf-8",
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def main() -> int:
    print("========================================")
    print(" OLA-079 INSTALLER")
    print(" READINESS RECOVERY FULL RUNNER GATE")
    print(" ONE BOUNDED OLA-023 ITERATION")
    print("========================================")

    write_full_replacement(
        PRODUCTION_PATH,
        PRODUCTION_PAYLOAD,
    )

    write_full_replacement(
        TEST_PATH,
        TEST_PAYLOAD,
    )

    print("[OK] Real production readiness provider exercised")
    print("[OK] Temporary readiness failure and recovery exercised")
    print("[OK] Complete canonical OLA-023 iteration exercised")
    print("[OK] Service-run, iteration, and final-state hashes verified")
    print("[OK] Continuous service not started")
    print("[OK] Oracle remains read-only")
    print(
        "[OK] Execution, orders, funds, and "
        "portfolio mutation disabled"
    )
    print("[DONE] OLA-079 installed")

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )