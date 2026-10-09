# Rerun sQetch at 150M trials/sector on the 38 rows whose 100M bound exceeds the
# original manuscript value in at least one sector.
#
# Run from the mm_manuscript_audit folder in the same Julia/GPU environment as the 100M run.
# A NEW base seed is used on purpose: with the old seed (1234) the first 100M trials would
# replay the 100M run's random stream, so most of the budget would re-search the same
# information sets. Seeds are still deterministic (5678 + registry index), so the run is
# reproducible.
#
# Afterwards, send back audit_sqetch_150M_rerun38/summary.csv. Each sector's reported bound
# becomes min(100M result, 150M result, verified witness); both runs are valid upper bounds.

include("audit_mm.jl")

const RERUN_IDS = [
    "table2_row036", "table2_row046", "table2_row050", "table2_row051", "table2_row063",
    "table2_row071", "table3_row019", "table3_row022", "table3_row026", "table6_row045",
    "table7_row056", "table7_row057", "table7_row065", "table7_row070", "table7_row073",
    "table7_row074", "table7_row083", "table7_row084", "table7_row094", "table7_row101",
    "table7_row104", "table8_row016", "table8_row025", "table8_row045", "table8_row047",
    "table8_row049", "table8_row050", "table8_row052", "table8_row057", "table8_row062",
    "table9_row019", "table9_row022", "table9_row023", "table9_row024", "table10_row010",
    "table10_row013", "table10_row014", "table10_row017",
]
@assert length(RERUN_IDS) == 38

# 1) Smoke test, as before (fast).
r = MMManuscriptAudit.run_audit(; ids=["example_Toric96"], trials=100_000,
                                 outdir="audit_gpu_smoke_rerun")
println(get(only(r), "error", only(r)["status"]))

# 2) The rerun. Resumable: re-running with identical settings skips finished rows.
rows = MMManuscriptAudit.run_audit(; ids=RERUN_IDS, trials=150_000_000, seed=5678,
                                    k_sub=64, outdir="audit_sqetch_150M_rerun38")

for row in rows
    println(row["id"], "  status=", row["status"], "  ",
            get(row, "error", "dX<=$(get(row, "sqetch_x_upper", "?")) dZ<=$(get(row, "sqetch_z_upper", "?"))"))
end
