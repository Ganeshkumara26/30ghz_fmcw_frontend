import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt

# Directories
DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
DIR_HANDOVER = os.path.dirname(os.path.dirname(DIR_SCRIPTS))
DIR_NETLIST = os.path.join(DIR_HANDOVER, "02_NETLIST", "experiments")
DIR_RAW = os.path.join(DIR_HANDOVER, "04_SIMULATION", "raw_exp")
DIR_FIGURES = os.path.join(DIR_HANDOVER, "05_FIGURES", "experiments")

# Ensure directories exist
os.makedirs(DIR_NETLIST, exist_ok=True)
os.makedirs(DIR_RAW, exist_ok=True)
os.makedirs(DIR_FIGURES, exist_ok=True)

# Helper function to run ngspice in WSL
def run_ngspice(netlist_path):
    # netlist_path should be relative to DIR_HANDOVER
    os.chdir(DIR_HANDOVER)
    result = subprocess.run(["wsl", "ngspice", "-b", netlist_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in {netlist_path}:\n{result.stdout}\n{result.stderr}")
    return result.returncode == 0
