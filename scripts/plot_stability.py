import skrf as rf
import matplotlib.pyplot as plt
import numpy as np
import sys

def plot_stability(name, filename, target_freq_ghz):
    try:
        ntwk = rf.Network(filename)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return
        
    freqs = ntwk.f
    # Find closest frequency index
    idx = np.argmin(np.abs(freqs - target_freq_ghz * 1e9))
    actual_freq = freqs[idx] / 1e9
    
    print(f"Plotting {name} at {actual_freq:.2f} GHz")
    
    # Extract S-params at this frequency
    s11 = ntwk.s[idx, 0, 0]
    s21 = ntwk.s[idx, 1, 0]
    s12 = ntwk.s[idx, 0, 1]
    s22 = ntwk.s[idx, 1, 1]
    
    delta = s11*s22 - s12*s21
    
    # Source stability circle (Input)
    Cs = np.conj(s11 - delta * np.conj(s22)) / (np.abs(s11)**2 - np.abs(delta)**2)
    Rs = np.abs(s12 * s21) / np.abs(np.abs(s11)**2 - np.abs(delta)**2)
    
    # Load stability circle (Output)
    Cl = np.conj(s22 - delta * np.conj(s11)) / (np.abs(s22)**2 - np.abs(delta)**2)
    Rl = np.abs(s12 * s21) / np.abs(np.abs(s22)**2 - np.abs(delta)**2)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    rf.plotting.smith(ax=ax, draw_labels=True)
    
    # Generate circle points
    theta = np.linspace(0, 2*np.pi, 100)
    
    source_circle = Cs + Rs * np.exp(1j * theta)
    load_circle = Cl + Rl * np.exp(1j * theta)
    
    ax.plot(np.real(source_circle), np.imag(source_circle), 'r-', linewidth=2, label=f'Source Stability Circle ({actual_freq:.2f} GHz)')
    ax.plot(np.real(load_circle), np.imag(load_circle), 'b-', linewidth=2, label=f'Load Stability Circle ({actual_freq:.2f} GHz)')
    
    # Shade forbidden regions (if |S11| < 1, center is stable, outside circle is unstable)
    # This is a simplification; shading requires exact stability conditions.
    
    ax.set_title(f'{name} Stability Circles at {actual_freq:.2f} GHz')
    ax.legend(loc='upper right')
    
    out_name = f"{name.split()[2].lower()}_stability_{int(actual_freq)}GHz.png"
    plt.savefig(out_name, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {out_name}")
    plt.close()

if __name__ == "__main__":
    plot_stability("30 GHz LNA", "lna_350GHz.s2p", 27.5)
    plot_stability("30 GHz LNA", "lna_350GHz.s2p", 30.0)
    plot_stability("30 GHz PA", "pa_350GHz.s2p", 28.8)
    plot_stability("30 GHz PA", "pa_350GHz.s2p", 30.0)
