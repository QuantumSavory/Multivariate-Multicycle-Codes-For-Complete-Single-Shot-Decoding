# MM [[144,6,(4,4)]] (weight 6)

This instance is **not** the MM [[144,6,(8,8)]] code of Table II (`table2_row002`) and of Figs. 13-14
(`Figure Provenance/MM_QECC_Database/MM_QECC_144_6_8_W6.h5`); the two have different check row spaces
(`Distance Audit/connected_cluster/match_simulation_matrices.csv`). It is not used in the revised paper.

Its distance is 4 in both sectors. Weight-4 nontrivial logical operators (one-based supports on these matrices):

* X sector (`HZ v = 0`, `v` outside the row space of `HX`): 2, 11, 17, 20
* Z sector (`HX v = 0`, `v` outside the row space of `HZ`): 124, 127, 133, 142

An exact integer-programming search over all six logical classes found no lighter operator.
