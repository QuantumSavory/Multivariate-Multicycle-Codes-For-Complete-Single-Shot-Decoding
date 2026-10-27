# Exact GF(2) rank audit for the single-shot matrices

This package lets you verify the following manuscript claim on your own cluster:

> For the [[144,12,12]] instance used in the single-shot experiment, MX has rank
> 22, whereas the X checks have 30 independent redundancies.

The numbers 22 and 30 are **expected claims to test** in `cases.toml`. They are
not substituted into the computation. Every rank is calculated by
`Nemo.rank(Nemo.matrix(Nemo.GF(2), A))`. No floating-point, real, or integer-ring
rank is used for the reported results.

## Run on the cluster

Upload and unpack `mm_rank_audit.zip` under `~/sqetch_work/mm_manuscript_audit`:

```bash
cd ~/sqetch_work/mm_manuscript_audit
unzip mm_rank_audit.zip
cd mm_rank_audit
set -o pipefail
julia --project="$HOME/sqetch_work" audit_ranks.jl \
  --out cluster_rank_results 2>&1 | tee cluster_rank_audit.log
```

One CPU core is sufficient. No GPU, sQetch, distance search, or sampling is used.
The script needs Nemo plus Julia standard libraries. If Nemo is not available
as a dependency in that environment, use a separate environment in this folder:

```bash
julia --project=. -e 'using Pkg; Pkg.add("Nemo")'
julia --project=. audit_ranks.jl --out cluster_rank_results \
  2>&1 | tee cluster_rank_audit.log
```

The output directory must be new; earlier results are never overwritten. A
mismatch or input error returns a nonzero exit code, after saving the results
and error records. Read `summary.csv` and the per-code `result.toml` files.
Do not treat merely reaching the end of the script as confirmation.

## Which matrices are checked?

The bundled inputs are unchanged exports from `Single-Shot Decoding/qc_matrices/`
in the manuscript repository, commit
`450759b16d5b652b97695a43e1710bbb99f99327`.

`source_provenance.json` records their hashes. The repository's
`codes_qc.json` identifies the inputs for the simulation, and the original
`export_from_quantumclifford.jl` is preserved for reference. The audit itself
reads the saved matrices; it does not regenerate them or invoke the exporter.
In particular, it does not rely on an arbitrary code sharing the same n and k.

It checks the three exported code instances:

- MM_144_12_12: HX, HZ, MX, MZ;
- TT_135_12_6: HX, HZ, MZ;
- BB_144_12_12: HX, HZ.

The distance components of these filenames are historical labels. This audit
neither measures nor certifies those distances. An absent MX/MZ file is reported
as not supplied, rather than interpreted as evidence that no relations exist.

To check your own checkout directly, instead use:

```bash
julia --project="$HOME/sqetch_work" audit_ranks.jl \
  --matrix-dir "/path/to/your/repository/Single-Shot Decoding/qc_matrices" \
  --out checkout_rank_results 2>&1 | tee checkout_rank_audit.log
```

Replace the path with the actual checkout location. The script saves copies and
hashes of the inputs it actually reads. It never transposes a matrix to make an
identity pass: qubits must be columns of H, and check outcomes columns of M.

## What the calculations mean

For H with m rows and n columns:

- `rank(H)` is computed exactly over GF(2).
- The vector space of relations among check rows is `ker(transpose(H))`.
- Its dimension is `m - rank(H)`, reported as `redundancy_x` or `redundancy_z`.
- `M * H == 0` checks that every supplied metacheck is a check relation.
- Provided this identity holds, `rank(M)` is the dimension of the supplied
  relation space, and `m - rank(H) - rank(M)` is the dimension not spanned by it.
- Therefore `rank(M) < m - rank(H)` establishes that the supplied metachecks do
  not span all check relations. This is a statement about these matrices.

If the quoted X-sector numbers pass, the unspanned relation space has dimension
30 - 22 = 8. This does not mean that M is an incorrect metacheck matrix; it means
that the complex supplies only a subspace of the full relation space.

The script also reports:

- matrix dimensions and all row/column weights;
- CSS commutation `HX * transpose(HZ) == 0`;
- `n` and `n - rank(HX) - rank(HZ)` (identified as the CSS dimension only when
  commutation holds);
- both X- and Z-check redundancy counts;
- both supplied metacheck ranks, identities, and span-completeness tests.

These are exact structural calculations. They do not establish distance,
confinement, decoding performance, or an asymptotic single-shot theorem.

## Extending the audit

Add another `[[cases]]` block to a copy of `cases.toml`, supplying its matrix
filenames and optional metachecks. Use `--manifest your_cases.toml` and
`--matrix-dir your_matrix_directory` to run it. Add expected scalar values under
`[cases.expected]` to test a particular statement; all reported quantities are
still calculated from the matrices first. This provides a repeatable way to
check other numerical rank, dimension, redundancy, and check-weight statements.
For weight claims, inspect the per-matrix weight arrays and extrema in result.toml.

This package covers the quoted claim and the related matrix identities above;
it is not an audit of every theorem or numerical statement in the manuscript.

## Saved evidence

Each output directory contains:

- `summary.csv`: one row per code;
- `<code>/result.toml`: ranks, dimensions, identities, weights, expected-claim
  comparisons, and PASS/FAIL status;
- `<code>/inputs/`: exact matrices used, with SHA-256 hashes in the result;
- `environment.toml`: Julia/Nemo versions, rank backend, script hash and arguments;
- the audit script, cases manifest, and available Julia Project/Manifest files;
- `completion.toml`: overall status. Errors are saved separately as `error.toml`.

Archive your cluster outputs together with the input package and terminal log:

```bash
cd ..
zip -r mm_rank_audit_cluster_results.zip mm_rank_audit
```

The delivered package contains inputs and scripts, not newly claimed cluster
results. Use your own saved run when updating the manuscript and response letter.
The built-in self-tests include a matrix with rational rank 3 but GF(2) rank 2,
so a change to the wrong field cannot silently pass that test.

## Execution checks

The audit was tested with Julia 1.10.10 and Nemo 0.57.1, including all three
input cases and an intentionally incorrect rank expectation. The incorrect
expectation produced FAIL and exit code 2. These are software validation checks;
no local test result directory is included in this package.
