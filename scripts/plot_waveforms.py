import os
import subprocess
import re
import matplotlib.pyplot as plt
import numpy as np

BASE_NETLIST = "complete_frontend.cir"
ARTIFACT_DIR = r"C:\Users\hvnth\.gemini\antigravity-ide\brain\ad948a02-99e4-4bbe-a8c0-36d25905484f"

def plot_waveforms():
    print("Preparing netlist for waveform extraction...")
    with open(BASE_NETLIST, "r") as f:
        content = f.read()

    # Make sure we are doing 100ns
    content = re.sub(r'tran 1p \d+n', 'tran 1p 100n', content)
    
    # Add print statement before .endc
    if "print v(vco_out_p) v(pa_out)" not in content:
        content = re.sub(r'quit', r'print v(vco_out_p) v(pa_out) v(if_amp_out) > waveforms.txt\n    quit', content)
    
    with open("temp_plot.cir", "w") as f:
        f.write(content)
        
    print("Running 100ns simulation to generate waveforms (this will take ~2-3 minutes)...")
    subprocess.run('wsl bash -c "ngspice -b temp_plot.cir"', shell=True)
    
    print("Parsing waveforms.txt...")
    times = []
    vco = []
    pa = []
    if_amp = []
    
    with open("waveforms.txt", "r") as f:
        lines = f.readlines()
        
    for line in lines:
        parts = line.split()
        if len(parts) >= 5 and parts[0].isdigit():
            try:
                times.append(float(parts[1]))
                vco.append(float(parts[2]))
                pa.append(float(parts[3]))
                if_amp.append(float(parts[4]))
            except ValueError:
                pass
                
    times = np.array(times)    # Read specific columns for V2
    time = data.iloc[:, 1]
    
    # We need to map the printed node columns correctly.
    # From complete_frontend_v2.cir:
    # 183: meas tran vco_vpp PP v(vco_out_p)
    # The actual transient raw print might not have the same column indexes.
    # Wait, the simulation output has 'time' and 'p_total'. It doesn't print the node voltages!
    # Ah! I didn't add print v(tx_ant) etc. to the .control block!
    
    print("Plotting PA/VCO 30GHz Waveform (Zoomed 20ns-20.5ns)...")
    plt.figure(figsize=(10, 5))
    mask_rf = (times >= 20.0) & (times <= 20.5)
    plt.plot(times[mask_rf], pa[mask_rf], label="PA Output (V)", color='red')
    plt.plot(times[mask_rf], vco[mask_rf], label="VCO Output (V)", color='blue', alpha=0.7)
    plt.title("30 GHz RF Transmission (20ns - 20.5ns window)")
    plt.xlabel("Time (ns)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACT_DIR, "rf_waveform.png"))
    plt.close()

    print("Plotting IF Amp 100MHz Waveform (Full 100ns)...")
    plt.figure(figsize=(10, 5))
    mask_if = times >= 10.0 # wait for startup transient to settle
    plt.plot(times[mask_if], if_amp[mask_if], label="IF Amp Baseband Output (V)", color='green')
    plt.title("100 MHz Baseband Beat Frequency (10ns - 100ns)")
    plt.xlabel("Time (ns)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ARTIFACT_DIR, "if_waveform.png"))
    plt.close()
    
    print("Waveforms successfully saved to artifacts directory.")

if __name__ == "__main__":
    plot_waveforms()
