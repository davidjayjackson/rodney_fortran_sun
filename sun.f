      PROGRAM SUN
C********************************************************************************
C     Program uses a model from Boots et al., 6 Feb. 2004, Vol 303 Science, 
C     Large Shifts in sunspot evolution relate to Umbra, Penumbra Structure.
C     Reads output, rgo_data.txt, from the VB Makemap program which estimates the 
C     sunspot counts and motions on the solar disk using Lat, Long
C     (or X, Y cordinates.) Data from RGO (rgo_data.sql)  
C********************************************************************************
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
      PARAMETER(MAXN=400,MAXL=10,MAXK=40)
      DIMENSION Y(MAXN),T(MAXN+2*MAXK),ETA(MAXN+2*MAXK)
      DIMENSION ETADEL(MAXN+2*MAXK),CONETA(MAXN+2*MAXK)
      DIMENSION ATA1(MAXL+1,MAXL+1),ATA1AT(MAXL+1,2*MAXK+1)
      DIMENSION SCRAT(MAXL+1,MAXL+1),A(2*MAXK+1,MAXL+1)
      DOUBLE PRECISION INF(8), avepores
C COMMON /CS2TIM/ is needed for Microsoft FORTRAN compiler
      COMMON /CS2TIM/ Y,T,ETA,ETADEL,CONETA,ATA1,ATA1AT,SCRAT,A
      CHARACTER*5 STRING
      CHARACTER*1 ADAT,COM
      CHARACTER*75 CAPT,LABEL
C    set N to Carrington rotations 3*27 days
      N=85 
C identify program to user
      WRITE(*,*)' Program simulates sunspot pore evolution   '
      WRITE(*,*)' from Umbra, Penumbra structure using  '
      WRITE(*,*)' State transition NLDE  '
      WRITE(*,*)' Number of days in run = ', N
C     use data from makemap output of sunspot evolution, rgo_data.txt
C     or data from MySQL (rgo_data.prn) 
      LOC=0
      ADAT ='Y'
      OPEN (25,FILE='rgo_data.prn',status = 'OLD')
      READ(25,8,ERR=350) NREC,LABEL
8      FORMAT(I6,A75)
C		open output to a csv file
      LOC=1
      OPEN (3,FILE='SUN.CSV')

      WRITE(*,*)' Enter number of Umbra seen'
      WRITE(*,*)' >'
      READ(*,*)beta
      WRITE(3,81) int(beta)
81     FORMAT(1(/),' Number of Umbra seen ' ,I3)
      WRITE(*,*)' Enter number of total sunspots seen'
      WRITE(*,*)' >'
      READ(*,*)rr
      WRITE(3,82) int(rr)
82     FORMAT(1(/),' Number of total sunspots ' ,I4)
       ispots = int(rr)
       rr = ((rr + 1) / 100.)
      WRITE(*,*)' Percentage of Umbra area with Penumbra - delta '
      WRITE(*,*)' >'
      READ(*,*)delta
      WRITE(3,83) delta
83     FORMAT(1(/),' Percentage of Umbra area with Penumbra ' ,F5.2)
      WRITE(*,*)' Percentage of sunspots in Umbra - gamma '
      WRITE(*,*)' >'
      READ(*,*)g
      WRITE(3,84) g
84     FORMAT(1(/),' Percentage of of sunspots in Umbra ' ,F5.2)
      WRITE(*,*)' Percent of Umbra area to total group area'
      WRITE(*,*)' >'
      READ(*,*)P
      Pr=(1.-P)/10
      WRITE(3,85) P
85     FORMAT(1(/),' Percent Umbra area to total group area ' ,F5.2)
C      WRITE(*,*)' Estimate duration of Umbra in days - K(1<K<85)'
C      WRITE(*,*)' >'
C      READ(*,*)K
       K = 1
C      IF(K.GT.27)K=27
C      WRITE(3,86) K
C86     FORMAT(1(/),' Duration of Umbra in days ' ,I3,1(/))
C      WRITE(*,*)' Confidence of seeing as percent - alpha '
C      WRITE(*,*)' >'
C      READ(*,*)alpha
       alpha = .95
C x = global frequency, z = nearest neighbor, use later for map clusters
        x = 1./Pr
        z = 8
C Set polynomial values, K, L line dimensions
C loop for data, by batches of N
C work with batches of the data file
      last = 1
      NREC = 1
      NEXT = 1
      ONE = 1
      NBATCH = N
C                   Header for data output   
      COM(1:1) = ','
      write(3,3) 'Days  ',COM,'Umbra',COM,
     *           'Pores',COM,'CWSA',COM,' CUA'
3      format(1X,A4,A1,6X,A5,A1,7X,A5,A1,2X,A4,A1,A4)

C main loop to collect data and compute group evolution

      DO WHILE(NEXT.GE.ONE)
C                       get next batch of data
        WRITE(*,*) ' Continue (1), Stop (0)'
        WRITE(*,*)' >'
        READ(*,*)NEXT
        npores = (int(avepores)/NREC)
        nspots = (ispots - npores)
        write(*,4) 'Sunspots = ',ispots,'Pores = ',npores,
     *             'Actual Sunspots = ',nspots
        write(3,4) 'Sunspots = ',ispots,'Pores = ',npores,
     *             'Actual Sunspots = ',nspots
4        format(1X,A10,I3,1X,A7,I3,1X,A17,I3)
        IF(NEXT.NE.ONE) GOTO 50

C       loop through the Carrington Rotations NBATCH times
        LOC=10
        NEWY = 1
          DO 100 IREC = NREC, NBATCH
             IF(ADAT.EQ.'Y') THEN
               READ(25,9,ERR=350) ICSG,iday,ICWSA,ILNS,ICLD,ICUA
9               FORMAT(6(I14))
               IF(iday.GT.last)last=iday
               SUSQ = FLOAT(ICUA)
C  set model parameters
               RINF=rr*FLOAT(ICUA)
               freq=g*FLOAT(ICUA)
               C=beta*FLOAT(ICUA)
               PG=P*FLOAT(ICUA)
               freq=(C/freq)**2
C              freq = 1-SQRT(freq**2/C**2) used to be for random tries
             ELSE
               SUSQ=1/Y(NEWY)
               RINF=rr*SUSQ
               freq=g*SUSQ
               C=beta*SUSQ
               PG=P*SUSQ
               freq=(C/freq)**2
C              freq = 1-SQRT(freq**2/C**2)
             ENDIF
C      use the cumulative log function to spike the evolution, K days
             time=FLOAT(IREC)
C             time=((time/N)+.01)+1.
             time=(time/N)+.01
             IF(IREC.LE.K) THEN
                F=0
                CALL ZCELLS(IREC-1,INF)
                DO 1 J=1,int(z)
                 F=INF(J)+F
1               CONTINUE
                POSQ=(F/z)
                CALL EXPO(N,time,PG,RINF,freq,C,F)
C                POSQ=F*POSQ
C               POSQ = POSQ*(delta+(g*alpha))
C  debug                   write(*,300)ICSG,POSQ,F
C                 ,PG,RINF,freq,C,time
C300                format(2X,I7,2(1X,E15.4))
C                  if(irec.eq.k)stop
             ELSE
C       chose even AND odd values for those to be pores
C       filter here with delta+g*alpha is more restrictive 
               POSQ = (1/FLOAT(IREC))
C               POSQ = POSQ*(delta+(g*alpha))
             ENDIF
C       choose even values for those to be removed (converge to 2)
             IF(MOD(IREC+1,2).EQ.1) THEN
               REMQ = -(1/FLOAT(IREC))
               REMQ = REMQ*(g*(1-alpha))
               REMQ = REMQ*delta
             ENDIF
      SUSQS=((1-Pr)*rr*(N*SUSQ+N*REMQ))/(z+Pr*rr*(x*SUSQ+x*REMQ))
      SUSQI=((1-Pr)*beta*N*(POSQ))/(z+Pr*beta*x*(POSQ))
               SUSQS = SUSQS*delta
C       filter here or at POSQ? filter here less restrictive 
               SUSQI = SUSQI*(delta+g*alpha)
               Y(NEWY) = (SUSQS*SUSQI)/N
             write(*,13) iday,COM,SUSQI,COM,SUSQS,COM,ICUA,COM,ICWSA
             write(3,13) iday,COM,SUSQI,COM,SUSQS,COM,ICUA,COM,ICWSA
13            format(1X,I4,2(A1,F12.4),A1,I4,A1,I4)
             avepores = avepores + SUSQS
           NEWY = NEWY + 1
100       CONTINUE
C next batch in the data file
C display number of Carrington Rotations 27 days
        NREC = NREC+N
        IF(ADAT.EQ.'Y')THEN
          IF(last.GT.85)last=27
          N=(last*3)-3
        ENDIF
        NBATCH = NBATCH+N

50    CONTINUE
      ENDDO
      GOTO 60
C
C           ERROR HANDLING
C

350     CONTINUE
        WRITE(*,360) LOC,IREC
360      FORMAT(3(/),'  Cannot find rgo_data.prn : ',
     *       ' At LOC=',I3,' records read =',I6)
        GOTO 60
400     CONTINUE
        WRITE(*,410) LOC,IREC
410      FORMAT(3(/),'  sun.csv must be locked : ',
     *       ' At LOC=',I3,' records written =',I6)

60     CLOSE(25)
       CLOSE(3)
70    END

      SUBROUTINE EXPO(N,time,PG,RINF,freq,C,F)
C     ************************* expo.FOR *************************
C     return F
C     This program models the likelyhood of evolution of sunspots given
C     sunspot numbers. Estimates for evolution are based on
C     magnitudes of the umbra and penumbra during observations.
C     The function f can be used to determine a slope, which gives a
C     likelyhood of pores over time. As sunspot numbers change
C     the slope moves in offset of time and increases or decreases. 
C
C            1). value of evolution rate = h
C            2). quantity of sunspots = m                   
C            3). interaction distance r                        
C            4). scaling constant = c
C            5). rate of reactions constant = k, T
C            6). estimate of evolution = SicE 
C            7). function of evolution = f 
C
C         The formuli used are as follows:
C
C            1). for h
C                         x = time before saturation 
C                         h = exp((((ln(v)) * pi)-1)cos-1)
C                         h = 1/(pi*2)*h
C
C            2). for m
C                         x = time before saturation 
C                         m = exp((((ln(v))/.4)-1)cos-1)
C                         m = 1/m
C
C            3). for r
C                          r = h/(m*c)
C
C            4). for e2
C                         e2 = inv(exp(atan(inv(ln(pi*gm)))))
C
C            5). for k, t
C                         k = inv(exp(atan(exp(pi*ln(ln(v))))))**3
C            6). SICe
C                SICe = 1/(3*pi*(h**3*v**3))*(3*sqrt(e2)/(4*pi*m*v))**(kT)
C
C            7). f = SICev * mc
C
C            8). c = exp(exp(inv(pi)*10)))
C
C        THIS ROUTINE PROVIDES THE S.DAT FILE FOR INPUT TO THE PASCAL
C        PROGRAM EXPOFIT.PAS, WHICH GRAPHICALLY CREATES A PLOT OF THE
C        VALUES AND DRAWS A LEAST SQUARES LINE TO FIT THE FUNCTIONS.
C     *****************************************************************
C
      DOUBLE PRECISION freq,H,C,J,K,M,F,SICE,ESQR,PI,KT,S1,S2,
     +                 PG,RINF,time
C
C     INITIALIZE PI
C
      PI = 3.141592654
C      time=time/N
C  assume a solar minimum, longer latency period,
C  DE-NORMALIZE for solar maximum, short latency period.  
        PG = 1.-((PG-RINF)/(PG+RINF))
        CALL ENERGY (time,H)
        CALL MASS (time,M)
        CALL E2 (time,ESQR)
        CALL JTEMP (time+1,J)
        K = J**3
        KT = DLOG10(K*PG)
        IF(KT.LE.0.0) KT=5/2
        S1 = (1/(3*PI*(H**3*freq**3)))
        S2 = (3*DSQRT(ESQR)/4*PI*M*freq)**KT
        SICE = S1*S2
        F = (SICE*freq)*(M*C)
C         alpha=H/(M*C**2)
C         write(*,1)alpha,freq,C,SICE,J,K,F
C1        format(1X,7(1X,E13.6))
      RETURN
      END
C     ************************* ENERGY.FOR *****************************
C
C     This subroutine given the time (positive number) uses
C     constant h :
C
C                               ((((lnv)*pi)-1)cos-1)
C                        h =  exp
C                        h = 1/(pi*2)*h
C
C     ******************************************************************
      SUBROUTINE ENERGY (time,H) 
      DOUBLE PRECISION LNH,H,PI,COSRAD,SINRAD,TEMP,TANRAD,time,
     +                 ANGLE,DEGTAN,EXFUNC
C
C     INITIALIZE PI
C
      PI = 3.141592654 
      LNH = DLOG(time)
C /* NATURAL LOG FOR H
      COSRAD = 1./(LNH*PI)
C /* FIND INTERNAL ANGLE
      SINRAD = DABS((COSRAD**2)-1.)
C /* CONVERT TO SIN RADIANS
      TEMP = DSQRT(SINRAD)
      TANRAD = TEMP/COSRAD
C /* CONVERT TO TANGENT
      ANGLE = -(DATAN(TANRAD))
C /* ARC TANGENT OF ANGLE
      DEGTAN = -(ANGLE)
C /* CONVERT TO XRAY FLUX
      EXFUNC = DEXP(DEGTAN)
C /* EXPONENTIAL VALUE OF H 
      H = 1./(EXFUNC)
C      H = H /(PI*2.)
C /* VALUE FOR H 
      RETURN
      END
C     ************************** MASS.FOR *****************************
C
C     This routine given the time (positive number)
C     calculates the gram mass according to the following formula:
C
C                              ((((lnv)/.4)-1)cos-1)
C                       m =  exp
C                       m = 1/m
C
C     ******************************************************************
C
      SUBROUTINE MASS (time,M) 
      DOUBLE PRECISION LNM,M,COSDEG,TAN,ARCTAN,DEGREE,time

10    CONTINUE
      LNM = DLOG(time)
C /* NATURAL LOG FOR MASS
      COSDEG = 1./(LNM/.4)
C /* FIND INTERNAL DEGREE (RADS)
      TAN = (DSQRT(DABS(1-COSDEG**2))/COSDEG)
C /* CONVERT TO TANGENT
      ARCTAN = DATAN(TAN)
C /* FIND ARC TANGENT VALUE
      DEGREE = ARCTAN
C /* CONVERT TO XRAY FLUX
      M = DEXP(DEGREE)
C /* EXPONENTIAL VALUE OF M
C      M = 1./M
C /* VALUE FOR M
      RETURN
      END
C     **************************** JTEMP.FOR ***************************
C
C     This subroutine given the time (positive number) uses
C     the following formula to calculate the equivalent of temperature
C
C                     J = exp(atan(exp(pi*ln(ln(v)))))
C
C     ******************************************************************
      SUBROUTINE JTEMP (time,J)
 
      DOUBLE PRECISION LNJ,J,PI,TANRAD,time,ANGLE,DEGTAN,EXFUNC
C
C     INITIALIZE PI AND EXFUNC
C
      PI = 3.141592654
      EXFUNC = 0
      LNJ = DLOG(time)
C /* NATURAL LOG FOR J
      IF (LNJ .LE. 0) GOTO 100
C /* FUNCTION FAILS AT ABSOLUTE 0
      TANRAD = DEXP(PI*(DLOG(LNJ)))
C /* EXPONENTIAL VALUE OF PI*(DLOG(LN(RS))
      ANGLE = DATAN(TANRAD)
C /* ARC TANGENT OF RAD ANGLE
      DEGTAN = ANGLE
C /* CONVERT TO XRAY FLUX
      EXFUNC = DEXP(DEGTAN)
C /* EXPONENTIAL VALUE J  
100   J = EXFUNC
C /* VALUE FOR J
      RETURN
      END
C     ****************************** E2.FOR ******************************
C
C
C                     ESQR = inv(exp(atan(inv(ln(pi*gm)))))
C
C     ******************************************************************
      SUBROUTINE E2 (time,ESQR)
      DOUBLE PRECISION LNE2,ESQR,PI,TANRAD,time,GM,COSRAD,SINRAD,
     +                 ANGLE,DEGTAN,EXFUNC
C
C     INITIALIZE PI AND EXFUNC
C
      PI = 3.141592654
      EXFUNC = 0
      COSRAD = (1/((DLOG(time)/.4)))**2
C /* FIND INTERNAL ANGLE
      SINRAD = DABS((COSRAD**2)-1.)
C /* CONVERT TO SIN RADIANS
      TEMP = DSQRT(SINRAD)
      TANRAD = TEMP/COSRAD
C /* CONVERT TO TANGENT
      GM = 1/(DATAN(TANRAD))
C
C              GM = DCOS((1/((DLOG(time)/.4)))**2)
C /* ADJUSTMENT FOR PI SO THAT CHARGE HAS MASS (SEE MASS.FOR)
      LNE2 = DLOG(PI*GM)
C /* NATURAL LOG OF PI*GM 
      TANRAD = 1/LNE2
C /* EXPONENTIAL VALUE OF PI
      ANGLE = DATAN(TANRAD)
C /* ARC TANGENT OF RAD ANGLE
      DEGTAN = ANGLE
C /* CONVERT TO XRAY FLUX
      EXFUNC = DEXP(DEGTAN)
C /* EXPONENTIAL VALUE E2
      ESQR = 1/EXFUNC
C /* VALUE FOR E2
      RETURN
      END
C
C     **************************** CPI.FOR ***************************
C
C     This subroutine is a close approximation for c
C
C                     c = exp(exp(inv(pi)*10))
C
C     ******************************************************************
      SUBROUTINE CPI(C)
 
      DOUBLE PRECISION PI,C
C
C     INITIALIZE PI 
C
      PI = 3.141592654
C /* GIVE C A VALUE
      C = DEXP(DEXP((1./PI)*10.))
C /* VALUE FOR C
      RETURN
      END
C
        subroutine zcells(timestep,inf)
c main routine   should be run for each timestep as a subroutine
c if timestep = 1 then SPUR subroutine will read the polypara.dat file.
c if timestep > 1 then SPUR subroutine will read the TIMENEW.DAT file
c written as a result of the SPUR equations from timestep 0.
c
c Beta values come from MOVES subroutine (input for sunspot (pore)
c movement of active regions, and other random beta values)
c
c This routine (zcells) passes back the percentage of visible pores
c for each polygon for that timestep. These pore values can be used
c to create the evolution map for that timestep and/or used in the target
c model.
c
c The input file polypara.dat is start condition at t = 0 for each polygon.
c The SPUR subroutine writes to unit 9, which should be TIMENEW.DAT
c
        INTEGER*4 timestep, k, LOC, POLYID, icell
        DOUBLE PRECISION S,E,I,R,A,G,M,B,inf(8),polybeta
c
c    For the timestep = 0 read POLYPARA.DAT, 
c    element 1 polyid, 2-8 are S,P,U,R,a,g,m and 9 is BETA
C
C     open polygon parameter file and read title record for timestep 0
C     mina and maxg represent evolution factors, expressed as days,
C
      icell=8
C       icell=1
      IF (timestep.EQ.0) THEN
        OPEN (9,FILE='TIMENEW.DAT')
        OPEN (7,FILE='polypara.dat')
        LOC = 1
        READ(7,30,ERR=300)DUMMY
C        mina = 99
C        maxg = 1

        do 22 k = 1, icell
         LOC = 2
         READ(7,99,ERR=300)POLYID,S,E,I,R,A,G,M,B
C           if(A .LT. mina) mina = A
C           if(G .GT. maxg) maxg = G
         CALL SPUR(POLYID,S,E,I,R,A,G,M,B,inf)
22      continue

        close (7)
        close (9)
      ELSE
        open (18,file='TIMEOLD.DAT')
        open (19,file='TIMENEW.DAT')

         do 24 k = 1, icell
         LOC = 3
         READ(18,99,ERR=300)POLYID,S,E,I,R,A,G,M,B

            if (S .LE. .00) S = .01
            if (E .LE. .00) E = .01
            if (I .LE. .00) I = .01

            call moves(B,polybeta)
            B = polybeta * 10.

C         CALL SPUR(POLYID,S,E,I,R,mina,maxg,M,B,inf)
         CALL SPUR(POLYID,S,E,I,R,A,G,M,B,inf)

24      continue

        close (18)
        close (19)

      ENDIF
30     FORMAT(A1)
99     FORMAT(I2,6(F5.2),F7.2,F6.2)
C
C      write new timenew.dat data to old timeold.dat for next iteration
C
        open (28,file='TIMEOLD.DAT')
        open (29,file='TIMENEW.DAT')

        do 124 k = 1, icell
         LOC = 4
         READ(29,99,ERR=300)POLYID,S,E,I,R,A,G,M,B
         WRITE(28,99,ERR=400)POLYID,S,E,I,R,A,G,M,B
124     continue

        close(28)
        close(29)
c
c
c  debug statment
c
        do 200 k = 1, icell
200        write(*,205) inf(k)
205     format(2X,8(F6.4))
        write(*,206) B
206     format(2x,F6.4)

        goto 999
C
C      Error messages
C

300    write(*,305) LOC
305    format(' zcells - Error reading file at LOC = ',I2)
       goto 999
400    write(*,305) LOC
405    format(' zcells - Error writing file at LOC = ',I2)

999    continue
c       stop
      return
      end


      SUBROUTINE SPUR(POLYID,S,E,I,R,A,G,M,BETAB,INF)
C ***********************    SPUR.F   *****************************
C *      Routine to simulate Olsen and Schaffer's SPUR equations  *
C *      Developed with help of E. Hundtoft., T. Crooks, and      *
C *      M. Brown. This routine writes a parameter file unit 9    *
C *      Differential non-linear coupled equations                *
C *****************************************************************
C       CHARACTER*1 DUMMY
        INTEGER*4 J,JK,K,K2,AGAIN,POLYID
        DOUBLE PRECISION G,INFECT,A,LATENT,M,LIFEXPT,BETA,BETAB,
     +         DELT,CRIT,
     +         MONTHS,S,E,I,R,INF(8)
        DOUBLE PRECISION SBEG,EBEG,IBEG,RBEG,S1,E1,I1,R1,
     +    S2,E2,I2,R2,SBAR,EBAR,IBAR,RBAR,SPOS,EPOS,IPOS,RPOS,
     +    SNEG,ENEG,INEG,RNEG,SHAT,EHAT,IHAT,RHAT,SERR,EERR,IERR,RERR,
     +    SPCT,EPCT,IPCT,RPCT,T,
C         DS,DE,DI,DR,
     +    SAV(11), EAV(11), IAV(11), RAV(11)
C
C     load in parameters for the disease from what is passed down
C     MONTHS = average life of animal
C
      MONTHS = 144.
      LATENT = A/M
      INFECT = G/M
      LIFEXPT = ABS(MONTHS - M/30.)
      SBEG = S
      EBEG = E
      IBEG = I
      RBEG = R
C
C     Inatialize constant variables
C
        DELT = .002
        SAV(1) = SBEG
        EAV(1) = EBEG
        IAV(1) = IBEG
        RAV(1) = RBEG
C
        S1 = SBEG
        E1 = EBEG
        I1 = IBEG
        R1 = RBEG
C
C Initialize first increment
C
        S2 = 1.1 * S1
        E2 = 1.1 * E1
        I2 = 1.1 * I1
        R2 = 1.1 * R1
        BETA = BETAB * 100.
        J = 50
        JK = J / 10
C
C       Print every JK times.
C
        AGAIN = 0
C
C       Outer loop at 530, averages for J iterations, and loads arrays.
C
        DO 530 K=1, J
C
C       Inner loop averages initial and all other values,
C       loop starts at 300 as long as AGAIN = 0.
C
300       CONTINUE

                SBAR = (S1 + S2) / 2
                EBAR = (E1 + E2) / 2
                IBAR = (I1 + I2) / 2
                RBAR = (R1 + R2) / 2

                T = SBAR + EBAR + IBAR + RBAR

                SPOS = T / LIFEXPT
                SNEG = SBAR * (1 / LIFEXPT + BETA * IBAR)
                SHAT = S1 + (SPOS - SNEG) * DELT
                SERR = SHAT - S2
                SPCT = 100 * (SERR / S2)

                EPOS = BETA * SBAR * IBAR
                ENEG = EBAR * (1 / LIFEXPT + 1 / LATENT)
                EHAT = E1 + (EPOS - ENEG) * DELT
                EERR = EHAT - E2
                EPCT = 100 * (EERR / E2)

                IPOS = EBAR / LATENT
                INEG = IBAR * (1 / LIFEXPT + 1 / INFECT)
                IHAT = I1 + (IPOS - INEG) * DELT
                IERR = IHAT - I2
                IPCT = 100 * (IERR / I2)

                RPOS = IBAR / INFECT
                RNEG = RBAR * (1 / LIFEXPT)
                RHAT = R1 + (RPOS - RNEG) * DELT
                RERR = RHAT - R2
                RPCT = 100 * (RERR / R2)

                AGAIN = 0
                CRIT = .00001
                IF (ABS(SPCT) .GT. CRIT) AGAIN = 1
                IF (ABS(EPCT) .GT. CRIT) AGAIN = 1
                IF (ABS(IPCT) .GT. CRIT) AGAIN = 1
                IF (ABS(RPCT) .GT. CRIT) AGAIN = 1

                S2 = (S2 + SHAT) / 2
                E2 = (E2 + EHAT) / 2
                I2 = (I2 + IHAT) / 2
                R2 = (R2 + RHAT) / 2

C
C Jump out of loop if AGAIN=1 and criteria is met
C
          IF (AGAIN .EQ. 1) GOTO 300
C
C We're done so let's load up the arrays for the screen print and the
C the input parameters to be sent to the output file
C
        IF (INT(K/JK) .EQ. K/JK) K2 = K/JK

                SAV(K2) = SBAR
                EAV(K2) = EBAR
                IAV(K2) = IBAR
                RAV(K2) = RBAR

C               DS = (S2 - S1) / DELT
C               DE = (E2 - E1) / DELT
C               DI = (I2 - I1) / DELT
C               DR = (R2 - R1) / DELT
C

        S1 = S2
        E1 = E2
        I1 = I2
        R1 = R2

        S2 = 1.1 * S1
        E2 = 1.1 * E1
        I2 = 1.1 * I1
        R2 = 1.1 * R1

        IF (K .EQ. J) GOTO 540
C
530	CONTINUE
C
C Write to screen for debug and review
C
540     CONTINUE

C       WRITE(*,545) S1,E1,POLYID,I1,R1
C545    FORMAT(' Sunspots (S1) = ',F4.2,/,
C     +        ' Penumbra (E1)      = ',F4.2,'          POLYID =',I3,/,
C     +        ' Umbra (I1)   = ',F4.2,/,
C     +        ' Removed (R1)      = ',F4.2,/)
C       WRITE(*,550) BETAB
C550    FORMAT(' Contact rate (b)  = ',F6.2)
C        WRITE(*,*) ' '
C        WRITE(*,*) '  Incr  Sunspot Penumbra  Umbra   Removed  Total'
C        WRITE(*,*) '  ----- ------- -------  -------  -------  -------'
C        DO 600 L=2, 10
C          T = SAV(L) + EAV(L) + IAV(L) + RAV(L)
C           IF (L .EQ. 2) THEN
C            WRITE(*,660) L - 1, SAV(1), EAV(1), IAV(1), RAV(1), T
C                T = SAV(L) + EAV(L) + IAV(L) + RAV(L)
C            WRITE(*,660) L * JK, SAV(L), EAV(L), IAV(L), RAV(L), T
C           ELSE
C               T = SAV(L) + EAV(L) + IAV(L) + RAV(L)
C            WRITE(*,660) JK * L, SAV(L), EAV(L), IAV(L), RAV(L), T
C           ENDIF
C600     CONTINUE
C660    FORMAT(I5,5(F9.5))
C
C       Write to unit 9 (TIMENEW.DAT) this polygon's output parameters
C
       WRITE(9,99,ERR=900)POLYID,SAV(10),EAV(10),IAV(10),RAV(10),
     +               A,G,M,BETAB
99     FORMAT(I2,6(F5.2),F7.2,F6.2)
C
C       Return the percentage of pores for this polygon
C
        INF(POLYID) = IAV(10)

       GOTO 999
C
C       Error on writing to file
C
900       WRITE(*,*) 'Error on write to unit 9 (SPUR)'

999       CONTINUE
        RETURN
       END

        subroutine moves(B,beta)
C
C  changes to the estimate of beta.
C
        real*8 B,beta
        integer C

        C = int(B)
        beta = ran2(C)

        return
        end

        function ran2(idnum)
c returns a uniform random deviate between 0. and 1.
c set idnum to any negative value to intialize
c or reintialize the sequence (Numerical Recipies)

        dimension ir(42)
        data iff /0/
c
c       initalize variables
c
        m=714025
        ia=1366
        ic=150889
        rm=1./m
c
c       if first time intialize the shuffle table
c
        if (idnum .lt. 0 .or. iff .eq. 0) then
           iff = 1
           idnum = mod(ic-idnum,m)
           do 11 j=1, 42
             idnum = mod(ia*idnum+ic,m)
             ir(j) = idnum
11         continue
           idnum=mod(ia*idnum+ic,m)
           iy=idnum
        endif
c
c this is the start except on initialization
c
        j = 1+(42*iy)/m
c
c unless there is a problem then re-intialize again
c
        if (j .gt. 42 .or. j .lt. 1) then
           iff = 1
           idnum = mod(ic-idnum,m)
           do 12 j=1, 42
             idnum = mod(ia*idnum+ic,m)
             ir(j) = idnum
12         continue
           idnum=mod(ia*idnum+ic,m)
           iy=idnum
        endif
c
c  finsh the deal
c
        iy = ir(j)
        ran2 = iy*rm
        idnum = mod(ia*idnum+ic,m)
        ir(j) = idnum
      return
      end
