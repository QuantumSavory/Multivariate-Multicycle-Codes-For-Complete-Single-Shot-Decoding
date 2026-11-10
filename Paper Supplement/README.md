# Paper supplement

Material from the original submission that the revised paper now keeps in this repository.

| File | What it contains | Cited in the paper |
|---|---|---|
| `MM_code_tables_full.pdf`, `MM_code_tables_full.tex` | Complete versions of Tables II–XI (all 368 instances). The paper lists a selection: all instances with certified exact distances, the instances discussed in the text, and representative instances across block lengths. | Appendix D |
| `MM_generating_algorithms.pdf`, `MM_generating_algorithms.tex` | Pseudocode for constructing MM codes and their check and metacheck matrices (formerly Appendix A). | Sec. VII |
| `subfamily_examples.md` | Julia sessions that build known code families (AMC, BB, TT, 4D toric, La-Cross, MB, GB, 2BGA, C2 and CxR) as MM codes (formerly Appendix E). | Sec. VI.C |
| `lifted_product_examples.jl` | Commands for the lifted-product examples: the four-fold [[96,12,(4,4)]] code, the three-generator case and the truncation example. | Appendix F |

In the tables, an entry `≤ d` is an upper bound given by the weight of a verified nontrivial logical operator, and an entry without `≤` is an exact distance established by matching upper and lower bounds. The evidence for every entry is in [`Distance Audit`](../Distance%20Audit/README.md), where each row can be found by its identifier (for example `table3_row025`).

The `.tex` files use the preamble of the manuscript and compile with `pdflatex` (RevTeX 4.2).
