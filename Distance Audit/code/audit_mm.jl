# Manuscript audit for multivariate_multicycle (14).zip.
# Include in Julia, then run_audit(; trials=50_000_000).
# sQetch weights are UPPER BOUNDS, never exact-distance certificates.
module MMManuscriptAudit
using Oscar
import QuantumClifford
import QuantumClifford.ECC
using TOML, Dates, SHA, Statistics, SparseArrays, Printf, Pkg
const ROOT = @__DIR__
module DistanceBridge end
const BRIDGE_LOADED = Ref(false)
const BRIDGE_HASH = Ref("")
const REFERENCE = TOML.parsefile(joinpath(ROOT,"independent_reference.toml"))

instances() = TOML.parsefile(joinpath(ROOT,"instances.toml"))["instances"]

# Packed row elimination over GF(2); no floating-point ranks.
function rowbasis(A)
    m,n=size(A);nw=cld(n,64);B=Dict{Int,Vector{UInt64}}()
    for i in 1:m
        v=zeros(UInt64,nw)
        for j in 1:n
            if !iszero(A[i,j]);v[cld(j,64)] ⊻= UInt64(1)<<((j-1)%64);end
        end
        reduce_row!(v,B)
        p=pivot(v)
        p>0 && (B[p]=v)
    end
    B
end
function pivot(v)
    for a in length(v):-1:1
        v[a]!=0 && return (a-1)*64+64-leading_zeros(v[a])
    end
    0
end
function reduce_row!(v,B)
    while true
        p=pivot(v)
        (p==0 || !haskey(B,p)) && return v
        v .⊻= B[p]
    end
end
function outside(v,B)
    packed=zeros(UInt64,cld(length(v),64))
    for j in eachindex(v)
        !iszero(v[j]) && (packed[cld(j,64)] ⊻= UInt64(1)<<((j-1)%64))
    end
    pivot(reduce_row!(packed,B))>0
end
rank2(A)=length(rowbasis(A))
zero_product(A,B)=all(iseven,nonzeros(sparse(Int.(A))*sparse(Int.(B))))
function valid_logical(v,H,B)
    all(iseven,H*Int.(v)) && outside(v,B)
end

function construct(e)
    R,x=Oscar.polynomial_ring(Oscar.GF(2),Symbol.(e["variables"]))
    orders=Int.(e["orders"])
    I=Oscar.ideal(R,[x[i]^orders[i]-1 for i in eachindex(x)])
    S,_=Oscar.quo(R,I)
    polys=[S(sum((prod(x[j]^Int(a[j]) for j in eachindex(x)) for a in p);init=zero(R))) for p in e["supports"]]
    c=ECC.MultivariateMulticycle(orders,polys)
    # One boundary construction only. These are the same assignments used by
    # QuantumClifford's parity_matrix_xz and metacheck_matrix_x/z methods.
    maps=ECC.boundary_maps(c)
    t=length(polys);q=t÷2
    hx=Matrix{Int}(transpose(maps[q]));hz=Matrix{Int}(maps[q+1])
    mx=q>=2 ? Matrix{Int}(transpose(maps[q-1])) : zeros(Int,0,size(hx,1))
    mz=q+2<=t ? Matrix{Int}(maps[q+2]) : zeros(Int,0,size(hz,1))
    return c,hx,hz,mx,mz
end

# Infer Oscar's exterior-basis ordering from symbolic differentials. This
# converts reviewer supports without assuming Oscar uses lexicographic blocks.
function koszul_subsets(t)
    R,x=Oscar.polynomial_ring(Oscar.GF(2),["a$i" for i in 1:t])
    K=Oscar.koszul_complex(x)
    levels=Vector{Vector{Vector{Int}}}();push!(levels,[Int[]])
    for degree in 1:t
        A=Oscar.matrix(Oscar.map(K,degree));prev=levels[end]
        @assert size(A,2)==length(prev)
        current=Vector{Vector{Int}}()
        for i in 1:size(A,1)
            candidates=Vector{Vector{Int}}()
            for j in 1:size(A,2)
                iszero(A[i,j]) && continue
                a=findfirst(y->y==A[i,j],x)
                a===nothing && error("Unexpected Koszul coefficient")
                push!(candidates,sort(unique(vcat(prev[j],[a]))))
            end
            @assert !isempty(candidates)
            J=first(candidates)
            @assert length(J)==degree && all(==(J),candidates)
            push!(current,J)
        end
        push!(levels,current)
    end
    levels
end
function reviewer_vector(e,n)
    N=prod(e["orders"]);t=length(e["supports"])
    @assert t==4
    canonical=[[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
    actual=koszul_subsets(t)[3]
    v=zeros(Int,n)
    for a in e["reviewer_z_support_zero_based"]
        block=Int(a)÷N+1;offset=Int(a)%N
        dest=findfirst(==(canonical[block]),actual)
        dest===nothing && error("Cannot map reviewer basis")
        v[(dest-1)*N+offset+1]=1
    end
    v
end
function weight_statistics!(r,H,side)
    rw=vec(sum(H;dims=2));cw=vec(sum(H;dims=1))
    for (name,values) in (("row",rw),("column",cw))
        r["$(name)_min_$side"]=minimum(values)
        r["$(name)_median_$side"]=median(values)
        r["$(name)_max_$side"]=maximum(values)
        r["$(name)_weights_$side"]=Int.(values)
    end
end
function weight_flags!(r,e,flags)
    for side in ("x","z")
        for stat in ("median","max")
            key="reported_row_$(stat)_$side"
            if haskey(e,key) && e[key]!=r["row_$(stat)_$side"]
                push!(flags,uppercase(key)*"_MISMATCH")
            end
        end
        key="reported_row_constant_$side"
        if haskey(e,key) && !(r["row_min_$side"]==e[key]==r["row_max_$side"])
            push!(flags,uppercase(key)*"_MISMATCH")
        end
    end
end
function save_toml(path,d)
    tmp=path*".tmp"
    open(tmp,"w") do io;TOML.print(io,d;sorted=true);end
    mv(tmp,path;force=true)
end
function save_mtx(path,A)
    m,n=size(A);I,J,V=findnz(sparse(A))
    open(path,"w") do io
        println(io,"%%MatrixMarket matrix coordinate integer general")
        println(io,"% Binary matrix; one-based indices; arithmetic over GF(2)")
        println(io,"$m $n $(length(V))")
        for k in eachindex(V);println(io,"$(I[k]) $(J[k]) $(V[k])");end
    end
end
function matrix_digest(A)
    # Row-major one byte per binary entry; dimensions included.
    bytes=UInt8.(vec(permutedims(A)))
    bytes2hex(sha256(vcat(codeunits("$(size(A,1)),$(size(A,2))\n"),bytes)))
end
function environment(outdir,wrapper,trials,seed,k_sub)
    d=Dict{String,Any}("julia_version"=>string(VERSION),"created_utc"=>string(now(UTC)),
      "trials_per_sector"=>trials,"base_seed"=>seed,"k_sub"=>k_sub,
      "instances_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"instances.toml")))),
      "wrapper_sha256"=>isfile(wrapper) ? bytes2hex(sha256(read(wrapper))) : "not_loaded")
    d["packages"]=Dict(string(p.name)=>string(p.version) for p in values(Pkg.dependencies()) if p.version!==nothing)
    if BRIDGE_LOADED[]
        try
            sys=DistanceBridge.pyimport("sys")
            d["python_version"]=DistanceBridge.pyconvert(String,sys.version)
            d["python_executable"]=DistanceBridge.pyconvert(String,sys.executable)
            d["sqetch_file"]=DistanceBridge.pyconvert(String,DistanceBridge._sqetch.__file__)
            try
                md=DistanceBridge.pyimport("importlib.metadata")
                d["sqetch_version"]=DistanceBridge.pyconvert(String,md.version("sqetch"))
            catch
                d["sqetch_version"]="unavailable; record local source commit separately"
            end
            d["cpu"]=Sys.CPU_NAME
            d["machine"]=Sys.MACHINE
            d["cpu_threads"]=Sys.CPU_THREADS
        catch ex
            d["python_metadata_error"]=sprint(showerror,ex)
        end
    end
    save_toml(joinpath(outdir,"environment.toml"),d)
    for name in ("Project.toml","Manifest.toml")
        p=Base.active_project()
        p===nothing && continue
        f=joinpath(dirname(p),name)
        isfile(f) && cp(f,joinpath(outdir,"active_"*name);force=true)
    end
end

function logical_basis_bounds!(r,hx,hz,bx,bz,dir)
    c=ECC.CSS(hx,hz);n=size(hx,2);k=r["k"]
    LX=Int.(QuantumClifford.stab_to_gf2(ECC.logx_ops(c))[:,1:n])
    LZ=Int.(QuantumClifford.stab_to_gf2(ECC.logz_ops(c))[:,n+1:2n])
    @assert size(LX)==(k,n) && size(LZ)==(k,n)
    @assert zero_product(hz,transpose(LX)) && zero_product(hx,transpose(LZ))
    @assert rank2(mod.(LX*transpose(LZ),2))==k
    for (side,L,H,B) in (("x",LX,hz,bx),("z",LZ,hx,bz))
        i=argmin(vec(sum(L;dims=2)));v=vec(L[i,:])
        @assert valid_logical(v,H,B)
        r["basis_witness_$(side)_upper"]=sum(v)
        r["verified_$(side)_upper"]=sum(v)
        save_toml(joinpath(dir,"basis_witness_$side.toml"),Dict("sector"=>side,"weight"=>sum(v),
           "support_one_based"=>findall(!iszero,v),"verified"=>true,
           "matrix_convention"=>"QuantumClifford matrices saved with this entry"))
    end
end

function audit_one(e;trials,seed,k_sub,outdir,save_matrices)
    id=e["id"];dir=joinpath(outdir,id);mkpath(dir)
    r=Dict{String,Any}("id"=>id,"source"=>e["source"],"source_line"=>e["source_line"],
      "input_sha256"=>e["input_sha256"],"trials_requested_per_sector"=>trials,
      "seed"=>seed,"k_sub"=>k_sub,"duplicate_of"=>e["duplicate_of"],
      "distance_certification"=>"UPPER_BOUNDS_ONLY","started_utc"=>string(now(UTC)))
    for (key,value) in e;startswith(key,"reported_") && (r[key]=value);end
    flags=String[];start=time()
    try
        c,hx,hz,mx,mz=construct(e)
        n=size(hx,2);@assert size(hz,2)==n
        @assert all(x->x==0 || x==1,hx) && all(x->x==0 || x==1,hz)
        r["css_ok"]=zero_product(hx,transpose(hz))
        r["mx_ok"]=zero_product(mx,hx);r["mz_ok"]=zero_product(mz,hz)
        @assert r["css_ok"] && r["mx_ok"] && r["mz_ok"]
        bx=rowbasis(hx);bz=rowbasis(hz);r["rank_x"]=length(bx);r["rank_z"]=length(bz)
        r["n"]=n;r["k"]=n-length(bx)-length(bz)
        # Dimensions certified by GF(2) rank, independent of any claimed values.
        for key in ("n","k");r[key]!=e["reported_"*key] && push!(flags,uppercase(key)*"_MISMATCH");end
        r["hx_sha256"]=matrix_digest(hx);r["hz_sha256"]=matrix_digest(hz)
        weight_statistics!(r,hx,"x");weight_statistics!(r,hz,"z");weight_flags!(r,e,flags)
        ref=REFERENCE[id]
        r["independent_structure_match"]=all(r[key]==value for (key,value) in ref)
        @assert r["independent_structure_match"] "QuantumClifford disagrees with independent reconstruction; inspect conventions/inputs"
        !isempty(e["duplicate_of"]) && push!(flags,"DUPLICATE_INPUT")
        if save_matrices
            for (label,H) in (("HX",hx),("HZ",hz),("MX",mx),("MZ",mz))
                save_mtx(joinpath(dir,label*".mtx"),H)
            end
        end
        if haskey(e,"reviewer_z_support_zero_based")
            v=reviewer_vector(e,n)
            ok=valid_logical(v,hx,bz);r["reviewer_z_valid"]=ok
            @assert ok "Reviewer witness failed; inspect basis convention before running sQetch"
            r["reviewer_z_upper"]=sum(v)
            save_toml(joinpath(dir,"reviewer_z_witness.toml"),Dict("weight"=>sum(v),"verified"=>ok,
              "support_one_based"=>findall(!iszero,v),"original_support_zero_based"=>e["reviewer_z_support_zero_based"]))
        end
        if r["k"]==0
            r["status"]="NO_LOGICAL_QUBITS";push!(flags,"NO_LOGICAL_QUBITS")
        else
            logical_basis_bounds!(r,hx,hz,bx,bz,dir)
            if haskey(r,"reviewer_z_upper");r["verified_z_upper"]=min(r["verified_z_upper"],r["reviewer_z_upper"]);end
            if trials>0
                dx,dz=Base.invokelatest(DistanceBridge.compute_distance,hx,hz;
                                     num=trials,seed=seed,k_sub=k_sub,d_target=nothing)
                for (side,d) in (("x",dx),("z",dz))
                    if d===nothing || !(1<=d<=n)
                        push!(flags,"SQETCH_"*uppercase(side)*"_FAILED")
                    else
                        r["sqetch_$(side)_upper"]=d
                    end
                end
                r["sqetch_support_status"]="Wrapper returns weights only; sQetch witnesses not independently checked"
                r["status"]=(dx===nothing || dz===nothing || !haskey(r,"sqetch_x_upper") || !haskey(r,"sqetch_z_upper")) ? "SQETCH_FAILED" : "COMPLETE_UPPER_BOUND_SEARCH"
            else
                r["status"]="STRUCTURAL_ONLY"
            end
            for side in ("x","z")
                ub=r["verified_$(side)_upper"]
                r["best_$(side)_upper"]=min(ub,get(r,"sqetch_$(side)_upper",ub))
                r["best_$(side)_support_verified"]=(r["best_$(side)_upper"]==ub)
                claim=e["reported_d"*side]
                r["reported_d$(side)_comparison"]=claim==0 ? "NO_SECTOR_CLAIM" :
                    r["best_$(side)_upper"]<claim ? "SMALLER_UPPER_BOUND_FOUND" :
                    r["best_$(side)_upper"]==claim ? "MATCHED_UPPER_BOUND_NOT_EXACT" : "SEARCH_DID_NOT_REPRODUCE_CLAIM"
                claim>0 && r["best_$(side)_upper"]<claim && push!(flags,"REPORTED_D"*uppercase(side)*"_TOO_HIGH")
            end
            r["best_d_upper"]=min(r["best_x_upper"],r["best_z_upper"])
            r["kd2_over_n_upper"]=r["k"]*r["best_d_upper"]^2/r["n"]
            # Scalar upper claims are NOT silently copied to both sectors.
            for key in ("reported_d","reported_d_upper")
                if haskey(e,key)
                    r[key*"_comparison"]=r["best_d_upper"]<=e[key] ? "UPPER_BOUND_REPRODUCED" : "NOT_REPRODUCED"
                    if key=="reported_d" && r["best_d_upper"]<e[key]
                        push!(flags,"REPORTED_SCALAR_D_TOO_HIGH")
                    end
                end
            end
            if haskey(e,"reported_d_lower") && r["best_d_upper"]<e["reported_d_lower"]
                push!(flags,"REPORTED_LOWER_BOUND_CONFLICT")
            end
        end
    catch ex
        ex isa InterruptException && rethrow()
        r["status"]="ERROR";r["error"]=sprint(showerror,ex,catch_backtrace());push!(flags,"ERROR")
    end
    r["elapsed_seconds"]=time()-start;r["finished_utc"]=string(now(UTC));r["flags"]=flags
    save_toml(joinpath(dir,"result.toml"),r)
    r
end

const COLUMNS=["id","source","reported_n","n","reported_k","k","rank_x","rank_z",
 "reported_dx","reported_dz","sqetch_x_upper","sqetch_z_upper","verified_x_upper","verified_z_upper",
 "best_x_upper","best_z_upper","best_x_support_verified","best_z_support_verified",
 "reported_dx_comparison","reported_dz_comparison","row_min_x","row_median_x","row_max_x",
 "row_min_z","row_median_z","row_max_z","column_min_x","column_median_x","column_max_x",
 "column_min_z","column_median_z","column_max_z","css_ok","mx_ok","mz_ok","reviewer_z_valid",
 "independent_structure_match","trials_requested_per_sector","seed","k_sub","elapsed_seconds","status","flags","duplicate_of","error"]
function csvcell(x)
    s=x isa AbstractVector ? join(x,";") : string(x)
    "\""*replace(s,"\""=>"\"\"")*"\""
end
function summarize(outdir)
    files=sort(filter(isfile,[joinpath(outdir,d,"result.toml") for d in readdir(outdir)]))
    rows=[TOML.parsefile(p) for p in files]
    open(joinpath(outdir,"summary.csv"),"w") do io
        println(io,join(COLUMNS,","))
        for r in rows;println(io,join([csvcell(get(r,k,"")) for k in COLUMNS],","));end
    end
    rows
end

"""
    run_audit(; trials=0, ids=nothing, max_n=typemax(Int), seed=1234,
               k_sub=64, outdir="audit_results", resume=true, save_matrices=true)

Default is CPU structural audit. Set trials=50_000_000 for 50M trials in EACH
sector. ids may be an explicit vector of instance IDs. Both sectors use the
same recorded per-instance seed. No early stop. Failed searches are not passed.
Resume requires the same input, trials, seed, k_sub and wrapper checksum.
"""
function run_audit(;trials::Int=0,ids=nothing,max_n::Int=typemax(Int),seed::Int=1234,
                   k_sub::Int=64,outdir::String=joinpath(ROOT,"audit_results"),
                   resume::Bool=true,save_matrices::Bool=true,
                   wrapper::String=joinpath(ROOT,"sqetch_wrapper_qt.jl"))
    @assert trials>=0 && seed>=0 && k_sub>0
    mkpath(outdir)
    if trials>0 && !BRIDGE_LOADED[]
        Base.include(DistanceBridge,wrapper);BRIDGE_LOADED[]=true
        BRIDGE_HASH[]=bytes2hex(sha256(read(wrapper)))
    end
    wrapperhash=trials>0 ? bytes2hex(sha256(read(wrapper))) : "not_loaded"
    trials>0 && BRIDGE_HASH[]!=wrapperhash && error("Wrapper changed in this Julia session; restart Julia")
    envpath=joinpath(outdir,"environment.toml")
    if isfile(envpath) && resume
        old=TOML.parsefile(envpath)
        # Do not mix settings/results silently in one directory.
        for (key,value) in (("trials_per_sector",trials),("base_seed",seed),("k_sub",k_sub),
                            ("instances_sha256",bytes2hex(sha256(read(joinpath(ROOT,"instances.toml"))))))
            get(old,key,nothing)==value || error("Settings changed ($key): use a new outdir")
        end
        current_packages=Dict(string(p.name)=>string(p.version) for p in values(Pkg.dependencies()) if p.version!==nothing)
        get(old,"packages",Dict())==current_packages || error("Package versions changed: use a new outdir")
        get(old,"julia_version","")==string(VERSION) || error("Julia version changed: use a new outdir")
        trials>0 && get(old,"wrapper_sha256","")!=wrapperhash && error("Wrapper changed: use a new outdir")
    end
    Base.invokelatest(environment,outdir,wrapper,trials,seed,k_sub)
    es=instances();idset=ids===nothing ? nothing : Set(ids)
    if idset!==nothing
        missing=setdiff(idset,Set(e["id"] for e in es));isempty(missing) || error("Unknown ids: $missing")
    end
    for (i,e) in enumerate(es)
        (idset!==nothing && !(e["id"] in idset)) && continue
        e["construction_n"]>max_n && continue
        id=e["id"];p=joinpath(outdir,id,"result.toml");entryseed=seed+i
        if resume && isfile(p)
            old=TOML.parsefile(p)
            if get(old,"status","") in ("STRUCTURAL_ONLY","COMPLETE_UPPER_BOUND_SEARCH","NO_LOGICAL_QUBITS") &&
               get(old,"input_sha256","")==e["input_sha256"] && get(old,"trials_requested_per_sector",-1)==trials &&
               get(old,"seed",-1)==entryseed && get(old,"k_sub",-1)==k_sub
                println("Resume: $id");continue
            end
        end
        println("[$i/$(length(es))] $id, printed n=$(e["reported_n"])");flush(stdout)
        r=audit_one(e;trials=trials,seed=entryseed,k_sub=k_sub,outdir=outdir,save_matrices=save_matrices)
        println("  $(r["status"]): $(join(r["flags"], "; "))");flush(stdout)
        summarize(outdir)
    end
    rows=summarize(outdir)
    println("Saved $(length(rows)) results to $(joinpath(outdir,"summary.csv"))")
    rows
end
export run_audit,instances,summarize
end
using .MMManuscriptAudit: run_audit
if abspath(PROGRAM_FILE)==@__FILE__
    trials=length(ARGS)>=1 ? parse(Int,ARGS[1]) : 0
    destination=length(ARGS)>=2 ? abspath(ARGS[2]) : joinpath(@__DIR__,"audit_results")
    run_audit(;trials=trials,outdir=destination)
end
