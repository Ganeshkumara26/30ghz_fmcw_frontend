import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_switch_bias_experiment():
    print("Running Switched-Capacitor Biasing Experiment...")
    
    # We will simulate the VCO with the switch OFF (d_ctrl = 0)
    # Case 1: Switch node biased at VDD/2 (Razavi method)
    # Case 2: Switch node floating or pulled to GND
    
    cases = [
        {"name": "VDD_Half", "r_pullup": "vcc_half", "label": "$V_{DD}/2$ Bias"},
        {"name": "GND", "r_pullup": "0", "label": "GND Bias"}
    ]
    
    for case in cases:
        netlist = f"""* Switch Biasing Comparison ({case['name']})
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

* Use 800uA reference to push the VCO into high-swing regime to demonstrate the failure mechanism clearly
I_ref vdd_ref ref_node 800u
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

* The pull-up resistors
R_pullup_n node_n {case['r_pullup']} 10k
R_pullup_m node_m {case['r_pullup']} 10k

X1 out_x out_y tail_node 0 npn13G2 m=4
X2 out_y out_x tail_node 0 npn13G2 m=4

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 1p 2n

.control
run
* Evaluate Vbc of the switch. 
* The switch is an NPN: collector=node_n, base=d_ctrl
let vbc = v(d_ctrl) - v(node_n)

* We want to save the transient waveform of Vbc to see if it goes positive (forward biased)
wrdata 04_SIMULATION/raw_exp/switch_{case['name']}.txt vbc
.endc
.end
"""
        cir_path = os.path.join(DIR_NETLIST, f"exp_switch_{case['name']}.cir")
        with open(cir_path, "w") as f:
            f.write(netlist)
            
        run_ngspice(f"02_NETLIST/experiments/exp_switch_{case['name']}.cir")

    plt.figure(figsize=(8, 5))
    try:
        data_vdd = np.loadtxt(os.path.join(DIR_RAW, "switch_VDD_Half.txt"))
        data_gnd = np.loadtxt(os.path.join(DIR_RAW, "switch_GND.txt"))
        
        # Plot only the steady-state portion (last 100ps)
        mask_vdd = data_vdd[:, 0] > 1.8e-9
        mask_gnd = data_gnd[:, 0] > 1.8e-9
        
        plt.plot(data_vdd[mask_vdd, 0]*1e9, data_vdd[mask_vdd, 1], linewidth=2, label="$V_{DD}/2$ Bias", color='tab:blue')
        plt.plot(data_gnd[mask_gnd, 0]*1e9, data_gnd[mask_gnd, 1], linewidth=2, label="GND Bias", color='tab:red')
        
        plt.axhline(y=0.6, color='k', linestyle='--', label='Forward Bias Threshold (0.6V)')
        
        # Annotate peak VBC values
        max_vbc_vdd = np.max(data_vdd[mask_vdd, 1])
        max_vbc_gnd = np.max(data_gnd[mask_gnd, 1])
        
        plt.annotate(f'Peak $V_{{BC}}$ = {max_vbc_gnd:+.2f} V\nForward-bias threshold $\\approx$ 0.60 V', 
                     xy=(1.9, max_vbc_gnd), xytext=(1.9, max_vbc_gnd + 0.1),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5), color='tab:red')
        
        plt.annotate(f'Maximum $V_{{BC}}$ = {max_vbc_vdd:+.2f} V\nMargin = {0.60 - max_vbc_vdd:.2f} V', 
                     xy=(1.9, max_vbc_vdd), xytext=(1.9, max_vbc_vdd - 0.2),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5), color='tab:blue')
        
        plt.xlabel('Time (ns)')
        plt.ylabel('Switch Base-Collector Voltage $V_{BC}$ (V)')
        plt.title('Switch Transistor $V_{BC}$ during High-Swing Oscillation (Switch OFF)')
        plt.grid(True)
        plt.legend(loc='lower right')
        plt.savefig(os.path.join(DIR_FIGURES, "fig_switch_bias.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Failed to plot switch bias data: {e}")

if __name__ == "__main__":
    run_switch_bias_experiment()
