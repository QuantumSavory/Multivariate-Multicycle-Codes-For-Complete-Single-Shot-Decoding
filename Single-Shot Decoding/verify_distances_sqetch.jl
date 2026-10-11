# Distance check of the exact matrices used in the single-shot simulations (qc_matrices/*.mtx,
# exported from QuantumClifford.jl), with the same sQetch settings as the paper's distance audit:
# 100 million trials per sector, sketch dimension 64, fixed seed. sQetch gives UPPER bounds.
#
# Run on a GPU node, in the Julia environment used for the sQetch audit, from this folder:
#     SQETCH_DIR=~/sqetch_work/mm_manuscript_audit julia verify_distances_sqetch.jl
# (SQETCH_DIR = the folder that contains sqetch_wrapper_qt.jl)
sqdir = expanduser(get(ENV, "SQETCH_DIR", "~/sqetch_work/mm_manuscript_audit"))
isfile(joinpath(sqdir, "sqetch_wrapper_qt.jl")) ||
    error("sqetch_wrapper_qt.jl not found in $sqdir; set SQETCH_DIR to the folder that contains it")
include(joinpath(sqdir, "sqetch_wrapper_qt.jl"))

function read_mtx(path)
    lines = filter(l -> !startswith(l, "%"), readlines(path))
    m, n, nnz = parse.(Int, split(lines[1]))
    M = zeros(Int, m, n)
    for l in lines[2:1+nnz]
        f = split(l); M[parse(Int, f[1]), parse(Int, f[2])] = 1
    end
    return M
end

const TRIALS = parse(Int, get(ENV, "TRIALS", "100000000"))
codes = [("MM [[144,12,<=12]]", "MM_144_12_12", "12, 12"),
         ("TT [[135,12,(14,6)]]", "TT_135_12_6", "14, 6"),
         ("BB [[144,12,12]]", "BB_144_12_12", "12, 12")]
open("distances_sqetch.csv", "w") do io
    println(io, "code,n,k,dX_upper,dZ_upper,expected_dX_dZ,trials,seed,k_sub,seconds")
    for (i, (name, tag, expected)) in enumerate(codes)
        hx, hz = read_mtx("qc_matrices/$(tag)_HX.mtx"), read_mtx("qc_matrices/$(tag)_HZ.mtx")
        t0 = time(); dx, dz = compute_distance(hx, hz; num=TRIALS, k_sub=64, seed=4321 + i); t = time() - t0
        n = size(hx, 2)
        println(rpad(name, 22), " n = ", n, "   d_X <= ", dx, "   d_Z <= ", dz, "   (expected ", expected, ")   ",
                round(t, digits=1), " s")
        println(io, "\"$name\",$n,12,$dx,$dz,\"$expected\",$TRIALS,$(4321 + i),64,$(round(t, digits=1))")
    end
end
println("written to distances_sqetch.csv")
