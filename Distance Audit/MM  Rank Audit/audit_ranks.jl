#!/usr/bin/env julia
# Exact binary linear algebra. All ranks are Nemo.rank over Nemo.GF(2).
import Nemo
using SHA, TOML, Dates
const F2 = Nemo.GF(2)

function read_binary_mtx(path)
    lines = readlines(path)
    isempty(lines) && error("Empty matrix file: $path")
    h = split(lowercase(strip(lines[1])))
    length(h) == 5 || error("Invalid Matrix Market header: $path")
    h[1:3] == ["%%matrixmarket", "matrix", "coordinate"] || error("Expected coordinate matrix: $path")
    h[4] in ("integer", "real", "pattern") || error("Unsupported value type: $path")
    h[5] == "general" || error("Only explicit general matrices are supported: $path")
    data = [strip(s) for s in lines[2:end] if !isempty(strip(s)) && !startswith(strip(s), "%")]
    isempty(data) && error("Missing dimensions: $path")
    dims = parse.(Int, split(data[1])); length(dims) == 3 || error("Invalid dimensions")
    nr, nc, nz = dims
    min(nr, nc, nz) >= 0 || error("Negative dimensions")
    length(data)-1 == nz || error("Entry count mismatch: $path")
    A = zeros(Int, nr, nc); seen = Set{Tuple{Int,Int}}()
    for s in data[2:end]
        v = split(s); length(v) == (h[4] == "pattern" ? 2 : 3) || error("Invalid entry: $s")
        i, j = parse(Int,v[1]), parse(Int,v[2])
        1 <= i <= nr && 1 <= j <= nc || error("Index outside matrix: $path")
        (i,j) in seen && error("Duplicate coordinate (ambiguous binary input): $path")
        push!(seen,(i,j))
        # Parse exact decimal text; do not silently reduce nonbinary input modulo 2.
        value = h[4] == "pattern" ? BigFloat(1) : parse(BigFloat,v[3])
        value in (0,1) || error("Nonbinary entry: $path")
        A[i,j] = Int(value)
    end
    return A
end

gf2(A::Matrix{Int}) = Nemo.matrix(F2, A)
filehash(path) = bytes2hex(sha256(read(path)))
function save_toml(path, value)
    open(path,"w") do io
        TOML.print(io,value; sorted=true)
    end
end

function selftest()
    # This matrix has rational rank 3 but binary rank 2.
    A = [1 1 0; 1 0 1; 0 1 1]
    @assert Nemo.rank(gf2(A)) == 2
    @assert Nemo.rank(Nemo.matrix(Nemo.QQ,A)) == 3
    @assert Nemo.rank(gf2(zeros(Int,3,4))) == 0
    @assert Nemo.rank(gf2([1 0; 0 1])) == 2
    @assert iszero(gf2([1 1 1]) * gf2(A))
    @assert !iszero(gf2([1 0 0]) * gf2(A))
    println("PASS self-tests: Nemo exact GF(2) rank (including binary vs rational rank).")
end

function matrix_record(A, Af)
    rw = vec(sum(A;dims=2)); cw = vec(sum(A;dims=1))
    return Dict{String,Any}("rows"=>size(A,1),"columns"=>size(A,2),
        "rank_gf2"=>Int(Nemo.rank(Af)),"row_weights"=>rw,"column_weights"=>cw,
        "row_weight_min"=>isempty(rw) ? 0 : minimum(rw),
        "row_weight_max"=>isempty(rw) ? 0 : maximum(rw),
        "column_weight_min"=>isempty(cw) ? 0 : minimum(cw),
        "column_weight_max"=>isempty(cw) ? 0 : maximum(cw),
        "nemo_matrix_type"=>string(typeof(Af)))
end

function audit_case(c, matrix_dir, out)
    id = c["id"]
    occursin(r"^[A-Za-z0-9_-]+$",id) || error("Unsafe case ID")
    dest = joinpath(out,id); mkpath(joinpath(dest,"inputs"))
    arrays = Dict{String,Matrix{Int}}(); finite = Dict{String,Any}()
    records = Dict{String,Any}(); input_info = Dict{String,Any}()
    for key in ("HX","HZ","MX","MZ")
        haskey(c,key) || continue
        path = abspath(joinpath(matrix_dir,c[key])); isfile(path) || error("Missing required input: $path")
        saved = joinpath(dest,"inputs",key*".mtx"); cp(path,saved;force=false)
        A = read_binary_mtx(saved); Af = gf2(A)
        arrays[key]=A;finite[key]=Af;records[key]=matrix_record(A,Af)
        input_info[key]=Dict("path"=>path,"sha256"=>filehash(saved),"saved_copy"=>"inputs/"*key*".mtx")
    end
    HX,HZ = arrays["HX"],arrays["HZ"]
    size(HX,2)==size(HZ,2) || error("HX and HZ must have the same number of columns; no automatic transpose")
    r = Dict{String,Any}("id"=>id,"field"=>"GF(2)","rank_backend"=>"Nemo.rank",
        "input_files"=>input_info,"matrices"=>records,"n"=>size(HX,2))
    r["rank_hx"]=records["HX"]["rank_gf2"];r["rank_hz"]=records["HZ"]["rank_gf2"]
    r["css_commutation"] = iszero(finite["HX"] * transpose(finite["HZ"]))
    r["k_rank_formula"] = r["n"]-r["rank_hx"]-r["rank_hz"]
    r["k_is_css_dimension"] = r["css_commutation"]
    r["redundancy_x"] = size(HX,1)-r["rank_hx"]
    r["redundancy_z"] = size(HZ,1)-r["rank_hz"]
    valid = r["css_commutation"]
    for (hkey,mkey,sector) in (("HX","MX","x"),("HZ","MZ","z"))
        r["metachecks_"*sector*"_supplied"] = haskey(arrays,mkey)
        haskey(arrays,mkey) || continue # Not supplied is not an assertion that no relations exist.
        H,M = arrays[hkey],arrays[mkey]
        size(M,2)==size(H,1) || error("$mkey must have one column per $hkey row; no automatic transpose")
        annihilates = iszero(finite[mkey]*finite[hkey]); valid &= annihilates
        r["m"*sector*"_h"*sector*"_zero"] = annihilates
        r["rank_m"*sector] = records[mkey]["rank_gf2"]
        if annihilates
            gap = r["redundancy_"*sector]-r["rank_m"*sector]
            @assert gap >= 0
            r["missing_relation_dimension_"*sector] = gap
            r["metachecks_span_all_relations_"*sector] = gap == 0
        end
    end
    comparisons = Dict{String,Any}()
    for (key,expected) in get(c,"expected",Dict())
        available = haskey(r,key)
        matches = available && r[key] == expected
        comparisons[key] = Dict("expected"=>expected,"available"=>available,"matches"=>matches)
        available && (comparisons[key]["observed"] = r[key])
        valid &= matches
    end
    r["expected_claim_checks"] = comparisons
    r["status"] = valid ? "PASS" : "FAIL"
    save_toml(joinpath(dest,"result.toml"),r)
    println("$(r["status"]) $id: n=$(r["n"]), k=$(r["k_rank_formula"]), rank(HX)=$(r["rank_hx"]), rank(HZ)=$(r["rank_hz"])")
    for sector in ("x","z")
        println("  ",uppercase(sector)," checks: ",r["redundancy_"*sector]," independent relations")
        if haskey(r,"rank_m"*sector)
            println("  rank(M",uppercase(sector),")=",r["rank_m"*sector],
                    "; MH=0: ",r["m"*sector*"_h"*sector*"_zero"],
                    "; missing relation dimension: ",get(r,"missing_relation_dimension_"*sector,"INVALID"))
        else
            println("  No metacheck matrix supplied for this sector.")
        end
    end
    flush(stdout)
    return r
end

function main(args=ARGS)
    selftest()
    if args == ["--self-test"]; return; end
    opts=Dict("--manifest"=>joinpath(@__DIR__,"cases.toml"),
              "--matrix-dir"=>joinpath(@__DIR__,"inputs","qc_matrices"),
              "--out"=>joinpath(pwd(),"rank_results_"*Dates.format(now(UTC),"yyyymmddTHHMMSSsss")*"Z"))
    length(args)%2==0 || error("Arguments: --matrix-dir PATH --manifest FILE --out NEW_DIRECTORY; or --self-test")
    for i in 1:2:length(args)
        haskey(opts,args[i]) || error("Unknown option: $(args[i])")
        opts[args[i]]=args[i+1]
    end
    out=abspath(opts["--out"]);ispath(out) && error("Output exists; choose a fresh --out directory: $out")
    cases=TOML.parsefile(opts["--manifest"])["cases"]
    mkpath(out);cp(@__FILE__,joinpath(out,"audit_ranks.jl"))
    cp(opts["--manifest"],joinpath(out,"cases.toml"))
    env=Dict("started_utc"=>string(now(UTC)),"julia_version"=>string(VERSION),
        "nemo_version"=>string(Base.pkgversion(Nemo)),"nemo_path"=>pathof(Nemo),
        "field"=>string(F2),"rank_backend"=>"Nemo.rank(Nemo.matrix(Nemo.GF(2), A))",
        "active_project"=>something(Base.active_project(),"none"),"command_arguments"=>args,
        "script_sha256"=>filehash(@__FILE__),"manifest_sha256"=>filehash(opts["--manifest"]))
    project=Base.active_project()
    if project !== nothing && isfile(project)
        cp(project,joinpath(out,"environment_Project.toml"))
        manifest=joinpath(dirname(project),"Manifest.toml")
        isfile(manifest) && cp(manifest,joinpath(out,"environment_Manifest.toml"))
    end
    save_toml(joinpath(out,"environment.toml"),env)
    for filename in ("source_provenance.json", "source_commit.txt")
        ref=joinpath(@__DIR__,filename)
        isfile(ref) && cp(ref,joinpath(out,"bundled_reference_"*filename))
    end
    results=Dict{String,Any}[]
    for c in cases
        try
            push!(results,audit_case(c,opts["--matrix-dir"],out))
        catch err
            r=Dict{String,Any}("id"=>c["id"],"status"=>"ERROR","error"=>sprint(showerror,err,catch_backtrace()))
            push!(results,r);mkpath(joinpath(out,c["id"]))
            save_toml(joinpath(out,c["id"],"error.toml"),r)
            println(stderr,"ERROR ",c["id"],": ",sprint(showerror,err))
        end
    end
    fields=["id","status","n","k_rank_formula","rank_hx","rank_hz","redundancy_x","redundancy_z",
            "rank_mx","rank_mz","mx_hx_zero","mz_hz_zero","missing_relation_dimension_x","missing_relation_dimension_z"]
    csvcell(x)="\""*replace(string(x),'"'=>"\"\"")*"\""
    open(joinpath(out,"summary.csv"),"w") do io
        println(io,join(fields,","))
        for r in results;println(io,join([csvcell(get(r,f,"")) for f in fields],","));end
    end
    ok=all(r->r["status"]=="PASS",results)
    save_toml(joinpath(out,"completion.toml"),Dict("all_pass"=>ok,"finished_utc"=>string(now(UTC)),"cases"=>length(results)))
    println("Saved ",out)
    ok || exit(2)
end
if abspath(PROGRAM_FILE) == abspath(@__FILE__)
    main()
end
