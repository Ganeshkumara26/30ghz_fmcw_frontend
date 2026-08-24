import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_rf_experiment():
    print("Running RF Characterization (fT and Capacitances)...")
    
    # We will sweep VBE to get different operating points, run an AC analysis to get fT, 
    # and print the results to a file using echo
    
    vbes = np.arange(0.70, 0.95, 0.01)
    ic_list = []
    ft_list = []
    
    for vbe in vbes:
        netlist = f"""* Device RF Characterization
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
VCE c 0 0.95
VBE b 0 {vbe:.3f} AC 1
X1 c b 0 0 npn13G2

.control
op
ac dec 10 1G 10G

setplot ac1
let h21_mag = mag(i(VCE) / i(VBE))
wrdata 04_SIMULATION/raw_exp/device_rf_ac.txt h21_mag

setplot op1
let ic = -i(VCE)
wrdata 04_SIMULATION/raw_exp/device_rf_dc.txt ic
.endc
.end
"""
        with open(os.path.join(DIR_NETLIST, "exp_device_rf.cir"), "w") as f:
            f.write(netlist)
        
        success = run_ngspice("02_NETLIST/experiments/exp_device_rf.cir")
        if success:
            try:
                data_dc = np.loadtxt(os.path.join(DIR_RAW, "device_rf_dc.txt"))
                ic_val = data_dc[1] if data_dc.ndim == 1 else data_dc[0, 1]
                data_ac = np.loadtxt(os.path.join(DIR_RAW, "device_rf_ac.txt"))
                # The AC simulation is a decade sweep 1G to 10G. Let's take the value at 10 GHz (the last point)
                freq_val = data_ac[-1, 0]
                h21_val = data_ac[-1, 1]
                ft_val = h21_val * freq_val
                if ic_val > 0:
                    ic_list.append(ic_val)
                    ft_list.append(ft_val)
            except Exception as e:
                print(f"Error reading data for vbe={vbe}: {e}")

    try:
        if ic_list:
            plt.figure(figsize=(8, 5))
            plt.plot(np.array(ic_list) * 1e3, np.array(ft_list) / 1e9, linewidth=2, color='tab:green')
            plt.xlabel('Collector Current $I_C$ (mA)')
            plt.ylabel('Transit Frequency $f_T$ (GHz)')
            plt.title('Transit Frequency vs Collector Current')
            plt.grid(True)
            plt.xscale('log')
            # Highlight our operating region (around 1 mA)
            plt.axvline(x=1.0, color='r', linestyle='--', label='Target Operating $I_C$ (1mA)')
            plt.legend()
            plt.savefig(os.path.join(DIR_FIGURES, "fig_device_ft.png"), dpi=300)
            plt.close()
    except Exception as e:
        print(f"Failed to plot RF data: {e}")

if __name__ == "__main__":
    run_rf_experiment()
