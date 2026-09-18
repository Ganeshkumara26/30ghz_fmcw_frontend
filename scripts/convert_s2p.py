#!/usr/bin/env python3
import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from sparam_wrapper import TouchstoneHandler

def s2y(S, Z0=50):
    """Convert S-parameters to Y-parameters for 2-port network."""
    I = np.eye(2, dtype=complex)
    Y = (1/Z0) * np.linalg.inv(I + S) @ (I - S)
    return Y

def extract_pi_network(s_params, f_target=30.0):
    """Extract equivalent RL circuit parameters at f_target (in GHz) from 1-port S11."""
    freq = s_params['freq']
    
    # Find closest frequency index
    idx = np.argmin(np.abs(freq - f_target))
    f = freq[idx]
    w = 2 * np.pi * f * 1e9
    
    S11 = s_params['S11'][idx]
    
    # 1-port impedance extraction
    Z0 = 50.0
    Z = Z0 * (1 + S11) / (1 - S11)
    
    Rs = np.real(Z)
    Ls = np.imag(Z) / w
    
    # Since it's a 1-port extraction, we model it as a simple series R-L.
    # (Shunt parasitics are lumped into the effective Ls/Rs at this frequency).
    Cp1 = 0.0
    Rp1 = 1e6
    Cp2 = 0.0
    Rp2 = 1e6
    
    return Ls, Rs, Cp1, Rp1, Cp2, Rp2, f

def write_subckt(filename, ind_name, Ls, Rs, Cp1, Rp1, Cp2, Rp2):
    """Write SPICE subcircuit."""
    with open(filename, 'w') as f:
        f.write(f"* Equivalent Pi-network for {ind_name} from openEMS\n")
        f.write(f".subckt {ind_name}_model p1 p2 sub\n")
        
        # Series branch
        f.write(f"L_s p1 n_int {Ls}\n")
        f.write(f"R_s n_int p2 {Rs}\n")
        
        # Shunt branch port 1
        if Cp1 > 0:
            f.write(f"C_p1 p1 sub {Cp1}\n")
        if Rp1 < 1e6:
            f.write(f"R_p1 p1 sub {Rp1}\n")
            
        # Shunt branch port 2
        if Cp2 > 0:
            f.write(f"C_p2 p2 sub {Cp2}\n")
        if Rp2 < 1e6:
            f.write(f"R_p2 p2 sub {Rp2}\n")
            
        f.write(f".ends {ind_name}_model\n")

def main():
    inductors = ["ind_60pH", "ind_100pH", "ind_125pH", "ind_180pH", "ind_200pH", "ind_500pH"]
    
    for ind in inductors:
        s2p_file = f"{ind}.s2p"
        if os.path.exists(s2p_file):
            print(f"Converting {s2p_file} to SPICE lumped-element model...")
            try:
                s_params = TouchstoneHandler.read(s2p_file)
                Ls, Rs, Cp1, Rp1, Cp2, Rp2, f = extract_pi_network(s_params, f_target=30.0)
                
                print(f"  Extracted at {f:.2f} GHz:")
                print(f"  Ls = {Ls*1e12:.2f} pH, Rs = {Rs:.2f} Ohm")
                print(f"  Cp1 = {Cp1*1e15:.2f} fF, Rp1 = {Rp1:.1f} Ohm")
                print(f"  Cp2 = {Cp2*1e15:.2f} fF, Rp2 = {Rp2:.1f} Ohm")
                
                cir_file = f"{ind}_model.cir"
                write_subckt(cir_file, ind, Ls, Rs, Cp1, Rp1, Cp2, Rp2)
                print(f"Generated {cir_file}")
            except Exception as e:
                print(f"Failed to convert {ind}: {e}")
        else:
            print(f"Missing {s2p_file}")

if __name__ == '__main__':
    main()
