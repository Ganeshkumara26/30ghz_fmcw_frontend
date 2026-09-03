import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_dc_experiment():
    print("Running DC Characterization...")
    # Netlist for DC Sweep
    netlist = """* Device DC Characterization
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
VCE c 0 0.95
VBE b 0 0.8
X1 c b 0 0 npn13G2

.dc VBE 0.75 0.95 0.005 VCE 0.5 1.5 0.5

.control
run
* We will just do a single VBE sweep for gm/Ic and plot families of Ic vs VCE
* Let's save Ic, Ib for different VCE
* Actually, it's easier to do two separate DC sweeps.
.endc
.end
"""
    # Let's write two separate netlists: one for VBE sweep, one for VCE sweep.
    netlist_vbe = """* Device DC Characterization - VBE Sweep
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
VCE c 0 0.95
VBE b 0 0.8
X1 c b 0 0 npn13G2

.dc VBE 0.70 0.95 0.005

.control
run
let ic = -i(VCE)
let gm = deriv(ic)
let gm_ic = gm / ic
* ro = 1 / deriv(ic) with respect to vce, but here we sweep VBE. We will extract ro in VCE sweep.
wrdata 04_SIMULATION/raw_exp/device_vbe.txt ic gm gm_ic
.endc
.end
"""
    
    netlist_vce = """* Device DC Characterization - VCE Sweep
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
VCE c 0 0.95
I_B b 0 2u
X1 c b 0 0 npn13G2

.dc VCE 0.2 1.5 0.02 I_B 1u 5u 1u

.control
run
let ic = -i(VCE)
wrdata 04_SIMULATION/raw_exp/device_vce.txt ic
.endc
.end
"""
    
    with open(os.path.join(DIR_NETLIST, "exp_device_vbe.cir"), "w") as f:
        f.write(netlist_vbe)
    
    with open(os.path.join(DIR_NETLIST, "exp_device_vce.cir"), "w") as f:
        f.write(netlist_vce)

    run_ngspice("02_NETLIST/experiments/exp_device_vbe.cir")
    run_ngspice("02_NETLIST/experiments/exp_device_vce.cir")

    # Plot VBE sweep results
    try:
        data_vbe = np.loadtxt(os.path.join(DIR_RAW, "device_vbe.txt"))
        vbe = data_vbe[:, 0]
        ic = data_vbe[:, 1]
        gm = data_vbe[:, 3]
        gm_ic = data_vbe[:, 5]

        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax1.set_xlabel('Collector Current $I_C$ (mA)')
        ax1.set_ylabel('$g_m$ (mS)', color='tab:blue')
        ax1.plot(ic * 1e3, gm * 1e3, color='tab:blue', linewidth=2)
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.set_xscale('log')

        ax2 = ax1.twinx()
        ax2.set_ylabel('$g_m / I_C$ (V$^{-1}$)', color='tab:red')
        ax2.plot(ic * 1e3, gm_ic, color='tab:red', linewidth=2)
        ax2.tick_params(axis='y', labelcolor='tab:red')

        plt.title('Transconductance and Efficiency vs Current')
        fig.tight_layout()
        plt.grid(True, which="both", ls="--")
        plt.savefig(os.path.join(DIR_FIGURES, "fig_device_gm_ic.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Failed to plot VBE data: {e}")

    # Plot VCE sweep results (Family of curves)
    try:
        data_vce = np.loadtxt(os.path.join(DIR_RAW, "device_vce.txt"))
        # ngspice wrdata for multiple sweeps outputs: vce1 ic1 vce2 ic2 ...
        # Each sweep has same number of points
        plt.figure(figsize=(8, 5))
        num_sweeps = data_vce.shape[1] // 2
        for i in range(num_sweeps):
            vce = data_vce[:, 2*i]
            ic = data_vce[:, 2*i + 1]
            plt.plot(vce, ic * 1e3, label=f'$I_B$ = {i+1} $\mu$A', linewidth=2)
            
        plt.xlabel('Collector-Emitter Voltage $V_{CE}$ (V)')
        plt.ylabel('Collector Current $I_C$ (mA)')
        plt.title('Output Characteristics ($I_C$ vs $V_{CE}$)')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(DIR_FIGURES, "fig_device_ic_vce.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Failed to plot VCE data: {e}")

if __name__ == "__main__":
    run_dc_experiment()
