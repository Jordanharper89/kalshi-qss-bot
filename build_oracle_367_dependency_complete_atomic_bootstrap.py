"""ORACLE-367 complete dependency-safe scanner -> pre-atomic certification installer.

Bundles the exact verified ORACLE-365 and ORACLE-366 module source files.
Restores both in the canonical execution package, then audits actual module imports.
Never modifies 322, 351, 352, 359, 360, 363 or 364. No new WS/RPC.
No wallet access, private-key printing, signing, broadcasting, or trading.
Native atomic builder remains unbound until separately certified.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import importlib
import json
import os
from pathlib import Path
import py_compile
import re
import sys
import tempfile
import unittest
import zlib

PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
DIRECTORY = Path('qseries_v2/oracle_execution/solana_atomic_executor')
PREEXISTING = ('oracle_359_lock_safe_handoff.py','oracle_363_verified_scanner_bus_binding.py','oracle_364_consolidated_event_handoff.py')
MODULES = {
    365: {'module': 'oracle_365_sqlite_columnar_event_handoff',
          'sha256': '4db5cec2043c712426f8ebb171a09af59a22ede8b440b571c1eed4b1dab6ca13',
          'z85': (
        'c-qZ8YjfMSvfuS9aN9XUs-YR#se4nk>={{N5>0K%mE@#79uI~RA&WIdssv?Q?exE&-39m*6)X3g4>vQm`M@rA7yAa7ufF<fJn8i>-IF)pop;&7i{dC)cp;N;'
        '8Hwa%zLjhf%ODNn$O})B_=&B&$d8vxyVdH)>rE(9!GcJpUKonRW}gCh`y^TaYQSDIZ;=L%f<21p5$-m-bQMP|j>4VY8pJ}fC{Ecr_Jie)WptdKy?%3k3P14o'
        'yAJ%kfuC<Jwn>6V59WFhJ87{vVd7aVwn!KAwtzPYQouS@bhAi2aRJk&lKDVkvJN7cE?o(>*d`L7feH4s3KlDtAh~OA$L8=dj%47AMEG{=9gHeiXXzGrmFy`<'
        'R{+e01GWqjnOZCno-dgPDAL6$i0;{P8;0<75hp%dCh?l4mEKykaOerL&!)dz2EdFaG4<x5Ad(XC$2Le{p7|~nuOGc|3xodHdLeKJ1TN!5z`P>#VY<x*X0uzP'
        'm`$$x7W*XT(|GY9fFv2*NAS*K^Cb5Cg(p*_3;6K?_abGHN6Vrl2#<s4F<yAcC`d5%?uC!4;0Hbk99V-nK`&0!a3U2JV}U4<Tp@u2wWeQv^;L^F=6tzLw~64K'
        '1?x?mq`(}kHBBK~t?XHHzwr_&6wD$94O-BM45%M(BUrrbJzPJhVKC2LM<8hZG()-a<O)V)x9U&n!S6DTvg=qX#2YVNm9SpJZ8l`H;|oyoAQah?B)^h>z@msZ'
        '`Rz_-m#J89mL-^Ug$obz${z&l{N*+ZQjl`mYF+>Qo;l3;Ly9C2l0Tl=apEmP!E;TwWgL2u$GtRO2MeC9pV6B2Chy%DKqK*H3B~I=ir393vT@)BxMB<#54Y>c'
        'OOze)%<MNiqurXg*W*bsUjoYnEOGDxptTCs>tz6D!{@P-+y@0N&yb_mNO>Yq7B;R9U>}Yy#=ribk!#KXB`B%jK{St_Gt5`LU-?CE*8c$5Pdo6Bo(u<5e(g>;'
        '7$rPEho{s22luMSFMAg*J~EVZLhSwV<;~ToH{lmIQx0O74Eru0k1l^RTCJ8ZmY}AIFx%Z0gMWztBZvwuwAB>{m$wati3|RU8Fo(mw;UZ%9FpPrRlx)GY69(S'
        'vpHn4$V3HJ2U^E@+XfF3hmSx94N=-*gRKERd;I`jz*INVnI&6cfhP!L%Hs#RRY1X#Q2&pUf#*2Yy!a0lo#g}2HS!4joT(q+H8CjBrx@)Doc)xbmZ6`MCd_1`'
        'jp*BUF;ttMNgy-?&D|8yB1VgHjBUC+d26)6>7|LD7;X$y?9z;}1mI2REfgk8)2s#*R&Hn0Rgn3xK!Frh;p9>&s77JcIVpriIM_sKvzsJwVj9EIbk@7P<QKoq'
        '+$p~rPOnfoHQk`UQED2uh4N*?uY1$!oslsC+{%@AcK)4XfV8y-wACZCfy}nO63>2c4^GDf?v~+Jt~75-!@R8@q#5Z-pKbk&v9I$;eSXFkB1r>?M?RDBHd&|`'
        'mS+?lFo2C0By7Ev;2_fg;^M}W(#~Xv;a?LNNK#&y0pigC*&b5zFA(^iEZqU0j&CMl#C7R^u~O`>SMO#poT=4f(|&I>awm}A@OP8(zuXZ60rI{(nGN3!-2nq}'
        '@%J~q$$%L-2Mj#V$mPG>xRc+=$)JlG&RlRjy@5MnqcI=3pE!hn{%MMLKfAwi_%j{8AK~AN$+$P@_og$WX_<kYV3G2`Hy^dsU`f*5M!-D_AP7e(t>+{AiFHb1'
        'RZi`(0Rk{82v|-}E`k8oExY%{B3OH2_T;v6hf8X7j6KXK#m9EpfsW!xXrguOkS2J_NR$0Fn?Z)9;{=PJB9-Y?k}J7biM405se9@6XY3nx4;fH7w`J(9kZFw)'
        'Fo5Pl0t?|KgMy4sBtJlM`3NcIJ!C!=1d1}Y79J*FTFZ61>0tU2*(%%$)5ysHUAW39y&PT*XRM<YP|@SCTOVb$#Ow{IW2VAr`$8^~U_%Koyt}<?-<8cuLBk6p'
        '@C|wbu=&GKM5Yv}Ne|j&T=+=ce%^xIkM3y3XT6I{R|i9`qvg$LdUK6=fjcmAH|a$?lV+C`w<2)B5&3E|bbONt8#87~pUuR$?VbF~JNc8}>5I<E_x$b~P~fOt'
        'vI~+&l=Jig%|Kc2oy!&Jn&?sQ$~7ulMwl`+1NRAPop?`$X_Q!i=N2==0P}w;4BG8IH8u*>;QxR%_y>s?F&;wbgE^8|z=wM&I2(FuV8vrJ;MWy^QRcyb!Yzcv'
        '3L^m-CeCMb3d@||cF(@O(;R|5#y-Sf5<4m<7FEGL<yBY`!ENYsrEC_}Q`z-GW#yUBA?crh|Aia^jHOgUV(Cb=71jn-qal&$I)<bU#U!E{V`-#b66Dh=mO|B8'
        'Ow~dGR$6cw_{wOo4udJNc3bWI1k)yEch`kosuyS{d3B{|%?qnE&TBM4Xh>DUsTz&2DIWqfVI4{nWA)=L7Emlkkc|Q60A&I%RguGDQ2k^cq=}bkmb62_8VUc-'
        'Jz&kz;Z;Xk^dCI4`>LnYBb4NC4Lz0~7<WvWZy7-yKqvLe4RQ>a0QL&9U>b)i21w8)C_pqXP#rX|idJ+>iCKmk#+7l^=0!Uqbu5`wZFG}uk;p8DCe~IVBeNce'
        'MrYl!D_{b&!6}6^7zHk~;x2Fw92Tga0|pdATIe|Ykp}$elytp1O(rPY^L-P>Rwodl6#L@~L6p1!lzfp7DhN7N7TniL|L-Bo0ZSPUKn($!oc>;8#x6BD;%&Ow'
        'rZzCeD97C?MVs$9$>p!VRh<BZ2h<dSPYX>qCUR4(H^@JsFp+rCy)ZkL3KKaTBt5lispOOvt8Mg<W5(gPgs-cxzN&-X<&bMHc|e*B%dmfsgUB@gX%Ib}I7hsN'
        'q(O~wXk+;N^ue9D40s-nn28#vFhc>-E>bF3*m^JqoK}4vP?uWV1;BF5rR=3_aMiUx965Ec?0@Ku-b3<vH5{mlv{bB+@x@QstV;ndx>WIH|Hvbv<j7V`fT(ID'
        'Jiv$o1MrXeXRxVw2umYq*P!agq_Eic;2SWPXz$q-LIA0#O#22vT6haX&`FtUMk^ytp;D0uXT7~U()sAn2Ou!+zvf4hBm4-ZDKLuoBB20OI~POAy`V!-nQKj6'
        '3Iz<MVZf_iKcoqiieAIKM>-P_3||M5pz3b80K|Z`6*W#W8LAmi?^?~16^$T_n!Ir)-I{c=mYrEh4K>-JaA!wx0wqB3r%<lT)FfCMyk-HylQCo^(RMu-*rU{='
        'Y=~oPSvLk;00N+@0z=a0<foG#bP@`R*ikc;)rqXISko#>t+zHXAtJx9Kb?x{*H*<#<V~VTZr9*?lsC7SO2EMNiz2_W81=3+qx<;+#4dP%Ft!R;%FmO(b*RT^'
        'Z$z@>8Xt#LLK8^oT_m1Uo|h;4aV1L%LmlWsm?&E8(2SdLvlBIWo4sbIywmC64}lVmn>Y-)LV~@?wJZb&QO?xpE%ruxm}a1i<GmNRCuis1b?+)wX^F*lwvJfU'
        'V(n1k{zqi8SX;us^n%bdu*uiInM}tMD7oKH-05^U9+f<`TIzD$Rdzrm=9&l6#TULq50p0~o2Ty$c)vFqkB0r;C3PI@p<<r^N}SQpl{x(BAcvZ}-r!?z)Q5QV'
        'X*l~ZzM1il!|4!9yvg{}^u_rK%wIEiy@8Axmj~o6z^zBIF212MPCegCJ@&^|Bs&|bcI+~!VtwgBjvx5Aw*dK%T_sgKZ-QLy_1sGDSD32!d#-?9qIO8t!azcE'
        'rt9M~>#{li#$K1|AY;#%Q<u^tL$q>YAjdJ=$E1I%`Miz7AbK#tOM`OUSKF)=J~ca_<L^AcSFiZ;V3H=gVy@iJWQ9XRWtSIp6|*mua)eDhFT^Hgrrz1GDQ~eV'
        'S&YR#VhGpQGcYo`Y&YvxuDX@f=VtWLolw)OS+PnUjX7m{Teaj!b6(7iwOJ5vrE*I$%X}0<dQ{3J)jpSYCs4`(>(v|zJK!{^dmu2Xw@pEJzZIBm6+qfI7{7am'
        '-CNWz+uyD?()?>ra}3q|hlH!ErnxPi+*!;>;|CFOV0alk7enZ&ad+E2J-f5^ajNY<$QufX;t^t%7@I?nb}3{rsQS1GGmHZtT!Nr>FvrIp&>Y=E)s0@d5qR!J'
        '4_xim<PBw`OC~@x(Pn1xAm7x~kN&PTu@9SMv2?iTPzC=Eyf>|1CI3KGE2&U({*ie^aJ4lpR7s*n)@cB1psb#lKxq9u);-VI<ml!w{-M?ERS$a9FZHJXktf|>'
        'vg17HLGRhn+Do?B`vkw}OXu`$$A&sLO+(O4=j^-#H*4>iD|L2G=>er0aCcs)uFjSm^vKi_qU{mkJ6cC+D=dr`4|;!1?Qc42+f?Uu4sCN5?M0NT3FMq(4?+`&'
        'mq25O#7-|XG4!I-+3R~2-WfNSKK3r5yqw&OX2UC&UyN@?gK5#4#R&`23ru>e=RnqpUQr*i&?QW_E|x6a&$K{q)NuWp&$n47itAP%eHkyjaHu?nsaHn*sjN+L'
        'S!#93y$Yn(RMQnEE)B+(;s8OxUA}e&UwF3&5&qb%-1F}V1()7Z6g#-K`@8^06+8-H@}YtrTX<@gjFJ}>A45BUHD?8MPNm942`0<-i<Kx3D7GoCC%yMqJ(aI<'
        '?BhC>^!FeD;N5Xd8scs0fDzSTR`U`K)XnwMTs=zt&QjAxB?A~$8#hw=<KCq^?Ykx<)Fu?<R;OL=4T0#XivprD+j}*=$^g>TgM4W<xAb&%HeYJa9*+Hb>rWZr'
        '5s`lrLxJ5@E)uUH=4}$tGYF1(#8*X-etIb0D@OF-Ea$8Cj=Ot};|4smzlzImbd^6dz+w`QCz}O-l0_J9ioz;I^?cA{k(H(E7<>;lG@)pGmHD~~1Z90I;f3j{'
        '8OT06uK+x)AQbHn{IQt(s5$^E$2yLmoH9Ah@tcsU0p{lwyWI%?#rz%<@0(+PrQ;>!HcVAR^o52*-i~OJnZ|RlRdT?J6xiNKVqb<rY|Jd&y{6+jl`_SpKXm>N'
        'H*^-2A`~N_RHyI2NFMP_A22Yupp%2-Z|O_|Qj1v#1i9Yzkljo!@jWOc<PFkps%i9L0VtU-$Nis+eKsJV*k{u{b!=RQyGklW{`a7m(1R<7x(H(_YOcA?cb5)R'
        'REbns8h{J0+=HWcnI*`**T*GUpdf49&C(^4%4y8K_x5&!T3_>QhUx(rT~<C@RrNJSSv`zywOMUoqZ5NQL|AZJRM_d7u7-v73wa1pmV-6}MWu@7w39WaYC!n`'
        'Ij#;Xbs?0wyf+(P4g0!y8;;(qlU_AYb(%6ecP4}NHl#hk{bHs@rvM=TchE!OgI|xALHZJiJ_O4j#Ex%eF{)l9?bS#Hp1+F)dm&X<3v6ZU+HM_=aPF_eSuL<>'
        'C<`})kY07vtT{$BmdlVS14>Oq9ZKi*XEpz)n(iH)>7yy+g<3>yXmTxdoG|Z(s(oaK{e`<5-M5x5qPs@V_~zR;mazeL_$H1+cyys2twkyz)61Ur>1pd=t!-T2'
        'TwU|om|wXw7kD(RdZB$tEx~NU7}oIgJ9uM&SE6%)5kLStmXRgY_em@f3;0O2*+<!5b_~^?37iKOV?Z>;$qrB9NPQYOt~8V8*<r%`W&5=O>71>aLZyu~ok{9m'
        '5#GXhIwR%JD+l-}QNsK-kf}-1Znv7V$Nt3a&0I!@OR`-(+R4lJ1}oBehBxqfIGVZd-HCy^@JvT!a3$+9wv;F<Qmjj`t@OuWGxyh7Eoa4+0Abe*wbjPrAy$T?'
        'sXLh=ZR3m+sK##GDNy(7z*eV5{0h)oYEOtDZMAC#b#iU8MZ8`IWe@yC$vf__9dj(Hk~<eug%Eq#j4UiW!ffMhAKXd1zEPrVkyA#5J8M#e%XSxk+kggqo{L8@'
        '%wp^9+q1R>Kh0=V--ge@`h*uX;u}hgt|f%zIzEqY8OC0E9JW)t^8&IzMG_x}>m^K49Oc{p5S)_Zuo|7W#v#Pzz<OvYss)af>1H#+(spEi*hVAXOYZV^HFx$K'
        ')wiIOch>(}Z>_wF-_JMqXw@j8uDdm;J^J<wfppu{B8AUy4>0?b#E>0jEbCPg{vm!BaguB|sYBim_jrHMPj1id9OKhuJbG^&OKn9|%0p;m?Yh)}FYERY3&p7y'
        '%#a`#)ypOhF>wq%v~+KeCxS8!RM_bLKbf|aa;VtSAc=#TkrT6x9w4IPYT{=*{|P;&@jD;`5AV$v@cY^LvZaY)E_YG75-B8ODk(ff&9g&Eu;TiMXL}QG%z8lk'
        '91Ej39Y%EsOP}|yZ`D7S7&u5e_!LMYBbEJPS@fcH?7Of7^B1gIh}bcpSWeP8gmR<(GHIAEqncyR%;!5kPXhn`7;V=w`ek~-r{l}ssK=oa_y|b~9<_$-bQ?j@'
        'M>@bE9G8#Y?a`3!eo`ntG&Sb3zN2N(*b!|v!({!dzq0lbX0EzD1R3Zuc&6{M@;=h(*&E|;>vSI*cI-4pwI^1~*bb~*N{a`;pB+iH2#&ff6<qn}dk0-^B%bh$'
        'fw)(dRuE;a75V>Hj>pKbY{6FGJKtLsV{}f=I-T|rHdC4FxqZYEC<xUpC~v}IKgKELbI&Q}bdxRhuO3A*$FR3^PTMwaqvQi&r96Pdv6oPIio}Lo%BSq`T@tUe'
        'ywId4dueQ~*O478AY$w%PfoYMnUu>d9)Z)9-)X7a^R76pOQ(+U1VK0JFB`ISdb0jKCp-CxsSm~QB$VE!v};N3JGJKfIW2b2mHug>UMz+($i3DeqM@c+j_ZpQ'
        'aBqUrF`gWC-q_wZ7d#&T*7DK^3fT$EpZ>|l6Z`<>;x~q+mi{KeYPU;=6&sq3#F#pZfWL1~PBAp=gH}=%U!|>nYKhUelUz_k&$+#8mAUjq=<V>dX@r_x-;%BD'
        'hcxsS?arHhA{Wk4i-`YJpUdB~;iABFs_lk`+5X!Fqo%2;WGv>)>c$@yNA(%0zuK)VM0RvbwLa^OPql7N{@JTNqboD@l6#Rl)m1Bl*mQoZe0EUno9;Cv%HNCr'
        'pmtOD#*{w%EcqK>IOPps`}D0<?C)mVy4vE+wpH5NrJavrV^_7+G=aKHr6{Sj$$>3ey5foYsK}wr75${tt+vm7-&k>vm9@Z*HS&cAA3J!X(9?O5gy&~e;O%Mo'
        'ZKa)hr;hhFp7f+csi#fHn|l;cKtuF~bN+3t{z}a~bNRd8@Um;XLL*W$tC=dZx2xQ#g`-bWv3u7%7k<3wa@s=Y)0@f1;Ya+E@59Y(F#c5Tay0D5DdKWsseLr*'
        '&4%NV{!|aYxhu{tO~#)%%=X?LeEti&dW&*@=9xR4W#4Y<=teC{2(O14oLMV#?V$##MesIG_T{|YOYXO8a2D5imy|x<h&QQjg{jYl!GqvjSeKwa!(T81`2B?c'
        'Z$o;5A6IWHUm1BD{LX=UdIHlpIWb-VR?DNVrejF3Gr?1!Sc|&>LYtYPa&~I4SUOk0vlj>9(lk6-XJ8=490-qS9E4hX&nKYm&5);`gG3k540f(zl6&a@AW0oT'
        'rCB*gfuFgV_}JF+w&(^$uC7Sx>JkL6E|l!Kl6|`>d!f~w!Z5!Y58To>b)|W_`RCx3xA|F}tOs66o3c?vRJVNIBYRUJt@{~k`h?%m&bT}Ji2Z-uG?}`i8TDeZ'
        'KWE0$7SUsnfU6_JKTt`vv)1cqJmXV$X4H3~4P|&UgaU&du<ZV33O8tuxIHr%PO*19V7Xo9kM<2T;}zB;6Ay+4dZrauucA7ALf6Hy6LqhHN8M-vcNP;J$KV|8'
        'mvf^lcM?4t9(_lHZnypo-_1>`'
          )},
    366: {'module': 'oracle_366_atomic_certification_pipeline',
          'sha256': '28ec1de6219f810b4798ed15be908373943bbe56e2e6d2df4f35f759b5656f2a',
          'z85': (
        'c-pl+Yj@hnlHdI+wAno?kq8BxI5**5<{XUWggZ8P0Ov8jtd0yK*0n&4B>b4H|NB-|Kh%<1*hyyh?A#!!ySlo%y58M>_Uzec-0PpX%~x;Ubc}htPU9$C_*t+p'
        'Hc8O*vv?KGjd_q{;WC{2Ss1UORh%rsHGE5)y}f?C+C)JX7)h{+{CThn)|nBm)69>eATgG4VtfkMi}*G*`lm<6OXDV3-@rec`|K)SJA0G4zg|PbSNr=fUmdjJ'
        'Klt}e3;ufr|GkF)4gmDZ57)+aJ-_nTUxS6Scb*2RAyGdt07$$B1S4be+erx61UC$i%)bu)ZlvM*YlJBJi)Orz?u{tMw)h;tBzkKj-r(He9n34d31If|O$Z;2'
        ')i%wH;BFJA_%hh|N#JeQY4~*=EG!syLF8&Qe_4d{%-I{3x~Et1Hd+{4=zS9;Kt!M{8~hZA7AOA8v+Zg#x%D^3<u;6<OKKbII5U8NNoIVS0LU1?g*Pxt^E$XU'
        '{P{dcp%J10(}EwtdNED>b?VP?4z>X#hnYpqRlLUbTOf22X7{*Qg@uG6z6NP$&oJ6X%9r5^I%ZckPGGTxb$=Ob;`x;U^HiwE$O`@Tjb##~S8G7Xcwt0<Vw$lg'
        '!5v`JOv66|n9T~g1xK{nty9Now_2yrc(sX>ENuXoS4Qfug65^azBYbqzkM0p1@kSim+{9ohPCv+CIRu4jgybJu&{_rh{Hnf*M?XRv3NHvgLCf2pI-+Vp&zfC'
        'z&^l6X}H=(93SZS5trq@d+bMPfXE!+Hduzq3gC^;`o=N{sQ+`ATe!ll@!VJgOrX#*%>2tR0@@n$t6+Y;*Mk95WVRe7WwbCghNCI14bWx5A>eXtf@Bp!M`)DA'
        'MwS3uI(yHaJ=<F*@yhVL<u=;_-+4wzL<4+)MF?oRw<q2uUx7K(Ks;aiY4GMXgD{U_GZJ^C0z@C_7$o95{JzVg@KStUZ=;C66#%dN^a@&tNA{2M;@@e!7Qf?^'
        '0p9r8l>+q)9z~PQy*CHh5k?Z@ME*+u0HOx3<l}uRerCaHvsC(ISBw?D$`|2Ee%!9Z3|Ue>ClMgy1W6JnrFTj2#}-@eo&EaW=o;o9DX>M5dN=zHY|?oYc#J85'
        'gbv6^f9-pW#XP~R=H9e7e(z49H%`-1K)fu2c&P^=+JP_@p9-Sa+k~4S0={=P_hw^n?4FIr`FIH|C`{giZJh-i)XODoy~w+a)6`pR{pisVK*9l499&BnVK6)#'
        'eg5GAKwR=M!u4f*CxG^Q!`}D{KyA0YR*U}IJMDe;rk}mTFH?7dU-n<^(>vIJUcYy8f-m3Fo5|qRo1BcM-uvDeykyM)<k8@$H+8+<d)GT95C;JE$UW|zpG>{8'
        '@#y2=$Q|QUV0~X0rla7=q=uk}5Z&h9+4<qGE+U!)4rf&>G5_bH-F(+;e)wl|c-H*gZ(gsOf6l(W+P7c7e)un#-Us)y_vUrASF8EXZ!Txw-mqqSdy8Nx73IQe'
        'pd2=gG~OojK#&}EK6LlI2Jk1a%uQf5s1@Th2bIw}b5_@jFtOM}+MOobzy|pnrkNLC(<AE?E(P@e=n4oDEE^sFFI#O4`TaJ`u7EzPz~V3PH_?xjhuKiOIk%u@'
        '0`Kx3_MF9ra&UL@H;ufppbK`Q7AR+|U_Fm<D|gLpwrsvN8=%{=gpUjlChiku$T)Sl(Sd+$jx+n7OBcBa1y~DM|1b@T<dH<laYkBcrjnD3z!+n;HC&V|mN^(s'
        'rogoB5o2iYXmEV&jydL_%h#D@UNGwg`HwgE&U%x{%oOv0`KDL?{=u8B2?XcD*I}<L4W<p}D!5yOpwTl6Cb*2Y=@p+I<F)MuC=mE7fqfEyQd#G6++n}G6=;4S'
        'S7oCdcuXt<VWaJ8?I#`?SsvJAi+H(|Jne56VP>H~4MAr~4rjQqp>tFm*1BOB|0(UceKIS8KatVIyMukfyps<-<^7wM@pbDbU=s2*tc;s46?{d@iqkGkX>-BQ'
        'pnz*uzHSrN@IoCwRF`@%oVxGFgXtIVxHmXCAG-=$e?RM1S*mw_G?+4mGLFZi-`ycnweOCngX4jFgyejG-Wwm`&$fYU3nFwh9DuC#4$missm#e7jy(7Cblmek'
        'O^n~&@d#w_`{7{to;@6nN4=wdZ!$G?Ob3{QUF?DR9HNl5Zv04c0cXJMek0zai3C$2dyC!}zZk6|B(U?>!B_vsfORD_co8nV&Gr&ZY8{*~B?em0IW!VQ4T5zU'
        '$C1T!gR=xP32ego6^GF%fWLh6TJ#1JnDI-u4G;dEcmPGm2j<*aGcfRI6s*O}e#t=?&y9UW8ZqpLVENO#EV)-j)h$SNW*0hu+adsYD~BPJL9r`*72M5(O=egh'
        'u?6um2qz#g{cO~a%AavOn3bHm@sBP|0^T?9cRq&zY;V?G$SQ6=dp9i)bP!tlR+jrXtQ!y#-h&!qj~pQ|n?Hd7XhtBNB4(F&&<#tnn_x~}laIzU^oET{ENr7|'
        'hQ>G8<ls7RpbpyK%EDBJ$2GwZ1tcm&A-{rNG9E-0Bt?G}E;IQw-zF)56OZUMgRze!1b^3h)hGxt-uM?r%?e&+fmFr={|_6&XqCPf4E8M7)NHI5U{J|-Y$E^L'
        'H7o-2-(ar&4HontY))lyE8Dy+;&ll!^jf}Q<bYxR#yAg<-9btYx{X}Kuz?@#H#>TOj|}q_v*Ded8{i;uc-Y_x6xE^PukWooN_GJ5Y*&BS3?Ano?Ser6&P?4^'
        'R-s3?$bKZC_#P9D8aS`l1=^E4pSQSZ%@9)S?rp0fge|;od%5eLhdMAkaqF$qF7DTS&z&W4ylle%b2UvHFa5hA`=K}n4?2p-3HF(nO9pVVr3uRo$KWG1K!rNw'
        'a;#Ay)2h=a^rT^QCO6o-8X2mfjR6`Gr1G8fH2}4l0;((DB!w?k^((J89i0yP9ynR!LEnXce>-<4Q}1KjtgNPaKK$s8Nwb1xe?N976K~T0;GXtOl}C!>UXy}C'
        'bcq>g&tC&Q)P=H4=`wmUj$@)_$bvuk^D>G3#oSLbd?>mydF(-WdBMVLRJqX<NcYaCA4X)BxDzl1degyZXsVP2i^?ji^zyVC+NtpAki{4-Xbvpo<WYo4eUV0S'
        '#wPh^;E6bq7H@^_fbVeVjy-VmhEte90c|UHHBnMXj4w)K%t(&3WMj>cU<Vz!U;+K^dZY8{WPlHR=y7lO-j(B)xC~r07J&gqBOZmFY@VH;o_W)ecj``E;5?i('
        '|A}w$tEpYBkG+!tO!-sq419~R+b^sWvKo$1FmdV^3DC&m>tKz8Z?>xqENmR%!-@qc*>htD9%sG5*aK^5Vm`JB#fD?+EMkn@(UV4wx;*8kGf*_f+bS-ngUJNA'
        'Sgr+l{72_t@0#3@*#P-bq?AzMA7I0H+jV&7tx~h0PNK}~ygi{RfIc_cDswS$RK+llQMjMaV9|~kYE15zDMT{VL$MB+!A6I1(gJd1=aO(2%oJjLbQ#4y6LR>P'
        '@WBD#A6=Ma7n0cGd?-BzbFXaZF-3tfTM<A3tGpm^H>eV7)Ww*&X$I)Jtsg1zU$9A0>&%%dD@S$}{b(@70jAtvp*Yf%Y_limJ-Gzbr$Rz{TeA;1K}Zo*X+H#U'
        '`_V<t9UXg|pG|2FUfaR}#>Fm5Qu!M;lCqoGkA__q!%`aOG6`BM0t%rN1!Gkj*F!A`k^F(67G%mU83V*4Y6(^OALTv5h@rQ2i=-490cm>LoAy7LyLNa!s!6;}'
        '%BUf?lvNl{BdMr8=@Ei-p+K3Hbx*O&3!@z0)G*0mZ}=<wE+pP)4EyvL)OT@SR+;aVIW0k=1PMhAgzT-Dhb)Y#IJoL`Q~<L^9h%30o;wEfX*l(AP5oWe=lLFw'
        '{@1J>sn_q1&WF><j}C*P0%!%Sx=!mynGR0f$_OZ<S15BVE@GO6g)cw`<@GXG7Ak^5QX?q%_4c4uxAeo_+2jK(KgN-`v4MPKbd~*L{?UHxp-A-zhp!1n=ku-0'
        'RU$Vmi#<gu;<4^R1>xAzki}>V>=XJR;g`P>wy>RZ1W1>P2bjHP?voyno(OQ(Bl{G%{{46aCM(9zl+{+I!jish4m_3Ri5#pcvBGFabv({cUVk*4x}T?2O;{X?'
        'B&}f9)WhiDeQ^lN^5q?F(>T&K)7YD%U)`Z#aGdt1$>;>|8N0osFFIVfG8US1CmO<yD7hlVM!ADgY*wqm&W9Kv1e<&`Jo!S7Q*Q1QapiFr=6khD<N8tN@rdiA'
        '>%~X@*z$TOQx6<WPoWPOYM|MIg%<^1X{TN=!~5|33+kYwlT#46?#T(rVAXEFP*fuM#}#v3uL8-oxL{!U5Y&+k(a?|q@nSS6qFSPdaO#My6-($*7Wy>uPTcpx'
        'qtzG~EHan}EtOGaB(4yec=Oui>6|=vq3tfC6L}8|(qm+hn_@6Y0fWD)UEWjhQPD2tj>l6)Jmz6p%AEyCxH{)zy7F~~3nAi^wYad%PQ|2<@y%ZhHK$o`?e+S<'
        'x>H~(SRxGY7v`jkf&y?E_tbjCeDA?l_ypU|J06Vz!;0Ecy+2&oCD<X$K(+WxOecciOf&Um7H*1d(r~dYbn_Rut6{~rO9YzhjY=X$6VX>~z8c$3*ggHxWa=G)'
        'R6O!9L3ZtIH=7{g3DTmYGLQT;HO8=~Pr_9Q+skq(vW?n_4T5DGdBe?o45E3oj_#$uatM-r0e(n!8#l2kgfE9d#V-Cb3lia?gbSb>mV}@cMFlYE7o{|W^i<Gw'
        '^1!hRGtaZqAOf#on?$y8xn02IyM@%Z&Ac9@qUuDE=7*jRbcEdp|66>`Kw-e2eiT2>{U}OhxLLlI1Bp;1E9OYpS5Lkw_DZuDNRRPV7S_yXC_C^ug1LVcFTgYO'
        '6Mv<KRWIYkJ@m&40cQa&Lu!39@gdpF&5pV6v`~tIgVSj<rvadt9RbZ`;LHyD_o3lXCRrrQ89)5NXr$D7IAiv&C8%f<8n*Gx?4!A`&YGC)fbsp!CgKGWFR6&('
        'K}@A<o&g&w$vaG#m&bv}c!P2w_`@dGG~Q<21E<w6{1h-tH$_ILBxbt7412asQSrRqf7hw#8lGrWn7X0cFGSJ^G&qP3go;LowJ!r)4o?D!lzSszJ)r$#%ZAw<'
        '`j&^Zc+4?SD$+nG00SNe!Ev0NGRb9Xv!;2T$ug1sLC<~|9g#YRjWGHI!mFW<UEn^!rHr+I>8iUxo1#@HN248{AH8?U#F|V;XT_09j(pBBB5p<UjK6iLb}vO%'
        'u*|D0+oYYBFU=?9i9bxIXA|1^LOVBf+qRI5DP;I)>HN$$x~2VWm6lNU;3+<}GRi?T2qWZAXi#BKc;_J3)beIYETCEP6#g}+W=y6LcaaK-gm`-Hcnm9s8UT~z'
        '0<(q=7N4s!WD)bnuqHgp(5%sfXGRNIQnt&>iPBxOnT~tI2^Mq-mqs^*Dl6i0S3*j=#yRbspiKZK!q|oJh7-5Q>Ijhgg4n6dxBm$Uk$j5R03HSA%k%LGtB~C$'
        '0m#r`?qj)Yn4u{RLSY_lfmP;7K#CDGg!3dk$L{oejFt?ou-Pb^Iys(z%{Izp{fUzGsEJ5|WYdKue?ENp<Y?$4LBww+E3fL9A4VrfsQW-{qvGjM`-f_7A8j{A'
        '2dq5X%pH{8Rk3Ru7u@Vs4f9!DFc1Iln>mkHuv@SI7Z8H(SbrQ);BghM`^>YRU<|8M4S7Ax8U-BjEnt|Vdtq|l+?;_ePJPr4rM8r}Ra(>-|6(K(&2rd(=t6Qr'
        'c2^<j?a%t9$#-#&5;ESgTL>3D<gz?mX%<VXIpuoQ`eBbOo+zpV{8;4&Pam?fXR|{l8_j|$>Bhkv*7-1s=hs+rCcf_&!uZSh1IfbqBd5?V{ty)vYU?L*h!~4F'
        'L=L=*Ln?(iI+?5Ik(@;)gVS@CR#iev8V(7UY;sZ%=RSVXLw?ez+}Gs(zk&nTG!KtaOTh(es#93hbh|1glfRz;r)THWnk@ngo{$-{UGd2C_3THTRvq*Hj3cX*'
        '>Lu~NDPCj9aR1{0)S1yF$<}0(ETud+ykZ#iY4Qi<P4DQR=aVUD&9m|7cz~g>A$TYQTz@?w3{wv3tpkN@9r?b%9y>E+MaB6uEL+Kzdgy2=ysPj^1(*ziU@~P0'
        'HoZHU4o(pmRzzy(P}wS!g*or{UH2%b<zSKn;vvS9!SBGf8h|n-*HPk$^5slq=deb88Qv9Iv9#UnqSM~j$aW<t+0ln8E4jK(eZ7MQelGen;u>J%h7;j*)=Vf^'
        '4KS3f#l}L`lG~1lb9mIPQyY%cfW^AlZH7Va5a&nY>7pc>5LY_zQxp-1tp?(wn*gA(eN5CSG<f2+*Rvg)Dmx0KROv{)tSbPjQ_3=)FMH>)``SLsFac?~r0|vp'
        'oZ=_<%JkS_jfcI*{3o<xYFwwM8BX9wlHUzG3r+v=7qc*^CF@RY<JaJx|LSF+s4jsM`11fJai?*|RPUnE`A*Cfl?9$A3fWJC=@84ML>&4-h7M2Y2;8SQxek&}'
        'U8GN(Fd^TAyb=Cuj%F7+C8``Phx_Ew!mb2VYyj|>Sy_r5aNt;N!he<;+@R|t&Qm$Ckrp8d_)-vp9rJ^>-yVt|z6R?cVW-kGUy(axh_LV_T#MS{g}wnxtHC#Z'
        'XswJ9v;DBa#jF(2r0Kv176}#$LIE0DjbboM?NdocRDtHin$j-|z+(88ktvQh;O>Dq=$h;d#j7`On*59;%jE#8E&N~=ua%l>%}6YsWGSJ!bbAT=kF!$}t7!@f'
        'K=So0;!b)6IU~N6N~RpyVQuh`WWLfh;T^Up7s7E^U<HF3n9{Mu1;L+*@Rag}j7$1zw;IL^9UO*D4#GkM+``%0bpvTgD$r&m%y!^Czj45L0VheN{5rS=TM*<t'
        'XIj1n409vL;7KdO<xgc3h)|}MK9ncSzvQSP!<BjZ_9~2mQd)2~PI)gG(&QT+^BM9T?&glxo)omZ^?^g3{YIsc8o1SiV05W`;zS0;vl1M{P;)l%2H%z=;PI`x'
        'B+v&Nl~#az;X8Cd(R&g{3CRM?ivk|XJE>|X6FLP^ywgP9iJs0-R*GRMhK=<hMYMuQ&|WGLWq6jb5*lPDUX`G;;t<74u{dH7r*dvy?%akJiomk6*%$|Cci9h+'
        'ZgPI+jwfW{AG*h*v8#74%DMd~j9Csr($ez)prCM-7b<YM?IV+wb-U%!ndbFyjCU)3|IbqW`>2iV$?J5_habR;ntu3FLT0ysQnkM0gVDKOSnRQ}v#sDv{&>-R'
        '+v?1Asy7i<;?tOEltuOQ-Fw)MGt*YHnb(~gUdDMt=XwaNgYqb~bejMcgGV|TJtZM+rSh}rL)vvtOyi+p7f$BM3?CNT&gp<5X)%l{-UOa>7ggKy*|TRuo~6%='
        'pBGFYs#iSZdMu?&IN(Kd8HHc3GIpCoo&(>#%nTP=u*|9=R%nZam6l5sij=ORJ~b>WtsS1aWMk~mX&O7G!V4OM1(g%uLL^NaJG7>-O<4K2Bqa`M?ig(mM0F_c'
        'Fl#(K%%N}tNTM{T7!b7!q#E^=RGG%E*SFy`0_)gMtj6Qm>W%eUBi;FT9Ih>qbN`!25rHu!&-q*IyfdA0FCN8IKGdIe<ZY8cDV0r>yC42lxj*7xH5W+y%em;`'
        'g#v$iGybF1eCN%cn|2k$y2M#o(2FA~?q|1uJ_Wgp^+vt-BIU;bqhVBY2wWXmoh~M#{Yz*7l=Q&~=M7N=6;-`y6VHDq+M>qiZ0w%(#(70yUVK^}mrW3Tba{r!'
        'v`O4mN*l{vl>^Mx4&R42os<@c91q6sr{2klStv<jqjElsC>4QHc#(G7Z(Cp_#8Kp}((VEH6dC>6KWMeskzrOJ+-=hf!M=Q@SOj5DQOHy;#I6Vdn;9?Q=+bo_'
        'wz%tu2OaR14m^V&EV?{uM3+9GS;Fp;*i)@LUErd)Yb-jI$tOkUsou6)WLq9kRXm#@KWJ6q3$+A9oG%)m52^H;ioJ^Gb8_T!K>S7lcCI!~kiGN!2Iws&!Y~XH'
        '(-j?wC=^1O!mmN9IRD}UJ3sAs_`jCC5x^6r{FmF*QY$>AkzItQ#Bd6tsI;hgy(BZprIoHT-wUxg0IXE8S#jzF>zgnEdxVlWlhH|U*rQ65^YIB-4kD>>OOY$+'
        'tp>6rTD0V>A)2*iVw~W;Rs(ie$>QA0{;?JI&41b`MJ|2dGd8Tld~&gJ6zZu)eSojlBA|oM$f)qFTv(K^faK(yIK25&Z@oBpNBzCjUk3S27Y>-@U{JyCg*jh~'
        '@#vD9?K%qA*A`vpwEkMWfkjM{hjS{P6e-&xy2^|>k2yJysSO;aMgq$`8~5Iy_Q2W-l6w#96T9HfJfQ=?z4v5!TB}v+b9JfUAQZb`d<!8K+hfQx^dnCmZAUA)'
        'IPk<har;xFKLS^E(s!-X-e)UZG%x~mJRY60OWeSIb(R6BRakJVanULTb&wGqkmo+=-K$HxIBMe&LtS_wBw0!pyUEU_c4z?lZJP`#f5#qlNi|a(SCr`;>LA{-'
        '%#JBH`z6+vQYN9YskPAQ@)2BEej$t5AvtY=E$-c>BGO+@22^qZC9j}pQ2GnJXG+w<tYSb2FW9p%HpgXqk)!aqH&`^99xt5zgS~2asRH;P`LH6?L}Xj~VN@>F'
        'D$2z|1VhP0=#6;^l-C(y?Brx{I+%*13KRH2nukRK^agwJ`U2IdD9`JcuB6TmgxJM<*6t0aN9B8HuOPaUxVxvxH78}-1j;sIXd_Tt$ZnfNVijpF2Xpt6P+_h>'
        'wKdHtje=lfapU1-8%tOBbRm*T$)d8_lhOIO4{JT@|H?uTctW2_2l<JmdBgF@*7ZCFoh~<vR0+*6XRcDg8zCWG8#F^PPqMGvQyb=?YV^VcYTP9HCU#9)`TV#>'
        'D#UIG8Z#WN@@HqeL3RYODDI#$J7!goPDlCaA8s6DFvP4aATn8%v)M5yU_`4Smuw5hTai&I09Ol3N!}N-{-eW*JN^jngE$_aT=1~UtlNF8TA*$;3_2tjIFQ^-'
        'F{Q?C6a}GV*mi<W14o>Pllx5W$f<)GOgzGO@igG<R0P2N?Ht4yMTGP5cB}=9ETI(z)(@x&3e$?s+^|ihvXPz0OnDozE$CgNegG8!r<d6&((j_#-tW}cwEeKw'
        '<f?Ns_o#^4?4X`t_0(LEP*G=V*T{4Ut9KpTd)qY6(LX7J{wPg&FhDBlYArzhq#mmxs9*5<;({lb4|_#tbH{arn%fBTs|I=R{Hj6z0)M~Qb<rT%`ijZMI0%#u'
        '78-Z=?G){LSS^M`!>-&fSa*{kLqIL_DjSaO=fU(RBD{s@E{Z?9y!W)5%~tr=)?W>i-wdOk+kB|dLTC9^r^&(xFi}R4N-rMM*w;yEdDR+fE_qGfI=-zGShGXS'
        '0YwSFiR*YePr8aniH3LH*`+IGI<JbHU%gGF1AF(5uGW<ndwc(tX%~;?clKK?yIfPH+txg*-Z6XT^VhFz<?@4$dB|QBE<EU%eR{iBSKw8>Ag2Cmkj{Zq5?;F7'
        'O*(i?{pCw}2)*$Fqe**znN%o&dcu7~T$-?WWcn3@3UsgH1ztxrLx1Da6bC;KM@L`qM5A{+_&mj16Zzpiy5w1QY_neU@a8rC2Dp3N!KPDt$Y%w{`70Lg32XN_'
        '3zaJH_FH)1O>-4O=e4c5V4wqwTLVwMvY}&Mn$O?7uD0BHZ$RfA@Jq{nLa7^XxmPVu+i@bFJF(iM^!%H0YQ9qnO&0l0MxS}dN4Zv>MDJ+OE*wPX5b4NvM?FZc'
        'o+Gz+9M-PEytcl-lV8}#k2NxWmq+)i_EzC=N3}of2Bou6ExGLADP}%O6}Z0i8VIK=zQ)&uQfnQ7E5+B?tFHVSrE%*)X00%g|LE~Vu<|QMVLGz<kDnjve3M5F'
        ';HTVw4>mtj&^f??HD$+7?f;Dm`8#BxmWow780AOk3_L3)oRZ=cmzX>F*oU=LCMeWvo*Cu&J4%5843M&e6bH1b^(d%u?RB9DL&77?abE@I{;~BV4J`5k2w+v`'
        'blVLY#@1Ycr5PH9<c|zo5U$;KQo-@DAHBCtgNjstKZXy<9BywhBzE4jr$GR3Zu^0uNrraK!yXV=j$FR0O-Fj**}Cy6N84y5=KV3PYD>L^IV&;n&I^k)IKU>}'
        'LGUMF@u+&j*tWp#(R*by7|P2E{y%YSw(VWY7{33^6oh*Hi7DvxH2)(SV#n>gxkiH(zc~JfQ7Y@PZaZIS{jD7uBv7&c1P<7}t6u(6xcfy=X4i!*8l1Rs@)Kxr'
        '2)QV(yD&#HIw^D>J^Tq2%1WN4jyXD-OFck9435rS@1%E%PN-I3(Xe?Pu1@diF%wADs6TYGndOj{3u1~zF>I(Yrmj=vn(RhL&A!Sz0G9rBVA}a@9$C`hM?Z^y'
        '!pF2PW*V%}-onBz3=ezUan+&6?2&G{2(d76J$?*k2}L4OwZKMQeo-aIgR1spG1XddBtR^s=&mNPwTnC@`CLo^b_+aNV`Fy7e|coiTJmnbo3MFlq5bFqKCQL1'
        '^5~qtZno@#&V{wIH<|*tMHg*n_@v8Xt-xf~9Z2phE`+^1lZS0D$grJtznO#lI%nDl;3Bo{Z)Sg+f<I(-+7GjbJ$<#evG@UUe=j!!F{)I5>~w66e0aV8u8!uE'
        'ZX%+yq89z_8fCcv0BzH>zdhL1GQp(#)G6ZFjh`T8QlXFjbXM&cXzyByNWp4|$Kw4SOKEAvYqwB+B2PuZ_Pkv97~^RC{nn9ZU|^8^QE^0gd<U$6#v=r|)f{HA'
        '+x4igV-z&_0EUJKUwzmQKQR+l4^o=bUQG_vY3(0iTU{nmGc%D^Y0c_+zUEAWPT{_J%@QwZt-{T(fvW@_F3q<2y!}eKcBrA#zA_YY8zvenn;1-YH5!Xp*cjf>'
        'N=gY6tW{Pgty?qJu8S6=pCtah2!#Bdf4OMSx_{eE^(R<Eb>W_Fg=nmuLNRVKJ>jOedJdMU_nq3Z#J-wcm#6T*J?xeUw~prM6i`!~M1%dNL3a_NV#bY3>&D|+'
        '+GYEJMNq<IT@AC6|NIxxouviq%x4}6&TpyLxt%d(9@(FNe1rnSI2)`j^S8;N$4mXr#)FS&eu3+6+E{k#cplEn^Fa1tFgDG2QGL1%v!E-ZPF%WS@aZI`KbMJ@'
        'iBV|kIEhyxC}q(bkrg8QQwdz%QUCFlDp|nfy2Ohm?!g;zk}bG3IAWt%O-;$OTR)v_X}-&CWHm&@u3hs-kEWOu;(tVoL!jIfj9Ztv5;-dT`=TO6<!`#;Zz(#x'
        '<m(nMHaWv5QCfjnzB`t_<9}rek75M)7Z^+`KE*`c7LRJ&;$NW3nmoy;te3xW{KdlaIe5!#Hq94zHj@Kjd1Y~eQRA&hd}`YBDlE|b_nV+g7r)zlv9Of5wqKS-'
        '&6Vhem&S`u7=o<rwes(puvPRu+q-&V&5pj?L46;d)Nit?OjC9-1w9gQv!Nrc5_VO}Zt3q-tnV!gUpst-Y<j>&V!vpe*iTq0_JggK$5yLRTrFl}^NL09badqA'
        'g~;kS9px|j6~4<Olp-BkU}n*Z(CVla%;HM{xz3K9EtZ_Sn6ov^Gw`9^;gl*#=&x3l>ws$nM1vKv;9vfldJ}hADH$=L6&VY3xwm^{i059v?@lK0VkrMg7@CYq'
        'iG6t^iuu7RR1R5Cc|3jP%+A({SAp>*&GO$$X>r}@#6rzHgI0WrCj@f)I~Nln9^+@VVc;5h9!d<)Gdt-$(DV+Li;0lN-v0q`^P-~'
          )},
}

def digest(data):
    return hashlib.sha256(data).hexdigest()


def payload(n):
    item=MODULES[n]
    # Reject changed or corrupted embedded source before any writes.
    try:
        raw=zlib.decompress(base64.b85decode(item['z85']))
    except (ValueError, zlib.error) as exc:
        raise RuntimeError('BUNDLED_MODULE_DECODE_FAILURE') from None
    if digest(raw)!=item['sha256'] or len(raw)>100_000:
        raise RuntimeError('BUNDLED_SOURCE_CHECKSUM_FAILURE')
    compile(raw.decode('utf-8'),item['module']+'.py','exec')
    return raw


# Both the supplied ORACLE-366 source and the separately certified user's installed
# ORACLE-366 binary are accepted. Never silently replace the already-running
# version with a different implementation.
KNOWN_EXISTING_366_SHA256 = '1a5c0bfb27fca5dcdc530facc2caa79b8f2ac74282a43accc6a6e7d0f339215d'

def targets():
    return {n: DIRECTORY/(MODULES[n]['module']+'.py') for n in MODULES}


def preflight():
    # Production source graph must already exist. Never install or modify
    # scanner internals as a side effect of this coordinator.
    missing=[x for x in PREEXISTING if not (DIRECTORY/x).is_file()]
    if missing:
        raise RuntimeError('REQUIRED_PREVIOUS_MODULE_MISSING:'+','.join(missing))
    for n in sorted(MODULES):
        payload(n)
    if not (DIRECTORY/'__init__.py').is_file():
        raise RuntimeError('EXECUTOR_PACKAGE_NOT_FOUND')


def atomic_put(target, raw):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file() and target.read_bytes()==raw:
        return False
    staged=target.with_name(target.name+'.oracle367.stage')
    try:
        staged.write_bytes(raw)
        if staged.read_bytes()!=raw:
            raise RuntimeError('INSTALL_STAGING_BYTES_MISMATCH')
        os.replace(staged,target)
        return True
    finally:
        staged.unlink(missing_ok=True)


def verify_modules(with_upstream_audit=True):
    expected=targets()
    for n,target in expected.items():
        permitted={MODULES[n]['sha256']}
        if n==366:permitted.add(KNOWN_EXISTING_366_SHA256)
        if not target.is_file() or digest(target.read_bytes()) not in permitted:
            raise RuntimeError('INSTALLED_'+str(n)+'_SOURCE_INTEGRITY_FAILURE')
        py_compile.compile(str(target),doraise=True)
    importlib.invalidate_caches()
    real365=importlib.import_module(PKG+'.'+MODULES[365]['module'])
    real366=importlib.import_module(PKG+'.'+MODULES[366]['module'])
    if Path(real365.__file__).resolve()!=expected[365].resolve():
        raise RuntimeError('ORACLE365_IMPORT_PATH_MISMATCH')
    if Path(real366.__file__).resolve()!=expected[366].resolve():
        raise RuntimeError('ORACLE366_IMPORT_PATH_MISMATCH')
    if real366.upstream() is not real365:
        raise RuntimeError('ORACLE366_365_IMPORT_GRAPH_MISMATCH')
    if not callable(real365.consume) or not callable(real366.live):
        raise RuntimeError('NATIVE_IMPORT_FUNCTIONS_MISSING')
    if with_upstream_audit:
        real366.audit()
    return real365,real366


def install():
    preflight()
    changed={}
    for n, target in targets().items():
        if n==366 and target.is_file():
            current_sha=digest(target.read_bytes())
            if current_sha not in (KNOWN_EXISTING_366_SHA256,MODULES[366]['sha256']):
                raise RuntimeError('UNKNOWN_ORACLE366_VERSION_REFUSE_OVERWRITE')
            changed[str(n)]=False
        else:
            changed[str(n)]=atomic_put(target,payload(n))
    real365,real366=verify_modules()
    print('[ORACLE367_INSTALL_PASS]',json.dumps({'modules':[365,366],
          'changed':changed,'import_graph':'366_TO_365_VERIFIED',
          'scanner_322_touched':False,'private_key_used':False,
          'signing':False,'broadcast':False}),flush=True)


def audit():
    a,b=verify_modules()
    print('[ORACLE367_AUDIT_PASS] ORIGINAL_352_AUDIT 364_BRIDGE 365_COLUMNAR '
          '366_CERTIFICATION_NO_NEW_WS_NO_KEY_NO_SIGN_NO_BROADCAST',flush=True)


def tests():
    class Cases(unittest.TestCase):
        def test_checksums(self):
            for n in MODULES:self.assertEqual(digest(payload(n)),MODULES[n]['sha256'])
        def test_future_imports_legal(self):
            for n in MODULES:compile(payload(n),MODULES[n]['module']+'.py','exec')
        def test_correct_graph(self):
            self.assertIn(b"oracle_365_sqlite_columnar_event_handoff",payload(366))
            self.assertIn(b"oracle_364_consolidated_event_handoff",payload(365))
        def test_safe_stage(self):
            with tempfile.TemporaryDirectory() as d:
                f=Path(d)/'mod.py'
                self.assertTrue(atomic_put(f,payload(365)))
                self.assertFalse(atomic_put(f,payload(365)))
                self.assertEqual(f.read_bytes(),payload(365))
        def test_unsigned_only(self):
            src=payload(366)
            self.assertIn(b'NATIVE_ATOMIC_PROVIDER_NOT_CERTIFIED',src)
            self.assertIn(b'sigVerify',src)
        def test_canary_size(self):
            self.assertIn(b'CANARY = 10_000_000',payload(366))
        def test_sqlite_query_only(self):
            self.assertIn(b'PRAGMA query_only=ON',payload(365))
        def test_no_322_replacement(self):
            self.assertTrue(all('322' not in x for x in PREEXISTING))
        def test_no_new_network_client(self):
            self.assertFalse(any('rpc' in m['module'] for m in MODULES.values()))
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Cases))
    if not result.wasSuccessful():return 1
    one,two=verify_modules()
    if one.tests()!=0 or two.tests()!=0:return 1
    print('[ORACLE367_TEST_PASS] BUNDLE_9 + INSTALLED_ORACLE365 + INSTALLED_ORACLE366',flush=True)
    return 0


def run(seconds=180,poll_ms=5,ttl_ms=2500,max_age_ms=1500):
    # Provider deliberately stays None: no speculative native API bindings.
    # This is a live read-only scanner -> pre-atomic certification run.
    _,executor=verify_modules()
    print('[ORACLE367_RUNTIME] ONE_CANONICAL_SCANNER_BUS 365_COLUMNAR_366_GATE '
          'NATIVE_PROVIDER_UNBOUND NO_NEW_WS NO_KEY_NO_SIGN_NO_BROADCAST',flush=True)
    return executor.live(seconds=seconds,poll_ms=poll_ms,ttl_ms=ttl_ms,
                         max_age_ms=max_age_ms,provider_module=None)


def main():
    p=argparse.ArgumentParser()
    for flag in ('install','test','audit','wallet-status','run'):
        p.add_argument('--'+flag,action='store_true')
    p.add_argument('--seconds',type=float,default=180)
    p.add_argument('--poll-ms',type=int,default=5)
    p.add_argument('--ttl-ms',type=int,default=2500)
    p.add_argument('--max-age-ms',type=int,default=1500)
    args=p.parse_args()
    if not any((args.install,args.test,args.audit,args.wallet_status,args.run)):
        p.error('SELECT_MODE')
    if args.install:install()
    if args.test and tests():return 1
    if args.audit:audit()
    if args.wallet_status:
        print('[ORACLE367_WALLET_ENV]',
              'PRESENT' if bool(os.environ.get('QSB_SOLANA_PRIVATE_KEY')) else 'NOT_SET',
              'KEY_NOT_PRINTED KEY_NOT_USED',flush=True)
    if args.run:return run(args.seconds,args.poll_ms,args.ttl_ms,args.max_age_ms)
    return 0

if __name__=='__main__':raise SystemExit(main())
