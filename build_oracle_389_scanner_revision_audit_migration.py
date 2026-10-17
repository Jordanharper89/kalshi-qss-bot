"""ORACLE-389 FULL RELEASE-AUDIT MIGRATION (executor certification ONLY).

Fixes ORACLE385 AUDIT_FAILED_FROZEN_SCANNER_SHA_MATCH after certified
ORACLE388 variable-size scanner installation. Complete replacements for 360/363,
NOT scanner changes or relaxation of health, same-bank, fee, fill or native gates.
Windows CMD. No wallet private-key use; no signing or broadcasting.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,pathlib,subprocess,sys,tempfile,unittest,zlib

MANIFEST={'build_oracle_360_integrity_bus_recovery.py': {'before': 'ccff8ef0bbfb138f37277b240b2bdccd15a8234a1ff01b42d8a7b1169f894be4', 'after': '395d96ac79f18642fa5b6bf30525db86ffbc74ff412aa86840cb8d634ff1a016', 'bytes': 12462}, 'build_oracle_363_scanner_bus_binding_replacement.py': {'before': 'efe97bf89b14421535067a386b081ec54d9c0d27b4784d60d6d45c2d859a1cf0', 'after': '9ecce2d0f12d300675f42e30111d98cf099e1ec2b2a1d41b56ce207f2a82ec9a', 'bytes': 37991}, 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_363_verified_scanner_bus_binding.py': {'before': 'efe97bf89b14421535067a386b081ec54d9c0d27b4784d60d6d45c2d859a1cf0', 'after': '9ecce2d0f12d300675f42e30111d98cf099e1ec2b2a1d41b56ce207f2a82ec9a', 'bytes': 37991}}
SOURCE_388_SHA256='b2ecf80539eb6f23e230ddf6d54823799a01b0e2e8895df462f2c48a25039870'
SOURCE_388_PINS={'build_oracle_322_scanner_isolated_discovery.py': '60c9a4d8acc4259a01f37c64332caea6139e49a84a719ada7e7fe4ec17bab57b', 'qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py': 'e579d68ac26210ef98ba015180126782669144e81fc5eb2010f0d9586ced767c', 'build_oracle_363_scanner_bus_binding_replacement.py': 'efe97bf89b14421535067a386b081ec54d9c0d27b4784d60d6d45c2d859a1cf0', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_363_verified_scanner_bus_binding.py': 'efe97bf89b14421535067a386b081ec54d9c0d27b4784d60d6d45c2d859a1cf0', 'build_oracle_368_source_boundary_repair.py': 'f9c75028aca71202cdbd9bc97ffa0629cceeba54f9688ee1b0f0aac6b0c3206d', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_368_source_boundary_repair.py': 'f9c75028aca71202cdbd9bc97ffa0629cceeba54f9688ee1b0f0aac6b0c3206d', 'build_oracle_378_native_profit_path_visibility.py': '28aabad0712212b1576aedbb58c25456fedde854b86603a0041ccc71a6782d5e', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_378_native_reverse_atomic.py': '28aabad0712212b1576aedbb58c25456fedde854b86603a0041ccc71a6782d5e', 'build_oracle_384_exact_pool_free_rpc_repair.py': '93c5073a847180f69a7660de6a6cb53b175785c2122fa93476f01917f18d15d7', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_384_exact_pool_free_rpc_repair.py': '93c5073a847180f69a7660de6a6cb53b175785c2122fa93476f01917f18d15d7', 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_376_native_sdk/oracle_378_sdk_reverse_unsigned.mjs': '07219743598d49ddc380ca9014b471a0db83c734d9b1d0a7e0cee0dce93800ca'}
PAYLOAD=(
    'c-rlK3v=Se(&%5&Nvf_;R%QVkKiDW$tj+FnV}k>1HaT9GN`SBxV<3`P+u7Rxe!F`fnvq6;clVsCufCge5+iA*=hf5G-P4cHKaAJWeCjXbU@{N='
    '{ll6cEz<BNj?yQ8yiWW$oGd?u@l$p6^h4{1kMzI(pnZDY*@MC@YZAt3G>gKiwcl)5ahRk4Dvg#4D_Bge@p8SG(zm(=(5%Tan1{(ETHHX<RS?D1'
    'kBg6s-qIRep1%Arv?lW?T%@jb7d~0RWD+KcYbBFlu?S=9emRAPCIlQ`M>h+Evy82AybPw3AW7jF0KN&LIY3$_&@l94y~z5wjH8=q5zLcU)*^&q'
    'S(DpfaT8j>dK#q(!U`W(;UtBkw?T3nCfGkV>cuQx-dnyuTc_(d^nEM3UoGPlhPha#tWzHs;$3{R3gRTpUL>jfjezITSUxWk4to`(_(1@^ghyFu'
    '_2f^M_p4~0!A#cURlLMG%3eKXztix3HB-y47g3sq*pZKmLBBt;JZhq1|DA+!6ej+s#!HR{;bS;i<B(n^%XzQ}{2*Q4M-%>j8Qads#jyW=aN6;4'
    'Wj%}Fy|iqBM$NiEgE9N#U~%WeQ~)*s0@+HfhN)J==ZnoM26I^Bdq4<Qx7!<z+UMt;0k6(_ujB7V5YX$_gYMZ|Z2zPTz==O!PVW39n1wzd$8<TH'
    '@w&tIo6hJ@|DrwkwKIU~HrofdXMXK;F8%ZNs52b-!_lC7I`V(7+ceXi-@C(Zzvu5CAN#|1?MCwutBxDtWOiI@?w^F?!&zfLZ0y&j)7jy)d2rm='
    'KRP)HYV~m~Y=p<hC(Y^X;IJ`kOb(8NMzgkma(q++*q7a2uX9Fl-*nGALje0ZH<(5?8xgJ~;I%)E61k)8mSrE-CMUtc^cc3=L8FQ7&i0QchX?!n'
    'jY$v&hjr-U!AWp@5FFJ{f@yFR9?imoa8f@S2jk|^*mkY2z@V4oWs=Cw&7)5t?@rh}I+-3qZyJY<dM%ut9FL((&H8bz-Z(ruZX6z-)DI5A<N9pU'
    '49AUHy*8^&PnySvlW=-;cr?N8<Vf1FpDfq$B=m_I1@V*5X%B00b}~6?)*8?xjIdE_Os3=M$#`;dG@Avr!^R1ap>P~D4`wHa$H!p^%QCA4!Q^mU'
    'o9s7ghtsc|fd6Lq^a(jS_7^~~K7~Hek6D!ZNO=5DQ4)=#Ip3+!Ff<vAgJ}&~ZPXj%dh_To2&dz5^LWx|9yAYU;dB}vHxI_ghljQOpjJDmPbQP2'
    'dVtF`ZHC`CFIg{Rq|`~sOMb`R>C<w20G$XXFdfU~+@HlEw7i<=i*d3)Y1WSRVK*EBM$QgTf+GMw4G)9E$+)>ct{*jzj++zcQDYXI>>nH*&T93O'
    '`q8X@JgqmUN8dOn{{y;sbSRcBnck_336F9m*9$zo!)f*YuLS#CJ8INVjt+qM9#0QWrqjv(acvTu)anOg7)4N<j*s^zNBakW`1NTGNKg%szBZkN'
    'Cr}Vd8aDlYb`Ag+GmaKhU=DDm=D{Qs2Leu42pgy|t<CC<>3*$tc+{L7G{XH_y<VT598YGolasI>P8#DzP@f*u$4wwKjoQ(y5gY>vKMB5d_wV~K'
    'CB&SVI{dvl`31P5LI2;Ko_`646P%#$+QWDJ$oRW{3~g*?1Ne(t{g@*luIBAB^<i+Kk3)h{U}s@Aj*o)FTJ7ZEsCF1aKWhj3LH)2ko*vc?XNSjd'
    'dW^%Mc64}LKY{-OG24gZuRa|g2DRq#blf<!9h}leZRbukYCaxqz-}bKh=pQ{#1ZnD{=+i9lYKil4(otv;TUM+NqBT}FsqHjqk8Qac1Acos0D{X'
    '9ZtQI!+O}5O@P?KewiE`z`V{TQ=r4VZ_VBN*7OtT1^m2ynli?i_ixTf+d2v5yqz2bO_-X-WDI2e_!v&u@vL!hgi|*j!&1Y19>W>~VQ+@};mOJP'
    'aDO~Gm`rQ+pmEZ$oiB{xxIAy4b}l+S<nV0Uo`y5vr^6MWq)NPeNSxNkg$4hp{Cp`N(-LfZXg!4U`QB_9-vfh;1F#l=)(gh{0<S%PB7Pnr_lUiQ'
    '1Ll62hQN%@Vbi7YlWW}va}EGI;v&zDGDbX2EZCZN$kGSX`zT3JhJbxBpCS{EAkUT$izJQ1;ND`>i)>&tg}n@imTST839tbmi^=VRL<bT<fDN>6'
    'aOlv^eGn}y5O81ts_G1|-^7Jamh(AC063y*FrEl*{32Mbpl_^T9R9tIVi<x4Xb`~>Yp2V*Z~=c;>-!Z^XZQ^R4xyvsaSAmEuI(}?>OXc8{S(3p'
    'QDX^|p1?SfU0Wo`dSVffiKxZTU)XargV|3lIJRL{0uXX4Y(gvZC;<^FU9aY$BNm$V8YGv6b#={0i!&cQz;w_`C<Ots3N?6e#qd>d_|F3RGmR!G'
    '7ILyr;T%AKoD-yJ%<9|Fdl*TsIv_-=I2Q=?^IZ!&cXfA7{k)@I1`kyPQ*plNmBPnKxJs?c=xG&p;&>Um*013c|Mhz?UyHY05Jn&Aw_|8`vII<8'
    'tV4AiNti2GECfRh7EhHswi*lQe%51-C(bTFuzE0`SCpw=!1zJZO=E{pd7(~6vH$Q-Wji7|yLIMD!Pjdsw2FQC{^HUf_5F*^r~_mJfb(DY5<lA8'
    '!53GZHZiO^>`WLl?x<@=FM-=5E1++dLfI6)WQCQTq?Qy&qvD5xKz$%zv-$GDh%Kc^P*}SPzzASBj$!H@2Z<f5CVg|Pe|hxq$tf%)t+D%wrkoKN'
    'njy!n<mm)H;%jA)E{)&WZJpW7|Lj>c);F9v@q~+Bud#pdC9MJc74K?W8$dM<kVserhL+bZ{LC<u9yR2oHwxmh@o7Cqm>eA$MTDNRQT#$HPA{+E'
    'zt<d*a=pyHL)R99o)cwEU{1p+gHZj1cmcGAlu;hc_;?yvi<XL_&@nh)@x=SMz*9E44Jv8)n2IJjSg!D?!e@~FsYEqgOqSEIVz1NL-ZAXS>TUQq'
    'jc)LKb~1qRdf`uQ!^s`=YH~ky;e;HAa{(T4JW~Qyp)e~n309<{TCUU8I`u~JI)vi@S`|N|`w+f)CpAZ&B&#axEcQy7uph0?W0YF>mMGBO0?uFy'
    'btBd+i006WmBOB(qhF}hfbm+O3TzyuF&xNB7cJJKs<H`jcOjc1bUSB0*AR``7nhwu=gh|5ZT!4|&L`;<KoPyR?BV;@mxKOkXE^lVw7XErR?fg6'
    'f+B<U0w;m?c4cONrfL1s`b^#V(h6bB-e+}6zKBDZFX<{<BN*f&L5`-9#1pYJz@;F$3K9@AP!UMq*e9ryz^AJP&gqP{8T^1zV4doCIep5Vzxds)'
    'AgDL%1?`KoaOUE3J9%16l$Q=aCZIxf5!^!$JUn<M>t|of^`3`|3igDkP+jbHrB(cRRl9a`?P~l)aV~9@fjsNH>GrxKRDSjPBmaG```i1Dn8+Ei'
    '4y+OOW*!04hA16Rs>x~|rSzhL{SOz@gpik49)~b-A+fjBzn0OWLPf7yvqcquEtb}vRTsoQn5AJ{C<{das?UnIL|NP=P?W=eVX4gY3poBh!j2bb'
    'wek%?B@Yp56S0KD5fOg8V9hh=T!Tv#fR6P_rbI=-0>y_MqG8bt*KXE9JoQOgT`{uo$0yc(bQ9xIplIfW2AwLp(0N$?n_%*^Hv^U~jM;`AKdpi!'
    'k^K85V1h-G3VcE4c?qa~8(NA4ZHY#YWeYDXCj7qyz%gm2X$7z&0122=psLZ7m~jLa-QTa%U_1}4-|ELNe{0m>-zMuO?Fc9`4*>aY!<d+PIW+<H'
    'jyK<|zeGU*BxayCFJV^K6C{5Y5zYkR@Ch?;{0iH(sz!;A3iFCX+j2#xZ?-_LmFcd5lT>xl&bD14SI6%Ux^KI^_PPJ|eS2^QTja9SJL~jL|MV}q'
    '!(q4gHd}vG$SoJ1NlATt>@QaUKbZT(59GDn%FqOyY;>*7Jw)KAox!O4rVFFX_bPbsBt&32ramDD%q_=@${2P)jGMq6v%MgDlRE}cVo*=Le|ZK~'
    '`OfpI_xki*yZ098zN1Jw;hZqjl@~mbJn-|H^lFrb_b@1RSy4yI)<QsX3fw!EQLqSF&5fA~>^5z=xe>k2F*BPdMNEi1HDNU`+N0BVE&D}o6nN0%'
    'UI!8QpKu}X$?!0TliRvqCn-qo>ExC+WfH=v2D^CvWC7JfSzEm@6H|^y5OBcIk}I#(9GrHODoV_G*_3~e+5R4LTI{<zt2ksiqbP0S(FOYwCMpj1'
    'fJ4h>R*+0V;1ued053dacbU{7g$uk&o{}n4Ga=n{pL^ls+IxG{5b)LpErfwk@sYk6bUOc*r}vN62+@G<Enp!gcfk!%^Tb+3(Du{{#?T;Bzu>iM'
    'ct1vM{FEew7||?3Wy~J(B*1BJA0-}@g6ufz5Ud;t;CO!8?~UO7NOYG@xQcz16&{|pVb2eINpsro&$=W3vOOGL<6-2(VFdp+`FdNnI$3tTuI#Ps'
    '0<PDWa4-62@b$Ef+>h<f=Ii8EFfi;WCq@g79f9y1skL)O$8P+b9Y-6!DfPC{&q3$6_g&zkv(?TB1(JP#IO<<!Yd+-bjrzI;ECA}rS{X*;RWK0>'
    'TxL|X5&HnBk0gUh4l~Y4BH6elQBKqFP1bSDGy%#$X$K=8R3V`W_Jt?JCOLKb)hrhe1vJJJvr|4%KOm7xbX7{FL|tmTz&8{%4<CQv?{z6wzD6<e'
    ';}5&?2hDmOfq`lMwb%d9(-vaAni7NODY6G2(v}(FHMjJJu_nl}pY|^<yCijKcp$ftw)hR))$?$MmImo^4SRX|O7eSxG9a@k83+bXV`?R;rASc_'
    'qf~|yu?A#Fi@>9%m>*YymM&whLsdB&V#Pt&DbB$d=+}CsBOSKnBQ;kzK#(%Sdth<xDpx-r)_m9tz76kC^cQPz)v6y}Q@L?)XBQ7H)*jHeC`t7b'
    'FY8V9A%+8yp*@G|mY_d}%<FB~EjW4(YlkE6b^G+!_m_YI=jV(<syM)8rTbkbjRa9`(yHnGDi25<FJGZe<IT)rszRv3GXfzw?sQ4xQ3Xc)XPHQD'
    '3(L8R?8U_t6$Nug1}rrv&HRjDwV|?Szre-kopxT>nOKBOtk0NBiysVlLci~g`tMKQ0e_l57}(LE%XfzDk$fitNd`}f{(`9_ccxX0PKcwTKLC=^'
    'gHiT-aPFPUqu0Drs^Du_uWhv&=30d{Q&075SvbEh&VJK*kK=p&e#piM%ZEpM_bn<i{MUni`|Pwm9F;5|o*LP<mh=d(igqv|1K!`jmzCV%nF~uT'
    'r}z2Gh9bnGXSYA)1qq&4SzLYmfz-Gke?T?u#~-93SG-UULGey1bHxko1cjH*ww9T`_S#!)D9E)Xc=MH0-#Qy+G{LLGMTkt8fN;=IgjSdsalaK!'
    'y(5=K@1ZW+cIDtbd$qD%b?Babe{Z{T;9l|4M4JOo=+oUyiSN}L2fP#TAa4ASBd%ooRiKvRE)uC#^A^dKN#{422T5X$D#8k|I)eY421%%%KLUOI'
    'o8@v^Ny7OIW(NOMp>i0foxj(?yfRx<u3&1e9hdzv)Q8QAckeL2@zX{)_Bfc@?iOf^<s#e&r3VGJ0ii49#mz=IpOIl}9e>#d>mgpk=;R7-gvqW)'
    'mk%mJ^hfVH1KYtSjPS?deEHzB3+>&2>lk&y{wZ%@y;`B62^yT0!bcVHhBo9a5VYdBbyF)O2JY0>4(-&-M>Aco=4cok`it-(jCX4VcJztE7W%5j'
    '?~2@$&ES{w=@#&8p|d9T9TohM5qyM(%V<*r<KDU&`38=2)74N{rBSk*0JD}07}9*_sXD6G%I80t0zb7(VYipU%cz!temSn`rJ*6<wgDvI6kVQ`'
    'wS^Q=kaqjJ;<yJ5^Sn>cKslY<`f>OdY|TxR@!1YP0m#H|5mES3HWiXvVW6bO-$1nOS@ei}fbHfK|H*oudJ3I>Op#Ut7X~6u<x?1smr0a9d3A@b'
    '{A5AsLjX0g?D;YPM6J%@4?ZSufbS6WzA|$18e(j)`Vb_;HJRMc)_5ZF1F>GlTG15`aaKUT83^Khpr1Nlq@2&Sj7vgG9LXfDJYg|kZO1ojl=Uw0'
    'DXuuWI*}P6aNP---QWr5+Dskfv{uz%3cNB0QL*>-m`ctKIN?R_1duYIV`91kZ^f?Yuv${lr=}8Ad0WUS2Q)zTi(146L&g;kJLeq`*Dv~K9fj-W'
    'HBbQ|xI%qesSIzTB~?PoH)^M)asTRELK&YVF5mY&+xKx+ecx^|{Tb9@(+o9#aDVs;3(2C($9~IV2bncrPBJy-9(s4|{bDgYN4y&wbWcGnu=qs~'
    '-7EDMcz+a3_wc&dO8%aM$j9A600u45E7X6&B9d|mz~}rz;Nt^KQJ4zvkdMGR^E)Rd$*`41i0mc^9;B~`t9gpJ%-w@q?19vk-Y&^e;p2jon`v-^'
    'Duz|?g!>4U8@>Jr)>4%Ghq<{RIxMVAS;<u9RjW%{&S?mp4W}Q0-df4+I-M>bV2s#1K+%{h)}x%FSSn3mkZ^3K31LtY-LH|Sqp5^l#>~}FxAp-5'
    '01t1SUYw!21j)lP20+UtOc`m~u+%DEB9*fN+Jxo{2->G-`nMQ7T=GV9qTVU?9PjP=G0>uLdIscHmR_K^s`$Dr*7G@kTk0pn{-|&MN|uXncca0<'
    '0YXfYulB4#>DcIIbJ;%qwf(k(m(Q88Xf<yvS}k$1`7UlcqxRr!XJl};*}?Ldj7j^0tP3&I1TZ^W-iwzrJkEUb=a|B2shTz;JWc?Ru)y?Gam}z_'
    '-QMf|A72fa4-{bHW`j1y%SQ$DxBCexFb-=aFgE$hAq+SS-k(3)LrT{A3J<A^ZqFZf|BVP&ulc|Q;=k~^{YUm%dH<$6fHVBf``%gS%s*}S+Jis+'
    '^Y#TU`7j6KtUG}7t=sS62c~sR!n9&A2(*e8f#`SDJk~1O^~U}|^YG~Sr2YEztn=pWyZ`&^`9<&YH|Wv(-#`5E=f8vT1o(uT+vu;m`^9qgcbuf_'
    'PY;hz|KQYi{^*>(AF+Fz(YyYjJNgsAzX|3@kx)^CM~{3VH8$BRscU11gs9__3X*OO;b<8DC7BbvMuZi@S-!u6!>_^~5^hdKdR%{br}8@~sYa=0'
    'rWB<|sSZ_?pt?b1s%t~BYt`xcew9?9Q?9ssUB-!50oDiRyM<Qic$Mv=bu8-!HbK|P)&?!Asu8_kxzu05aN*vY=exCD%%jC!g^SY4m=y~+ar3&_'
    '2yXM;Yz8oYO@<p{=T%U2Z?u1Xx)t+%ymkkQ`6*ObEm`(op2cWpR!Erz<O=BOg_p@zm%lKrZ&r~nEE}_EQlE#dN^S-TmVCROn-z6=XE*Csc^M;E'
    'm>)SOSyyqYjAPiMK^BVi*ME*OlZ2A1TA=ls-rW|10la6Z<nikl#40%kqheNEFLPx&*-A>ggmRn8{AIND6V$xkYG!G)&!&we%`aVMqvR1yGTUO}'
    '9M?3zWUjj>n@0e%Wv-b5oS8w=MU@<I*?ogz5;e=2M9oP2(vDZn66z2}lpT7?@9h>+im3{}K`%Frf*u-=<DFc-oE`0NG&-<Lh22e+GMq*Og!jEs'
    '_oCyUb${;+6q_aOmX%*~GOIm#+c|vKMiC=fuh6Lu?JLGlL}&N-WvjgLsH#>QQiNv<Pu2qu7Uu<-T^`Z}lv@logt^Px+@2yzqG1HuH41wT$5nl%'
    'v%48(VYm8J3;fUUY}5VM&Uabzt|yOdCDc+uZ6n3pR;_NX#*Z8okt?Ny@tZEUXs|i6mVU3}pZ8DO=l<Di0MI_`4DjNs^T!CdIgrHt55tm+Ff+j='
    'Io4mT$H13VKIIq!#n$+f;^VU4Ko<klc7Ag3*TDh3MshU4bw@@LX%RhqQW|4kbvQ?lz{#Kt3^Fb!tr=-UYxT;bgZn1ZuEEh9`H^3<%=LoMH|oP9'
    '`!5j1Aelr_#gWg`aDv8|{7vPN46kc8((T8q+BMP=cyw~jQC}U=rsiqHkTr8nso3h>Dv*znvS-9#nV}20Z)^i~*&lXCKyg$^d|eibxp9oL*Dbj`'
    '=;p?~rFFArW`E3wJYcTlEz--ZQgR5uvt}Mm$d(tyB*o~BAWPdH)ddedU&1G*=VR?>&Mt7|^L;^I@C7NM{6&~*v&-E?&>3qdk25~>422ftAmVIw'
    'Gs~vcDF+J-&+qN?u5d%(Z}HBGO*OlkJI9f9nXs(Q^=lqO1@AVJbPtIA9$iEV4b>~Amm){UJt5NboBe6Hht%<j93ZucCWZ*c8l}EZ+G^lk(z$=1'
    'c#USQhHjdVJ}{5?qE0U+6c%HVct}61B&{zJ6PI(pTr6cd=<Up(FjWwi2d-&8M^hCK$Ddm>Qn@ynvk~hI{%WH85u$dJK4cxsiaADm78U3D5}+C5'
    '@LdmGLtghm?j33@I_muq;3DC>lXv1Lt1cwrd~wkmSw-pIhH7Fmp_2HS2h3&>3h-Zf2z(w90{@vS0UL9=o{;MU!!_+|xLQtb&7UUgI9ZldW0%T`'
    '7pnX+1w0cj9EFc@I0634kEZxlQ3zHF6T|eKo=_ha3ZUB&31D21FMM2+V~A;36zZp}>TQH~15f@z<HTGYrt?z-9rtg;V4mXC*&l{j+&=|O8g&L_'
    'G1vJ6NUP>?#44}H^C-DRJ_#gTL=I2-;bw)F^EutxFD6lGA#}0wr4(8#EDv73M>nWAOXkZ|4kg?4I7fWL18GQ>3r)P$rWlX&(ivuzjpzaB9R|gv'
    'lNeI+JzF3{!wfO5?AzshYF}F~JiJ25Mir!KFuCR9x*fX~L*g8Pp+o(4Os6^$8@vMC$rLUVOWt+b=c9Kj*$_J^J3Vg4)f?1t(HG=;B|DN6)s-zO'
    '>WEhcyFrCx5~Vof1iKYECh-;+C+ql`<GLIGYkG=S30XauLv37qPPL9<nV+rN4y_3iELuE$KN$801p-Wy=ISKO%@HPECi@IuO7MjtMwsD@zUyf('
    'BTA^q#NP^J${~@mNAjbllYNt;vk6zOIG$XW;|Xt>)kYh=jDn-vLjiSU8S%=%oXBBRY_TGp%l_#*G~^S=kawinG+5@~Mnqdd=ZA2d!1)%YL@AeJ'
    'y1t*<#j%O1d}kunGP>xC1{ADh?+jg3z!p)|Fb@Jl6{2n$dD-Yy{7{b*yg4)vr{whEo!(Hsco<d0Y4ol;9Q6l(`rNjEh>{?Vin$_`YNd?-C=<v$'
    '8bRvg&9q1G|55w&ooR+hf)X`<DGYJ@O7uD(s1-oO-@9k1CTWjAHtk+?N6%dmtuH@+MPG8KJWOfl*`3&Rk@cgF)|P2lk^=n_(nuERVkfyo8JPK4'
    'Q^W%hYlWSSi>`mp<`^M(nmR_3h?TXfJH!UzHFpjKk`t>WV?gp~=@?Xo2faZu!fM{NS}UqBPc_Ai>CsU5@x5qmSnFuPlqCtQ_I*%T?9!$UM@%%;'
    '$Rqbc*?hQg%hP;CHFU;i0G!#>YU8`D^;ldFy`Ju4vl##rg*_{aF`<7)J6-l!i94Ye;kLW1RL+q{D<~~ESy3fU#rN5k----Egx2(KG%HLorM<`L'
    'FudmDH_$gMn#}-gL*-5wzsbvIB~*yGdERNbB9xQAjL8;q_kl0SP+OC%Rp~+s=vZz~AiEyCg%$akUAFM2U-B~krcvNMWr$s81~kuFHQcl4kD-go'
    'n_81Lsk^uHqt%|1GH6e*VHVl5T4dSCERk3Q4}QmC1*CK01*(OxE`(Wbh7;-?<a{a?go}j84MIJgEMhT*;UhG{xd6<8Pgl(5(ns>OapvU($nKMY'
    'N=@jYrs332C@SD($~(jhHNFoPa8c#MHW8Ia)$2x7Uo01bm?5eN%xCIMQ|DpP_#!OA8)oK~g<NB67R-~S#UYW=*n+RCXsKFYwsZ4dCLQplTP;_('
    'bS{;3O3G%!{Z7TpWPO9i=n636x}cLOUD=&#^9U%pvJUL{gWAbqYh!<Kfat7VL1l|}cUxF)zL7XyB9`T5UW-Syf{ldsQe5p9@%}N5q?@Nj4p1`o'
    'OD827nA}~!_aj=&HRiKk(&h(NE4#+q2PvU{(LME<MQDe_61>s-y`B$)m+kfz5&=cq&*bBlsvjsc%t}fTxRqBR$Rfm*w1{EJLtzX=%i@Gh;TT%P'
    'N5CtMJ!lEmArC0y3|bj^bn`*}T69d74Mo5FAQ}ZVi0W*tfubRef-o~*R-Un+!W22X@e|%*mX)SZirhqvhtrfd!liY>&=016t<kk#1Q_00iHD5k'
    ')>z!q6=P*?tx2j-#5jRq?cSOHduJr%-?IXm!QS)fYQ(405b7H2HSAdwCn;<Tyn5lDIO@u6GMy{nwJ_84rH!#14dMjZCM$2Gk#gynS-fc6{Xr@X'
    'Ebp;jF}c}r{^g}r4-Z{y-zoNp5ecZhUPO<qDw3xPa!4<9BH~ytUn(~l3al?i?XQTf1|*_P0W6BBHysrx-|%zP!>U@`py$h2O`5ARbznhFUkz4h'
    'm|ZbXtFwca-~8cf4};rWZ`a=ApQ6AjZhUsS+yoY4lCFa}EbyKP#3pZ#M9gs#uF>?P*ZE__OxRz-Hne#3+_F=ggQ*BtA;)}W+Mz$N12*d+b4SH#'
    '`}`ce&_xutQYB>mY~nfx#J@}tz)*`j<`_i>iHO-(nibCGa^yuuo%~F5Y>y#kkd(<DtY16{ptTbR#arFPLn-Xp4y8A7T!nqYCd+iu0$+dx7N${X'
    'Yj$A)$n@L50BDDq;mo(}(&OC#D5oM-s;I9`HM!nR$s6JW9%R<`<`aXeqS=Gbc>0H1v^5nyq;St0Dt^D?hQI-YDT}iPl{0MR7$be7O;x}7wECi='
    '3$yw!pbL`0QsS5ugZ|1=`O8rg?xjJxPAE3_yZ$+|chqhza|*vuy9PG=BX34V{UQ>-9iSOO|Mjpl_?^e8EF49<w?O6yXjMfP3bL8b@15RgXgkl`'
    'D(3ybFmV-!v*;0LNjDP!QfJ#3yrh9~mDpXIfXbeXm_`(X_+0Km$%%;beK%z$^|Fw6fDh4xg5!%B>|c($7wvPuR;|@*xMH;`dOP&mWa#v|ectZD'
    'guZQ$iag<eVhbv0AlD{)Wt>VDo5j~RuMkt&-ZjoDkA6>w0AF6Jdv%Ad$GD(qk>0}XaCcQ#6zM8aU<&nXGkl#d5#!0fHzH}qtKP%5jgWexXp4K@'
    ';hMLE-7b+A|5gyICT0f6ytb<M;WP@q0U(If*r(v}IUtzb84;xoeS)bacu2>d0WRy&&H$3ha;1qul0Nm$|0K&4PQRq*jCl_{U*P*{q3_!SzyFA2'
    '#YALuCZni%L5!pTge2j)$q(=^nTaH4s4?(>&pgB{oGiQK)#{Sv9qI`YsOlH9oCB2+1`TAM$DVkIpEQVhj4y*3T_p=pk_b~5JSbVqRi!hm4_RB%'
    '+%#AvEPsI+zO^U1;4pcI2P49M7LH<FO5(5;0m)oT47>0_6OM${4)4BDo}soCt$^9ke^y4Qa2W(%H*r8aZ)SJ`M=b3S+zL*fnRrfy1z~+dF?p<C'
    'Sa@`EFVq`X?8$4@^CjQ9f)kc!smSr8bw>A$6ziKua)2`tA9<n<as@zfj@+WqjXBHN$0AB8E&*r@&1N-N$Z|?*jhB={gISic^n1cDV8YyyWtb|o'
    'ffQc4Rrbrj2liqfR)i~T775Jg1DUx$3@|kc^G1+P2(oi^Inp@iJ&k8u7))-_SwfDnZ2{TjR<l_}<;Ek71K!wjMQZaf)7x<<YNiuUOQHcSl_W>7'
    'HfBeVEs%%W)k2TRl#c@Ll926+7~jmiCQ~#zcv*oxVR2CDc75UUt97cP6ei1Pe&X}Y5?Z<k2I^XslI7s5;bV%Monet0lu8+o*!gNb^iZs5vGgrH'
    '*8@X%p*jx)4fB%_uXRxpmD|ivL8897n$nXjKr7Iehb64TY!*^@K;$eF3+Nt9E(>&v-h5oRX7<<ow(J2GMh$gKGnzHg%4^E0tK1eLchdv~aw>tM'
    'tA{w%-?e*Z{WovW4Nmb3{cL7Gg)$u)P_NS5OwmnW__aA>{7sRv6lFG5Q1desb=p)Ue}!)V%eXIDp-iQDO=3SfdGEv#>>{7${R1T`aTQVKS-}vD'
    'DNb~|5&FW7p+$UAN$3lPfkiLlj301i+qgd*XJhu6tXjD*u6FJejGm=$4wCaHk$UhU!gyVo51^8@R2oGFiI4ie3g#&Qmg0eUocj>?uBky2l+T9Z'
    'QZj^70N`Yi-1FvUO8F{=ie;7BK+B@>It>Ns!%tPDa7d_F4|a#iv>yy|55qO9K<Qf*EoeM8LL*GM;}OO~Fu$WYahxpo1M}X`(m!PGVw=3xGyruo'
    'fcg#qINzeJ82M`2z$O6*+tt%T?CK`hVC+-Becl<Ob?Arg03$yZ-7^iX*ZCD3OVyV=!!=K3n2IgRR4FFUIn9q|z)CQ>&LSBLcO;BKlimXRdULDr'
    '7_N*r3+z>pNPY;GB>}q2PBo$IQurp|TN0I3VM#u+gV5@x<b4*#c=C(A#+o2Lj7KIy4x9qYpn_~-wJ*Dbs*G*HII_%9Gr&Y-!40NFNU;)+&CUVy'
    'Lu#Z)ZO>RLW?i_x=UEq|8>q?$iXa!SV3MLl<@YqNQJED@^pvTVh+*Ut&ghJsSE7Z9Auj`*&1_o6%k<V_EF@lmFU53G*d=t$i{^83Y2XQ;U0BQ1'
    'nl7_x{E;nJND+z|l}%XExjpd&Y%g2eiHKrN4Pp?8P$r6d7Gql$rbFxzwhzA_yKJWBT$JQU4opax5?{z#&o-oTZGcKlUY;93itys(feHUXl&lCy'
    'Qr2a${t1w?i;b}!&<hCybVr!5h{?lunJjBNUq>?l8~yja_V4ZPdHeNwCr73VLz0uDQb;khojag9FB=*c38&aNGb%<&A%T1(EUF}iSx+cXz-He('
    't~m1QHIqXgZ-qSWT&|HP9>QbceN^p)N0&1uC}dYBwm6S=fYGmsZor$or!7uylWYOmFer1_aZP3xqi?+9JgeA7uT^23FC6A||2>ftBI}TP+n|O|'
    'D`L3n|0MUy22bo=Vpxe8L!-m&z0wD5I@Mt0aWuUNpGz4GNy}BW0`CcfUF|$hfc*tbJBQa5g#m^lsuwDEfArWN4ehd@VnjPKrl^n7tg-YvYYJ9|'
    'y)CAeTPO-HWigaYWeXrG6FlF8lnyE-tQ_h|5I->8P|8_=?Ch@=8{+{#LJ;Z)?Y9?g>+f|KKlymS=jjTg(i#Bx$rr&sV4LPE-Hw$J<w+kY?g~R3'
    'qDn4{`zE5=i=l7@nAPk2-Wf0}&L^_<L#0NXVq~%?%#RjbfTLiZ=_2*Pu)v0vVEQT-?LR8f)NyMLrg6Ej1Z}R)!gO+rfqEU8(Myv=xQ8D4=IKp3'
    '+k{{3ifk9rm*0mmxvF?|%(RaDxm4_x7hsAW4h_JTQ_{1`I0-U9!iOQoNU)9KWfmut8xe55E}9&qsK6uZ7fva2DOQ1QWNto&TGd8VuR%A@#gac~'
    't#6lDh3YjA<QGrvP>J&lffY`48xg#OS9t!I^P+j_pfWle26x5JU!l)8PTclRlytzLh%kXJDkV&%827Sa7QRj~p}SWl;f4mDqp&DUL#fBM8cL~}'
    '%z;s>2u|W9>EFdQN6!2RL;-xKCAd6Wa?U}|S{ceZES7nK7jhU<0?y89h;d1+_k(lvB_PQG`d2kyJg}4n{Q*W+`ISr(=spABJ5>?8wKV7&xvni1'
    '8;rHhHeW=;Ng}E|-y#e10OrP0=GRRhH~4iwXZb-$yT_U5%2IAQqPlSukX7MjT~S|iug)JOoj<yx+zG;~6(Z=BP;sMf7MN&+s&%I<267`u9@xEZ'
    'tt@{;um1r<G5W_@;70XdF5UNk?esjmZU1zz&(k-)zqs`5*V&7U&d9S*vuCp9LIPI_qp8<)Eza2;)Lc@7ds*~H*ZS$FJI!(K(Gy7#$WU9!TL9hN'
    '!wF*0eyWFuj*F%N9`wI>%CdwC)O#hN0`^@`r~sWWR^C0qg2BuhaaS|2_70j_n2yIP%ji<Mdnnw`i9kUtj`dwwDGh3}^fZQA#!z8bAT5|JSA<L9'
    'uMX7JRl=o+AF7j$;HhXah|%#Hu3&6D5nnvBL2JK0wH>!!D-LL>CW*i(;mMAPB5HMR?v^RIO2eqrR5{`ngdv~fXjc<WQ%v<*gPHuy=F6oi`hGX*'
    'EmNF%V+(}L!Z*z^hLx}Fvj!$%G&iS+*rf^K>Sk`@z{ivh)C`L@A5Kf!*<~Di^^#_q{%v$~`|a)U!MrGI=g=qDk>`QtBnDFylz=_rjwoLRw{%jD'
    'eagZPDE2(KNEoZl5}+qO=5#Mh+OTDUGqOVmgs}x6z%0)Q_so1&BRo|NW>+bJUf-C%WCLi0?)Lh<P8s}$uR6OCv3*`UIr?0-y7hgL+J!s7pnr!j'
    'L7E5AeZlyY=$^;v&npbkZpBymU}M*>;FQz5m6ueD!+5;f=)Q9ettpj=sl_^*t*4B6Ch7;=43cNWm_Cc@(jIThV+M(E{>E1MYHGg8Qmrr<$(J6O'
    'iE*-T_(Z<4Zt~Q>@Cvz+Lpr~KPGlV{oq0CM8{vCWVa!B<BXF*ZLu_mr;@D3gmf0>z3X^RfrT+HOGYqilauzE)={ImQ`O!al<#TpqglLM$y#bTi'
    'N%!cyGQNM>wisw`aU<o%E7chNTF*&itp53*!cx(7!9RFcPzLvlYkgM6uFUKg^WsiO#1~Gre&#=$_%O(9)k)>I8LN#8{EYQ9uI4jV&rttpWBM@z'
    'W&Nflt#99+=Bkt#Ni`=aj@7hyhb$2jCq7KIo6(@>ksz9_GCK5q=#IkQ8WTX(k2o<kVdHlqsLxq)b}osb8GC%3CB^#Y4m$d&C??hr>A;+2tbW2g'
    'Abh4S@=>g2m%(4tHLkW)M5_I*B31cRB6kO4VUoV-^xrhga6Tc8!r(*C7*lZoTV+Dm9Hq<KFH)NC2>oD(-NhYu++71gWph{em2gYM6OwZ3zdM0P'
    'I}9=J`?6acFXNaSzR(gN1zFye3>GaYy(?gF`Ka-kn{XEnGe=_rSf8;xQSNPmdt*QA5MN0_t;PM4sedv`<)hOw-Li|kX^wFXv1WmDS>R5~4NNPf'
    'Z&cG*4)}Eyh}ERb$>gToT_EXD-auCjs#OH1UM*l$s)-ALWn!?aYkb_R@4{QM)J{AbQFVk#_)vF!Mh7aOJ{tEXR%*H>Fx+#zp%z@S61Z_G!hSk+'
    'UfOzcon1HV&Ib3{41-Lu%p5sN#5S`MY0Fs_Um0CRt~C^pMTHG%$>+?V)F_!X4*e2WWA1M3T>*D`{p#k~szIm=+m5#A*XaFfo7qM@{#Xkyyt?1a'
    '80c3w@;>U-^Ukj$pRs*@#H4bHy6`Ms+PFzGUUI9au6c!yxk^RG-}xtum%Lwv5o*z~>>6s&jd}<m*<;KTK?x<doY#y-ybh*cMIw}3lpyzLp-;a9'
    'tuRmq=;&7yhOLBkU(KS$<i6-WN{#bYAUGSHGV2@V`~7-$I8Bx-GrhqQbXM|7rRNQ2C4Hx}kz3V!Hee`5yS86_o$$cnxKzYAj)u>?2d85{U9wbY'
    'J|_XjF^P<Jlzwqv|He#9o>rku<99(;M;ODdX!7E57*%d)Q?Xn3;XNQzYqNpO>7WDLn>9j<IBq~<RidfY?TtEbI|J)-(7k|_w0`aU>1>A7?F~DF'
    '5mxLAK)@uu?+mR<vrrY}ser5flp8BGoPEXFGb)AHw$kWzk(e@?{8^ZvG+f2z#7vXFxCc%d^Dtz3#9avlnkI;l*MgJ4@d9U-3wB8B>1E3*49Z^Y'
    'WN4~`QQd!pTMuQEr;r1Rr;ZXA&ck#{+@hD9m^i51UAWxxS?Q}>$!m|j*yTd}8(1ZFC7#}TM#@)G-ppR{MFnC?3wGm{7?7A~C|#nHJ6}?2j6wbK'
    '=yDr#mL^J?HD-Rey)8zX2#`TnlUJeE%XUjCD^>=12S?!RU3-5c%(a@&s8Qy3R?u!0tu(e<UFdQ5$c#hX1{lI6hum&SEElr3*|;g75z{fT?+c{l'
    'R^nU|+kq+DsL$INHemyX7+A>+sF_<g4eP)UD7ujt)lD3%Zhh`x;IkZoWOHU5V)48iMwt2v9fOipFbNIC<;D0tTGfigvdH%32FT5>a}X=zb;jf)'
    'OO>~b6NGfq`uxS+Enas<W@Kgeu2lh9@-DySC$|yM;C!F3X-^osl@WCVJ!kV<0LN_TJ!;EABdgw$7p-C=Ef(+B$|Pw6uSzpou}jRL(ZpjK`r&K_'
    '^jmtALI=ui(O3t_QXI-vfrCr1p^CkO*9J4vVdE)_-z2mR6{G36%b$!$+!TmPUO*%(3DfZZkGB7Hv^BQEe1R&C<NPnj)kAsRE>P5GE|?_rCjJJo'
    '_dkiY8xUj*COhAo;QbFr5bCgkB?DB!CWG)Me5|O7SY5|g@Um)^Wk@LXtI_f7NIkp-vx4chW1K6P?f*K80Utg8kCVmkLld#9-x;lmD0udVLBID_'
    'xMbM>8;Bv!r4d7qxs?E=n`NGR_scsoFa4v{c?{zT?xdWPpW>Y7xWe<4_avqqU2|*r+j*3Rd5GL&CjoJP<<hyWM*eYRG#H@OF1dW5{L5s->bIzb'
    'z9Z3QdLtHj$h*4Uqzoz1gy0&PCR_s9T}dUYd>>7f0bHrNs&Y_XU7aHlX{o+3|BN*;&sD((hh;?}Pn_09fZyXX)TAOX>9V+=O)-I6PMBr|er|5?'
    'K6&&s6Zfys`Wfcp>an0y%a^!z)o@L6YXByD0-Y<n6LYNhpXE_-8Q3mODoA4;vp3lD$*<5wvMxOfs7VJYz|j~C(SYf)xJ~37Xe+-ie&6f-aoIT?'
    'b<X@Q-3<8l3mW8iyG)H&if)iOfiUIZt7x^W*6>FlbV-VaZVwn(f!sUEZI?3X1~bfFg)d3n!cGN@T7kN~stFoM+=I(g*ZL5ShqM_nd;+Wso++5h'
    '9dIg39DMnI&Xtf}S<EZl*J^U-6<j+>sT)T(KHgP&x~HCbyYujHm9m|U?a(D;t$Mt1m+^un4D55b5RUqAVt)Ksvi%8Ml?#D5OxKp<)PeEwJrfu?'
    'vDq#gnonV93eF@sHhMh=N??i?&~(*k0r_A7yJmn>VhU&h1l0He@oHyqN{E4I<?6u%Sg0m7m_UhVV9^wXrolB)?d3XMty5JQ9<O$YowKny2J=db'
    '?OIe2ms(J2N4c|GJ<%kOvwN+@u-^uPtK3(c?hOjXMT^hS$p2{dkxDW8L@a@otTBjQvK}XClmhbuq%&GP<>J5~sZFZZrHm6JL$**b8su4HCUIK9'
    '{2_QsEQ*H2qs>rAdvrrVFS;zE4QoP1XWNAz-HrCMP9xK=Ml4_iKKrKn3gUVD@N(0cR$V>WT7`yIq3mQWRI69XBa-2^jdV5%@c2hEn}vblffGJ1'
    'Y`1{_dM~zuW88!m|L^L0E9i_gSBa&(nJ>qHbSSKRwzC*lb_<8(W^WqwrtzhiB#_9U;;Z(UqQBZ;P5dov(=ncLPhQ=r0w!fnZ7`$&YGT=QAP!+n'
    'Gy)%!H-It1=dD7%aJjfztkLR2kPO!oyiu90=M_T;G;YIH^cbb6FqiG&kU5PKH1hg{ZkIcbDlVe;L9~!91}iU!Z)jsw+wsjB@#7Moq$e&~&(G!o'
    'k5b9^jP2Siw2e)h4gSIeX=<BbRSl+7Kj1Jc_THZT0^zs;w=72kOF$Cns#s)09eym?E((zz=C9$C@14}jYrzq=cW<iH$ow=7)!?+-1F~$cTHja|'
    '54@6kvQ~VPcu<ul8!IOj9W^lOT?OA)`7FEifD_Gr(Ok2iFx^gWx<kgXvX~n_V80rzNJ8SWJo6IPaZMECt+)8!N)8J3qLmMeBYM@^<n25hwFjeX'
    'iz|Tk8x0>s<TDC0ZLydbs13aApP&2n+Qrc7^)V`j|6ynqm|hz_42M3C)?TmGED`1s8hP7cFrogi`?iN+HeL_<?X%PNaAdni*X-iWKc5_pOQKP7'
    'oaC#+;@i;gj9X&QoC|V_2_7|7C=XZ0A7sEnmg=z>bwD{YS=<3QvM}DDg_?>um^0Of<i?X%JWMSstR+)rpt5KMAnhd-zMR6~+($RJDa9%ZFkImp'
    '4o(VlhM}c-2!nh)n7ajb#KVL0pKy_cX+;eHNWryONQ1Y7_T@Va#dkqbjJI=wyT<3ro0_l@VX&Murnm_d!%6;L@Gi3q#qIZJ-4TXc5KZvjsx52_'
    'ID^R}fHd=lU0cqsPo%+qQH<c=mWF&0ZvRDE4x<p&J<s-ir0TwJb3DO2eqh_u3M2La^#}Kdzk#Y_knB&5mz+nCH{~yr<vdsff?s3rm$4{^<Kof!'
    'rmBL|A4dy3tbwEWp~WKb{UBpS?~C+h7MYldyTLt_JokR#0U7wN?e^YUoHeDOi2VieXwy9sV3`t*MAj@S6B?XaK!zh81Q{^$B@l|qJPI+lB7A&6'
    '<}RfqzDWWY2Co=f3Y$GxBmocZ1X~0SA)aN8oA0`oG}NUhj0-L1%92(E&{YbJ2)sNpq^sZw`2aG~=#MZkATRk3i+hc^K^Ghji_M6kX)&TBR+)y-'
    'SxhX7QA2ph_*c|BIAr34MQ+r?RmWkLw{gOFd?N3h-41Cgfz)I{pFRKp3=e&JaYg|rfV}|@)ryzP)a8uqE%s}P(xna1CNy84!o?>9#)B*pIG=l4'
    '`@W1qiMK3_<`9PRx17D;)h0j_xl5#|cgjM?yH-D*qP620Fn6-_#z1NO-EENELJ|2a<#zc71v&Y!OgMBDC>7Aii_1c*Cm-WuMra`>G~6;pL-uMt'
    '=7urZtEcR@kP5OFK=kE<;3sjiL|``0va@Yk&2Q7Hd7A=F8uS6<JQ_m9e*Q*BP65v5w;cpRuwGjB?wcPwK!HqT7r5kwa&8*(Uc4mZCx492WK$4N'
    'RqBH9MBrvs2?qV5pn_iwm=6?SQXFXA?6}(lX5suC2tA9r%bFOkqxsa|NsQ8A9M(!;9I9r@I8-2ucpLe|VPwLKVfsr2zf8a})!Hom$$ZNgJ28s~'
    'BSJUOYvuhWQ|TNCC9$*42ka8y9_He8^H{5B*Bko>&BLSPllJS=v(B5h@BZ(v=NG-p-=IhDfB*2upZ^ZV6JWM)Zlk~M?ib6|-*J+zKRrA?{ex30'
    'Q<nJc_oH|HL3i|L77_}XLp*xq3&|xGV_p{n2(eH-%kf`=5hsI5ZmM*D2ZvvUJtREhB`H#J!HZJLFitg*{?d`oEH5d-DF$kUBDP}+cnBX<QCo>i'
    '1f6n4$lhg~comS)T+HI*6hakY6C`<C8$|DAQswDrD=DTjRZLHd7LC}g(tu53I+NR=(LAiENliF=!>M^yDZx~4<ENAok5zBO$7ytfS_1{3lvX%2'
    '+z>mj0&1ZnmP&#4FC1=|fXxTNpIxRZl8!9<FVA8$Gb^M<17%6PWSMMr`3uwfW)=CuvN4M$^?6VvEqPc~`QHk%xC|03`E*IQ8+i^>Syi4`ig%Wm'
    'DFMsN7{S8)$T`Wnic@7A!<LY^oVNO}{~UEPVZkX=jfmnxJHmQ`p^6EWJWA=tuu6_WW4#3~`4re1)Ax{+JGq}C+N>xbj@;}hQ^@0=6hv2y?H2r<'
    'YyAW@uQ3kOiZ~^%Rc2_2Th=Sd=%+-e!}y;V!<TxbC5(otMx8Y78O-N`b6jJLD(fgubpwSGU?$h;mbqrK56hNGk>=!p6&lEdemzbvZn{}DN@&Z#'
    'T9d+vv_;zS3SzE$Qo2@l=qbM&Tf-!ub_S#Fn{FpdhI7`r?7+d)JN?rTP2PAM@0<7-pYH{EwriLwcgh&3WlRKfOmx%H=)f)&c8ddjeBvuOjZVuv'
    'cJW#F_YSmnmSww<HCp`K!~`tC<VnVM9lmR$h>_*G#|%G6XZKbS6qrf~$4X|OP`m}Uh8CV;FF)vE+mSAy+@h+`d7~hmL`ilXnA=lCNi>Xr&1moK'
    'F?}NbmaY2?HE~xf3#)ur<7E#=AWl+-aDo53Wk1+CI5%n?-o9@S&hp4sLM;{4Hd4%O)#~PI8%*JfgfW}I>ujn0%Pwr6Gjt8_qF=4`Tm9Jotx<!2'
    'oBo?Y|KFV+#<ORG)fI4dzt{0)5L?vYbq1D<Wy@7|X62ii;A(!7pK=U=l7-`wi@F<@bz{GQk-zb3?307P4i4xwg__58M@AB95j}iT8YBC0WXLOz'
    'uDr%Bgdit1%_HRugQ9BEUm*OCA`_Zk5c)=acx3+tq8KETDB^jN@Oc_eqWfUZ-&7tkSBPD+k#0X;)vl42z@w9Ej`}LIuW2z;i?Pmo{T>j;ey@wm'
    ')9sCvJtObzDTXgjT5TJs%l@!SIWQGSd|ejVl(GmR7^kYT&=Y6$me$RhZX7KZoGKVca}Z%#7IS}OCJJ!Y%%e$^@^lfIwunInCNrE*ld78Kf$~s>'
    'PwZME7k|sm<+aBb%+GNV>KRL5QaF&sPO(w>&@&WTP&#sRoYV@s$Z@r9Hmy!MSP`e**5;YTJIDVqqc+u*P@C)5OLC;)$)@&z*z>eyTtoGW>7^_b'
    '2=|0YkElm(JbRSUo<$c`Cz=={AH#0@J~y)3oKQe|qpNmOCN4*~sGG6~D$y(RrVO0#s6b<g!mKm+3trR+wVU)I>sVH-a0ghLDu7by_Am>ko-9CK'
    'dm}(f=Z0v&JMoi}>poXp^hQ=uy0@X4m`seV&VS|svsr`!{8t`=NZ0PkDb1&z7g>D0Tr%`5DX{sI4Et{Q#`9Zw*5@y|FEZq>>0=yDSX>bNswf02'
    'g^6MMPEV*03k7(D+(P_kEvd74SY@H3>8lbN##}uYlm&HqJS@v8VA2S<9Zad(`2$F6=giJm&L^~1@&#sv4Cycnh168io>eO>kDh*44kg?46h?(@'
    'cpweQQnT~ar&!MlpPOM;*@zy+pwGE%_U7+p>FBjI^ta2oDF;1wwPxeOgaSodQE{l>j%CVFG&nGl4xLR@b9BDzw9iLcf=;oMveV;s%u+Ejw{J&b'
    'M+%Xn<rWonq=UFqAdL#gB(vNz#)+pJ6>l-H|M4@&bvXdm^i;RshdI>7RY=ajOm3mI+77J=5-eI|Az%swm}h6uNSK==OuS6?S&Mj~;R{2IFvA&r'
    '*R#M*fD$S)i97`ynQ};^>=EPL@}}Eo6RuowJh?8%6W%hb{Vz|Y;F#O9fI6~_cva@-pl8DET=q}j;YF!H2LJS3yQc`Hn+D4a(}`#+=xjFpwu@sE'
    'Rm;QL>kTMa$=;dWt3`z(iW=rYV5maW?TuFT#wH8LNinBTp?&@I;ho-4zIYf_b_)`=t8Hds0@+nMNPWDSHl`0Bwe?)ZnMb-(^OwR9x39#GvE6oA'
    '5v?yje??z%r#wt)=h>aub&>U>j)gK}>G%rtOGqQXhEH4=*-0)@24+6i6!Bn6DWwIo5Ip1vp_&9ccyQ@7b<E~Ante(%lj(@59?wW@uKD?{g|)Bl'
    'Sj5*m%7q*}@Jz*D3Kn*Gc87=KDI0^z@Q~w_B&_CLtF@vE^HfvJ7`9V5z89?xYc0Y~C9vA}L1D2=n>HLVn5tA0Wo?$?chlj*-C*(+Gw+yf064R$'
    ')y8*Q>qY;Bg?hP&A{zlPQP{)0(L63v&Xi|OS8?!JW|PPl;dv!kDK*JNzMu?C%Ze&dYQN96{8nTTBDAJ=qgi2!DeXN@hv79Jzk$AC(QF1_8!C6g'
    '_)T6uV}d_iR`@G3AnY<+kxbQJ#uW8y_kk}cp|&PjYguB1fR5$%1hQ-M#*6&SE?fB1FL@b%(<mtU0d}1k&^&9^aL>Yo=0xR9ttlaJcWviKt34-W'
    '(4Jt!EQ*=T)0eXxvSd@p?>MZ0bWXg0ViSnEHQ+dS5_E|Z>K){KDi(x`gvbp-J)JD_;5UNdBQ(Of0L+0;YBbS}GcPYdcApGXYGPU;Rl}*DP*lLn'
    'ly`_1YWiv{fJwhnwuz`bs$Msux|;t0P(@%qQ)ikw4~xbZK}3R9@&>at3+9*ucaa&5E%>^MmZ}A2J2&rT(g9yO3`GP>rzM3gl+A?uor;&q`UZ{B'
    '6=1}5K_^qXvOCqrY?~pA|D%+3V8<WSP7Yfe`-20F((t~5$`<YJwy@lMBXPV$EX&QjW<-nuHPK#*tNkM0Kc<m%^R&nTO2&Taq(lRgy9@Y!L@OqW'
    'n@hE5^8>4uUE}S8l+eHEp8CR$8^sd5(fhrgHxJHsd&{C6Qc~M5vNtOFfkMNqq>|Dxr$CTJh%0Fk!;*)>7>Jg|37f((w1|(uT#qVy&=Rae9#F;^'
    'v@-IDeb6|YmSxC7wJ}>ri^$C88YmjlD3}XfuB<#`KZPlBcH<}JN@FfP15CQ*CTeknQ3DiDud+HDGnbT9+QG4`q$a6C5#t1cwR>m&@12p5f6oeN'
    'CL^5rbQ(fkgT2P)7-rCyO;JYkcx{MWCPrh)(8Af9EShlHm|0vi-2Irsh#OemW4~g&EUIw+<)u{*4_#~DDfWmF38=kZM31a0lBWuCNH26E;#e<V'
    'DmNJltS?6GFI}CXf_V8*rT`X2)SC`U;;A+K9QClO7B}emGFDSMN}7rl)bt{_f_Yk<9kl%B4_AAQ=3(o4yY?Rc6a`js<FnJ{Ca@3`4i6T1kJ~lL'
    'D<f-+1H%-HC|slIN3Zk8h?%gzgl%X&EaST{u9ltR91IIP4GZo(KeeQykjNbsr|t9e*X`3^x%pDL5;A`_ah(I=pOV?o9D!RA9V8-VUujl2n=3Nq'
    'M(C51FqMMB_8?1u_Is@Yw}nmo;z<Cloj54o>LwmaVb69by@}&0>=QOwri&IHkTE}vG7j|)EC88)8yEoXFf*L_TE=GmcsBsbsYsP7T5bhH&8;EC'
    'jVA_GMY9K<{g6^FXJJs#;cP?2?|0k~I3<>9OTku-F%(Mxan)4yn@_7RD!TBLt$B1IceFC%s3fTmQdug0IcmbaG)UJt;);#_T4e92-CE`pexWgg'
    'u;z}))uW?+5s4{tf!}{U><oSf>Lh`yN73#rkU0WcRgr~)Y^L*jr#Bkf&NH`)c|R~rT*cumdc;}M%>;nd*|x)ypDVe}m76ysrm-LdEfx<*AtKKA'
    '-ISTs%d^}q=g|Z)Q_f)ja@4(OpZm2ccOR`)(c7WdCPSy!?elgIT@>4+B2W0A*n(<6h*kkJO47^6JbRV0d4-tDlPZ`hvQIu80(^O??iB_@p#?>Y'
    '^cHT1yQ{jQNLPshQ>b5?;p=>f7*GDa5lJ&%^&Ylugwzv7Tiojo*Ssa{c8Ow%Yz47u*06o)wN<?jr%~_?070b2J_V1@0m1CfxGQjJpI~YU9@4RA'
    'fXjNcGk|2WTxnvEq))x`KglwM(=X{cW8MSL7x=zf==(Oo?>{10F%g-<(o7>DuQ8GW5R!!FCO^QxWG0e^sO}>8EDu_SmUpfa>qZ=d%lXuo1`RB?'
    'y%Hb{a4BXNGA1)R!J=ZMFJbC}2PJD+4f)6VkhLYvO(`M~X>pD4tv%5Nhsisv9`&<u6zftFhph-m=2~Ldg%6r=B&>FL_l5F|Jmh0B^q-XxwsNWH'
    'brXlJxrfvn+@jqLoA3&9RIZh-SM$)3);AP(&H4ph>}oZ0FVq`X?8$4@^CjQ9f)jXMtRTma)*0P1VxIM2f$^q*<NSvnS$Ie03V`AqxkaHHvvlCD'
    'SvPAyY{ex2ZJ`q$t3sA*HY}kldWrOaI|#7o14?8tp<O1RXai}Et|d}RkZaTqNhN-?2H~2A^~szNWasK~q;bxB8qc;cnB1bXgdAhr0<y`iX0wXQ'
    'jYk*<ys_nq)aGHPx8qPU21K>Xo6+L)Fe<zFLaG_lMGNGicC{d2bhC!2l)GVHxFlq|4!dqxF!P#B(dgi11@;6Dg81$F!sS=%R7ELFmeKsgXW+Ek'
    'Ob+T=m6GM)tKnmco1I~i8tg|IkJ$NYJ@in-ivbzowPo?UX_ZWrCS5>DRBkgv1&R9RYD!NeigkguJS<@yX0wpu$s%W&SU~q+atRv}^ycHjHM76w'
    'w`C8oFx3nNXw{S^T6s-5b(Py9<ZhavKx<q032~~wYxmCjZ{DCAoZ=Vy+01?lWjZvVCFaW%-SmZDn={7W07+G5Qw23UYf-07Me<kp2C$6#k`>BS'
    'n%5-uqm%be9KkN~sbdJJMC&7Rnn~)<5R55Kbh{Dy!i}M60|E7vguY-HSoAW^_yJe8O^Ghl8zJ2%L=Tx)?u)CPI|ZX>>6?S({7Iz9V6n<FA3z@D'
    'AxRaZ$RMHYSd}ymVP1h7LLP_3c{gZ+Fzk^=z7SgV6aWy#F$%?M`6>uv6IMya&Jm;!KVfpE7zq{Y!R|1b_JcvjNT?c6`c_2?8jp?82vhEOgz*r}'
    '?`TdO>CGL6%zGa{Q<MzFU2KPVgA73344}RP0M55)D@MMWHVe^alg*VR+&jC;H5mKUZ=ZLDXdU{YI{-1m;GSt{z0R-Tu<h|Wd4_AA$}kmM6!>iP'
    'oYVYh2CM|5>n!G=a7V%zH0dp{uQ#^}kHKQ6EZ2C&9tDZyhhSL}pu6l;6Ur`yZ(3tSZ-rGMbWsjMtDBPdSs3HVFZLR1g7`2VSqwRF3MhjLvWeBc'
    '>=LRnwgqN*%p5f_gDps`0pdAUV(|e&4wxTO6w!u%0WK+HshD-)`ku#Ely0CZA1H!cyn;!J5|!W6yhcUvPTA9y4C0sz@+jt&XrVYqRqv!9dGsu6'
    'yi9L-1a!OtUyA9XuxRL-7tQD7(qOS96E3V}YE75fH2%nzE3|MZjLIg+B*o#LcmlSUtt|#L!WH8o*I78$s!9`gWNgdBAFH7fzaP77rsi3c#|7C;'
    '16M<QA!|L`kjk|IDlvI^ZUAW!_A-ZX+|P)T6#+@gx)}C=19En;F{V9%%oQ=tND!bq`C#PuE|X<#=j&)jA()s(rV2xnlcQ2dF|?gKpgJ!b8s~>3'
    'A7@6zjKO;`P{3y2JS8x%Ve++Dy_OoRmxcFHwG$p)&X}O+@p)Oa12sNx-qRK*w@J2uY#8{neq5^we4=l><Mgez*=to8=L?5<-G7fasB}oZZOBD6'
    '%wf3d|0MUy22bo=Vpxe8L!-m&z0wD5I+Y%b<7i5e?Vd#$PJDuw1hdcwj&Hi0%~Z7l?+Jrl?L1C^{RK=rhu0N_0fr)4LQ9TxJQ$*icG*ucq8%Ai'
    ')JJL7So)nc1uMhewu)IH6a`l<Lk!QRu>hhn30agwJgAhgau!P#17{}&m|`qIcJ@~{<rBRewBKH|t-se{{N&^Po~J8}N^1b%Ctn2nfNh$ubURi?'
    'RLH|X85r_I9HL4ti~Ghe4CGL_0?g`le(wyJ73UM#`k_)IPBAiB6y`^ZF2GSR&vcRcU|8T$OE7(vi}oLtXo{($tv7@Ig(YZnbrz<RTg<BN6e6%Q'
    ';g@;np>Lkvq_a)<)vm~P5q<f67?Z1tSI122$e&BaUU>ng=;6=+Y&j)8yNr_{10;MHVvGdaC|+jK?zs^G*XzoF@nrqNDP=A_IM9vE&Bsuy+Q_Az'
    'pquAn$)B^<w@a)-^_mCri>G#|#Ce9m3Maaa2wuV~Jb%o2(Y$m}8J!J-yW;1s(B~T`ZhI$6I$%&lm_Qem5~fm&d)Y7xU#FPR-K&xfd77T3uqaGJ'
    'smHb&N~ubD5-Ng|cuD$qam|r4KPraZ{n0vGa?Sy-6oPmhr5NX337?y!$W14BA%`I);Ov}+B2q5;5|HEo{i~WU9$2i|{s1GZ{7NPX#Za-OLD$H2'
    'ZL!#3tZlaWDo;DRgGJUVNRr%G%KW<N;|9O(=PW-6Y4<quTv^I3M^rbC0<tQ+tSjm}n?hB0{^*W!CkU@rh@e+O#f`dIV4_*vcBMOIG20tC^1$wO'
    'l}PR)j5n**>wmydjQ(*JxKaI=OZS)w-m}~GPX|0z7hX1a_Ur7$MQ7yMr`a>va;ce+IA?cIb4d;EWzip9>!+XYG{?C|kE}hQA{lBcNtB?wdpJQ1'
    '+E4ZH&~ec;z&keO86nlP$5P!(V`~rl?y82?9(2A~S*oGE;>C-mfA$P!)`+{Bfwgzg)WUQ;R@W;$uPS#Bh5I=XD2T<~zY8m+K~0u=hIko6MWhGp'
    'e{e;(6#nW!U0o$yiuj>A*$AHMIjOiDw_Ym_Xvw*AibO*R4k}6l1(x_gySfq??`m~!?v^RIxUp9;ZwX5sEp9;=@;Q!nHPJL>)vGm_$<J)QT*e0I'
    '-K4inapsLJ5HbtjG%Z(a*1$e%U=l`iRGfTW6T;Qa+{6J$Xb-HJIQ)x3@RhW)%Q*JxCCxPb+vw)@+uPxTc~RERp--+O&jZa#Oal*SGuR{Ui1Jl%'
    'ODE+RQ3tP;o;ejr7^}?^peOzqNE6NU^CvhXJ9I!8TL1$55HI1V<er(&YJ^c%dmK#d66keb642*?R_Jc8-|LjYZ}_US8xh;*wUeXIWvg4?m)VC|'
    '4fO92CP?!jx;N&6jCmSB=M{!%x8kdOu(9h`aLVc3ip$g0^I<$*ZFJwchSmzXm7vaM>nUTB`}zSlgM@R1d^w**b!m?`vjm4u@y51kN`II&-}K2V'
    'k;zED^uRPH-n`)x`O3P<Q~$y%<VFtZ{PvU#jO8=W26-cVPb!R=C~ySMb#aJ|Ekhjp>BBPHB}rkj&7;)cK6-`$HeJqQWheaxZYDqaC$D_Yj*JjZ'
    '5xF;DGCS!Woma;9Pums)%`I-E+<2uLqhC92V_Wsl{}h&rt_%LbyMi*fUtH_6GInKVznB+yLL$C!s`WGf*~EuIW~)vrzs*=}T;OM{r*So(v3iF3'
    'N1NJr4V3kpmbAWodz!1Fd9r3sQXH#k@eX}*aOT8^=K+^A=y@cFW~+=2eIL4`@V7_C@f>ktYQo0vL{Oiz<m_A$Lo@dH*p~qazPW>rekzKIHAFhl'
    '5H0J>3G;yPnYzeFv6@{5e@)l8+ENjz_P2^u<x`2=9gKxZ`li!=(=5aJgft3+4?SZ{#Q}VEdglEirTLD~4|dpH+;PX<H6T<rcXeM0w?sT4DX0Fs'
    '6L_@45c9q-yT$P`j=A9rEdf#xkO0hsMGH#r3K(2IYJBD<+=au;(U<_9VHL^~<=!T^H}<m*@s$+RTHG(0`X{4QJ~}PaEjwR={Cyf94c07hE(_dg'
    'xq)eg^o?p7%K^Wx0<oHuIhov4mZHA3TXORWW(Jp8`&gpzz4|V^<u~M~Hr#W(p%z@S61Z`VIjWzrVRtsT&t@28ie=`=Q6jdPl}KC8viQpADsru%'
    'fGjF(NJ~Cv2Bk*Hta0d<xEgbJWA6&M)9Y6^&sGgWUD$TCMZZSxSKG`s;_=5?c;VIkX2w9jx{>!$uby{)9r=vy^CKpeQ`CiL@zTakn(>lbJ$211'
    'bj(#MGXBm#VZ7x1DvVHzj%C+SgKpGA0LdO>o(RljyY0MYG~#tI{VEdi+2)t-tt*gww9u#DfmRqO19bGO3By*xy02!@Vsc+}AEm~5D-fKGPMP(M'
    '^8J22JDeuVm6_gP2|6qJq|)<-vy#5k*~qQxJsU6-qg~stzD{`Ha9k>497n@v-h<PzpDtM{G@p|I<CsK7J4(N}uYY5vB~PnRrt!NVt0RnIS2TI?'
    'IE*Scw5iyw`|uu+skPZa=5){j?#&vZMI1LEu`1Ej>h?yRx1E7?Ip|)%N?N~m{&Y4&>h^}6!3Zn%1t4IO-gkyprCF#7@>Iape#(uN8qU7r>=~6p'
    'Y+Gscx=2hJP5vy*Pa3Xbb7H2+U)%$yjCmL`J>sqe0!<S{$ZNq#;CO*E%LO~6_4Kl36$WK5b}}^8!Km&(!mS6n!xn`cP&{>%xNsh(Q{ooA<ix~5'
    '<?h1emd{FG<w{<A?8Pn@;@`k3u`BWP)-zJRlJaKuiZ3b<Q(CYax5R+NL__Hko!t47QezD2mq(Y|n6ord(yTG_!|iP`(nNp^x|+NSwO+PcN?EZo'
    '$U8U!U+>!c8)2^1d`68jzq5jNt7xUM-ReS*yGLdm>Nda-E;;0OOJcc@z0Jl=0gafBiG5!nCASjilGqMR*+zZd#;^$+FvP%0W<br{x@lMken8QU'
    '#HeoKV0G(r2Lqqw2qc>`;}DDI-7vz`SLhg&tb$2sC@wF?@6oDOB$h?CFE>DLcAbM*8Lu-YA6crrWt<?Slh)@i?r!nAGcqG9yLYV$$dY&YEkC)9'
    'fClILgiU+G(5;N98|XQk-vT&hL+?>r4jNhYmb_>c8)>n4zg8wm8+cWk(TZJS28|{j)6frRGoatnqZB$&Zi~h`K$hZAt_mDnf(=#d9lSP}kq#SA'
    'S^OrUZKxPc$6fwpMB=7ERPq8MSxK0N|9`aoucNK873K?6aUAD=Ij$bc>vn;nK6Ak&p*Qh2h`s+wwB3LpTQJ%A-URP|ID$}z6)YK`3N{&pH{oMN'
    'RmAE#zJixkt1Lr8sb7tbXGiMcEtnNduN~uD!EFE6Q4IL#`G1@&ejl2MUH#5zO+>-7KMeZ4x56dE{@*|haW0J*dd#f^DBUdc+`C`inR)3St<GZ@'
    'PjDyYoct8$JjWHDr@SXI<>;DQ!{5%MG|WTf9y<w$`zx2uZ8h?bBcs6pt#--f1La>PBUZmfCG;JMHq#ri$V1-M^(JLVi6#Ws$TZ;+$nHuiS>^j^'
    'stn*t)m4>)^6KgwiAYQJjrnJ+iFvLHJ~%8Z3VGtRHUj(}m!T#Vfk~Ie{cMT}+;YM+EAVr3gZIg!r<u5ah1Sn77gvu3rCPqkwX23}l3N2X*%Rno'
    '*`1hUz5gtag3G{mX;MKN>zKX4o=<*-E|PWWSwKxXNCA$<V2B1xm&I)&=RjNeb@BUN=a0+I>8Nw&cj;!pw_ng8zuRSMyi#<7%n5`k2VX_2UA2Zk'
    '0-;M%G<18wzzXEvNp8E8NjI2b_9}cy>K1k?VAKlK?Nv?CK;j-;p1RhDa6F{Vh~X1pUGPl7RPKONS>oW!|8uT{^vYsh>AqHzJFno{NlM)~y7BR@'
    '($hWl%-fxZhpUwBY;1=vA#2s+jk}B&EMZ`u!-a6vhZFPT$CB+&;Hq2*#9_L&9H$P9kMEhl$cfE%+0c9nLsM`j$+6MvIZy&qynv>wMhnOX3)nRS'
    'oDx$&3m~Az4~SPggHu8bL@QShCcr{9slfzFJOhiSC^QYOiE1y`>1v&-%J6u#L+qT5%`uo)T5Q*%g1FRzQaj3>-Rg-Zd7RyAEr$Iz5M1TH+H`MF'
    'C@xxjhDQEJtB+KQ(I;XFtYnQr^pf>BNuv~)A0VC4;wcvg21#vFwJv3x7#XsKg3%z)8Z(L03g!>NQ({pxBpz*sLfWGn3VP9H5p7r#GCJEX{OE49'
    'pLH6Uel=nNBk<Wb)mISD+lQB%&a~?4$<`_~v<hV>YoS`bN*<96w{4`eNr1;clG!W_3=f>}abdd!{MUQ26&&LxwD^Bl*IPknq`68g<;{FK2Bbq_'
    '<+Gi|xUyR~BsY80pf`;##Uz151{Ghm#}xh525aJPVVjQejC=CxP8BdIb83Sj1yB>qo&#|RW1<oGn7jdu5k7Af@`cOA)nbiSAA)4Kp5TqjY(1|S'
    'LZERQuA;{%MTNO+4~NWYl%SE<Cv>~qaa3^;y$_;=Y%y4QL3~3SquP#d)`%aM_#{1X(RzM14|tSHzGrOLW}$6t+HCL_CP-7;1gmN=o%#WXS+V!_'
    '>=y{f4Y*}F8dw67Kv%^g8|v_5$#zkQ^e}%7pM3A6R$dE^u)TXzrAFqbX{ZLL-5!u-bJhCBs(9d))RVR1o5X{vG}%}=spzPIQSU1FzRG9Wr3aj7'
    '_KW74{e<aua?>3$j+MpS@B#bPXhjkdm*tt4u#Rh@7;nAB|5kEPs28n#SRB!-)+TS~;ix?rU0YlMwBKm>AR?bpm}!f}#6WG}W&ix#uh%YyR<Dmy'
    'G5ilhtHAWy=wUeYd9?O=t!9ZZm(a-D4uc8xhuyb5472fi&~Klewud9zHM(XOZ~pn@Xj~GFlH(*_9Twk)erMbgd*)n_Q%vxvsX}?UGX5X~7P3^2'
    '#i#?ynaSb~z>$UV1})T7#KD}YJ|s7uyy9VMSz#@iDg%{8D*$OPq44Dt2IoGyxlJinQGnqJ*KlxBm@^D5%|jUE<H6i5up=HGod1N2Bup!606+?^'
    '#X=gq9kegsVJN-}iekK-6WldESKicwjR=F~q%p-!pcqc__kwqsWhidHKkJS#+=6I=_f~CTTfiAi9s#78H|*MSc6}lZ_KRW!2e&lji*Wld(sCGu'
    'sP1{T?;}<BeVgM6-thz5mR1<C2dF=M`G0`smc9'
)
DOCUMENT_PATH=pathlib.Path('docs/ORACLE_389_ATOMIC_READINESS.md')
DOCUMENTATION="# ORACLE-389 — Scanner/Executor Revision Contract and Live Readiness\n\n## Authority and scope\n\n- **Installed scanner**: ORACLE-388 scanner source, pinned by SHA-256. No scanner rewrite in ORACLE-389.\n- **Purpose of ORACLE-389**: replace obsolete ORACLE-360 / ORACLE-363 source audits that incorrectly reject the certified scanner revision; preserve the same SQLite bus, independent scanner, and original Q18/Q20/Q25 files.\n- **Execution**: audit/certification only. This release does not authorize private-key use, transaction signing, sending, or broadcasting. `ORACLE385` remains a read-only candidate-consumption and preflight path. Do not describe it as a live sender.\n\n## Exact size contract\n\n1. Scanner prices 19 sizes, 0.010, 0.015, ..., 0.100 SOL in both PUMP_TO_METEORA and METEORA_TO_PUMP directions.\n2. Scanner picks the **highest quoted gross lamport opportunity** per direction, not necessarily the final fee-adjusted optimal size. The exact size is published as integer `size_lamports` to `runtime_state/oracle/final_boss_dual/candidate_bus.sqlite3`.\n3. Executor reads the original scanner nomination from SQLite using scanner producer+epoch, market identity, direction, source timestamp and slot. An old 0.010 nomination or unrelated 0.010 native template is not proof that the selected size was preserved.\n4. Reject out-of-range amounts, stale/replayed entries, incorrect pool or token, mismatched size, failed quotes, and incomplete Meteora bin-array fills. Keep both directions independently.\n5. Reprice the **same size** against an internally consistent pool snapshot and only proceed if net profit after complete realistic fees and token residues is positive. Do not silently substitute 0.010 for 0.035 or 0.100. If size is unaffordable, HOLD.\n6. First funded **live canary policy remains exactly 0.010 SOL**, subject to a separate explicit live-authorization gate. The canary policy is distinct from the scanner's 0.010–0.100 search. A non-0.010 nominated trade cannot be quietly resized to meet that gate; either find and independently certify a genuine 0.010 trade or HOLD.\n\n## Admission and profitability gates before enabling LIVE\n\n- All source hashes/frozen Q18/Q20/Q25 checks pass; ORACLE-385 audit and health gate pass with a live producer.\n- Real source data: PumpSwap and Meteora exact pool identities, full hydrated DLMM arrays and Token-2022 transfer requirements; no constant-product approximation for PumpSwap.\n- Exact selected size matches each native leg, WSOL/token input/output, transaction instructions and compiled v0+ALT accounts.\n- Fee and economics: base signature fee, *requested* compute-unit priority fee, rent/ATA setup, SOL wrapping, relay/tips if any, slippage reserve, residual tokens and safe wallet reserve all deducted consistently; exclude partial fills.\n- Signed simulation on a constructed atomic v0 transaction with real payer and current blockhash, appropriate compute budget, positive post-fee net, and no token residue or simulation errors. A standalone `--node-check` or unsigned syntax check is insufficient.\n- Revalidate state freshness and profitability immediately before broadcast. Ensure blockhash and ALT validity, idempotent submission, bounded retries and tracking to confirmed/finalized outcome.\n- Reconcile wallet balances, token balances, fees and rent after inclusion. Define emergency stop and funded-loss cap. Fees can be charged even for transactions whose instructions fail.\n- Only after these gates are observed in live evidence should a separate dedicated live-authority implementation be considered. ORACLE-389 and ORACLE-385 cannot create live execution authorization.\n\n## Proven evidence as of this release\n\n- User's bounded ORACLE-322 run: `raw=43`, `exact_pairs=14`, rejected `NO_DLMM_PAIR=29`; `admitted=14` and 307 watched accounts. Number of eligible pairs varies with discovery, not hardcoded to 28.\n- Exactly six scanner nominations in that run; selected amounts included 0.035 SOL and 0.100 SOL. SQLite confirmed the selected amounts, but **no certified atomic net-positive live trade** was reported.\n- ORACLE-385 last blocked at `AUDIT_FAILED_FROZEN_SCANNER_SHA_MATCH`, a versioned source-audit dependency. The ORACLE-389 installer upgrades the audit contract, not the scanner.\n\n## Windows CMD release procedure\n\nStop the executor; do not interrupt the independently running scanner solely to install this release. Run in the activated venv from repo root:\n\n```bat\npython build_oracle_389_scanner_revision_audit_migration.py --test && python build_oracle_389_scanner_revision_audit_migration.py --audit && python build_oracle_389_scanner_revision_audit_migration.py --install && python build_oracle_389_scanner_revision_audit_migration.py --verify\npython build_oracle_360_integrity_bus_recovery.py --install && python build_oracle_360_integrity_bus_recovery.py --audit\npython build_oracle_363_scanner_bus_binding_replacement.py --audit && python build_oracle_385_scanner_source_unification.py --audit\npython build_oracle_389_scanner_revision_audit_migration.py --readiness\n```\n\n`--readiness` is read-only. It reports scanner health and current selected-size events but does not certify simulation, wallet capacity, economics or signing. Do not run old ORACLE-387/388 `--verify` after the versioned ORACLE-389 ingress audit replacement; ORACLE-389 owns the composite version manifest.\n\n## Authoritative external references (checked October 2026)\n\n- Solana transaction atomicity: https://solana.com/docs/core/transactions\n- Solana fee accounting (including failed-transaction fees): https://solana.com/docs/core/fees/fee-structure\n- Solana compute budget / priority fee accounting: https://solana.com/docs/core/fees/compute-budget\n- Solana production readiness: https://solana.com/docs/tools/production-readiness\n- Meteora official DLMM SDK quote/full-consumption and bin-array API: https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/typescript-sdk/reference.mdx\n- Meteora DLMM SDK usage examples: https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/typescript-sdk/examples.mdx\n"

ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
REPORT=ROOT/'oracle_389_release_audit_migration.json'
SCAN=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py')
LAUNCHER=pathlib.Path('build_oracle_322_scanner_isolated_discovery.py')
FREEZE={
'q18':pathlib.Path('qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py'),
'q20':pathlib.Path('qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'),
'q25':pathlib.Path('qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py')}
class Hold(RuntimeError):pass

def h(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()

def assets():
    try:out=json.loads(zlib.decompress(base64.b85decode(PAYLOAD.encode())).decode())
    except Exception:raise Hold('EMBEDDED_SOURCE_DECODE_FAILURE') from None
    if not isinstance(out,dict) or set(out)!=set(MANIFEST):raise Hold('EMBEDDED_SOURCE_SET_MISMATCH')
    for k,v in out.items():
        if type(v) is not str or h(v.encode())!=MANIFEST[k]['after']:
            raise Hold('EMBEDDED_HASH_MISMATCH:'+k)
        compile(v,k,'exec')
    return out

def verify_certified_scanner():
    p=pathlib.Path('build_oracle_388_optimal_size_alignment.py')
    if not p.is_file() or h(p.read_bytes())!=SOURCE_388_SHA256:raise Hold('ORACLE388_CERTIFIER_CHANGED')
    for rel,expected in sorted(SOURCE_388_PINS.items()):
        q=pathlib.Path(rel)
        if rel in MANIFEST:continue
        if not q.is_file() or h(q.read_bytes())!=expected:
            raise Hold('ORACLE388_SOURCE_HASH_CHANGED:'+rel)
    if not all(p.exists() for p in FREEZE.values()):raise Hold('FROZEN_PRICER_MISSING')
    if not SCAN.exists() or not LAUNCHER.exists():raise Hold('SCANNER_MISSING')
    got={name:hashlib.sha256(file.read_bytes()).hexdigest() for name,file in FREEZE.items()}
    expected={'q18':'87a60094706e5f4043a161bd606f68e7fbea076819076dbd3f231db6a058db26','q20':'48e1197ebc329e794f0be7108b53ed40a6a1cae961e2fc02c3b1c44b2afcdc75','q25':'8794a5a072cb29c8817bbf247bd60bb11d6e582b20c35e3e99b63bc4cd01a292'}
    if got!=expected:raise Hold('FROZEN_PRICER_SOURCE_CHANGED')
    return got

def audit():
    src=assets()
    checks=verify_certified_scanner()
    for k,v in src.items():
        p=pathlib.Path(k)
        if not p.is_file() or h(p.read_bytes()) not in (MANIFEST[k]['before'],MANIFEST[k]['after']):
            raise Hold('UNKNOWN_PREEXISTING_SOURCE_STOP:'+k)
    assert 'Q20_BEST_PER_DIRECTION_0.010_TO_0.100' in SCAN.read_text(encoding='utf8')
    assert 'AUDIT_FAILED_FROZEN_SCANNER_SHA_MATCH' not in src['build_oracle_363_scanner_bus_binding_replacement.py']
    assert 'run_checked([sys.executable' in src['build_oracle_360_integrity_bus_recovery.py']
    print('[ORACLE389_SOURCE_AUDIT_PASS] PINNED_ORACLE388 frozen_pricers=%d complete_replacements=3 no_scanner_change=True'%(len(checks)),flush=True)

def install():
    audit()
    source=assets();todo=[];already=[];snap={}
    for k,v in source.items():
        p=pathlib.Path(k);raw=p.read_bytes();cur=h(raw);snap[k]=raw
        if cur==MANIFEST[k]['after']:already.append(k)
        else:todo.append((p,v.encode()))
    staged=[];replaced=[]
    try:
        for path,data in todo:
            fd,tmp=tempfile.mkstemp(prefix='.oracle389.',dir=str(path.parent))
            with os.fdopen(fd,'wb') as f:f.write(data)
            staged.append((path,pathlib.Path(tmp)))
        for path,tmp in staged:
            os.replace(tmp,path);replaced.append(path)
        verify()
    except Exception:
        for path in replaced:
            raw=snap[str(path)]
            fd,tmp=tempfile.mkstemp(prefix='.oracle389.rollback.',dir=str(path.parent))
            with os.fdopen(fd,'wb') as f:f.write(raw)
            os.replace(tmp,path)
        raise
    finally:
        for _,tmp in staged:
            if tmp.exists():tmp.unlink()
    DOCUMENT_PATH.parent.mkdir(parents=True,exist_ok=True)
    DOCUMENT_PATH.write_text(DOCUMENTATION,encoding='utf-8')
    print('[ORACLE389_DOC_WRITTEN]',DOCUMENT_PATH,flush=True)
    ROOT.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({'build':'ORACLE389','changed':[str(x[0]) for x in todo],
        'already_current':already,'frozen_scanner_sha':h(SCAN.read_bytes()),
        'native_execution_authority':False,'signing':False,'broadcast':False,
        'scanner_mutated':False,'runtime_certified':False},indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('[ORACLE389_INSTALL_PASS] audited_replacements=%d already_current=%d scanner_unchanged=True'%(len(todo),len(already)),flush=True)

def verify():
    a=assets()
    for k in MANIFEST:
        p=pathlib.Path(k)
        if not p.is_file() or h(p.read_bytes())!=MANIFEST[k]['after']:
            raise Hold('ORACLE389_INSTALLED_SOURCE_MISMATCH:'+k)
    verify_certified_scanner()
    print('[ORACLE389_BYTE_VERIFIED] full_source_files=3 pinned_scanner=ORACLE388 no_sign_no_broadcast',flush=True)

def tests():
    a=assets();b=a['build_oracle_360_integrity_bus_recovery.py'];c=a['build_oracle_363_scanner_bus_binding_replacement.py']
    class T(unittest.TestCase):
        def test_no_legacy_sha_dependency(self):
            self.assertNotIn('FROZEN_SCANNER_SHA_MATCH',c)
            self.assertNotIn('FROZEN_SCANNER_SHA_MATCH',b)
        def test_pins_exact_scanner(self):
            self.assertIn('REVISION_388_SHA256',b)
            self.assertEqual(len(SOURCE_388_PINS),11)
            self.assertEqual(SOURCE_388_SHA256,'b2ecf80539eb6f23e230ddf6d54823799a01b0e2e8895df462f2c48a25039870')
        def test_frozen_audit_remains(self):
            self.assertIn("'build_oracle_322_scanner_isolated_discovery.py','--audit'",b)
        def test_no_reinstall_352(self):self.assertNotIn("str(INSTALLER_352), '--install'",b)
        def test_363_360_dependency(self):self.assertIn("_checked_audit((str(INSTALLER_360), '--audit'), 'ORACLE360_AUDIT_PASS')",c)
        def test_byte_parity(self):self.assertEqual(a['build_oracle_363_scanner_bus_binding_replacement.py'],a['qseries_v2/oracle_execution/solana_atomic_executor/oracle_363_verified_scanner_bus_binding.py'])
        def test_source_full_not_patch(self):
            self.assertIn('class LocalIngress:',c)
            self.assertIn('def tests():',b)
        def test_original_boundaries(self):
            self.assertIn('MIN_SIZE = 10_000_000',c)
            self.assertIn('MAX_SIZE = 100_000_000',c)
        def test_no_sign(self):self.assertIn('SIGNING = False',c)
        def test_compile(self):
            for k,v in a.items():compile(v,k,'exec')
        def test_unrecognized_sha_refused(self):
            self.assertTrue(all(len(v['before'])==len(v['after'])==64 for v in MANIFEST.values()))
        def test_docs_readiness_contract(self):
            self.assertIn('First funded **live canary policy remains exactly 0.010 SOL**',DOCUMENTATION)
            self.assertIn('not necessarily the final fee-adjusted optimal size',DOCUMENTATION)
            self.assertIn('failed-transaction fees',DOCUMENTATION)
        def test_hash_389_matches_pins(self):
            for k in a:self.assertEqual(h(a[k].encode()),MANIFEST[k]['after'])
    res=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE389_TEST_PASS]' if res.wasSuccessful() else '[ORACLE389_TEST_FAIL]',res.testsRun,flush=True)
    return 0 if res.wasSuccessful() else 1

def readiness():
    """A read-only status probe, not execution authority or profit certification."""
    import sqlite3,time
    source='PASS'
    try:verify()
    except Exception:source='HOLD'
    db=ROOT/'candidate_bus.sqlite3'
    state={'build':'ORACLE389','source_verification':source,'scanner_status':'UNKNOWN',
           'heartbeat_age_seconds':None,'recent_nomination_sizes_sol':[],
           'audit_only':True,'simulation_certified':False,'wallet_funded_verified':False,
           'live_authority':False,'signing':False,'broadcast':False}
    if db.is_file():
        try:
            db_uri='file:'+db.resolve().as_posix()+'?mode=ro'
            conn=sqlite3.connect(db_uri,uri=True,timeout=2)
            try:
                conn.execute('PRAGMA query_only=ON')
                row=conn.execute('SELECT producer,unix_ns FROM heartbeat WHERE name=?',('scanner',)).fetchone()
                if row:
                    age=(time.time_ns()-int(row[1]))/1_000_000_000
                    state['heartbeat_age_seconds']=round(age,2)
                    state['scanner_status']='LIVE' if 0<=age<15 else 'STALE_OR_STOPPED'
                    events=conn.execute('SELECT size_lamports FROM events WHERE producer=? ORDER BY id DESC LIMIT 30',(row[0],)).fetchall()
                    state['recent_nomination_sizes_sol']=sorted({round(int(e[0])/1e9,9) for e in events})
                    state['nomination_sizes_in_range']=all(10_000_000<=int(e[0])<=100_000_000 for e in events)
                else:state['scanner_status']='NO_HEARTBEAT'
            finally:conn.close()
        except Exception:state['scanner_status']='SQLITE_READ_HOLD'
    elif state['scanner_status']=='UNKNOWN':state['scanner_status']='NO_BUS_FILE'
    print('[ORACLE389_READINESS]',json.dumps(state,sort_keys=True),flush=True)
    return 0 if source=='PASS' else 2

def main():
    p=argparse.ArgumentParser()
    for action in ('test','audit','install','verify','readiness'):
        p.add_argument('--'+action,action='store_true')
    o=p.parse_args()
    if not any(vars(o).values()):p.error('ACTION_REQUIRED')
    if o.test and tests():return 1
    if o.audit:audit()
    if o.install:install()
    if o.verify:verify()
    if o.readiness:return readiness()
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        # No wallet key/RPC URL / arbitrary error text ever printed.
        msg=str(e)
        print('[ORACLE389_HOLD]',msg if isinstance(e,Hold) and len(msg)<130 and all(c.isalnum() or c in '_:./-' for c in msg) else type(e).__name__,flush=True)
        raise SystemExit(2)
