import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_tuning_experiment():
    print("Running Tuning Curve Experiment...")
    
    # We will simulate the VCO with the switch OFF (d_ctrl = 0) and ON (d_ctrl = 1.2)
    # For each, we sweep ctrl from 0V to 1V in steps of 0.2V to plot the two tuning curves
    
    v_ctrl_list = np.arange(0.0, 1.1, 0.2)
    d_ctrl_list = [0.0, 1.2]
    
    results = {d_ctrl: {"v_ctrl": [], "freq": []} for d_ctrl in d_ctrl_list}
    
    for d_ctrl in d_ctrl_list:
        for v_ctrl in v_ctrl_list:
            netlist = f"""* Tuning Curve (d_ctrl={d_ctrl}, v_ctrl={v_ctrl:.2f})
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
Vcont ctrl 0 {v_ctrl:.2f}
V_dcont d_ctrl 0 {d_ctrl}

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

* Ideal tail current equivalent to the current mirror
I_tail tail_node 0 1m

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 1p 2n

.control
run
meas tran t1 WHEN v(out_x)=v(out_y) FALL=30
meas tran t2 WHEN v(out_x)=v(out_y) FALL=31
let period = t2 - t1
let freq = 1.0 / period

wrdata 04_SIMULATION/raw_exp/tuning_{int(d_ctrl)}_{int(v_ctrl*10)}.txt freq
.endc
.end
"""
            cir_path = os.path.join(DIR_NETLIST, f"exp_tuning_{int(d_ctrl)}_{int(v_ctrl*10)}.cir")
            with open(cir_path, "w") as f:
                f.write(netlist)
                
            success = run_ngspice(f"02_NETLIST/experiments/exp_tuning_{int(d_ctrl)}_{int(v_ctrl*10)}.cir")
            if success:
                try:
                    data = np.loadtxt(os.path.join(DIR_RAW, f"tuning_{int(d_ctrl)}_{int(v_ctrl*10)}.txt"))
                    freq = data[1] if data.ndim == 1 else data[0, 1]
                    if freq > 10e9:
                        results[d_ctrl]["v_ctrl"].append(v_ctrl)
                        results[d_ctrl]["freq"].append(freq)
                except:
                    pass

    plt.figure(figsize=(8, 5))
    try:
        # Plot sub-band 0 (d_ctrl = 0.0)
        vc0 = results[0.0]["v_ctrl"]
        f0 = np.array(results[0.0]["freq"]) / 1e9
        if vc0:
            plt.plot(vc0, f0, linewidth=2, marker='o', label="Sub-band 0 (Switch OFF)", color='tab:blue')
            
        # Plot sub-band 1 (d_ctrl = 1.2)
        vc1 = results[1.2]["v_ctrl"]
        f1 = np.array(results[1.2]["freq"]) / 1e9
        if vc1:
            plt.plot(vc1, f1, linewidth=2, marker='s', label="Sub-band 1 (Switch ON)", color='tab:orange')
            
        # Extract f_min and f_max from the simulated data
        all_freqs = []
        if vc0:
            all_freqs.extend(f0)
        if vc1:
            all_freqs.extend(f1)
            
        f_min = np.min(all_freqs)
        f_max = np.max(all_freqs)
        
        plt.axhspan(f_min, f_max, color='gray', alpha=0.2, label=f'Total Range: {f_min:.2f} - {f_max:.2f} GHz')
        
        plt.xlabel('Varactor Tuning Voltage $V_{ctrl}$ (V)')
        plt.ylabel('Oscillation Frequency (GHz)')
        plt.title('VCO Tuning Curves (Sub-bands)')
        plt.grid(True)
        plt.legend(loc='lower right')
        plt.savefig(os.path.join(DIR_FIGURES, "fig_tuning_curves.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Failed to plot tuning data: {e}")

if __name__ == "__main__":
    run_tuning_experiment()
