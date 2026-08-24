import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_buffer_experiment():
    print("Running Buffer Characterization...")
    
    netlist = """* Buffer Characterization
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ
.include "02_NETLIST/parameters.inc"

Vcc pad_vdd 0 {VDD}

* The buffer circuit (Half circuit, single-ended)
* We use a bias tee / AC coupling just like in the real circuit
V_in in 0 DC 0 AC 1

C_ac_x in buf_in_x {C_AC_COUPLING}
R_fb_x buf_in_x buf_out_x {R_FB}
X_buf_x buf_out_x buf_in_x 0 0 npn13G2 m=1
R_load_x pad_vdd buf_out_x {R_LOAD}

.control
op
ac dec 50 1G 100G

let v_out = v(buf_out_x)
let av_mag = mag(v_out)
let av_db = 20 * log10(av_mag)
let z_in = v(in) / -i(V_in)
let c_in = -1 / (2 * 3.14159 * frequency * imag(z_in))

wrdata 04_SIMULATION/raw_exp/buffer_av.txt av_db
wrdata 04_SIMULATION/raw_exp/buffer_cin.txt c_in
.endc
.end
"""
    with open(os.path.join(DIR_NETLIST, "exp_buffer.cir"), "w") as f:
        f.write(netlist)
        
    success = run_ngspice("02_NETLIST/experiments/exp_buffer.cir")
    
    if success:
        try:
            data_av = np.loadtxt(os.path.join(DIR_RAW, "buffer_av.txt"))
            data_cin = np.loadtxt(os.path.join(DIR_RAW, "buffer_cin.txt"))
            
            freq = data_av[:, 0] / 1e9 # GHz
            av_db = data_av[:, 1]
            c_in = data_cin[:, 1] * 1e15 # fF
            
            fig, ax1 = plt.subplots(figsize=(8, 5))
            
            color1 = 'tab:blue'
            ax1.set_xlabel('Frequency (GHz)')
            ax1.set_ylabel('Voltage Gain (dB)', color=color1)
            ax1.plot(freq, av_db, color=color1, linewidth=2, label='Gain ($A_v$)')
            ax1.tick_params(axis='y', labelcolor=color1)
            ax1.grid(True)
            
            ax2 = ax1.twinx()
            color2 = 'tab:red'
            ax2.set_ylabel('Input Capacitance $C_{in}$ (fF)', color=color2)
            ax2.plot(freq, c_in, color=color2, linewidth=2, linestyle='--', label='$C_{in}$')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            # Highlight 30 GHz
            ax1.axvline(x=30.0, color='k', linestyle=':', label='30 GHz Operating Point')
            
            plt.title('Buffer Voltage Gain and Input Capacitance vs Frequency')
            fig.tight_layout()
            
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='lower left')
            
            plt.savefig(os.path.join(DIR_FIGURES, "fig_buffer.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f"Failed to plot buffer data: {e}")

if __name__ == "__main__":
    run_buffer_experiment()
