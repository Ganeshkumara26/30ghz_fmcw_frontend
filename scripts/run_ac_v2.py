import os
import subprocess
import re
import matplotlib.pyplot as plt
import numpy as np

def run_opamp_ac():
    print("Running AC Analysis on OpAmp Baseband Driver...")
    
    # Create an AC testbench for the OpAmp
    ac_cir = """* AC Testbench for OpAmp Driver
.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ
.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib" res_typ

.options method=gear reltol=1e-3

Vdd vdd 0 2.5
Vss vss 0 0

* AC input
V_in_p in_p 0 dc 1.3 ac 1.0
V_in_n in_n 0 dc 1.3

.include "baseband/netlists/opamp_driver.cir"

* Unity gain feedback
X_dut in_p out out vdd vss opamp_driver

* 2pF ADC sampling load
C_load out vss 2p

.control
    ac dec 50 1Meg 10G
    set filetype=ascii
    write opamp_ac.raw v(out)
    quit
.endc
.end
"""
    with open("tb_opamp_ac.cir", "w") as f:
        f.write(ac_cir)
        
    subprocess.run('wsl bash -c "ngspice -b tb_opamp_ac.cir > tb_opamp_ac.log"', shell=True)
    
    # Parse raw file
    # Format of AC raw file is slightly different (complex numbers)
    # I will parse the ascii AC file
    data = parse_ac_raw("opamp_ac.raw")
    
    freq = data['frequency']
    v_out = data['v(out)']
    
    magnitude = 20 * np.log10(np.abs(v_out))
    phase = np.angle(v_out, deg=True)
    
    plt.figure(figsize=(10, 6))
    
    ax1 = plt.subplot(2, 1, 1)
    ax1.semilogx(freq, magnitude, 'b')
    ax1.set_title('Bode Plot: Baseband OpAmp (Active Anti-Aliasing Filter)')
    ax1.set_ylabel('Magnitude (dB)')
    ax1.grid(True, which="both", ls="-")
    
    # Find 3dB bandwidth
    dc_gain = magnitude[0]
    idx_3db = np.where(magnitude <= dc_gain - 3.0)[0][0]
    f_3db = freq[idx_3db]
    ax1.axvline(f_3db, color='r', linestyle='--', label=f'3dB Bandwidth: {f_3db/1e6:.1f} MHz')
    ax1.legend()
    
    ax2 = plt.subplot(2, 1, 2)
    ax2.semilogx(freq, phase, 'g')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Phase (deg)')
    ax2.grid(True, which="both", ls="-")
    
    plt.tight_layout()
    plt.savefig("C:/Users/hvnth/.gemini/antigravity-ide/brain/ad948a02-99e4-4bbe-a8c0-36d25905484f/plot_ac_opamp.png")
    plt.close()

def parse_ac_raw(filename):
    return parse_ac_ngspice(filename)
    
def parse_ac_ngspice(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    vars = []
    parsing_vars = False
    parsing_data = False
    
    freq = []
    v_out = []
    
    for line in lines:
        if line.startswith("Variables:"):
            parsing_vars = True
            continue
        if line.startswith("Values:"):
            parsing_vars = False
            parsing_data = True
            continue
            
        if parsing_vars:
            parts = line.split()
            if len(parts) >= 2:
                vars.append(parts[1].lower())
        elif parsing_data:
            parts = line.split()
            if len(parts) == 2 and ',' in parts[1]:
                # Index and frequency row
                comp = parts[1].split(',')
                freq.append(float(comp[0]))
            elif len(parts) == 1 and ',' in parts[0]:
                # Voltage row
                comp = parts[0].split(',')
                v = complex(float(comp[0]), float(comp[1]))
                v_out.append(v)
                
    return {'frequency': np.array(freq), 'v(out)': np.array(v_out[:len(freq)])}

if __name__ == "__main__":
    run_opamp_ac()
