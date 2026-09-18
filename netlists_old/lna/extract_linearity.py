import subprocess
import numpy as np
import os
import matplotlib.pyplot as plt

netlist_template = """* 30 GHz LNA Linearity Test
.lib "../../../../junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ

.subckt lna_core in out vdd vss
    X1 c b e vss npn13G2l m=1
    R_bias vdd b 20k
    C_in in b 200f
    L_in in vss 200p
    L_e e vss 50pH
    L_load vdd c 150pH
    C_out c out 150f
.ends

V_vdd vdd 0 1.2
V_vss vss 0 0

* Input Port (50 ohms) with varying power
V1 in_src 0 sin(0 {V_AMP} 30G)
R1 in_src in 50

* Output Port (50 ohms)
R2 out 0 50

X_lna in out vdd vss lna_core

.control
    tran 1p 2n
    wrdata tran_out.txt v(out)
    quit
.endc
.end
"""

pin_dbm_sweep = np.arange(-30, 5, 2)
pout_dbm_list = []
gain_list = []

for pin in pin_dbm_sweep:
    # Convert Pin (dBm) to Voltage amplitude
    # P(W) = V_rms^2 / R -> V_amp = sqrt(P * 50) * sqrt(2) * 2 (source voltage is 2x matched port voltage)
    p_watts = 10**(pin / 10) * 1e-3
    v_amp = np.sqrt(p_watts * 50) * np.sqrt(2) * 2
    
    netlist = netlist_template.replace("{V_AMP}", f"{v_amp}")
    with open("lna_lin_tb.cir", "w") as f:
        f.write(netlist)
        
    subprocess.run(['ngspice', '-b', 'lna_lin_tb.cir'], capture_output=True)
    
    # Extract fundamental tone amplitude at 30 GHz from transient
    data = np.loadtxt("tran_out.txt")
    t = data[:,0]
    v_out = data[:,1]
    
    # Steady state (last 1 ns)
    mask = t > 1e-9
    t_ss = t[mask]
    v_ss = v_out[mask]
    
    # FFT to find fundamental
    N = len(t_ss)
    dt = t_ss[1] - t_ss[0]
    V_fft = np.fft.fft(v_ss)
    freqs = np.fft.fftfreq(N, dt)
    
    idx_30g = np.argmin(np.abs(freqs - 30e9))
    v_out_amp = 2.0 * np.abs(V_fft[idx_30g]) / N
    
    pout_watts = (v_out_amp / np.sqrt(2))**2 / 50
    pout_dbm = 10 * np.log10(pout_watts * 1000)
    
    pout_dbm_list.append(pout_dbm)
    gain_list.append(pout_dbm - pin)

pout_dbm_list = np.array(pout_dbm_list)
gain_list = np.array(gain_list)

# Find P1dB
linear_gain = gain_list[0]
p1db_idx = np.argmin(np.abs(gain_list - (linear_gain - 1.0)))
p1db_in = pin_dbm_sweep[p1db_idx]
p1db_out = pout_dbm_list[p1db_idx]

print(f"Linear Gain: {linear_gain:.2f} dB")
print(f"Input P1dB: {p1db_in:.2f} dBm")
print(f"Output P1dB: {p1db_out:.2f} dBm")
print(f"Estimated IIP3 (IP1dB + 9.6dB): {p1db_in + 9.6:.2f} dBm")

os.makedirs("plots", exist_ok=True)
plt.figure()
plt.plot(pin_dbm_sweep, pout_dbm_list, 'b-o')
plt.plot(pin_dbm_sweep, pin_dbm_sweep + linear_gain, 'r--')
plt.plot(p1db_in, p1db_out, 'ro', markersize=10)
plt.xlabel('Input Power (dBm)')
plt.ylabel('Output Power (dBm)')
plt.title(f'LNA Linearity (P1dB = {p1db_in:.1f} dBm)')
plt.grid(True)
plt.savefig("plots/lna_p1db.png")
