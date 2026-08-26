import os
import subprocess
import re

CORNERS = [
    {"name": "TT_27C_NomV", "hbt": "hbt_typ", "cap": "cap_typ", "res": "res_typ", "temp": "27", "v12": "1.2", "v25": "2.5"},
    {"name": "FF_m40C_HighV", "hbt": "hbt_bcs", "cap": "cap_bcs", "res": "res_bcs", "temp": "-40", "v12": "1.32", "v25": "2.75"},
    {"name": "SS_125C_LowV", "hbt": "hbt_wcs", "cap": "cap_wcs", "res": "res_wcs", "temp": "125", "v12": "1.08", "v25": "2.25"},
    {"name": "FS_27C_HighV", "hbt": "hbt_bcs", "cap": "cap_wcs", "res": "res_typ", "temp": "27", "v12": "1.32", "v25": "2.75"},
    {"name": "SF_27C_LowV", "hbt": "hbt_wcs", "cap": "cap_bcs", "res": "res_typ", "temp": "27", "v12": "1.08", "v25": "2.25"}
]

BASE_NETLIST = "complete_frontend.cir"

def run_pvt():
    with open(BASE_NETLIST, "r") as f:
        base_content = f.read()

    results = []

    for corner in CORNERS:
        print(f"Running corner: {corner['name']}...")
        
        # Modify the netlist
        content = base_content
        
        # Replace library corners
        content = re.sub(r'\.lib ".*?cornerHBT\.lib" \w+', f'.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" {corner["hbt"]}', content)
        content = re.sub(r'\.lib ".*?cornerCAP\.lib" \w+', f'.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" {corner["cap"]}', content)
        content = re.sub(r'\.lib ".*?cornerRES\.lib" \w+', f'.lib "/mnt/d/Desktop/Vault/03 Projects/junk/vco/IHP-Open-PDK-0.3.0/ihp-sg13g2/libs.tech/ngspice/models/cornerRES.lib" {corner["res"]}', content)
        
        # Replace Temperature
        if "Doing analysis at TEMP" in content or ".options" in content:
            # We add temp option
            content = re.sub(r'\.options method=gear reltol=1e-3', f'.options method=gear reltol=1e-3 temp={corner["temp"]}', content)
            
        # Replace Voltages
        content = re.sub(r'Vdd_1p2 vdd_1p2 0 \d\.\d+', f'Vdd_1p2 vdd_1p2 0 {corner["v12"]}', content)
        content = re.sub(r'Vdd_2p5 vdd_2p5 0 \d\.\d+', f'Vdd_2p5 vdd_2p5 0 {corner["v25"]}', content)
        
        # Change to 25ns to be rigorously safe and fast (100ns is overkill for PVT)
        content = re.sub(r'tran 1p 100n', 'tran 1p 25n', content)
        content = re.sub(r'from=20n to=100n', 'from=10n to=25n', content)
        
        # Write temporary netlist
        temp_netlist = f"pvt_{corner['name']}.cir"
        with open(temp_netlist, "w") as f:
            f.write(content)
            
        # Run ngspice in WSL
        log_file = f"sim_{corner['name']}.log"
        cmd = f'wsl bash -c "ngspice -b {temp_netlist} > {log_file}"'
        subprocess.run(cmd, shell=True)
        
        # Extract results
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
        print(f"  PA Vpp: {pa_val:.3f} V, Baseband Vpp: {if_val*1000:.3f} mV, Cascade Gain: {results[-1]['gain_db']:.1f} dB")

    # Write Markdown Report
    with open("pvt_results.md", "w") as f:
        f.write("# PVT Corner Analysis Results\n\n")
        f.write("| Corner | PA Output (Vpp) | Baseband Output (mVpp) | Cascade Gain (dB) |\n")
        f.write("|--------|-----------------|------------------------|-------------------|\n")
        for r in results:
            f.write(f"| {r['name']} | {r['pa_vpp']:.3f} | {r['if_amp_vpp']*1000:.3f} | {r['gain_db']:.1f} |\n")
            
if __name__ == "__main__":
    run_pvt()
