import os
import sys
import numpy as np
import CSXCAD
from openEMS.ports import LumpedPort

# Add path for sparam_wrapper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from sparam_wrapper import TouchstoneHandler

def main():
    inductors = ['ind_200pH', 'ind_180pH', 'ind_100pH', 'ind_60pH', 'ind_500pH']
    
    for ind in inductors:
        out_dir = os.path.abspath(f'./{ind}_em')
        if not os.path.exists(out_dir):
            print(f"Directory {out_dir} not found.")
            continue
            
        print(f"Post-processing {ind}...")
        try:
            CSX = CSXCAD.ContinuousStructure()
            # Dummy geometry, just need the port object to read the files
            port1 = LumpedPort(CSX, 1, 50, [0,0,0], [0,0,1], 'z', excite=True)
            port2 = LumpedPort(CSX, 2, 50, [0,0,0], [0,0,1], 'z', excite=False)
            
            freq = np.linspace(10e9, 50e9, 401)
            port1.CalcPort(out_dir, freq)
            port2.CalcPort(out_dir, freq)
            
            S11 = port1.uf_ref / port1.uf_inc
            S21 = port2.uf_tot / port1.uf_inc
            S22 = S11
            S12 = S21
            
            TouchstoneHandler.write(f'{ind}.s2p', freq, S11, S12, S21, S22)
            print(f"Saved {ind}.s2p")
            
        except Exception as e:
            print(f"Failed to post-process {ind}: {e}")

if __name__ == '__main__':
    main()
