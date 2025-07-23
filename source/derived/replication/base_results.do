
quietly sum F1
global N1 = r(N)
quietly sum B1
global N2 = r(N)

foreach j in rc rt rcalt rtalt rccond rtcond bc bt bcalt btalt bbc bbt B BB BBB Bcond Balt BBalt jk jkalt {
	matrix `j' = J($N2,3,.)
	}
foreach j in p palt ppalt {
	matrix `j' = J($N2,1,.)
	}

quietly generate Start = 1 if _n == 1
quietly replace Start = Start[_n-1] + F4[_n-1] if _n > 1 & F4 ~= .
quietly generate Finish = Start + F4 - 1
quietly generate double B3 = abs(B1/B2)
mkmat Start Finish F4 F3 in 1/$N1, matrix(info)
mkmat B1 B2 B3 in 1/$N2, matrix(B)

forvalues i = 1/$N2 {
	quietly replace ResB`i' = . if ResSE`i' == 0
	quietly replace ResSE`i' = abs(ResB`i'/ResSE`i')
	quietly replace ResB`i' = abs(ResB`i')
	}

*Statistics derived from the randomization distribution (randomization-c, randomization-t)
*randomization-t
forvalues i = 1/$N2 {
	quietly sum ResSE`i'
	global N = r(N)
	quietly sum ResSE`i' if ResSE`i' > B[`i',3]*.999999
	matrix rt[`i',1] = (r(N)+1)/($N+1)
	quietly sum ResSE`i' if ResSE`i' > B[`i',3]*1.000001
	matrix rt[`i',2] = r(N)/($N+1), $N
	}
*randomization-c 
forvalues i = 1/$N2 {
	quietly sum ResB`i'
	global N = r(N)
	quietly sum ResB`i' if ResB`i' > abs(B[`i',1])*.999999
	matrix rc[`i',1] = (r(N)+1)/($N+1)
	quietly sum ResB`i' if ResB`i' > abs(B[`i',1])*1.000001
	matrix rc[`i',2] = r(N)/($N+1), $N
	}

*Statistics derived from the paper's regressions themselves
capture sum BIV1
if (_rc == 0) {
	quietly replace B1 = BIV1 if BIV1 ~= .
	quietly replace B2 = BIV2 if BIV2 ~= .
	quietly replace B3 = abs(B1/B2)
	mkmat B1 B2 B3 in 1/$N2, matrix(B)
	}
quietly generate DF = .
forvalues i = 1/$N1 {
	quietly replace DF = F3[`i'] if _n >= info[`i',1] & _n <= info[`i',2]
	}
quietly generate double p = Ftail(1,DF,(B1/B2)^2) if DF ~= .
quietly replace p = chi2tail(1,(B1/B2)^2) if DF == .
mkmat p in 1/$N2, matrix(p)


foreach j in rc rt p {
	svmat double `j'
	}
generate CoefNum = _n
generate paper = "`paper'"
generate RegNum = .
forvalues i = 1/$N1 {
	quietly replace RegNum = `i' if _n >= info[`i',1] & _n <= info[`i',2]
	}
save stats_`paper', replace

