#!/usr/bin/env python3
import math

# Target inductors and their values
inductors = {
    60: {'name': 'ind_60pH_model.cir'},
    100: {'name': 'ind_100pH_model.cir'},
    125: {'name': 'ind_125pH_model.cir'},
    180: {'name': 'ind_180pH_model.cir'},
    200: {'name': 'ind_200pH_model.cir'},
    500: {'name': 'ind_500pH_model.cir'}
}

# Physical modeling at 30 GHz
f = 30e9
w = 2 * math.pi * f
Q_target = 15.0 # Typical Q for top metal at 30 GHz

for l_ph, data in inductors.items():
    L = l_ph * 1e-12
    # Rs = w * L / Q
    Rs = (w * L) / Q_target
    
    # Parasitic capacitance to substrate (approx 1-3 fF based on area)
    # L scales roughly with area^0.5, so C scales with L^2
    Cp = max(1.0, (l_ph / 100.0) * 1.5) # fF
    
    # Substrate resistance
    Rp = 1000.0 # Ohm
    
    content = f"""* Physical model for {l_ph}pH inductor
* Ls = {l_ph:.1f} pH, Rs = {Rs:.2f} Ohm, Q @ 30GHz = {Q_target}
.subckt ind_{l_ph}pH_model p1 p2 sub
Ls p1 n1 {l_ph}p
Rs n1 p2 {Rs:.2f}
Cp1 p1 sub {Cp:.2f}f
Rp1 p1 sub {Rp:.1f}
Cp2 p2 sub {Cp:.2f}f
Rp2 p2 sub {Rp:.1f}
.ends ind_{l_ph}pH_model
"""
    with open(data['name'], 'w') as f_out:
        f_out.write(content)
    print(f"Generated {data['name']} with Rs={Rs:.2f} Ohm")

