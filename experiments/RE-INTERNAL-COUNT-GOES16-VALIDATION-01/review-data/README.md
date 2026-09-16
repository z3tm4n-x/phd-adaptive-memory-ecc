# Existing trial records for independent review

Published at the user's explicit request to make the existing trial-level
records accessible to the reviewer. This narrowly extends the original
outside-Git storage arrangement for this 3.85 MB review bundle only.
No experiment was rerun; code, configurations, samples and scientific outputs
from delivery `c0dd38ab3c01917e8e4bb165ecfae122b86dd9ae` are unchanged.
This transfer assigns no review verdict or scientific acceptance.

[Download the ZIP](RE-INTERNAL-COUNT-GOES16-VALIDATION-01-trials-c0dd38a.zip)

ZIP size: 3,847,091 bytes. SHA-256:
`b252c9f7fcc8155e484f5cb05f5f42216e0e53cb4983114c41583943ba5777d5`.

The ZIP contains exactly these three unchanged files at its root. Their hashes
were checked both before packaging and by reading each ZIP entry against the
[original manifest](../outputs/raw_results_manifest.json):

| File | Bytes | SHA-256 |
|---|---:|---|
| growth_trials.npz | 1321598 | d3829610cc6918a3f9a7ed9d9c9c936086ca43333640f605a3c3dabbdc03daa9 |
| peak_trials.npz | 1328625 | 49b420c08ca88e99a6df9ac4c27fe44742411eb07d3e1b7361857d0576e100ae |
| typical_trials.npz | 1326322 | 99abf83e635ee999e75c4a23345f1b59b3dbb3bb6685585afdfd5f5a7f1589a4 |

Each NPZ has `samples[20000,5,8]`, `event_hashes`, `event_counts`, and
`utc_index`. Policy order and all eight sample fields are documented in
[REPRODUCE.md, section 4](../REPRODUCE.md#4-storage-and-provenance).
Reading these saved arrays requires NumPy, not h5py, numba or llvmlite.
The original manifests remain immutable historical provenance; their Windows
paths describe the execution host, while this bundle supplies remote access.
