import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_tank_experiment():
    print("Running Tank Characterization...")
    
    netlist = """* Tank Characterization
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ

.subckt spiral_ind_53ph p1 p2 sub
L_s p1 n_int 53p
R_s n_int p2 0.312
C_sub1 p1 sub 2f
C_sub2 p2 sub 2f
.ends spiral_ind_53ph

* Tank components
X_ind1 vcc out_x 0 spiral_ind_53ph
X_ind2 vcc out_y 0 spiral_ind_53ph

* Base caps (W=17.11u, L=17.11u) ~ approximately 535fF total per leg
X_cbase_x out_x 0 cap_cmim l=17.11u w=17.11u
X_cbase_y out_y 0 cap_cmim l=17.11u w=17.11u

I_ac out_y out_x AC 1
V_cc vcc 0 0.95

.control
op
ac lin 500 25G 35G

let v_diff = v(out_x) - v(out_y)
let z_tank = v_diff
let y_tank = 1.0 / z_tank
let r_p = 1.0 / real(y_tank)
let x_s = imag(z_tank)
let r_s = real(z_tank)
let z_mag = mag(z_tank)
let q_tank = abs(x_s) / r_s

wrdata 04_SIMULATION/raw_exp/tank_rp.txt r_p
wrdata 04_SIMULATION/raw_exp/tank_rs.txt r_s
wrdata 04_SIMULATION/raw_exp/tank_xs.txt x_s
wrdata 04_SIMULATION/raw_exp/tank_zmag.txt z_mag
wrdata 04_SIMULATION/raw_exp/tank_q.txt q_tank
.endc
.end
"""
    with open(os.path.join(DIR_NETLIST, "exp_tank.cir"), "w") as f:
        f.write(netlist)
        
    success = run_ngspice("02_NETLIST/experiments/exp_tank.cir")
    
    if success:
        try:
            data_rp = np.loadtxt(os.path.join(DIR_RAW, "tank_rp.txt"))
            data_rs = np.loadtxt(os.path.join(DIR_RAW, "tank_rs.txt"))
            data_xs = np.loadtxt(os.path.join(DIR_RAW, "tank_xs.txt"))
            data_zmag = np.loadtxt(os.path.join(DIR_RAW, "tank_zmag.txt"))
            data_q = np.loadtxt(os.path.join(DIR_RAW, "tank_q.txt"))
            
            freq = data_rp[:, 0] / 1e9
            r_p = data_rp[:, 1]
            r_s = data_rs[:, 1]
            x_s = data_xs[:, 1]
            z_mag = data_zmag[:, 1]
            q_tank = data_q[:, 1]
            
            # Plot 1: |Z| and Rp
            fig, ax1 = plt.subplots(figsize=(8, 5))
            ax1.set_xlabel('Frequency (GHz)')
            ax1.set_ylabel(r'Impedance Magnitude $|Z|$ ($\Omega$)', color='tab:purple')
            ax1.plot(freq, z_mag, color='tab:purple', linewidth=2, label='|Z|')
            ax1.tick_params(axis='y', labelcolor='tab:purple')
            
            ax2 = ax1.twinx()
            ax2.set_ylabel(r'Parallel Resistance $R_p$ ($\Omega$)', color='tab:red')
            ax2.plot(freq, r_p, color='tab:red', linewidth=2, linestyle='--', label='Rp')
            ax2.tick_params(axis='y', labelcolor='tab:red')
            
            # Find f0 (resonance frequency where Rp is max or z_mag is max)
            max_idx = np.argmax(r_p)
            f0 = freq[max_idx]
            rp_f0 = r_p[max_idx]
            q_f0 = q_tank[max_idx]
            
            ax2.plot(f0, rp_f0, 'ro')
            ax2.annotate(f'$f_0$ = {f0:.2f} GHz\n$R_p(f_0)$ = {rp_f0:.1f} $\Omega$', 
                         xy=(f0, rp_f0), xytext=(f0+1, rp_f0-10),
                         arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
            
            plt.title('Tank Impedance and $R_p$ vs Frequency')
            fig.tight_layout()
            plt.grid(True)
            plt.savefig(os.path.join(DIR_FIGURES, "fig_tank_z.png"), dpi=300)
            plt.close()
            
            # Plot 2: Re{Z} and Im{Z}
            plt.figure(figsize=(8, 5))
            plt.plot(freq, r_s, linewidth=2, color='tab:blue', label=r'$\Re\{Z\}$')
            plt.plot(freq, x_s, linewidth=2, color='tab:green', label=r'$\Im\{Z\}$')
            plt.xlabel('Frequency (GHz)')
            plt.ylabel('Impedance ($\Omega$)')
            plt.title('Tank Impedance (Real and Imaginary Parts)')
            plt.legend()
            plt.grid(True)
            plt.savefig(os.path.join(DIR_FIGURES, "fig_tank_re_im.png"), dpi=300)
            plt.close()

            # Plot 3: Q factor
            plt.figure(figsize=(8, 5))
            plt.plot(freq, q_tank, linewidth=2, color='tab:orange')
            plt.plot(f0, q_f0, 'ko')
            plt.annotate(f'$Q(f_0)$ = {q_f0:.1f}', 
                         xy=(f0, q_f0), xytext=(f0+1, q_f0-2),
                         arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
            
            plt.xlabel('Frequency (GHz)')
            plt.ylabel('Quality Factor $Q$')
            plt.title('Tank Quality Factor vs Frequency')
            plt.grid(True)
            plt.savefig(os.path.join(DIR_FIGURES, "fig_tank_q.png"), dpi=300)
            plt.close()
        except Exception as e:
            print(f"Failed to plot Tank data: {e}")

if __name__ == "__main__":
    run_tank_experiment()
