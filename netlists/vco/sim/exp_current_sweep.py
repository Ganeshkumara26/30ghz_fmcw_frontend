import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_current_sweep_experiment():
    print("Running Current Optimization Sweep...")
    
    ibias_sweep = np.arange(0.2e-3, 1.3e-3, 0.1e-3)
    freq_list = []
    vpp_list = []
    valid_i = []

    for ibias in ibias_sweep:
        netlist = f"""* Bias Current Sweep (Ideal Source)
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ

.include "02_NETLIST/parameters.inc"

.subckt spiral_ind_53ph p1 p2 sub
L_s p1 n_int 53p
R_s n_int p2 0.312
C_sub1 p1 sub 2f
C_sub2 p2 sub 2f
.ends spiral_ind_53ph

Vcc pad_vdd 0 {{VDD}}
V_half vcc_half 0 {{VDD/2}}
Vcont ctrl 0 0.5
V_dcont d_ctrl 0 0.0

* Tank
X_ind1 pad_vdd out_x 0 spiral_ind_53ph
X_ind2 pad_vdd out_y 0 spiral_ind_53ph
C_var1 out_x 0 C='40f - 30f * v(ctrl)'
C_var2 out_y 0 C='40f - 30f * v(ctrl)'
X_cbase_x out_x 0 cap_cmim l=17.11u w=17.11u
X_cbase_y out_y 0 cap_cmim l=17.11u w=17.11u
X_cswitch_x out_x node_n cap_cmim l=9.35u w=9.35u
X_cswitch_y out_y node_m cap_cmim l=9.35u w=9.35u
X_switch node_n d_ctrl node_m 0 npn13G2
R_pullup_n node_n vcc_half 10k
R_pullup_m node_m vcc_half 10k

* Core (m=4)
X1 out_x out_y tail 0 npn13G2 m=4
X2 out_y out_x tail 0 npn13G2 m=4

* Ideal Current Source
I_tail tail 0 {ibias}

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 0.1p 1.5n

.control
run
* measure freq and swing
meas tran t1 WHEN v(out_x)=v(out_y) FALL=20
meas tran t2 WHEN v(out_x)=v(out_y) FALL=21
let period = t2 - t1
let freq = 1.0 / period
meas tran vmax MAX v(out_x) FROM=1n TO=1.5n
meas tran vmin MIN v(out_x) FROM=1n TO=1.5n
let vpp = vmax - vmin

wrdata 04_SIMULATION/raw_exp/bias_{int(ibias*1e6)}uA.txt freq vpp
.endc
.end
"""
        cir_path = os.path.join(DIR_NETLIST, f"exp_bias_{int(ibias*1e6)}uA.cir")
        with open(cir_path, "w") as f:
            f.write(netlist)
            
        success = run_ngspice(f"02_NETLIST/experiments/exp_bias_{int(ibias*1e6)}uA.cir")
        if success:
            try:
                data = np.loadtxt(os.path.join(DIR_RAW, f"bias_{int(ibias*1e6)}uA.txt"))
                f_val = data[1] if data.ndim == 1 else data[0, 1]
                v_val = data[3] if data.ndim == 1 else data[0, 3]
                if f_val > 10e9 and v_val > 0.05:  # ensure it actually oscillated
                    freq_list.append(f_val)
                    vpp_list.append(v_val)
                    valid_i.append(ibias)
            except Exception as e:
                pass

    if valid_i:
        fig, ax1 = plt.subplots(figsize=(8,5))
        color = 'tab:red'
        ax1.set_xlabel('Tail Bias Current ($\mu$A)')
        ax1.set_ylabel('Oscillation Frequency (GHz)', color=color)
        ax1.plot(np.array(valid_i)*1e6, np.array(freq_list)/1e9, color=color, linewidth=2, marker='o')
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()  
        color = 'tab:blue'
        ax2.set_ylabel('Output Voltage Swing ($V_{pp}$)', color=color)  
        ax2.plot(np.array(valid_i)*1e6, np.array(vpp_list), color=color, linewidth=2, marker='s')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.axhline(y=0.3, color='k', linestyle='--', label='Min Required Swing (300mV)')
        ax2.legend(loc='lower right')

        plt.title('VCO Frequency and Swing vs Bias Current (Ideal Source)')
        fig.tight_layout()  
        plt.grid(True)
        plt.savefig(os.path.join(DIR_FIGURES, "fig_bias_sweep.png"), dpi=300)
        plt.close()

if __name__ == "__main__":
    run_current_sweep_experiment()
