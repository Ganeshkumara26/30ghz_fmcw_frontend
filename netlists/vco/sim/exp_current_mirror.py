import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_current_mirror_experiment():
    print("Running Current Mirror Verification...")
    
    netlist = """* Current Mirror Verification
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ

.param IREF=400u
.param MREF=4
.param MT=10

I_ref vdd_ref ref_node {IREF}
V_dd vdd_ref 0 0.95

* Diode connected reference
X_ref ref_node ref_node 0 0 npn13G2 m={MREF}

* Tail current source
X_tail tail_node ref_node 0 0 npn13G2 m={MT}

* Sweep the voltage at the tail node (mimicking VCO common-mode variation)
V_tail tail_node 0 0.5

.dc V_tail 0.1 0.95 0.05 temp -40 120 40

.control
run
let i_tail = -i(V_tail)
let ratio = i_tail / 400e-6

wrdata 04_SIMULATION/raw_exp/mirror_dc.txt i_tail ratio
.endc
.end
"""
    with open(os.path.join(DIR_NETLIST, "exp_current_mirror.cir"), "w") as f:
        f.write(netlist)
        
    success = run_ngspice("02_NETLIST/experiments/exp_current_mirror.cir")
    if success:
        try:
            data = np.loadtxt(os.path.join(DIR_RAW, "mirror_dc.txt"))
            
            # The dc sweep has outer loop Temp, inner loop V_tail
            # Let's count how many temp steps: -40, 0, 40, 80, 120 (5 steps)
            # data has shape (N, 5) ? No, wrdata outputs for each temp sweep
            # The columns are v_tail1 i_tail1 ratio1 v_tail2 i_tail2 ratio2 ...
            num_temps = data.shape[1] // 4
            temps = [-40, 0, 40, 80, 120]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
            for i in range(num_temps):
                v_tail = data[:, 4*i]
                i_tail = data[:, 4*i + 1] * 1000 # convert to mA
                ratio = data[:, 4*i + 3]
                
                ax1.plot(v_tail, ratio, linewidth=2, label=f'{temps[i]}$^\circ$C')
                ax2.plot(v_tail, i_tail, linewidth=2, label=f'{temps[i]}$^\circ$C')
                
            ax1.axhline(y=2.5, color='k', linestyle='--', label='Ideal Ratio (2.5)')
            ax1.axvspan(0.5, 0.8, color='grey', alpha=0.2, label='VCO CM Region')
            ax1.set_ylabel('Mirror Ratio ($I_{tail} / I_{ref}$)')
            ax1.set_title('Current Mirror Tracking and Delivery vs Tail Voltage')
            ax1.grid(True)
            ax1.legend(loc='lower right')
            
            ax2.axhline(y=1.0, color='k', linestyle='--', label='Ideal Current (1.0 mA)')
            ax2.axvspan(0.5, 0.8, color='grey', alpha=0.2)
            ax2.set_xlabel('Tail Node Voltage $V_{CM}$ (V)')
            ax2.set_ylabel('Delivered $I_{tail}$ (mA)')
            ax2.grid(True)
            ax2.legend(loc='lower right')
            
            fig.tight_layout()
            plt.savefig(os.path.join(DIR_FIGURES, "fig_current_mirror.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f"Failed to plot Current Mirror data: {e}")

if __name__ == "__main__":
    run_current_mirror_experiment()
