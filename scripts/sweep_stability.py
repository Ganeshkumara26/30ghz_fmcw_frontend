import subprocess
import skrf as rf
import numpy as np
import re
import os

def check_unconditional_stability(filename):
    try:
        ntwk = rf.Network(filename)
    except:
        return False, 0
    
    freq = ntwk.f
    valid_idx = np.where(freq > 2e9)[0]
    
    s11 = ntwk.s[valid_idx, 0, 0]
    s21 = ntwk.s[valid_idx, 1, 0]
    s12 = ntwk.s[valid_idx, 0, 1]
    s22 = ntwk.s[valid_idx, 1, 1]
    
    delta = s11 * s22 - s12 * s21
    k_factor = (1 - np.abs(s11)**2 - np.abs(s22)**2 + np.abs(delta)**2) / (2 * np.abs(s12 * s21) + 1e-15)
    mu_factor = (1 - np.abs(s11)**2) / (np.abs(s22 - np.conj(s11) * delta) + np.abs(s12 * s21) + 1e-15)

    min_k = np.min(k_factor)
    min_mu = np.min(mu_factor)
    max_delta_mag = np.max(np.abs(delta))
    
    is_stable = (min_k > 1) and (max_delta_mag < 1) and (min_mu > 1)
    return is_stable, min_mu

def sweep_lna():
    print("Sweeping LNA R_cb_stab...")
    cir_file = "30ghz_lna_sparam.cir"
    with open(cir_file, 'r') as f:
        content = f.read()
        
    for r_val in range(5, 51, 5):
        new_content = re.sub(r'\.param r_cb_stab = \d+', f'.param r_cb_stab = {r_val}', content)
        with open(cir_file, 'w') as f:
            f.write(new_content)
            
        subprocess.run(["Xyce", cir_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        stable, min_mu = check_unconditional_stability("lna_350GHz.s2p")
        print(f"  R_cb_stab = {r_val} Ohms -> min_mu = {min_mu:.3f} | Stable: {stable}")
        if stable:
            print(f"✅ LNA Unconditionally Stable with R_cb_stab = {r_val} Ohms!")
            break

def sweep_pa():
    print("\nSweeping PA R_snub...")
    cir_file = "30ghz_pa_sparam.cir"
    with open(cir_file, 'r') as f:
        content = f.read()
        
    for r_val in range(10, 51, 5):
        new_content = re.sub(r'\.param r_snub = \d+', f'.param r_snub = {r_val}', content)
        with open(cir_file, 'w') as f:
            f.write(new_content)
            
        subprocess.run(["Xyce", cir_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        stable, min_mu = check_unconditional_stability("pa_350GHz.s2p")
        print(f"  R_snub = {r_val} Ohms -> min_mu = {min_mu:.3f} | Stable: {stable}")
        if stable:
            print(f"✅ PA Unconditionally Stable with R_snub = {r_val} Ohms!")
            break

if __name__ == "__main__":
    sweep_lna()
    sweep_pa()
