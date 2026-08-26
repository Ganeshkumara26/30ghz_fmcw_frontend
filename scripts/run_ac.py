import os
import subprocess
import re

BASE_NETLIST = "complete_frontend.cir"

def run_ac():
    with open(BASE_NETLIST, "r") as f:
        base_content = f.read()

    # ==========================================
    # 1. RF Chain AC Analysis (Target -> Balun)
    # ==========================================
    print("Running AC Analysis on RF Chain (Antenna -> LNA -> Balun)...")
    content_rf = base_content
    
    # Add AC 1 to the RF input source
    content_rf = re.sub(r'V_target target_node vss dc 0 sin\(0 0.0001 30.1G 0 0\)', 'V_target target_node vss dc 0 ac 1', content_rf)
    
    # Replace the control block
    control_rf = """
.control
    ac dec 20 10G 50G
    
    * Measure maximum RF gain and bandwidth
    meas ac rf_gain_max MAX vmag(mix_rf_p)
    meas ac rf_gain_30g FIND vmag(mix_rf_p) AT=30G
    
    * Dump results
    print vmag(mix_rf_p) > ac_rf_results.txt
.endc
"""
    content_rf = re.sub(r'\.control.*\.endc', control_rf, content_rf, flags=re.DOTALL)
    
    with open("ac_rf_sim.cir", "w") as f:
        f.write(content_rf)
        
    subprocess.run('wsl bash -c "ngspice -b ac_rf_sim.cir > ac_rf.log"', shell=True)
    
    # Extract RF Gain
    with open("ac_rf.log", "r") as f:
        rf_log = f.read()
    rf_max = re.search(r'rf_gain_max\s*=\s*([0-9\.eE+-]+)', rf_log)
    rf_30g = re.search(r'rf_gain_30g\s*=\s*([0-9\.eE+-]+)', rf_log)
    
    print(f"  Max RF Gain (linear): {rf_max.group(1) if rf_max else 'Failed'}")
    print(f"  RF Gain at 30GHz (linear): {rf_30g.group(1) if rf_30g else 'Failed'}")

    # ==========================================
    # 2. Baseband IF AC Analysis (Mixer Out -> ADC)
    # ==========================================
    print("Running AC Analysis on Baseband Chain (IF Amp -> ADC)...")
    content_if = base_content
    
    # We must inject an AC source at the IF node. The mixer output is if_p. 
    # To do this safely without breaking DC bias, we add an AC coupled source.
    if_injection = """
* AC Injection for IF Amp
V_if_ac if_ac_node vss dc 0 ac 1
C_if_inject if_ac_node if_p 10u
"""
    # Insert before .control
    content_if = re.sub(r'\.control', if_injection + '\n.control', content_if)
    
    control_if = """
.control
    ac dec 20 1Meg 10G
    
    * Measure baseband characteristics
    meas ac if_gain_100m FIND vmag(if_amp_out) AT=100Meg
    meas ac if_gain_max MAX vmag(if_amp_out)
    
    * Dump results
    print vmag(if_amp_out) > ac_if_results.txt
.endc
"""
    content_if = re.sub(r'\.control.*\.endc', control_if, content_if, flags=re.DOTALL)
    
    with open("ac_if_sim.cir", "w") as f:
        f.write(content_if)
        
    subprocess.run('wsl bash -c "ngspice -b ac_if_sim.cir > ac_if.log"', shell=True)
    
    # Extract IF Gain
    with open("ac_if.log", "r") as f:
        if_log = f.read()
    if_max = re.search(r'if_gain_max\s*=\s*([0-9\.eE+-]+)', if_log)
    if_100m = re.search(r'if_gain_100m\s*=\s*([0-9\.eE+-]+)', if_log)
    
    print(f"  Max IF Gain (linear): {if_max.group(1) if if_max else 'Failed'}")
    print(f"  IF Gain at 100MHz (linear): {if_100m.group(1) if if_100m else 'Failed'}")
    
    # Write Markdown Report
    with open("ac_results.md", "w") as f:
        f.write("# AC Analysis Results\n\n")
        f.write("## RF Chain (LNA + Balun)\n")
        f.write(f"- Peak Voltage Gain: {rf_max.group(1) if rf_max else 'N/A'}\n")
        f.write(f"- Voltage Gain at 30 GHz: {rf_30g.group(1) if rf_30g else 'N/A'}\n\n")
        f.write("## Baseband Chain (IF Amp)\n")
        f.write(f"- Peak Voltage Gain: {if_max.group(1) if if_max else 'N/A'}\n")
        f.write(f"- Voltage Gain at 100 MHz: {if_100m.group(1) if if_100m else 'N/A'}\n")

if __name__ == "__main__":
    run_ac()
