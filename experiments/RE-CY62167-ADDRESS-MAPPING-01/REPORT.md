# RE-CY62167-ADDRESS-MAPPING-01 — transformed XY → external address

## Result

**Disposition: B — MAPPING RECOVERED WITH BOUNDED EXCEPTIONS.**

For ordinary three-integer records, the supplied transformed CY62167 XY coordinates admit an exact reproducible affine mapping to the external `2^21 x 8` address space. The model was fitted **only** on `clust_C720MeV.txt`: GF(2) feature rank is `25/25`, the affine solution is unique in the declared model class, training residuals are `0/5122`, and frozen validation gives `0/143590` mismatches. The only exceptions are an independently recognizable zero/service-like class: 18 records are `AMBIGUOUS`, five of them address-bearing and all five inconsistent with the ordinary mapping. They were excluded by pre-fit record signatures, never by mapping residual.

Permitted conclusion: **the supplied transformed physical-map coordinates admit a reproducible empirical mapping to the external ×8 address space over the observed ordinary CY62167 irradiation records.** This does **not** recover the proprietary `A → internal ECC word/parity` layer.

## 1. Raw provenance

The handoff names `New Folder(1).zip`; the actually uploaded mandatory input is `New Folder(3).zip`. This filename difference is the only input-name deviation.

Before any member payload is read, the script records ZIP metadata and archive hash. Supplied archive:

- size `5,016,468` bytes;
- SHA-256 `16ab27789329adbbccdf9a7e5d0e15e855440d3f52b8dd93a384317a4635770a`;
- 28 raw TXT members;
- `22,866,004` uncompressed bytes.

After that pre-read step each member is independently MD5/SHA-256 hashed. All 28 MD5s match the public Zenodo `10.5281/zenodo.8314389` checksums. `input_manifest.json` records member listing and provenance. Raw irradiation files are not committed.

## 2. Semantics of three integer fields

The status is deliberately layered.

**SOURCE-SUPPORTED:** CY62167GE30-45ZXI is a 16-Mbit SRAM externally organized as `2^21 x 8`; controlled campaign literature states that manufacturer logical-to-physical descrambling information was used to construct the XY physical-map representation; exact proprietary ECC mapping is not public.

**SOURCE-SUPPORTED raw-format fact:** timestamped cell rows contain three integers. Existing controlled parsing therefore preserved them conservatively as `(field0_raw,x,y)`; the available public raw documentation does not explicitly label the first column as external address.

**EMPIRICALLY ESTABLISHED:** ordinary leading integers lie in the 21-bit external-address range after model-independent service filtering; one C720-only affine map exactly reproduces every ordinary independent address-bearing irradiation series; its algebra maps `2^24` supplied grid positions to `2^21` addresses with eight preimages per address.

**INFERENCE:** for the ordinary three-field population, the data identify the semantics as `(A,x,y)` with very strong empirical support, where `A` is the external 21-bit byte address.

**UNKNOWN:** semantics of the bounded zero/service-like class; D0…D7 assignment among same-address grid positions; proprietary `A → ECC word/parity` mapping.

The same classification is machine-readable in `data_contract.json`.

## 3. Parser, eligibility, and deduplication

All `173835` clusters parse with exact `NUMBER OF EVENTS == parsed cell rows`; all header XY bounds match parsed cells; no coordinate exceeds the declared 12-bit `0..4095` grid. Total raw cells: `299154` = `150403` two-field + `148751` three-field.

Pre-fit classes:

| class | rows |
|---|---:|
| PHYSICAL_ELIGIBLE | 148731 |
| PHYSICAL_NO_ADDRESS | 150390 |
| STRICT_SERVICE | 15 |
| AMBIGUOUS | 18 |

`STRICT_SERVICE` requires the already established `03:03:03` + all-zero singleton signature plus a leading integer outside the 21-bit address range. In-range `03:03:03` all-zero singleton rows are `AMBIGUOUS`; non-timestamped two-field cluster-0 all-zero rows are also `AMBIGUOUS`. No rule depends on fitted residuals.

Event-local deduplication key is `(source_file,segment_id,cluster_id,x,y)`. A conflicting address for one such key is reported rather than resolved. No conflicts occur. Nineteen duplicates are removed: `148731` primary raw rows → `148712` deduplicated rows. Full primary unique `(A,x,y)` count is `147785`.

## 4. Training and identifiability

Only `clust_C720MeV.txt` participates in fit/feature selection. It contributes `5122` eligible records, `5122` after event-local deduplication, and `5122` unique triples.

For

`X=[1,x0,…,x11,y0,…,y11]`,

`rank_GF(2)(X)=25`.

Thus each 21 address-bit equation has one unique affine coefficient vector in this model class; no representative is chosen from an underdetermined family.

## 5. Recovered equations

All operations are XOR/GF(2), bits LSB-indexed:

```text
A0  = y4
A1  = y11
A2  = 1 xor x10 xor x11
A3  = 1 xor x9 xor x11
A4  = 1 xor x8 xor x11
A5  = 1 xor y10 xor y11
A6  = 1 xor x3 xor x8
A7  = y0
A8  = 1 xor x7 xor x8
A9  = 1 xor x2 xor x8
A10 = y8
A11 = y5
A12 = y6
A13 = y7
A14 = y3
A15 = y9
A16 = y2
A17 = y1
A18 = 1 xor x0 xor x8
A19 = 1 xor x1 xor x8
A20 = x11
```

Affine constant at `(x,y)=(0,0)` is `A=787324`. Exact feature order, coefficient masks/matrix representation and equations are exported in `address_mapping_coefficients.json` and `address_mapping_equations.md`. Training mismatches: **0**.

## 6. Strict held-out validation

After fitting, coefficients are frozen. Other address-bearing files are validation only.

- held-out primary raw: `143609`;
- event-local duplicates removed: `19`;
- held-out checks: `143590`;
- exact matches: `143590`;
- mismatches: **0**;
- total held-out unique triples: `142707`;
- novel held-out triples not seen in training: `142663`;
- held-out/training overlap: `44`;
- full-dataset unique triples: `147785`.

Every ordinary held-out file has zero failures. Counts per file are in `heldout_by_file.csv`; `validation_summary.json` contains an empty ordinary mismatch list and explicit no-leakage guards. Two-field files remain parsed/provenanced but cannot validate `A` because they contain no candidate address.

## 7. Ambiguous-record audit

`ambiguous_records.csv` preserves full context for all 15 strict-service and 18 ambiguous rows. Among the 18 ambiguous rows, 13 are two-field all-zero records with no observed address. Five are address-bearing `03:03:03` all-zero singleton records:

- four have observed leading integer `0`;
- `clust_U142.8GeV.txt` has `640`;
- all have `(x,y)=(0,0)`, for which the ordinary mapping predicts `787324`.

Hence all five address-bearing ambiguous rows mismatch the ordinary mapping. This is diagnostic only: it neither proves they are service records nor weakens the exact result for the separately defined ordinary population. This bounded unresolved class is the reason for disposition B rather than A.

## 8. Algebraic structure

Write `A=c xor Mz`, `z=(x0…x11,y0…y11)`. The recovered linear part has:

- `rank_GF(2)(M)=21`;
- `dim ker(M)=3`;
- kernel basis `{x4,x5,x6}`;
- XOR coordinate deltas `(16,0)`, `(32,0)`, `(64,0)`;
- eight preimages for every external address.

Because the supplied grid has `4096×4096=2^24` positions and external byte address has `2^21` values, `2^24/2^21=8`. **External ×8 consistency: PASS.** This is an internal algebraic consistency check, not evidence for banks, transistor layout or D0…D7 labels. A 16-step relation follows mathematically from `x4` in the transformed grid only.

## 9. `W32_seq` downstream scenario

Defined only as

`W32_seq(x,y)=floor(A(x,y)/4)`.

Semantics: four consecutive external ×8 addresses are treated as the 32 data cells of one analysis codeword. It is **not** the actual manufacturer ECC map.

For this scenario: linear rank `19`, kernel dimension `5`, 32 supplied-grid positions per scenario word, kernel basis `{x4,x5,x6,y4,y10 xor y11}`. The minimum nonzero supplied-grid displacement is 16 (via `x4` or `y4`). A nominal 16-step relation therefore emerges mathematically, but does not prove manufacturer 16-bit interleaving or parity placement.

## 10. Required answers

1. Three fields: ordinary rows are empirically identified as `(A,x,y)`; first-field address semantics are not directly documented in the raw text specification.
2. Primary dataset: only pre-model `PHYSICAL_ELIGIBLE` three-field rows.
3. Training correspondences: `5122`; GF(2)-independent feature directions: `25`.
4. Feature rank: `25`.
5. Unique affine mapping: **YES**.
6. Equations: Section 5 / exported files.
7. Training residuals: `0/5122`.
8. Held-out residuals: `0/143590` ordinary checks.
9. File-specific ordinary failures: none.
10. Ambiguous records: 18; five address-bearing mismatches, 13 with no observed address.
11. Linear rank/kernel: `21`, dimension `3`, basis `{x4,x5,x6}`.
12. External `2^21 x8` consistency: **PASS**.
13. `(x,y)→A`: reproducibly recovered and independently validated for ordinary records.
14. `A→W`: proprietary data/parity ECC organization remains unknown.
15. `W32_seq`: valid declared scenario with 32 grid positions/word and a 16-step relation; **not actual proprietary W**.

## 11. Reproducibility

Commands used:

```bash
python address_mapping.py --archive '/mnt/data/New Folder(3).zip' --output-dir .
CY62167_ARCHIVE='/mnt/data/New Folder(3).zip' python -m unittest -v
python -m compileall .
```

Tests cover parser integrity, classification invariants, event-local dedup/conflicts, exact GF(2) rank, known synthetic affine recovery, rank-deficient detection, exact 21-bit reconstruction, training/held-out guard, order independence, exported-equation/coefficient equivalence, archive checksum/parser integration, and direct full-primary evaluation. **12/12 passed; compileall passed.**

The execution container has no direct GitHub network clone; repository state is read/written through the authorized GitHub connector. This does not affect raw-data calculations. No raw data are committed.

## 12. Next scientific step

Do not revisit GOES/RADAR/rate or ordinary `(x,y)→A`. The next bounded task should consume this exact mapping and address the residual **`A→W` uncertainty together with already established observation-process censoring**. `W32_seq` may be used as one explicitly labeled scenario/identified-set input, not promoted to manufacturer truth.
