import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_neg_res_experiment():
    print("Running Negative Resistance Characterization...")
    
    # We will sweep I_bias for a fixed m=4, and sweep m for a fixed I_bias=1mA
    
    ibias_list = [0.2e-3, 0.4e-3, 0.8e-3, 1.2e-3]
    m_fixed = 4
    
    plt.figure(figsize=(8, 5))
    
    for ibias in ibias_list:
        netlist = f"""* Negative Resistance Sweep
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ

V_bias tail 0 {ibias}
V_cm1 cm1 0 0.95
V_cm2 cm2 0 0.95

* Use large inductors to feed DC bias to collectors without shorting AC
L_bias1 cm1 out_x 10m
L_bias2 cm2 out_y 10m

I_ac out_y out_x AC 1

X1 out_x out_y tail 0 npn13G2 m={m_fixed}
X2 out_y out_x tail 0 npn13G2 m={m_fixed}

.control
op
ac lin 500 25G 35G

let v_diff = v(out_x) - v(out_y)
let z_in = v_diff
let g_in = real(1 / z_in)

wrdata 04_SIMULATION/raw_exp/negres_{int(ibias*1e6)}uA.txt g_in
.endc
.end
"""
        cir_path = os.path.join(DIR_NETLIST, f"exp_negres_{int(ibias*1e6)}uA.cir")
        with open(cir_path, "w") as f:
            f.write(netlist)
            
        success = run_ngspice(f"02_NETLIST/experiments/exp_negres_{int(ibias*1e6)}uA.cir")
        if success:
            try:
                data = np.loadtxt(os.path.join(DIR_RAW, f"negres_{int(ibias*1e6)}uA.txt"))
                freq = data[:, 0] / 1e9
                g_in = data[:, 1]
                plt.plot(freq, -g_in * 1e3, linewidth=2, label=f'$I_{{bias}}$ = {int(ibias*1e6)} $\mu$A')
            except Exception as e:
                print(f"Error plotting {ibias}A: {e}")

    plt.xlabel('Frequency (GHz)')
    plt.ylabel('Negative Conductance $-G_{in}$ (mS)')
    plt.title(f'Cross-Coupled Pair Negative Conductance vs Frequency (m={m_fixed})')
    # Target Rp from our tank experiment was ~110 Ohms, so Gp = 1/110 ~ 9 mS.
    # The required -G_in for 3x startup margin is > 3*Gp = 27 mS.
    plt.axhline(y=9.1, color='r', linestyle='--', label='Tank Loss $G_p$ (~110 $\Omega$)')
    plt.axhline(y=27.3, color='black', linestyle=':', label='Required Margin ($3 G_p$)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DIR_FIGURES, "fig_negres_ibias.png"), dpi=300)
    plt.close()
    
    # -------------------------------------------------------------
    # Now sweep multiplicity m for a fixed Ibias
    
    ibias_fixed = 0.8e-3
    m_list = [1, 2, 4, 8]
    
    plt.figure(figsize=(8, 5))
    for m in m_list:
        netlist = f"""* Negative Resistance Sweep m
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ

V_bias tail 0 {ibias_fixed}
V_cm1 cm1 0 0.95
V_cm2 cm2 0 0.95

L_bias1 cm1 out_x 10m
L_bias2 cm2 out_y 10m

I_ac out_y out_x AC 1

X1 out_x out_y tail 0 npn13G2 m={m}
X2 out_y out_x tail 0 npn13G2 m={m}

.control
op
ac lin 500 25G 35G

let v_diff = v(out_x) - v(out_y)
let g_in = real(1 / v_diff)

wrdata 04_SIMULATION/raw_exp/negres_m{m}.txt g_in
.endc
.end
"""
        cir_path = os.path.join(DIR_NETLIST, f"exp_negres_m{m}.cir")
        with open(cir_path, "w") as f:
            f.write(netlist)
            
        success = run_ngspice(f"02_NETLIST/experiments/exp_negres_m{m}.cir")
        if success:
            try:
                data = np.loadtxt(os.path.join(DIR_RAW, f"negres_m{m}.txt"))
                freq = data[:, 0] / 1e9
                g_in = data[:, 1]
                plt.plot(freq, -g_in * 1e3, linewidth=2, label=f'm = {m}')
            except:
                pass

    plt.xlabel('Frequency (GHz)')
    plt.ylabel('Negative Conductance $-G_{in}$ (mS)')
    plt.title(f'Cross-Coupled Pair Negative Conductance vs Frequency ($I_{{bias}}$ = 800 $\mu$A)')
    plt.axhline(y=9.1, color='r', linestyle='--', label='Tank Loss $G_p$ (~110 $\Omega$)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DIR_FIGURES, "fig_negres_m.png"), dpi=300)
    plt.close()

if __name__ == "__main__":
    run_neg_res_experiment()
