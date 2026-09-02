# RE-GOES19-PROTON-RATE-01 — reproduction commands

## Inputs

- Unpack the exact GOES archive listed in `input_manifest.json`.
- Check out RADAR at `b032505d4d1b15403b8ad06aef578339f6d1c6b4` outside this repository.
- Use `experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv` from the task starting history.

## Commands

```bash
python -m pip install numpy h5py pytest
python -m unittest -v experiments/RE-GOES19-PROTON-RATE-01/test_rate_pipeline.py

# In a Python 3.12 environment with pinned RADAR dependencies installed:
python experiments/RE-GOES19-PROTON-RATE-01/radar_converged.py \
  --radar-root /path/to/RADAR \
  --sigma-csv experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv \
  --out /tmp/re-goes19-radar

python experiments/RE-GOES19-PROTON-RATE-01/rate_pipeline.py \
  --goes-dir /path/to/unpacked/goes010226 \
  --transport /tmp/re-goes19-radar/radar_transport.npz \
  --sigma-csv experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv \
  --out /tmp/re-goes19-rate
```

Pinned RADAR GitHub Actions validation run used for the released transport: `33621228858` (21 shielding tests PASS; converged 192-point production matrix).

## Expected core output SHA-256

- `goes19_audit.json`: `fbc53e60d28cff3a8aaf8d518cd3b4fcb45d2dafbe08a64f4d13e5ed51d06ee1`
- `sigma_bit_model.csv`: `11656dc74600d7a1955c6f25ecd46da71ced586f891ac27d47a393bc87febc83`
- `summary_by_shielding.csv`: `6ea8d227b12851cb5e33f47a5dfa6bd51de91ee60983714351688203b4bc0d95`
- `proton_rate_5min.csv`: `713eceb0df3faa4ea0eb50f6381c5a26cfb77a969f82e059f58815e8469f1e09`
- `radar_validation.json`: `c7b01f28d8fd395f62be32b54413d5e38c461d2e18aa779321ea03f6eea3f772`
- `rate_diagnostics.json`: `b051ccfc26008b81e43644d1326e25696a89e3fdfccd1da1301c234db036ddcf`

Note: after any intentional output-schema change, hashes must be regenerated and `validation_report.json` updated.

## Public archive drift

On 2026-09-02, a bytewise re-check against the then-current NOAA archive found 52/59 files unchanged and seven revised public files dated 2026-01-14 through 2026-01-20. Reproduction of this task must use the PI-controlled files matching `goes_files.sha256`; downloading current files by filename alone is not sufficient for those seven dates.


## Final controlled branch release

The final branch artifact is described by `final_release_manifest.json`. NOAA revised seven source files after the PI-controlled archive was captured. `noaa_revision_semantic_patch.json` restores the changed scientific dataset values; after restoration, all 59 HDF5/NetCDF dataset arrays have the exact controlled data-layer SHA-256 `f745cead0ffa2b76d4b9fdd6c236f873c46054880c3aaf2c5e4be94070826815`.

The pinned RADAR transport remains the validated artifact from Actions run `33621228858`. Output floating-point CSV bytes can vary in the last digits across Python/NumPy/host implementations, so the final release uses exact input/artifact fingerprints plus a numerical invariant gate. The authoritative SHA-256 values for the committed branch outputs are recorded in `final_release_manifest.json`.
