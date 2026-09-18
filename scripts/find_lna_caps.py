import os, subprocess, re

orig = open('30ghz_lna_standalone.cir').read()

best_gain = -999
best_c = 0

print('Sweeping C_lna_res...')
for c in range(100, 250, 10):
    text = re.sub(r'C_lna_res lna_out 0 \d+f', f'C_lna_res lna_out 0 {c}f', orig)
    open('30ghz_lna_standalone.cir', 'w').write(text)
    
    subprocess.run(['Xyce', '30ghz_lna_standalone.cir'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        out = subprocess.check_output(['python3', 'parse_results.py', '30ghz_lna_standalone.cir']).decode()
        for line in out.split('\n'):
            if 'Voltage Gain:' in line:
                val = float(line.split(':')[1].split('dB')[0].strip())
                if val > best_gain:
                    best_gain = val
                    best_c = c
                print(f'C = {c}f -> Gain = {val:.1f} dB')
    except:
        pass

print(f'Best C = {best_c}f with Gain = {best_gain:.1f} dB')
open('30ghz_lna_standalone.cir', 'w').write(orig)
