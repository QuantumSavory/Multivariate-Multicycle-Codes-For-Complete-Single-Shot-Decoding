# Figure 3: code-capacity comparison with the Tesseract decoder

`tesseract_LER_vs_p.png` is Fig. 3 exactly as published in the paper: logical error rate versus
physical error rate under code-capacity noise for MM [[96,12]] (two instances), MM [[96,44,4]],
single-shot decodable 4D topological codes and 2D topological codes, decoded with
`TesseractSinterDecoder` (30 log-spaced values of `p` in [1e-4, 1e-1], 2 x 10^4 shots per value,
beam 5, priority-queue limit 10^4, 10 DetIndex orderings, no revisiting of detectors).

**Status: incomplete.** The raw Sinter statistics, the circuits and the plotting script for this
figure are not yet in the repository, so the figure cannot be regenerated from this archive. The
matrices of the codes are in `QECCs/` (MM, 4D Toric, 4D Surface). The two [[96,12]] instances are
labelled in the figure by the distance values used in the simulation; Table I lists the certified
instances `QECCs/MM/MM_96_12_4_W12` (4,4) and `QECCs/MM/MM_96_12_8` (8,8). Which matrices were
simulated should be confirmed when the run data are added.
