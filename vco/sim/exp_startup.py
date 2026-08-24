import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_startup_experiment():
    print("Running Startup Dynamics Experiment...")
    
    netlist = """* Startup Dynamics
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

I_ref vdd_ref ref_node {IREF}
V_dd vdd_ref 0 {VDD}
X_ref ref_node ref_node 0 0 npn13G2 m={MREF}
X_tail tail_node ref_node 0 0 npn13G2 m={MT}

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

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 0.5p 3n

.control
run
wrdata 04_SIMULATION/raw_exp/startup.txt v(out_x) v(out_y)
.endc
.end
"""
    with open(os.path.join(DIR_NETLIST, "exp_startup.cir"), "w") as f:
        f.write(netlist)
        
    success = run_ngspice("02_NETLIST/experiments/exp_startup.cir")
    
    if success:
        try:
            data = np.loadtxt(os.path.join(DIR_RAW, "startup.txt"))
            time = data[:, 0] * 1e9
            vx = data[:, 1]
            vy = data[:, 3]
            vdiff = vx - vy
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
            
            ax1.plot(time, vx, color='tab:red', label='$V_{out,x}$', linewidth=1)
            ax1.plot(time, vy, color='tab:blue', label='$V_{out,y}$', linewidth=1, alpha=0.7)
            ax1.set_ylabel('Absolute Voltage (V)')
            ax1.set_title('Oscillator Startup Dynamics (Single-Ended)')
            ax1.grid(True)
            ax1.legend(loc='lower right')
            
            # Extract t_startup
            steady_mask = time > 2.5
            if np.any(steady_mask):
                ss_vdiff = vdiff[steady_mask]
                vpp_ss = np.max(ss_vdiff) - np.min(ss_vdiff)
                target_amp = 0.9 * (vpp_ss / 2)
                startup_idx = np.where(vdiff > target_amp)[0]
                if len(startup_idx) > 0:
                    t_startup = time[startup_idx[0]]
                    ax2.axvline(x=t_startup, color='k', linestyle=':', label=f'$t_{{startup}}$ = {t_startup:.2f} ns')
                    ax2.annotate(f'Startup time to 90% amplitude = {t_startup*1000:.0f} ps',
                                 xy=(t_startup, target_amp), xytext=(t_startup + 0.2, target_amp),
                                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
            
            ax2.plot(time, vdiff, color='tab:green', linewidth=1, label='$V_{diff}$')
            ax2.set_xlabel('Time (ns)')
            ax2.set_ylabel('Differential Voltage (V)')
            ax2.set_title('Oscillator Startup Dynamics (Differential)')
            ax2.grid(True)
            ax2.legend(loc='lower right')
            
            fig.tight_layout()
            plt.savefig(os.path.join(DIR_FIGURES, "fig_startup.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f"Failed to plot startup data: {e}")

if __name__ == "__main__":
    run_startup_experiment()
