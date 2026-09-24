# Reproduction — RE-INTERNAL-COUNT-GOES16-VALIDATION-01

Tested on Windows 11 x64, Python 3.12.14. Exact package versions in
outputs/environment.json. Commands below assume repository-root PowerShell,
a short external working directory (e.g. C:/work/g16), and authenticated Git
access if required. Do not put downloaded files, JIT caches or raw trials in Git.
No historical package needs editing. Scientific execution is frozen at
870a3c5d725793dd45ff2cc2feaf6e8885df0df9; the delivery adds only postprocessing/docs.

## 1. Environment and inputs

```powershell
$task = 'experiments/RE-INTERNAL-COUNT-GOES16-VALIDATION-01'
$external = 'C:/work/g16'
New-Item -ItemType Directory -Force $external
py -3.12 -m venv "$external/venv"
$python = "$external/venv/Scripts/python.exe"
& $python -m pip install numpy==2.3.5 scipy==1.18.1 numba==0.67.0 llvmlite==0.49.0 h5py==3.16.0 matplotlib==3.11.2 psutil==7.2.2
$env:OPENBLAS_NUM_THREADS='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:NUMBA_CACHE_DIR="$external/jit"
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='core.longpaths'
$env:GIT_CONFIG_VALUE_0='true'
git clone https://github.com/z3tm4n-x/RADAR "$external/radar"
git -C "$external/radar" checkout --detach b032505d4d1b15403b8ad06aef578339f6d1c6b4
New-Item -ItemType Directory -Force "$external/raw"
$manifest=Get-Content "$task/input_manifest.json" -Raw | ConvertFrom-Json
foreach ($file in $manifest.files) {
    curl.exe -fL --retry 3 $file.url -o "$external/raw/$($file.name)"
    $actual=(Get-FileHash "$external/raw/$($file.name)" -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $file.sha256) { throw "Input hash mismatch: $($file.name)" }
}
& $python "$task/prepare.py" --raw "$external/raw" --radar "$external/radar" --cache "$external/cache" --out "$external/rebuilt-input"
(Get-FileHash "$external/rebuilt-input/derived_rates.csv" -Algorithm SHA256).Hash
```

Expected derived-rate hash:
e3a1ce8f2a33cd9a60b22039c86ae8f1f7214458850d5a0b609042eace1bc3ac.
Manifest retrieval timestamps, absolute paths and elapsed times are host-dependent;
their regeneration does not replace the frozen input manifest. Compare scientific
tables/arrays, not those host fields. Use a fresh cache to repeat RADAR transport;
a populated cache skips the expensive rebuild. Do not assume cache validity:
compare transport array hashes with input_manifest.json.

prepare writes JSON with the host newline convention. The committed task JSON
is LF. On a Windows checkout obey the task .gitattributes (eol=lf); do not rewrite
frozen manifests in place. The production prereg guard checks exact code/config/
input bytes against the prereg commit and all listed upstream hashes.
On a different checkout, preserve the original upstream bytes; unexpected hash
differences require investigation, not disabling the guard.

## 2. Tests and fixed production

```powershell
& $python "$task/check.py" --raw "$external/raw" --cache "$external/cache" --out "$external/checks.json"
& $python -m compileall -q $task
$prereg='870a3c5d725793dd45ff2cc2feaf6e8885df0df9'
foreach ($case in @('growth','peak','typical')) {
    & $python "$task/experiment.py" --case $case --prereg $prereg --out "$external/production"
    if ($LASTEXITCODE -ne 0) { throw "Execution failed: $case" }
}
& $python "$task/deliver.py" --raw-results "$external/production" --prereg $prereg
```

deliver deliberately rewrites only task outputs. Use a disposable checkout if
comparing with the publication snapshot. The procedure reruns no CTMC sweeps.
Three independent case processes are also allowed; seed allocation and streams
do not depend on batches or scheduling. The production run shown here used
three case processes, each OPENBLAS_NUM_THREADS=1.

Expected: 20000 trials per case, five policies; no computational failures.
Risk counts, ordered [Proposed,disabled,Fixed,Precomputed,PA-DOM]:
growth [24,3,2,2,35], peak [40,3,2,5,87], typical [0,0,0,0,0].
11 unit tests, no failures/errors; compileall exit0.
Independent convolution relative discrepancy <=6.67e-16, selected indices
[732,753,157]. Floor .07667519552414698, delta .00021960410931119292,
s0 .023324804475853028. See checks_preproduction.json.

Runtime on the recorded host: input preparation (including fresh matrix
construction) 22.86 s; production growth56.82, peak59.40, typical47.94 s including
kernel building/JIT use and serialization. These overlap, not three additive
wall-clock intervals. Peak process working sets: 201469952, 202067968, 201048064
bytes. Fresh dependency installation/downloads are additional; allow minutes,
not a hardware WCET claim. Postprocessing/replay approximately 9 s.
Raw trial archives are approximately 1.3 MB each, outside Git.

## 3. What is independently checked, what is reproduced

check.py's explicit all-word chronological oracle owns sets of erroneous bits,
check epochs, toggle updates, corrected counts, first passage and completed pass
counts. It never calls the production physical update. It shares original
controller _choose/_observe/_analog_next and numerical tables; it is not an
independent proof of those controller functions. Deterministic boundaries plus
80 randomized streams x5 policies compare failure time, pass count and every
completed [start,period,end,count,pending] trace row. The mutation sentinel merges
two distinct word addresses in production; the independent oracle rejects its
spurious first passage.

Input checks independently sum trapezoids and transport-matrix products on ten
direction/rows, directly check raw unit conversion/direction and all array
normalizations. Spectral reconstruction, sigma and transport matrices are shared:
this is not independent validation of RADAR physics or instrument calibration.
Fixed300 test explicitly enumerates W word offsets on two synthetic profiles
against the exact-rational formula. The full profiles then use that same formula.

deliver regenerates all 60000 streams and their hashes and replays trials
[0,1,2,19999] for every case/policy (60 executions), exact numeric equality.
It recomputes all aggregate CSVs byte-for-byte and independently totals events,
survival costs and paired counts. These are reproducibility checks, not a second
simulation engine. A separate full input rebuild from fresh RADAR matrices is
recorded in final_checks.json. Original package files remain unstaged/unedited.

## 4. Storage and provenance

Raw local directory on execution host:
`C:/Users/Иван/.codex/.chatgpt-projects/g-p-6a8f0744f95081919477f597a4962b6b/tmp/goes16-production`.
Input files: sibling goes16-input; transport/spectral cache: goes16-cache;
RADAR clone: radar-b032; fresh rebuild: goes16-rebuild-cache/goes16-rebuild-input.
These local paths are not a public download service. Public source URLs,
fixed seeds and code are sufficient to regenerate them.

NPZ schema: samples[20000,5,8] fields failure,complete passes,busy seconds,reads,
writes,first-failure-or-H seconds,updates,sum internal risk rewards;
event_hashes[20000], event_counts[20000], utc_index. Policy order is fixed.
Each event hash covers little-endian float64 times, int32 words, int8 bits
concatenated in that order. Trial schema stores no removed observations.
Failing computations would remain NaN plus failure records and would suppress
the corresponding complete-sample inference. None occurred.

Raw file and array hashes: outputs/raw_results_manifest.json.
Small deliverable hashes: outputs/output_hashes.json. Run metadata contains
runtime; image SVG IDs are salted deterministically, creation date suppressed.
Hashes of host-specific metadata can differ after reproduction.

Windows note: initial long-path JIT writes failed; short cache resolves it.
Initial production launches stopped inside git-show before stream generation;
process-local core.longpaths=true resolves it without modifying execution code.
Ten old CSVs appear dirty due to tracked CRLF/attributes even at fresh checkout,
but their raw blobs match base. Twenty-five other files underwent only checkout
newline conversion (listed with before/after hashes in preservation.json).
No content difference, historical rewrite or staged old path is accepted.
The committed Git tree outside this task must equal the base exactly.
