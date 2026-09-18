import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_pvt_experiment():
    print("Running PVT Analysis Experiment...")
    
    vdd_list = [0.9, 0.95, 1.0]
    temp_list = [-40, 27, 85, 120]
    
    results = {vdd: {"temp": [], "freq": [], "vpp": []} for vdd in vdd_list}
    
    for vdd in vdd_list:
        for temp in temp_list:
            netlist = f"""* PVT Analysis (VDD={vdd}, Temp={temp})
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ
.include "02_NETLIST/parameters.inc"

.subckt spiral_ind_53ph p1 p2 sub
L_s p1 n_int 53p
R_s n_int p2 0.312
C_sub1 p1 sub 2f
C_sub2 p2 sub 2f
.ends spiral_ind_53ph

Vcc pad_vdd 0 {vdd}
V_half vcc_half 0 {vdd/2}
Vcont ctrl 0 0.5
V_dcont d_ctrl 0 0.0

I_ref vdd_ref ref_node {{IREF}}
V_dd vdd_ref 0 {vdd}
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

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5 temp={temp}
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

wrdata 04_SIMULATION/raw_exp/pvt_{int(vdd*100)}_{temp}.txt freq vpp
.endc
.end
"""
            cir_path = os.path.join(DIR_NETLIST, f"exp_pvt_{int(vdd*100)}_{temp}.cir")
            with open(cir_path, "w") as f:
                f.write(netlist)
                
            success = run_ngspice(f"02_NETLIST/experiments/exp_pvt_{int(vdd*100)}_{temp}.cir")
            if success:
                try:
                    data = np.loadtxt(os.path.join(DIR_RAW, f"pvt_{int(vdd*100)}_{temp}.txt"))
                    f_val = data[1] if data.ndim == 1 else data[0, 1]
                    v_val = data[3] if data.ndim == 1 else data[0, 3]
                    if f_val > 10e9:
                        results[vdd]["temp"].append(temp)
                        results[vdd]["freq"].append(f_val / 1e9)
                        results[vdd]["vpp"].append(v_val)
                except Exception as e:
                    print(f"Failed to read VDD={vdd}, Temp={temp}: {e}")

    # Plotting
    fig, ax1 = plt.subplots(figsize=(8, 5))
    color1 = 'tab:blue'
    ax1.set_xlabel('Temperature ($^\circ$C)')
    ax1.set_ylabel('Oscillation Frequency (GHz)', color=color1)
    
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('Buffer Output Swing $V_{pp}$ (V)', color=color2)
    
    markers = {0.9: 'v', 0.95: 'o', 1.0: '^'}
    linestyles = {0.9: ':', 0.95: '-', 1.0: '--'}
    
    for vdd in vdd_list:
        temps = results[vdd]["temp"]
        freqs = results[vdd]["freq"]
        vpps = results[vdd]["vpp"]
        if temps:
            ax1.plot(temps, freqs, color=color1, marker=markers[vdd], linestyle=linestyles[vdd], linewidth=2, label=f'Freq (VDD={vdd}V)')
            ax2.plot(temps, vpps, color=color2, marker=markers[vdd], linestyle=linestyles[vdd], linewidth=2, label=f'Vpp (VDD={vdd}V)')
            
    ax1.tick_params(axis='y', labelcolor=color1)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    plt.title('PVT Analysis: VCO Robustness over Temperature and Supply')
    fig.tight_layout()
    
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='center left', bbox_to_anchor=(1.15, 0.5))
    
    ax1.grid(True)
    plt.savefig(os.path.join(DIR_FIGURES, "fig_pvt.png"), dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    run_pvt_experiment()
