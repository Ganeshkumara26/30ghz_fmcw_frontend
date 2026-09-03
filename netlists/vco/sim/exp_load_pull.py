import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_load_pull_experiment():
    print("Running Load Sensitivity (Load Pull) Experiment...")
    
    cl_list = [10, 50, 100, 200, 500] # fF
    freq_list = []
    vpp_list = []
    
    for cl in cl_list:
        netlist = f"""* Load Sensitivity (CL = {cl}fF)
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

I_ref vdd_ref ref_node {{IREF}}
V_dd vdd_ref 0 {{VDD}}
X_ref ref_node ref_node 0 0 npn13G2 m={{MREF}}
X_tail tail_node ref_node 0 0 npn13G2 m={{MT}}

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

X1 out_x out_y tail_node 0 npn13G2 m=4
X2 out_y out_x tail_node 0 npn13G2 m=4

C_ac_x out_x buf_in_x {{C_AC_COUPLING}}
C_ac_y out_y buf_in_y {{C_AC_COUPLING}}
R_fb_x buf_in_x buf_out_x {{R_FB}}
R_fb_y buf_in_y buf_out_y {{R_FB}}
X_buf_x buf_out_x buf_in_x 0 0 npn13G2 m=1
X_buf_y buf_out_y buf_in_y 0 0 npn13G2 m=1
R_load_x pad_vdd buf_out_x {{R_LOAD}}
R_load_y pad_vdd buf_out_y {{R_LOAD}}

* The Variable Load Capacitance
C_L_x buf_out_x 0 {cl}f
C_L_y buf_out_y 0 {cl}f

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 1p 2n

.control
run
meas tran t1 WHEN v(out_x)=v(out_y) FALL=30
meas tran t2 WHEN v(out_x)=v(out_y) FALL=31
let period = t2 - t1
let freq = 1.0 / period

meas tran vmax MAX v(buf_out_x) FROM=1.5n TO=2.0n
meas tran vmin MIN v(buf_out_x) FROM=1.5n TO=2.0n
let vpp = vmax - vmin

wrdata 04_SIMULATION/raw_exp/load_{cl}fF.txt freq vpp
.endc
.end
"""
        cir_path = os.path.join(DIR_NETLIST, f"exp_load_{cl}fF.cir")
        with open(cir_path, "w") as f:
            f.write(netlist)
            
        success = run_ngspice(f"02_NETLIST/experiments/exp_load_{cl}fF.cir")
        if success:
            try:
                data = np.loadtxt(os.path.join(DIR_RAW, f"load_{cl}fF.txt"))
                f_val = data[1] if data.ndim == 1 else data[0, 1]
                v_val = data[3] if data.ndim == 1 else data[0, 3]
                if f_val > 10e9:
                    freq_list.append(f_val / 1e9)
                    vpp_list.append(v_val)
            except Exception as e:
                print(f"Failed to read {cl}fF: {e}")

    if freq_list:
        fig, ax1 = plt.subplots(figsize=(8, 5))
        
        color1 = 'tab:blue'
        ax1.set_xlabel('Load Capacitance $C_L$ (fF)')
        ax1.set_ylabel('Oscillation Frequency (GHz)', color=color1)
        ax1.plot(cl_list, freq_list, marker='o', color=color1, linewidth=2, label='VCO Frequency')
        ax1.tick_params(axis='y', labelcolor=color1)
        
        # Determine the maximum frequency shift (frequency pushing)
        max_f = max(freq_list)
        min_f = min(freq_list)
        delta_f = max_f - min_f
        
        ax2 = ax1.twinx()
        color2 = 'tab:red'
        ax2.set_ylabel('Buffer Output Voltage Swing $V_{pp}$ (V)', color=color2)
        ax2.plot(cl_list, vpp_list, marker='s', color=color2, linewidth=2, linestyle='--', label='Output Swing')
        ax2.tick_params(axis='y', labelcolor=color2)
        
        f0_val = freq_list[0]
        plt.title(f'Buffer Reverse Isolation & Load Driving\nMax $\Delta f$ = {delta_f*1e3:.1f} MHz = {(delta_f/f0_val)*100:.2f}% of {f0_val:.1f} GHz')
        fig.tight_layout()
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper center')
        
        plt.grid(True)
        plt.savefig(os.path.join(DIR_FIGURES, "fig_load_pull.png"), dpi=300)
        plt.close()

if __name__ == "__main__":
    run_load_pull_experiment()
