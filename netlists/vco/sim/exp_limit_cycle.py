import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_output_power_experiment():
    print("Running Output Power & Limit Cycle Experiment...")
    
    # 1. Transient simulation to measure RMS output voltage and calculate Pout in dBm.
    # 2. Extract and plot the steady-state trajectory limit-cycle.
    
    netlist = """* Limit Cycle and Output Power
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

C_ac_x out_x buf_in_x {C_AC_COUPLING}
C_ac_y out_y buf_in_y {C_AC_COUPLING}
R_fb_x buf_in_x buf_out_x {R_FB}
R_fb_y buf_in_y buf_out_y {R_FB}
X_buf_x buf_out_x buf_in_x 0 0 npn13G2 m=1
X_buf_y buf_out_y buf_in_y 0 0 npn13G2 m=1
R_load_x pad_vdd buf_out_x {R_LOAD}
R_load_y pad_vdd buf_out_y {R_LOAD}

* DC blocking and 50 ohm load for Pout measurement
C_block_x buf_out_x rf_out_x 1p
C_block_y buf_out_y rf_out_y 1p
R_50_x rf_out_x 0 50
R_50_y rf_out_y 0 50

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 0.2p 3n

.control
run
* 1. Calculate Pout from transient
meas tran vrms_x RMS v(rf_out_x) FROM=2n TO=3n
meas tran vrms_y RMS v(rf_out_y) FROM=2n TO=3n
let pout_w_x = (vrms_x * vrms_x) / 50
let pout_dbm_x = 10 * log10(pout_w_x * 1000)
wrdata 04_SIMULATION/raw_exp/pout.txt pout_dbm_x vrms_x

* 2. Save trajectory
wrdata sim/raw_results/raw_exp/vco_traj.txt v(out_x) v(out_y)
.endc
.end
"""
    with open(os.path.join(DIR_NETLIST, "exp_limit_cycle.cir"), "w") as f:
        f.write(netlist)
        
    success = run_ngspice("src/netlist/experiments/exp_limit_cycle.cir")
    if success:
        try:
            # Read Pout
            pout_data = np.loadtxt(os.path.join(DIR_RAW, "pout.txt"))
            pout_dbm = pout_data[1] if pout_data.ndim == 1 else pout_data[0, 1]
            vrms = pout_data[3] if pout_data.ndim == 1 else pout_data[0, 3]
            vpp_approx = vrms * 2 * np.sqrt(2)
            
            # Read Trajectory
            data = np.loadtxt(os.path.join(DIR_RAW, "vco_traj.txt"))
            t = data[:, 0]
            mask = t > 2.5e-9 # use late steady state
            t = t[mask]
            vx = data[mask, 1]
            vy = data[mask, 3]
            v_diff = vx - vy
            
            # Extract single period via positive zero crossings
            crossings = np.where((v_diff[:-1] < 0) & (v_diff[1:] >= 0))[0]
            idx1, idx2 = crossings[-2], crossings[-1]
            t_cyc = t[idx1:idx2] - t[idx1]
            v_cyc = v_diff[idx1:idx2]
            f0 = 1.0 / t_cyc[-1]
            w0 = 2.0 * np.pi * f0
            
            # Plot Limit Cycle
            fig, ax1 = plt.subplots(figsize=(8, 5))
            color1 = 'tab:blue'
            ax1.set_xlabel('Time normalized to period (t/T)')
            ax1.set_ylabel('Differential Voltage $V_{diff}$ (V)', color=color1)
            ax1.plot(t_cyc / t_cyc[-1], v_cyc, color=color1, linewidth=2, label='Trajectory')
            ax1.tick_params(axis='y', labelcolor=color1)
            
            plt.title(f'Steady-State Limit Cycle\\n$P_{{out}}$ = {pout_dbm:.2f} dBm | Freq = {f0/1e9:.3f} GHz')
            fig.tight_layout()
            
            plt.grid(True)
            plt.savefig(os.path.join(DIR_FIGURES, "fig_limit_cycle.png"), dpi=300)
            plt.close()
            
            print(f"Pout = {pout_dbm:.2f} dBm")
            print(f"Freq: {f0/1e9:.3f} GHz")
        except Exception as e:
            print(f"Failed to plot phase noise data: {e}")

if __name__ == "__main__":
    run_output_power_experiment()
