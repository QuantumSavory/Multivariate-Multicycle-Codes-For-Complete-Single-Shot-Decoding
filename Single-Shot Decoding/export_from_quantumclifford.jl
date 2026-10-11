# Export the check and metacheck matrices of the three main-figure codes directly from
# QuantumClifford.jl (MultivariateMulticycle constructor) into qc_matrices/*.mtx, for the
# single-shot simulations. Run once, in the Julia environment with QuantumClifford and Oscar:
#     julia export_from_quantumclifford.jl
using QuantumClifford, QuantumClifford.ECC, Oscar

gf2(M) = mod.(Int.(Matrix(M)), 2)

function write_mtx(path, M)
    idx = findall(!iszero, M)
    open(path, "w") do io
        println(io, "%%MatrixMarket matrix coordinate integer general")
        println(io, size(M, 1), " ", size(M, 2), " ", length(idx))
        for c in idx
            println(io, c[1], " ", c[2], " 1")
        end
    end
end

# metachecks act on check outcomes: return M oriented so that M * H == 0, or nothing if none
function metachecks(f, c, H)
    M = try
        gf2(f(c))
    catch err
        err isa ArgumentError || rethrow()
        return nothing
    end
    M = size(M, 2) == size(H, 1) ? M : permutedims(M)
    @assert all(iszero, mod.(M * H, 2)) "metacheck matrix does not annihilate the check matrix"
    return M
end

function export_code(tag, c)
    Hx, Hz = gf2(parity_matrix_x(c)), gf2(parity_matrix_z(c))
    @assert all(iszero, mod.(Hx * permutedims(Hz), 2))
    Mx = metachecks(metacheck_matrix_x, c, Hx)
    Mz = metachecks(metacheck_matrix_z, c, Hz)
    mkpath("qc_matrices")
    write_mtx("qc_matrices/$(tag)_HX.mtx", Hx)
    write_mtx("qc_matrices/$(tag)_HZ.mtx", Hz)
    Mx === nothing || write_mtx("qc_matrices/$(tag)_MX.mtx", Mx)
    Mz === nothing || write_mtx("qc_matrices/$(tag)_MZ.mtx", Mz)
    println(rpad(tag, 14), " n = ", code_n(c), "  k = ", code_k(c), "  H_X ", size(Hx), "  H_Z ", size(Hz),
            "  M_X ", Mx === nothing ? "none" : size(Mx), "  M_Z ", Mz === nothing ? "none" : size(Mz))
end

# MM [[144,12,<=12]] (table3_row002): orders (3,2,2,2) for (w,x,y,z)
R4, (w, x, y, z) = polynomial_ring(GF(2), [:w, :x, :y, :z])
S4, _ = quo(R4, ideal(R4, [w^3 - 1, x^2 - 1, y^2 - 1, z^2 - 1]))
export_code("MM_144_12_12", MultivariateMulticycle([3, 2, 2, 2],
    [S4(w^2*x*y + w + x*y*z), S4(w^2*x + w*x*y + z), S4(w^2*x*z + w*x + x*y*z), S4(w^2*y*z + w*x*y + x*y*z)]))

# TT [[135,12,(14,6)]] (test/test_ecc_trivariate_tricycle.jl): orders (5,3,3) for (x,y,z)
R3, (x3, y3, z3) = polynomial_ring(GF(2), [:x, :y, :z])
S3, _ = quo(R3, ideal(R3, [x3^5 - 1, y3^3 - 1, z3^3 - 1]))
export_code("TT_135_12_6", MultivariateMulticycle([5, 3, 3],
    [S3(1 + x3 + x3^3*y3^2), S3(1 + x3*z3^2 + x3^2*y3*z3), S3(1 + x3*y3^2*z3 + x3^2*y3*z3)]))

# BB [[144,12,12]] gross code: orders (12,6) for (x,y), A = x^3 + y + y^2, B = y^3 + x + x^2
R2, (x2, y2) = polynomial_ring(GF(2), [:x, :y])
S2, _ = quo(R2, ideal(R2, [x2^12 - 1, y2^6 - 1]))
export_code("BB_144_12_12", MultivariateMulticycle([12, 6], [S2(x2^3 + y2 + y2^2), S2(y2^3 + x2 + x2^2)]))
println("written to qc_matrices/")
