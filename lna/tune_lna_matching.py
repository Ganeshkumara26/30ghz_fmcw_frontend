import subprocess
import numpy as np

netlist_template = """* LNA Matching Tune
.lib "../../../../junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ

.subckt lna_core in out vdd vss
    X1 c b e vss npn13G2l m=1
    R_bias vdd b 20k
    
    * Input Matching
    C_in in node_x {C_IN}f
    L_in node_x b {L_IN}p
    
    L_e e vss 50pH
    L_load vdd c 150pH
    C_out c out 150f
.ends

V_vdd vdd 0 1.2
V_vss vss 0 0

V1 in 0 dc 0 ac 1 portnum=1 z0=50
V2 out 0 dc 0 ac 0 portnum=2 z0=50

X_lna in out vdd vss lna_core

.control
    sp dec 50 20G 40G 0
    let f30 = 30G
    let freq_diff = abs(frequency - f30)
    let min_diff = vecmin(freq_diff)
    
    * Write out S11 magnitude at 30GHz
    wrdata s11_out.txt S_1_1 S_2_1
    quit
.endc
.end
"""

best_s11 = 0
best_params = (0, 0)
best_s21 = 0

# Sweep Cin from 20f to 300f
# Sweep Lin from 10p to 400p
C_sweep = np.arange(20, 300, 20)
L_sweep = np.arange(10, 400, 20)

print("Tuning LNA Input Matching Network (S11 @ 30GHz)...")

for C in C_sweep:
    for L in L_sweep:
        netlist = netlist_template.replace("{C_IN}", str(C)).replace("{L_IN}", str(L))
        with open("lna_tune.cir", "w") as f:
            f.write(netlist)
        
        subprocess.run(['ngspice', '-b', 'lna_tune.cir'], capture_output=True)
        
        try:
            data = np.loadtxt("s11_out.txt")
            freq = data[:,0]
            idx_30g = np.argmin(np.abs(freq - 30e9))
            
            s11_re = data[idx_30g, 1]
            s11_im = data[idx_30g, 2]
            s11_mag = np.sqrt(s11_re**2 + s11_im**2)
            s11_db = 20 * np.log10(s11_mag)
            
            s21_re = data[idx_30g, 3]
            s21_im = data[idx_30g, 4]
            s21_mag = np.sqrt(s21_re**2 + s21_im**2)
            s21_db = 20 * np.log10(s21_mag)
            
            if s11_db < best_s11:
                best_s11 = s11_db
                best_params = (C, L)
                best_s21 = s21_db
                print(f"New Best! C={C}fF, L={L}pH -> S11={s11_db:.2f} dB, S21={s21_db:.2f} dB")
        except Exception as e:
            pass

print(f"\nOptimization Complete.")
print(f"Optimal Matching: C_in = {best_params[0]} fF, L_in = {best_params[1]} pH")
print(f"Resulting S11 = {best_s11:.2f} dB, S21 = {best_s21:.2f} dB")
