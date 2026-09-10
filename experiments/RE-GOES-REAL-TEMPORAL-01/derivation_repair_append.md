
## Numerical-map repair after Scientific Review 01

Scientific Review 01 did not invalidate the analytical envelope or `Q` derivation; it showed that the historical conversion of continuous `g` into a finite policy/resource partition was unsafe near close transitions. The corrected numerical layer follows the piecewise algebra explicitly.

Within one envelope segment,

\[
u_0(g)=a_0+s_0g,\qquad u_1(g)=a_1+s_1g,
\]

and, for one fixed action pair,

\[
Q(g)=A u_0(g)^2+C u_0(g)u_1(g)+E u_1(g)^2.
\]

Thus an action-feasibility transition is a root of a Decimal quadratic on that segment. The repair solves the equation and writes an outward interval `[g_-,g_+]`. The actually serialized/re-read endpoints are independently required to satisfy

\[
Q(g_-)-\epsilon < 0 < Q(g_+)-\epsilon,
\]

except when the relevant equality is a model/domain threshold rather than a certificate root. The configured ordinary half-width is `10^{-18}`. Distinct roots are not merged by distance; identical events are collapsed only after equality of the underlying threshold equation is established.

Model-nonempty and replay-compatibility thresholds are not certificate roots. For finite-decimal anchors and ceiling `B`, their exact value is a rational number

\[
g_{\min}=\max_{i<k}\frac{|y_i-y_k|}{B|i-k|}.
\]

The corrected map stores the exact numerator/denominator and an outward Decimal enclosure. A rounded decimal rendering of `g_min` is never used to decide compatibility. At exact equality the accepted `<=` semantics put the model/replay condition on its valid side.

The exported domain is the disjoint semantic union of (i) resolved open policy cells, (ii) verified certificate or model/replay boundary enclosures and (iii) explicit equality/end-point records. Resource savings and retention are not assigned inside enclosure bands. An overlap whose ordering/equality could not be proved would be exported as `UNRESOLVED`; none remains in the repaired run.
