# Lifted-product examples of Appendix F ("Lifted-product structure of MM codes") of
# "Multivariate Multicycle Codes for Complete Single-Shot Decoding".
# The commands reproduce the Julia REPL session behind the appendix; expected outputs are in the comments.
# Requires QuantumClifford.jl with the Oscar, Hecke and Nemo extensions, JuMP and HiGHS.

# 1. The [[96,12,(4,4)]] MM code over Z_2^4 (t = 4)
import Oscar, Hecke, Nemo, QuantumClifford;
using QuantumClifford.ECC: MultivariateMulticycle, LiftedCode, LPCode, parity_matrix_x, parity_matrix_z, code_n, code_k, code_s, distance, DistanceMIPAlgorithm;
f(w, x, y, z) = [w*z + x*y*z, w + x*y*z, w*y*z + x*y, x*y*z + x*z];
F2, _ = Oscar.finite_field(2, 1, "a");
R, (w, x, y, z) = Oscar.polynomial_ring(F2, ["w", "x", "y", "z"]);
S, _ = Oscar.quo(R, Oscar.ideal(R, [w^2 - 1, x^2 - 1, y^2 - 1, z^2 - 1]));
mm = MultivariateMulticycle([2, 2, 2, 2], [S(p) for p in f(w, x, y, z)]);
println(code_n(mm), code_k(mm))   # expected: (96, 12)

# 1b. The same polynomials as 1x1 matrices over F_2[Z_2^4]; the two factor codes
GA = Hecke.group_algebra(Hecke.GF(2), Hecke.abelian_group([2, 2, 2, 2]));
F = f(Hecke.gens(GA)...);
L = [LiftedCode(reshape([Fi], 1, 1); repr=Hecke.representation_matrix) for Fi in F];
println(code_n(L[1]), code_s(L[1]))   # expected: (16, 16)
C = LPCode(L[1], L[2]); D = LPCode(L[3], L[4]);
import JuMP, HiGHS;
println(code_n(C), code_k(C), distance(C, DistanceMIPAlgorithm(solver=HiGHS)))   # expected: (32, 8, 2)
println(code_n(D), code_k(D), distance(D, DistanceMIPAlgorithm(solver=HiGHS)))   # expected: (32, 8, 2)

# 2. Three-generator case (t = 3) and its two-generator component
R2, (x, y) = Oscar.polynomial_ring(F2, ["x", "y"]);
S2, _ = Oscar.quo(R2, Oscar.ideal(R2, [x^3 - 1, y^3 - 1]));
a, b, c = S2(x^2*y + x^2*y^2), S2(1 + x*y^2), S2(x + x^2*y);
bt = MultivariateMulticycle([3, 3], [a, b, c]);
bb = MultivariateMulticycle([3, 3], [a, b]);
println(code_n(bt), code_k(bt), code_n(bb), code_k(bb))   # expected: (27, 3, 18, 2)

# 3. Truncating a factor complex changes the code: 3D toric example on Z_3^3
R3, (x, y, z) = Oscar.polynomial_ring(F2, ["x", "y", "z"]);
S3, _ = Oscar.quo(R3, Oscar.ideal(R3, [x^3 - 1, y^3 - 1, z^3 - 1]));
toric = MultivariateMulticycle([3, 3, 3], [S3(1 + x), S3(1 + y), S3(1 + z)]);
GA3 = Hecke.group_algebra(Hecke.GF(2), Hecke.abelian_group([3, 3, 3]));
a, b, c = Hecke.gens(GA3);
lp = LPCode([1+a 1+b], reshape([1+c], 1, 1));
println(code_n(toric), code_k(toric), code_n(lp), code_k(lp))   # expected: (81, 3, 81, 11)
