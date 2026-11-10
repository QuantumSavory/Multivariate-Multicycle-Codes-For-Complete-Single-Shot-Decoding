# Subfamilies of MM codes: construction examples

These examples accompany Sec. VI.C of *Multivariate Multicycle Codes for Complete Single-Shot Decoding*. Each one builds a known code family as an MM code with `MultivariateMulticycle` from QuantumClifford.jl and prints $(n, k, d)$. They were an appendix of the original submission and are reproduced here as recorded Julia REPL sessions.

Requirements: QuantumClifford.jl with the Oscar extension, JuMP and Gurobi.

`DistanceMIPAlgorithm` returns the optimal distance only when the solver finishes. With a `time_limit`, a returned value is an upper bound unless the solver reports an optimal solution. The printed distance is the minimum over the $X$ and $Z$ sectors.

## Abelian Multicycle codes

### [[96, 6, (8,8)]] AMC code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l, m, p, r = 16, 1, 1, 1;
julia> R, (w, x, y, z) = polynomial_ring(GF(2), [:w, :x, :y, :z]); # polynomial ring R = F_2[x,y]
julia> I = ideal(R, [w^l - 1, x^m - 1, y^p - 1, z^r - 1]); # Ideal I = (x^l - 1, y^m - 1)
julia> S, _ = quo(R, I);  # quotient ring S = R/I
julia> A = S(1 + w); # A(x,y) in S
julia> B = S(1 + w^3); # B(x,y) in S
julia> C = S(1 + w^5); # C(x,y) in S
julia> D = S(1 + w^7); # D(x,y) in S
julia> c = MultivariateMulticycle([l, m, p, r], [A, B, C, D]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi))
(96, 6, 8)
```

## Bivariate Bicycle codes

### [[144, 12, (12,12)]] BB code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l=12; m=6;
julia> R, (x, y) = polynomial_ring(GF(2), [:x, :y]);
julia> I = ideal(R, [x^l-1, y^m-1]);
julia> S, _ = quo(R, I);
julia> A = S(x^3 + y + y^2);
julia> B = S(y^3 + x + x^2);
julia> c = MultivariateMulticycle([l,m], [A,B]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi))
(144, 12, 12)
```

## Trivariate Tricycle codes

### [[72, 6, (12,6)]] TT code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l, m, p = 4, 3, 2;
julia> R, (x, y, z) = polynomial_ring(GF(2), [:x, :y, :z]);
julia> I = ideal(R, [x^l - 1, y^m - 1, z^p - 1]);
julia> S, _ = quo(R, I);
julia> A = S(1 + y + x*y^2);
julia> B = S(1 + y*z + x^2*y^2);
julia> C = S(1 + x*y^2*z + x^2*y);
julia> c = MultivariateMulticycle([l,m, p], [A, B, C]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi))
(72, 6, 6)
```

## 4D Toric codes

### [[96, 6, (4,4)]] 4D Toric code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l, m, p, r = 2, 2, 2, 2;
julia> R, (w, x, y, z) = polynomial_ring(GF(2), [:w, :x, :y, :z]);
julia> I = ideal(R, [w^l - 1, x^m - 1, y^p - 1, z^r - 1]);
julia> S, _ = quo(R, I);
julia> A = S(1 + w);
julia> B = S(1 + x);
julia> C = S(1 + y);
julia> D = S(1 + z);
julia> c = MultivariateMulticycle([l, m, p, r], [A, B, C, D]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi))
(96, 6, 4)
```

## La-Cross codes

### [[98, 18, (4,4)]] La-Cross code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> n = 7;
julia> R, (x, y) = polynomial_ring(GF(2), [:x, :y]);
julia> I = ideal(R, [x^n-1, y^n-1]);
julia> S, _ = quo(R, I);
julia> A = S(1 + x + x^3);
julia> B = S(1 + y + y^3);
julia> c = MultivariateMulticycle([n,n], [A,B]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi, time_limit=900))
(98, 18, 4)
```

## Multivariate Bicycle codes

### [[48, 4, (6,6)]] MB code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l=4; m=6;
julia> R, (x, y) = polynomial_ring(GF(2), [:x, :y]);
julia> I = ideal(R, [x^l-1, y^m-1]);
julia> S, _ = quo(R, I);
julia> z = x*y;
julia> A = S(x^3 + y^5);
julia> B = S(x + z^5 + y^5 + y^2);
julia> c = MultivariateMulticycle([l,m], [A,B]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi, time_limit=900))
(48, 4, 6)
```

## Generalized Bicycle codes

### [[30, 8, (4,4)]] GB code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l=15; m=1;
julia> R, (x, y) = polynomial_ring(GF(2), [:x, :y]);
julia> I = ideal(R, [x^l-1, y^m-1]);
julia> S, _ = quo(R, I);
julia> A = S(1 + x^2 + x^8);
julia> B = S(1 + x + x^4);
julia> c = MultivariateMulticycle([l,m], [A,B]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi, time_limit=900))
(30, 8, 4)
```

## Abelian two-block group algebra codes

### [[16, 2, (4,4)]] 2BGA code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l=2; m=4;
julia> R, (s, x) = polynomial_ring(GF(2), [:s, :x]);
julia> I = ideal(R, [s^l-1, x^m-1]);
julia> S, _ = quo(R, I);
julia> A = S(1 + x);
julia> B = S(1 + x + s + x^2 + s*x + s*x^3);
julia> c = MultivariateMulticycle([l,m], [A,B]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi, time_limit=900))
(16, 2, 4)
```

## Cyclic hypergraph product codes

### [[450, 32, (8,8)]] C2 code

```julia-repl
julia> using Oscar; using JuMP; using QuantumClifford.ECC;
julia> l=15; m=15;
julia> R, (x, y) = polynomial_ring(GF(2), [:x, :y]);
julia> I = ideal(R, [x^l-1, y^m-1]);
julia> S, _ = quo(R, I);
julia> A = S(1 + x + x^4);
julia> B = S(1 + y + y^4);
julia> c = MultivariateMulticycle([l,m], [A,B]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi, time_limit=900))
(450, 32, 8)
```

### [[240, 8, (8,8)]] CxR code

```julia-repl
julia> using Oscar; using QuantumClifford.ECC;
julia> l=15; m=8;
julia> R, (x, y) = polynomial_ring(GF(2), [:x, :y]);
julia> I = ideal(R, [x^l-1, y^m-1]);
julia> S, _ = quo(R, I);
julia> A = S(1 + x + x^4);
julia> B = S(1 + y);
julia> c = MultivariateMulticycle([l,m], [A,B]);
julia> import Gurobi;
julia> code_n(c), code_k(c), distance(c, DistanceMIPAlgorithm(solver=Gurobi, time_limit=900))
(240, 8, 8)
```
