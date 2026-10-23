# Distance audit for multivariate multicycle codes

This directory contains the construction inputs, saved matrices, randomized
distance-search results, logical witnesses, and connected-cluster records
used to audit the code parameters reported in the manuscript.

We distinguish **verified upper bounds** from **certified exact distances**.
A verified nontrivial logical operator establishes an upper bound on the
distance. An exact distance requires a matching lower bound from completed
connected-cluster searches.

## Directory guide

All paths below are relative to `Distance Audit/`.

| Path | Contents |
|---|---|
| `code/` | Construction registry, audit scripts, search wrappers, and witness-verification scripts |
| `results/sqetch_100M/` | Original sQetch searches requesting 100 million trials per CSS sector |
| `results/sqetch_150M_rerun38/` | Additional sQetch searches requesting 150 million trials per sector for 38 selected instances |
| `results/distm4ri/` | Earlier dist-m4ri random-window searches and saved outputs |
| `connected_cluster/` | Original connected-cluster certification campaign |
| `connected_cluster_tableI/` | Additional certification campaign for three Table I instances |
| `four_codes_rw_20261016T195147Z/` | Additional random-window searches for four larger instances |
| `final/` | Consolidated distance tables and logical-witness collections |
| `Original Archives/` | Original ZIP archives of the uploaded cluster results |

The two connected-cluster folders contain separate campaigns. Each preserves
its own input matrices, manifest, scripts, logs, and results.

## Current status of the consolidated tables

The Table I addendum and the four-code random-window campaign are now available
in this directory, including their detailed search records.

**The consolidated files in `final/` have not yet been fully reconciled with
these additions.** In particular, `final/distance_bounds_revised.csv` still
contains historical entries labelled `sQetch, unverified (dagger)` for
`table3_row025`, `table3_row027`, `table4_row023`, and `table4_row026`.
Those entries must not be interpreted as verified upper bounds.

Until the consolidated tables are updated, consult the supporting campaign
records for the additional results. Historical outputs are retained for
provenance; their presence does not mean that every historical estimate remains
a reported manuscript value.

## Construction and structural checks

The construction registry records the defining polynomials and moduli for
each instance. The Julia audit reconstructs the codes using the
`MultivariateMulticycle` constructor in QuantumClifford.jl with Oscar.

The structural audit checks:

- CSS commutation over GF(2);
- the number of physical qubits, obtained from the number of matrix columns;
- the number of logical qubits,
  `k = n - rank(HX) - rank(HZ)`, using ranks over GF(2);
- parity-check row weights;
- the applicable metacheck identities.

An independent Python reconstruction is included in `code/`.

## Sector conventions and logical witnesses

For the saved binary parity-check matrices `HX` and `HZ`:

- An **X-sector** logical support `v` satisfies `HZ * v = 0` and lies outside
  the row space of `HX`.
- A **Z-sector** logical support `v` satisfies `HX * v = 0` and lies outside
  the row space of `HZ`.

A verified support of weight `w` establishes `dX <= w` or `dZ <= w`,
respectively. The overall CSS distance is `d = min(dX, dZ)`.

Witness supports recorded as one-based indices refer to columns of the
associated saved matrices. A witness must be checked against those matrices
and their qubit ordering.

Code names, block lengths, and logical dimensions alone do not establish that
two instances are the same code. Transferring a distance result requires an
appropriate matrix comparison or an explicit equivalence.

## Randomized distance searches

### sQetch campaigns

The original sQetch campaign requested 100 million trials per CSS sector with
sketch dimension 64. A subsequent campaign requested 150 million trials per
sector for 38 selected instances.

The outputs, parameter records, and available environment information are
preserved under `results/sqetch_100M/` and
`results/sqetch_150M_rerun38/`.

A scalar estimate does not itself provide a saved logical witness. Candidate
values must be supported by a valid nontrivial logical operator before they
are treated as verified upper bounds. Increasing the number of randomized
trials does not establish a lower bound or certify an exact distance.

### dist-m4ri random-window searches

The random-window algorithm searches for nontrivial logical operators.
Saved supports can be verified by checking their syndrome, stabilizer
membership, and weight.

The earlier search outputs are stored under `results/distm4ri/`.

The additional campaign in `four_codes_rw_20261016T195147Z/` covers:

| Registry ID | Physical qubits `n` | Logical qubits `k` |
|---|---:|---:|
| `table3_row025` | 840 | 18 |
| `table3_row027` | 864 | 12 |
| `table4_row023` | 672 | 12 |
| `table4_row026` | 768 | 12 |

Its saved script invokes dist-m4ri with:

- random-window search: `method=1`;
- a limit of `steps=100000000`;
- a time limit of `timeout=1800` seconds per sector;
- one thread per search: `threads=1`;
- confinement-profile computation disabled: `smax=0`;
- seeds 202610161 through 202610168 across the eight sector searches.

The step count is a requested limit, not a statement that every run completed
100 million steps. The saved output records the work actually performed.

The campaign preserves:

- `binary_sha256.txt` and `dist_m4ri_help.txt`;
- `run_script.sh`;
- the input `HX.mtx` and `HZ.mtx` for each instance;
- matrix hashes;
- per-sector commands, start and finish times, exit codes, standard output,
  error logs, and witness files.

These searches provide upper bounds only. When combining campaigns, retain
the smallest verified upper bound for each sector. A later search need not
improve an earlier result.

## Connected-cluster certification

The connected-cluster campaigns use dist-m4ri to exclude successive weights.
Completed exclusions establish lower bounds. When the lower bound matches
the weight of a verified nontrivial logical operator, the sector distance
is exact.

A timeout or interruption does not exclude the weight that was still being
searched. Only completed searches contribute to the recorded lower bound.

### Original campaign

`connected_cluster/` contains the original certification campaign. Its
`cc_results/summary.csv` records the status and bounds for each sector.

The supporting records include input matrices, commands, logs, exit records,
and available logical witnesses. The directory also contains
`validate_certificates.py` and a saved `validation.csv`.

From `Distance Audit/`, run:

```bash
cd connected_cluster
python3 validate_certificates.py
```

The validator checks saved evidence, including logical-witness validity and
the completed-weight records required by the reported exact distances.
It does not independently rerun the exhaustive searches.

See `connected_cluster/README.md` for the campaign's reproduction and
continuation instructions.

### Table I addendum

`connected_cluster_tableI/` contains the completed additional campaign for
three Table I instances.

Its saved `cc_results/summary.csv` reports:

| Instance ID | `n` | `k` | `dX` | `dZ` | Status |
|---|---:|---:|---:|---:|---|
| `TabI_MM_96_12_4_W12` | 96 | 12 | 4 | 4 | Exact in both sectors |
| `TabI_MM_96_12_8` | 96 | 12 | 8 | 8 | Exact in both sectors |
| `TabI_MM_144_40_4` | 144 | 40 | 4 | 4 | Exact in both sectors |

The directory contains the complete extracted campaign records, including:

- input matrices and the campaign manifest;
- the Python runner, shell launcher, and Slurm submission script;
- `campaign.log`;
- the summary CSV and per-sector `result.json` files;
- per-weight commands, standard output, error logs, exit records, and
  witness files.

The per-sector JSON records include matrix hashes, distance bounds, recorded
logical supports, and references to the supporting exclusion logs.

The summary CSV is an index to the evidence. It should be distributed with
the detailed records rather than used as a standalone certificate.

## How to check a distance claim

For an upper-bound claim:

1. Identify the instance and sector.
2. Locate the saved parity-check matrices and logical support.
3. Verify that the support has zero syndrome.
4. Verify that it lies outside the appropriate stabilizer row space.
5. Count its weight.

For an exact-distance claim, additionally inspect the completed
connected-cluster exclusions establishing the matching lower bound.

The existing witness-verification script checks the earlier consolidated
witness collection. Run it from `Distance Audit/`:

```bash
python3 code/verify_witnesses.py \
    final/dist_m4ri_witnesses.toml \
    results/sqetch_100M
```

This command checks that specific collection. It does not automatically
validate every later campaign or establish connected-cluster lower bounds.

## Original archives

`Original Archives/` contains:

- `tableI_CC_results_20261016.zip`;
- `four_codes_rw_20261016T195147Z.zip`.

The ZIP files preserve the original uploaded bundles. The extracted
directories make the same campaign evidence accessible for inspection.

## Relationship to decoding experiments

The repository's `Figure Provenance/` directory separately contains archived
decoding experiments, including logs, result tables, plots, and available
circuit files.

Distance certification and decoding performance are distinct checks.
Historical distance labels in simulation logs are input metadata; they do
not independently certify a distance. Their interpretation requires matching
the simulated instance to the corresponding audited code.