# Independent check of the dist-m4ri witnesses using YOUR audit code (audit_mm.jl).
# Rebuilds HX, HZ from the printed polynomials with QuantumClifford, then checks each support:
#   sector "z": HX*v == 0 (mod 2) and v not in rowspace(HZ)   -- same test as the reviewer witnesses
#   sector "x": HZ*v == 0 (mod 2) and v not in rowspace(HX)
# Run from the mm_manuscript_audit folder:  julia --project=<your project> verify_witnesses.jl
include(joinpath(@__DIR__, "audit_mm.jl"))
using TOML
const M = MMManuscriptAudit
W = TOML.parsefile(joinpath(@__DIR__, "..", "final", "dist_m4ri_witnesses.toml"))["witness"]
E = Dict(e["id"] => e for e in M.instances())
cache = Dict{String,Any}()
nok = 0
for w in W
    id = w["id"]
    hx, hz, bx, bz = get!(cache, id) do
        _, hx, hz, _, _ = M.construct(E[id])
        (hx, hz, M.rowbasis(hx), M.rowbasis(hz))
    end
    v = zeros(Int, size(hx, 2)); v[w["support_one_based"]] .= 1
    ok = w["sector"] == "z" ? M.valid_logical(v, hx, bz) : M.valid_logical(v, hz, bx)
    global nok += ok
    println(rpad(id, 16), " sector=", w["sector"], "  weight=", sum(v), "  sQetch=", w["sqetch_bound"],
            "  valid_logical=", ok)
end
println("\n", nok, " of ", length(W), " witnesses are valid nontrivial logical operators")
