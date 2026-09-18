#!/bin/bash
rm -f *.prn
for f in 30ghz_lna_standalone.cir 30ghz_if_amp_standalone.cir 30ghz_mixer_standalone.cir 30ghz_pa_standalone.cir 30ghz_vco_standalone.cir 30ghz_rx_chain.cir 30ghz_tx_chain.cir 30ghz_frontend_v65.cir; do
  echo "Running $f"
  Xyce "$f" > /dev/null
done
python3 parse_results.py
