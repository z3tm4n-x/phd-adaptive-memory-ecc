# Reproduce the bounded conditional result

Run in a clone with the delivered branch checked out. Do not check out/rewrite
old scientific packages. Commands below use PowerShell and Python3.12.
The delivery SHA in the user-facing publication message identifies the code.

```powershell
git fetch origin a9d9b74b9ac03a4eb20b209eb14552d5b914e21a
git fetch origin d59de85eb46ae1fa254f3b936ce6fa64c28bcff0
Set-Location experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01/reference-continuation-01
python calculate.py --output bounds.json
python check_bounds.py
python -m unittest -v test_reference
python -m compileall -q .
```

The first command uses exact decimals as fractions and checks input SHA/metadata.
The checker does not import that calculator. No random numbers, seeds, transport
or Monte Carlo are used. bounds.json is deterministic; validation timestamps/
duration/host paths are not expected to be byte-identical across machines.

## Source-to-pin regeneration (optional repeat of primary-file extraction)

Download the three PDF files to the relative local paths in source_manifest.json.
Download the AMD a7all.zip to its recorded relative path. Those paths resolve
to the workspace sibling tmp/pdfs/cy62167-reference directory. Check every
SHA256 before extraction. Full PDFs and ZIP are not committed.

```powershell
python -m pip install --target ../../../../tmp/cy62167-tools pdfplumber==0.11.9 pypdf==6.10.0 pyslang==9.1.0
$env:PYTHONPATH = (Resolve-Path ../../../../tmp/cy62167-tools).Path
python make_pins.py
```

This rebuilds pinmap.json and reference_pins.xdc deterministically from primary
bytes; verifies uniqueness and power-bank assignment. The SRAM pin expansion
is the visually checked Figure5 transcription; bank identity is independently
joined from AMD's package member. No layout/STA check is implied.

## Actual RTL execution

Icarus13.0 portable Windows tool was assembled without system installation.
TOOLS.json lists every archive URL suffix and published SHA256. Use the
following in the package directory (requires network; do not skip hash checks):

```powershell
$ErrorActionPreference = 'Stop'
$toolRoot = [IO.Path]::GetFullPath((Join-Path (Get-Location) '../../../../tmp/iverilog'))
New-Item -ItemType Directory -Force $toolRoot | Out-Null
$toolSpec = Get-Content -Raw TOOLS.json | ConvertFrom-Json
foreach ($item in $toolSpec.archives) {
    $target = Join-Path $toolRoot $item.local
    Invoke-WebRequest -Uri ($toolSpec.url_prefix + $item.file) -OutFile $target
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower() -ne $item.sha256) {
        throw ('Tool hash mismatch: ' + $item.file)
    }
    tar -xf $target -C $toolRoot
    if ($LASTEXITCODE -ne 0) { throw 'Tool archive extraction failed' }
}
python run_rtl.py
python check_rtl.py
python validate.py
python audit_delivery.py
```

run_rtl.py creates vectors and compiled/mutated simulation files under tmp/iverilog,
never in earlier packages. Its child-process PATH includes the portable DLLs.
IVERILOG_BIN may point to an equivalent verified Windows bin directory.
The preserved command/output logs include harmless Icarus sensitivity-widening
warnings. Two deliberately wrong RTL mutants must compile AND fail simulation;
a compiler error does not count as a rejected mutant.

validate.py requires pyslang9.1.0 available through PYTHONPATH. In the execution
environment its native DLL required approved unsandboxed execution; no sandbox
disable is performed by scripts. check_rtl.py uses ASCII relative filenames
because this build's absolute Cyrillic filename handling failed.

Tests and recorded scopes:

- reference_tb: 3955 vectors; nominal ideal digital SRAM stub; no analog timing.
- schedule_tb: five prep launches and an explicitly injected near-epoch state,
  then1024 scrub reservations,3069 legal saturated reads, soft/hard reset and
  incomplete-preparation boundary rejection. It does not simulate24h or all
  524288 prep writes. Calendar gaps are exhaustively checked analytically/
  numerically in check_bounds.py.
- No Vivado route, XDC application, min/max hold report, SRAM hardware or
  full physical-transfer verification was executed. These remain conditions,
  not commands claimed to have succeeded.

## Preservation and publication checks

```powershell
git diff 003c2346c4135b3d2f24dac0981e60cb2f179384 HEAD --name-only
git log --format='%H %P' -2
git ls-remote --heads origin research/cy62167-executor-timing-gate-01
```

All committed changes since003c must be under this reference-continuation-01
directory. MANIFEST includes before/after SHA256 for the original five Stage-0
files and exact canonical input blobs. audit_delivery also detects unrelated
CSV status entries whose raw bytes equal HEAD; it does not normalize/edit them.
Re-running validation changes local run logs; do not amend the immutable
delivered commit merely to replace timestamps.
