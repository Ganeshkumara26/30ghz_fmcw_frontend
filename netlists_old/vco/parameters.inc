* VCO 30 GHz Target Parameters

* Supply Voltage (Reduced to lower AM-PM conversion per Razavi noise argument)
.param VDD=0.95

* Tail Current Bias (Halved from original to reduce noise/swing tradeoff)
.param IREF=400u

* Current Mirror Ratios (Quadrupled multiplicity to reduce flicker noise contribution)
.param MREF=4
.param MT=10

* Switched Capacitor Bias (Pull-up resistors to keep switch nodes at VDD/2)
.param R_PULLUP=10k
.param VDD_HALF='VDD/2'

* Buffer Configuration (Self-biased CE)
.param C_AC_COUPLING=500f
.param R_FB=10k
.param R_LOAD=200
