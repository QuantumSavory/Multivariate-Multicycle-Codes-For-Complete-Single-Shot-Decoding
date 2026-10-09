# ============================================================================
#  sqetch_wrapper.jl
#
#  Thin Julia -> Python bridge over the sqetch GPU distance estimator.
#  API surface mirrors the QDistRnd-era `compute_distance(hx, hz; num)` so it
#  drops into the existing search loop with zero call-site changes.
#
#  Semantics: sqetch returns an UPPER BOUND on the CSS distance; the bound
#  tightens as `num` grows.  Same convergence behavior as DistRandCSS.
# ============================================================================

using PythonCall
using QuantumClifford: stab_to_gf2
using QuantumClifford.ECC: CSS, logx_ops, logz_ops

const _sqetch = pyimport("sqetch")
const _np     = pyimport("numpy")
const _pynone = pybuiltins.None

# Convert an Int Julia matrix to numpy uint8 in {0,1}
_to_np_u8(M) = _np.asarray(UInt8.(mod.(M, 2)))

# sqetch returns Optional[int]; unwrap to Union{Int,Nothing}
_maybe_int(x) = pyis(x, _pynone) ? nothing : pyconvert(Int, x)

"""
    logical_bases(hx, hz) -> (L_X, L_Z)

Compute physical-support logical bases for a CSS(hx, hz) code:
* `L_X` is a basis of X-type logicals as an `(kx, n)` GF(2) Int matrix.
* `L_Z` likewise for Z-type logicals.

Both are extracted from the symplectic tableau returned by QuantumClifford:
`stab_to_gf2(logx_ops)` has shape `(kx, 2n)` with the X-support in columns
`1:n` and the Z-support in columns `n+1:2n`.
"""
function logical_bases(hx, hz)
    n   = size(hx, 2)
    c   = CSS(hx, hz)
    L_X = stab_to_gf2(logx_ops(c))[:, 1:n]
    L_Z = stab_to_gf2(logz_ops(c))[:, n+1:2n]
    return L_X, L_Z
end

"""
    compute_distance(hx, hz; num=1000, d_target=nothing, k_sub=64, seed=nothing)
        -> (dx, dz)

Drop-in replacement for the QDistRnd-era `compute_distance`.  Returns the
smallest logical-coset weights observed by sqetch across `num` random-ISD
trials, one call per CSS direction.  Returns `(nothing, nothing)` on any
failure (CSS orthogonality violation, kernel error, unavailable GPU, ...).

Keyword args beyond `num` are optional and safe to ignore for the swap; they
map straight through to `sqetch.estimate_distance`:

* `d_target` — early-stop the moment a codeword lighter than this is found.
  Wire this to the same threshold the search uses to accept a code.
* `k_sub`    — sketch dimension.  64 is fine for n up to ~1000.
* `seed`     — RNG seed; `nothing` uses wall-clock microseconds.
"""
function compute_distance(hx, hz;
                          num::Int = 1000,
                          d_target::Union{Nothing,Int} = nothing,
                          k_sub::Int = 64,
                          seed::Union{Nothing,Int} = nothing)
    if !iszero(mod.(hx * hz', 2))
        @warn "CSS orthogonality violated, skipping"
        return nothing, nothing
    end
    try
        L_X, L_Z = logical_bases(hx, hz)

        HX_np = _to_np_u8(hx)
        HZ_np = _to_np_u8(hz)
        LX_np = _to_np_u8(L_X)
        LZ_np = _to_np_u8(L_Z)

        d_tgt_py  = isnothing(d_target) ? _pynone : d_target
        seed_py   = isnothing(seed)     ? _pynone : seed

        # (H_X, L_X) -> bound on d_Z ; (H_Z, L_Z) -> bound on d_X
        rz = _sqetch.estimate_distance(HX_np, LX_np;
                 num_trials=num, d_target=d_tgt_py, k_sub=k_sub, seed=seed_py)
        rx = _sqetch.estimate_distance(HZ_np, LZ_np;
                 num_trials=num, d_target=d_tgt_py, k_sub=k_sub, seed=seed_py)

        return _maybe_int(rx.best_weight), _maybe_int(rz.best_weight)
    catch e
        @warn "sqetch distance failed: $e"
        return nothing, nothing
    end
end
