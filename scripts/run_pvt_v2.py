import os
import subprocess
import re
import matplotlib.pyplot as plt
import numpy as np
import time

CORNERS = [
    {"name": "TT_27C_NomV", "hbt": "hbt_typ", "cap": "cap_typ", "res": "res_typ", "temp": "27", "v12": "1.2", "v25": "2.5"},
    {"name": "FF_m40C_HighV", "hbt": "hbt_bcs", "cap": "cap_bcs", "res": "res_bcs", "temp": "-40", "v12": "1.32", "v25": "2.75"},
    {"name": "SS_125C_LowV", "hbt": "hbt_wcs", "cap": "cap_wcs", "res": "res_wcs", "temp": "125", "v12": "1.08", "v25": "2.25"},
    {"name": "FS_27C_HighV", "hbt": "hbt_bcs", "cap": "cap_wcs", "res": "res_typ", "temp": "27", "v12": "1.32", "v25": "2.75"},
    {"name": "SF_27C_LowV", "hbt": "hbt_wcs", "cap": "cap_bcs", "res": "res_typ", "temp": "27", "v12": "1.08", "v25": "2.25"}
]

BASE_NETLIST = "complete_frontend_v2.cir"

def parse_ngspice_ascii(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    vars = []
    parsing_vars = False
    parsing_data = False
    data = []
    
    for line in lines:
        if line.startswith("Variables:"):
            parsing_vars = True
            continue
        if line.startswith("Values:"):
            parsing_vars = False
            parsing_data = True
            data = [[] for _ in range(len(vars))]
            continue
            
        if parsing_vars:
            parts = line.split()
            if len(parts) >= 2:
                vars.append(parts[1].lower())
        elif parsing_data:
            parts = line.split()
            if len(parts) == 2:
                data[0].append(float(parts[1]))
            elif len(parts) == 1:
                for i in range(1, len(vars)):
                    if len(data[i]) < len(data[0]):
                        data[i].append(float(parts[0]))
                        break
                        
    return {vars[i]: np.array(data[i]) for i in range(len(vars))}

def run_pvt():
    with open(BASE_NETLIST, "r") as f:
        base_content = f.read()

    results = []
    plt.figure(figsize=(10,6))

    for corner in CORNERS:
        print(f"Running corner: {corner['name']}...")
        
        content = base_content
        
        # Replace library corners
        content = re.sub(r'\.lib ".*?cornerHBT\.lib" \w+', f'.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" {corner["hbt"]}', content)
        content = re.sub(r'\.lib ".*?cornerCAP\.lib" \w+', f'.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" {corner["cap"]}', content)
        content = re.sub(r'\.lib ".*?cornerRES\.lib" \w+', f'.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib" {corner["res"]}', content)
        
        # Replace Temperature
        if "cshunt=1f" in content:
            content = re.sub(r'\.options method=gear reltol=1e-3 cshunt=1f', f'.options method=gear reltol=1e-3 cshunt=1f temp={corner["temp"]}', content)
            
        # Replace Voltages
        content = re.sub(r'Vdd_1p2 vdd_1p2 0 \d\.\d+', f'Vdd_1p2 vdd_1p2 0 {corner["v12"]}', content)
        content = re.sub(r'Vdd_2p5 vdd_2p5 0 \d\.\d+', f'Vdd_2p5 vdd_2p5 0 {corner["v25"]}', content)
        
        # Change transient time to 30ns to capture at least some IF cycles, since 100ns takes 1 minute, 30ns is 18s.
        content = re.sub(r'tran 1p 100n', 'tran 1p 30n', content)
        content = re.sub(r'from=20n to=100n', 'from=15n to=30n', content)
        
        # Inject write command to get raw data
        raw_file = f"pvt_v2_{corner['name']}.raw"
        write_cmd = f"set filetype=ascii\n    write {raw_file} v(opamp_out) v(tx_ant)\n"
        if "set filetype=ascii" in content:
            content = re.sub(r'set filetype=ascii\n\s*write.*?\n', write_cmd, content)
        else:
            content = content.replace("quit\n.endc", write_cmd + "    quit\n.endc")
            
        # Write temporary netlist
        temp_netlist = f"pvt_v2_{corner['name']}.cir"
        with open(temp_netlist, "w") as f:
            f.write(content)
            
        # Run ngspice
        log_file = f"sim_v2_{corner['name']}.log"
        cmd = f'wsl bash -c "ngspice -b {temp_netlist} > {log_file}"'
        subprocess.run(cmd, shell=True)
        
        # Extract scalar results
        with open(log_file, "r") as f:
            log_data = f.read()
            
        pa_vpp = re.search(r'pa_vpp\s*=\s*([0-9\.eE+-]+)', log_data)
        if_amp_vpp = re.search(r'if_amp_ripple_vpp\s*=\s*([0-9\.eE+-]+)', log_data)
        
        pa_val = float(pa_vpp.group(1)) if pa_vpp else 0.0
        if_val = float(if_amp_vpp.group(1)) if if_amp_vpp else 0.0
        
        results.append({
            "name": corner["name"],
            "pa_vpp": pa_val,
            "if_amp_vpp": if_val,
            "gain_db": 20 * __import__("math").log10(if_val / 200e-6) if if_val > 0 else -999
        })
        print(f"  PA Vpp: {pa_val:.3f} V, Baseband Vpp: {if_val*1000:.3f} mV")
        
        # Plot data
        try:
            data = parse_ngspice_ascii(raw_file)
            plt.plot(data['time']*1e9, data['v(opamp_out)'], label=corner['name'])
        except Exception as e:
            print(f"Error parsing raw file for {corner['name']}: {e}")

    plt.xlim(10, 30)
    plt.title("5-Corner PVT Overlay: OpAmp Baseband Output")
    plt.xlabel("Time (ns)")
    plt.ylabel("Voltage (V)")
    plt.legend()
    plt.grid(True)
    plt.savefig("C:/Users/hvnth/.gemini/antigravity-ide/brain/ad948a02-99e4-4bbe-a8c0-36d25905484f/plot_pvt_overlay.png")
    plt.close()
    
    # Write Markdown Report
    with open("C:/Users/hvnth/.gemini/antigravity-ide/brain/ad948a02-99e4-4bbe-a8c0-36d25905484f/pvt_v2_results.md", "w") as f:
        f.write("### PVT Corner Analysis Results (Integrated V2)\n\n")
        f.write("| Corner | PA Output (Vpp) | Baseband Output (mVpp) |\n")
        f.write("|--------|-----------------|------------------------|\n")
        for r in results:
            f.write(f"| {r['name']} | {r['pa_vpp']:.3f} | {r['if_amp_vpp']*1000:.3f} |\n")

if __name__ == "__main__":
    start = time.time()
    run_pvt()
    print(f"PVT Simulation completed in {time.time() - start:.1f} seconds.")
