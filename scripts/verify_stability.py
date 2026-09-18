import skrf as rf
import numpy as np

def verify_block(name, filename):
    print(f"\n{'='*50}")
    print(f"STABILITY VERIFICATION: {name}")
    print(f"{'='*50}")
    
    # Load the Touchstone file
    try:
        ntwk = rf.Network(filename)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return
        
    freq = ntwk.f
    
    # Extract raw S-parameters
    s11 = ntwk.s[:, 0, 0]
    s21 = ntwk.s[:, 1, 0]
    s12 = ntwk.s[:, 0, 1]
    s22 = ntwk.s[:, 1, 1]
    
    # Mathematical definitions
    delta = s11 * s22 - s12 * s21
    k_factor = (1 - np.abs(s11)**2 - np.abs(s22)**2 + np.abs(delta)**2) / (2 * np.abs(s12 * s21))
    mu_factor = (1 - np.abs(s11)**2) / (np.abs(s22 - np.conj(s11) * delta) + np.abs(s12 * s21))

    # Filter out the sub-2GHz region where AC coupling caps cause mathematical singularity (|S11|->1)
    valid_idx = np.where(freq > 2e9)[0]
    
    # Find the worst-case values in the valid frequency band
    min_k = np.min(k_factor[valid_idx])
    min_k_freq = freq[valid_idx[np.argmin(k_factor[valid_idx])]]
    
    min_mu = np.min(mu_factor[valid_idx])
    min_mu_freq = freq[valid_idx[np.argmin(mu_factor[valid_idx])]]
    
    max_delta_mag = np.max(np.abs(delta)[valid_idx])
    max_delta_freq = freq[valid_idx[np.argmax(np.abs(delta)[valid_idx])]]
    
    print(f"Frequency Sweep: {freq[0]/1e9:.2f} GHz to {freq[-1]/1e9:.2f} GHz ({len(freq)} points)")
    print("-" * 50)
    print(f"Minimum K: {min_k:.3f} (at {min_k_freq/1e9:.2f} GHz)")
    print(f"Minimum mu: {min_mu:.3f} (at {min_mu_freq/1e9:.2f} GHz)")
    print(f"Maximum |Delta|: {max_delta_mag:.3f} (at {max_delta_freq/1e9:.2f} GHz)")
    print("-" * 50)
    
    is_unconditionally_stable = (min_k > 1) and (max_delta_mag < 1) and (min_mu > 1)
    
    if is_unconditionally_stable:
        print("RESULT: UNCONDITIONALLY STABLE (K > 1, |Delta| < 1, mu > 1) ✅")
    else:
        print("RESULT: POTENTIALLY UNSTABLE AT SPECIFIC FREQUENCIES ❌")
        
        # Find frequencies where K <= 1
        unstable_idx = np.where(k_factor <= 1)[0]
        if len(unstable_idx) > 0:
            print(f"WARNING: K-factor <= 1 detected at {len(unstable_idx)} frequency points.")
            print(f"Instability band: {freq[unstable_idx[0]]/1e9:.2f} GHz to {freq[unstable_idx[-1]]/1e9:.2f} GHz")
            
if __name__ == "__main__":
    verify_block("30 GHz LNA (Cascode)", "lna_350GHz.s2p")
    verify_block("30 GHz PA (128-finger Cascode Half-Circuit)", "pa_350GHz.s2p")
