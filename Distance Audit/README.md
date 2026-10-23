# Distance audit for multivariate multicycle codes

This directory preserves the cluster results used to audit the code parameters
reported in the manuscript. It includes construction inputs, parity-check
matrices, randomized distance searches, logical witnesses, and
connected-cluster certification records.

The original outputs are retained unchanged. This README explains how the
different campaigns relate to one another and where to find their evidence.

## Interpreting the results

We distinguish two types of distance statements:

- **Verified upper bound:** a nontrivial logical operator of weight `w`
  establishes `dX <= w` or `dZ <= w`.
- **Exact distance:** a verified upper bound matches a lower bound established
  by completed connected-cluster searches.

Randomized searches alone do not establish exact distances. A scalar estimate
without a verified logical witness should not be treated as a certified
upper bound.

For a CSS code, the overall distance is `d = min(dX, dZ)`.

## Directory guide

All paths below are relative to `Distance Audit/`.

| Directory | Contents |
|---|---|
| `code/` | Construction registry, structural-audit scripts, distance-search wrappers, and witness-verification scripts |
| `results/sqetch_100M/` | Original sQetch campaign requesting 100 million trials per CSS sector |
| `results/sqetch_150M_rerun38/` | Additional sQetch campaign requesting 150 million trials per sector for 38 selected instances |
| `results/distm4ri/` | Earlier dist-m4ri random-window searches and saved outputs |
| `connected_cluster/` | Original connected-cluster certification campaign |
| `connected_cluster_tableI/` | Additional certification campaign for three Table I instances |
| `four_codes_rw_20261016T195147Z/` | Additional random-window searches for four larger instances |
| `final/` | Historical consolidated tables and witness collections |
| `Original Archives/` | Original ZIP archives of the additional cluster campaigns |

## Historical summaries and subsequent campaigns

The CSV files in `final/` preserve summaries prepared at earlier stages of
the audit. Despite the directory name, they do not incorporate every
subsequent campaign.

In particular, `final/distance_bounds_revised.csv` contains entries labelled
`sQetch, unverified (dagger)` for:

- `table3_row025`;
- `table3_row027`;
- `table4_row023`;
- `table4_row026`.

These historical estimates are not verified upper bounds. Additional
random-window searches for these instances are preserved in
`four_codes_rw_20261016T195147Z/`, together with their logical witnesses.

The additional exact-distance results for three Table I instances are
preserved separately in `connected_cluster_tableI/`.

Readers should consult the relevant campaign records when interpreting these
additions. A later search does not automatically replace an earlier verified
bound: the smallest valid upper bound available for each sector remains
applicable. Exactness additionally requires a matching certified lower bound.

## Construction and structural checks

The registry in `code/` records the defining polynomials and moduli for each
instance. The Julia audit reconstructs the codes using the
`MultivariateMulticycle` constructor in QuantumClifford.jl with Oscar.

The structural checks include:

- CSS commutation over GF(2);
- the number of physical qubits, obtained from the matrix column count;
- the number of logical qubits,
  `k = n - rank(HX) - rank(HZ)`, using ranks over GF(2);
- parity-check row weights;
- the applicable metacheck identities.

An independent Python reconstruction is also included.

## Sector conventions

The saved matrices use the following conventions:

- **X sector:** a logical support `v` satisfies `HZ * v = 0` over GF(2)
  and lies outside the row space of `HX`.
- **Z sector:** a logical support `v` satisfies `HX * v = 0` over GF(2)
  and lies outside the row space of `HZ`.

Witness supports recorded as one-based indices refer to columns of the
associated saved matrices.

Distance results apply to those matrices and their qubit ordering.
A shared code name, block length, or logical dimension is insufficient
to establish that two instances have the same distance.

## Randomized distance searches

### sQetch

The original campaign requested 100 million trials per CSS sector with
sketch dimension 64. A further campaign requested 150 million trials per
sector for 38 selected instances.

The outputs and available parameter and environment records are retained in:

- `results/sqetch_100M/`;
- `results/sqetch_150M_rerun38/`.

These files document the searches as performed. Increasing the trial count
can improve a candidate upper bound, but it does not prove that a lighter
logical operator is absent.

### Additional random-window searches for four instances

The campaign in `four_codes_rw_20261016T195147Z/` covers:

| Registry ID | Physical qubits `n` | Logical qubits `k` |
|---|---:|---:|
| `table3_row025` | 840 | 18 |
| `table3_row027` | 864 | 12 |
| `table4_row023` | 672 | 12 |
| `table4_row026` | 768 | 12 |

The saved script invokes dist-m4ri with:

- `method=1`: random-window search;
- `steps=100000000`: maximum requested search steps;
- `timeout=1800`: time limit in seconds per sector;
- `threads=1`;
- `smax=0`;
- seeds 202610161 through 202610168 across the eight sector searches.

The requested step limit is not a statement that every run completed
100 million steps. Consult the individual outputs for the work performed.

The directory preserves:

- the executable hash and program help;
- the run script;
- input matrices and matrix hashes;
- per-sector commands;
- start and finish times;
- exit codes;
- standard output and error logs;
- saved logical witnesses.

These searches provide upper-bound evidence, not exact-distance certificates.

## Connected-cluster certification

The connected-cluster campaigns search successive weights using dist-m4ri.
Completed exclusions establish lower bounds. A sector is reported as exact
when its lower bound matches the weight of a verified nontrivial logical
operator.

A timed-out or interrupted search does not exclude the weight that was still
being searched.

### Original campaign

`connected_cluster/` contains the original certification campaign.

Its `cc_results/summary.csv` lists the recorded bounds and status for each
sector. Supporting files include the input matrices, manifest, commands,
logs, exit records, and available witnesses.

The directory also contains `validate_certificates.py` and saved validation
results. From `Distance Audit/`, run:

```bash
cd connected_cluster
python3 validate_certificates.py
```

This checks the saved certificate records. It does not independently rerun
the exhaustive searches.

See `connected_cluster/README.md` for instructions specific to that campaign.

### Table I addendum

`connected_cluster_tableI/` contains the completed additional campaign for
three Table I instances.

Its saved `cc_results/summary.csv` reports:

| Instance ID | `n` | `k` | `dX` | `dZ` | Status |
|---|---:|---:|---:|---:|---|
| `TabI_MM_96_12_4_W12` | 96 | 12 | 4 | 4 | Exact in both sectors |
| `TabI_MM_96_12_8` | 96 | 12 | 8 | 8 | Exact in both sectors |
| `TabI_MM_144_40_4` | 144 | 40 | 4 | 4 | Exact in both sectors |

The complete campaign records are included:

- input matrices and manifest;
- runner and submission scripts;
- campaign log;
- summary CSV;
- per-sector `result.json` files;
- per-weight commands, output, error logs, exit records, and witnesses.

The per-sector JSON files record matrix hashes, lower and upper bounds,
logical supports, and references to the supporting exclusion logs.

The original campaign and the Table I addendum remain separate so that each
campaign's inputs and outputs can be inspected in their original context.

## Checking a reported distance

For an upper-bound claim:

1. Locate the instance's saved matrices and logical support.
2. Check that the support has zero syndrome.
3. Check that it is outside the appropriate stabilizer row space.
4. Count its weight.

For an exact-distance claim, also inspect the completed connected-cluster
exclusions establishing the matching lower bound.

The earlier consolidated witness collection can be checked from
`Distance Audit/` using:

```bash
python3 code/verify_witnesses.py \
    final/dist_m4ri_witnesses.toml \
    results/sqetch_100M
```

This command checks that particular witness collection. It does not
automatically check the later campaigns or establish lower bounds.

## Original archives

`Original Archives/` contains:

- `tableI_CC_results_20261016.zip`;
- `four_codes_rw_20261016T195147Z.zip`.

The archives preserve the uploaded cluster bundles. Their extracted
directories provide access to the individual records.

## Relation to decoding experiments

The repository's `Figure Provenance/` directory contains archived decoding
experiments, including logs, result tables, plots, and available circuit files.

Distance certification and decoding performance are separate checks.
Distance labels in historical simulation logs are input metadata; they do
not independently certify a distance. They should be interpreted using the
audit records for the corresponding code instance.