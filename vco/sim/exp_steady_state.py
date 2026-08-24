import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_steady_state_experiment():
    print("Running Steady State Amplitude Limiting Experiment...")
    
    netlist = """* Steady State Amplitude Limiting
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ
.include "02_NETLIST/parameters.inc"

.subckt spiral_ind_53ph p1 p2 sub
L_s p1 n_int 53p
R_s n_int p2 0.312
C_sub1 p1 sub 2f
C_sub2 p2 sub 2f
.ends spiral_ind_53ph

Vcc pad_vdd 0 {VDD}
V_half vcc_half 0 {VDD/2}
Vcont ctrl 0 0.5
V_dcont d_ctrl 0 0.0

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

* Add current sensing voltage sources in series with collectors
V_sense1 out_x c1 0
V_sense2 out_y c2 0

X1 c1 out_y tail_node 0 npn13G2 m=4
X2 c2 out_x tail_node 0 npn13G2 m=4

I_tail tail_node 0 1m

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 0.1p 1.6n

.control
run
let i_c1 = i(V_sense1)
let i_c2 = i(V_sense2)
let vdiff = v(out_x) - v(out_y)

wrdata 04_SIMULATION/raw_exp/steady_state.txt vdiff i_c1 i_c2
.endc
.end
"""
    with open(os.path.join(DIR_NETLIST, "exp_steady_state.cir"), "w") as f:
        f.write(netlist)
        
    success = run_ngspice("02_NETLIST/experiments/exp_steady_state.cir")
    
    if success:
        try:
            data = np.loadtxt(os.path.join(DIR_RAW, "steady_state.txt"))
            # Filter for last 200ps
            mask = data[:, 0] > 1.4e-9
            time = data[mask, 0] * 1e12 # ps
            vdiff = data[mask, 1]
            ic1 = data[mask, 3] * 1e3 # mA
            ic2 = data[mask, 5] * 1e3 # mA
            
            fig, ax1 = plt.subplots(figsize=(8, 5))
            
            color1 = 'tab:red'
            ax1.set_xlabel('Time (ps)')
            ax1.set_ylabel('Differential Output Voltage $V_{diff}$ (V)', color=color1)
            ax1.plot(time, vdiff, color=color1, linewidth=2, label='$V_{diff}$')
            ax1.tick_params(axis='y', labelcolor=color1)
            ax1.grid(True)
            
            ax2 = ax1.twinx()
            color2 = 'tab:blue'
            ax2.set_ylabel('Collector Current (mA)', color=color2)
            ax2.plot(time, ic1, color=color2, linewidth=1.5, label='$I_{C1}$')
            ax2.plot(time, ic2, color='tab:cyan', linewidth=1.5, label='$I_{C2}$', linestyle='--')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            plt.title('Steady-State Oscillation and Current Steering')
            fig.tight_layout()
            
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='upper right')
            
            plt.savefig(os.path.join(DIR_FIGURES, "fig_steady_state.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f"Failed to plot steady state data: {e}")

if __name__ == "__main__":
    run_steady_state_experiment()
