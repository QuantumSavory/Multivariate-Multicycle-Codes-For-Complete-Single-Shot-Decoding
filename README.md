[![Paper](https://img.shields.io/badge/paper-arXiv%3A2601.18879-B31B1B.svg)](https://arxiv.org/abs/2601.18879)

# Multivariate Multicycle Codes for Complete Single-Shot Decoding

**Feroz Ahmed Mian, Owen Gwilliam, and Stefan Krastanov**

Code matrices, numerical experiments, and computational records accompanying
[the paper](https://arxiv.org/abs/2601.18879).

The paper develops a Koszul-complex formulation of multivariate multicycle (MM)
codes. Over finite abelian group algebras, this is a reformulation of abelian
multicycle (AMC) codes at the corresponding homological degree. The repository
contains explicit code instances, distance searches and certification records,
and finite-instance confinement and decoding experiments.

## Finding the data

| To inspect or reproduce | Start here |
|---|---|
| Code matrices and examples | [QECCs](QECCs/) and [HDF5 loading notebook](Loading_QECCs_from_HDF5.ipynb) |
| Defining polynomials, moduli, and structural checks | [Distance audit code and registry](Distance%20Audit/code/) |
| Distance bounds, witnesses, and certification records | [Distance audit guide](Distance%20Audit/README.md) |
| Revised Figures 4, 5, 7, and 8 | [24 October simulation archive](Figure%20Provenance/update%20Figures04_05_07_08/README.md) |
| Single-shot metacheck experiments | [Single-shot decoding guide](Single-Shot%20Decoding/README.md) |
| Historical figure data and logs | [Figure provenance](Figure%20Provenance/) |
| Native dist-m4ri confinement runs | [Confinement campaign](Distance%20Audit/distm4ri_confinement_20261023/README.md) |
| Additional experiment notebooks | [Numerical experiments](Numerical%20Experiments/) |

## Code construction and matrix files

MM instances are constructed with
[QuantumClifford.jl](https://github.com/QuantumSavory/QuantumClifford.jl)
and Oscar. See the
[`MultivariateMulticycle` documentation](https://qc.quantumsavory.org/stable/ECC_API/#QuantumCliffordOscarExt.MultivariateMulticycle)
for the constructor and examples.

The repository includes Matrix Market (`.mtx`) files and HDF5 (`.h5`) files.
`HX` and `HZ` denote the X- and Z-type parity-check matrices; metacheck and
logical-operator matrices are included where available. The
[loading notebook](Loading_QECCs_from_HDF5.ipynb) describes the HDF5 data.
Use the loading code associated with an experiment to preserve its matrix
orientation and qubit ordering. Stim simulations use circuits generated from
these matrices; the matrix files themselves are not Stim circuits.

For binary parity-check matrices with qubits as columns,

$$
H_X H_Z^{\mathsf{T}} = 0,
\qquad
k = n - \operatorname{rank}_{\mathbb{F}_2}(H_X)
      - \operatorname{rank}_{\mathbb{F}_2}(H_Z).
$$
Historical filenames and plot labels are retained. A distance appearing in a
filename is not, by itself, a distance certificate. Match an instance using its
defining data or saved matrices, not only its label or its values of `n` and `k`.

## Distance results

Distance records distinguish three kinds of evidence:

- **Search estimate:** a value returned by a randomized search.
- **Verified upper bound:** a saved nontrivial logical operator whose weight,
  zero syndrome, and nonmembership in the stabilizer row space have been checked.
- **Exact distance:** a verified upper bound matching a lower bound established
  by completed connected-cluster exclusions.

For an X logical operator, check membership in `ker(HZ)` and nonmembership in
`rowspan(HX)`; interchange X and Z for a Z logical operator. The overall CSS
distance is `min(dX, dZ)`. A timeout does not exclude the weight still being
searched, and randomized trials alone do not establish exactness.

The [distance audit guide](Distance%20Audit/README.md) explains the original
sQetch searches, later dist-m4ri searches, and witness-verification commands.
The following records are especially useful:

| Campaign | Evidence |
|---|---|
| Original connected-cluster campaign | [Records and verification instructions](Distance%20Audit/connected_cluster/) |
| Three additional Table I instances | [Table I certification records](Distance%20Audit/connected_cluster_tableI/) |
| Four larger instances with historical unverified estimates | [Additional random-window runs and witnesses](Distance%20Audit/four_codes_rw_20261016T195147Z/) |

**The CSV files in `Distance Audit/final/` are historical summaries.** They do not
include every later campaign. In particular, the unverified dagger entries for
`table3_row025`, `table3_row027`, `table4_row023`, and `table4_row026` must be read
alongside the additional random-window records linked above. Earlier verified
upper bounds remain valid for the same matrices; use the smallest verified bound
available for each sector and check for a matching certified lower bound.

## Decoding experiments and figures

### Revised Figures 4, 5, 7, and 8

The [24 October 2026 rerun](Figure%20Provenance/update%20Figures04_05_07_08/README.md)
contains the phenomenological and circuit-level memory experiments for these
figures. It records the circuits actually sampled, detector error models,
decoder settings, software versions, raw Sinter statistics, circuit resources,
and plotting inputs.

Use its [run and plotting instructions](Figure%20Provenance/update%20Figures04_05_07_08/RUN_INSTRUCTIONS.md)
to reproduce the experiment or redraw the saved results. The earlier
`Figure04/`, `Figure05/`, and `Figure07_08/` directories remain as historical
records; the linked revision campaign is the source for the updated figures.

### Single-shot decoding

[Single-Shot Decoding](Single-Shot%20Decoding/README.md) contains the metacheck
experiments, exported matrices, simulation and plotting scripts, raw counts, and
run log. Its README describes the noise model, decoder variants, stopping rules,
and statistical intervals.

### Other archived figures

[Figure Provenance](Figure%20Provenance/) groups the earlier experiments by
figure number, with result tables, logs, plots, and available circuit files.
For example, the saved overlapping-window experiments are in
[Figure09](Figure%20Provenance/Figure09/) and
[Figure10](Figure%20Provenance/Figure10/).
Figure numbers refer to the manuscript versions used when the archives were
created.

Folders with a README describe the current paper's figures:
[Figure03](Figure%20Provenance/Figure03/README.md) (code capacity; run data not yet archived),
[Figure09](Figure%20Provenance/Figure09/README.md) and
[Figure10](Figure%20Provenance/Figure10/README.md) (overlapping windows; published images,
inferred stopping rules, and [plot_plateau_xz.py](Figure%20Provenance/plot_plateau_xz.py) to redraw
them), and [Figure13_14](Figure%20Provenance/Figure13_14/README.md) (LRC, weight-6 codes).

### Corrections of 6 November 2026

* The weight-6 MM code labelled `MM_216_6_12_W6` / `MM [[216,6,12]]` in Figs. 13-14 has nontrivial
  logical operators of weight 6 in both sectors, so its distance is at most 6 (an exact search gives 6),
  not 12. The operators and a checker are in
  [Figure13_14](Figure%20Provenance/Figure13_14/README.md). The sampled data are unaffected.
* [match_simulation_matrices.py](Distance%20Audit/connected_cluster/match_simulation_matrices.py),
  cited by the Table I addendum, is now included with its output
  (`match_simulation_matrices.csv`). It records which saved matrices (Table I, simulation codes,
  HDF5 database) have the same row spaces as certified instances.
* Single-shot Fig. 6: the MM label is now [[144,12,12]] (certified) instead of [[144,12,≤12]];
  the README lists the certified distances of all three codes.
* `QECCs/MM/MM_144_6_4` is documented as a distinct [[144,6,(4,4)]] instance, not the certified
  [[144,6,(8,8)]] of Table II and Figs. 13-14.

Use each campaign's recorded settings and plotting convention: the experiments
do not all use the same decoder, per-round normalization, or uncertainty
interval. Historical records vary in completeness. A configuration in a later
script or notebook does not establish the settings of an earlier run.

## Confinement profiles

The [native dist-m4ri campaign](Distance%20Audit/distm4ri_confinement_20261023/README.md)
preserves the input matrices, executable and version information, commands,
logs, and observed profiles for eight MM instances in both sectors.

These profiles report the minimum **nonzero syndrome weight observed** at each
reported cluster weight during the search. They are not automatically certified
minima over all connected supports, and a missing entry does not mean zero.
The campaign README explains the search settings and stopping conditions.

Finite-instance distance, confinement, and decoding results provide different
kinds of evidence. The presence of metachecks or a finite observed profile does
not by itself prove complete single-shot decoding for an asymptotic family.

## Reproducing and citing a run

Start with the README for the relevant campaign and its saved inputs. Use its
recorded software versions where available, preserve the original outputs, and
save new runs separately. When reporting a result, identify the repository
commit and the campaign directory so the matrices, settings, and outputs can be
located together.

If you use these constructions or data, please cite:

```bibtex
@article{mian2026multivariate,
  title={Multivariate Multicycle Codes for Complete Single-Shot Decoding},
  author={Mian, Feroz Ahmed and Gwilliam, Owen and Krastanov, Stefan},
  journal={arXiv preprint arXiv:2601.18879},
  year={2026}
}
```

See [LICENSE](LICENSE) for the repository license. Questions and corrections can
be raised through [GitHub issues](https://github.com/QuantumSavory/Multivariate-Multicycle-Codes-For-Complete-Single-Shot-Decoding/issues).
