---
title: "Drag, part 2: Drag due to lift and the polar"
short_title: Drag due to lift and the polar
---

This is the second part of Lecture 7, *Drag Prediction*. It adds lift and Mach number to the parasite drag of [](parasite-drag.md): span efficiency, a worked polar, the polar at high lift, ground effect, and compressibility drag. It then assembles the three polars the RFP asks for and checks them. The figures are redrawn after the figures on the slides and reduced to the point each slide makes.

:::{note} What to take from this lecture
- Induced drag is set by the aspect ratio and the span efficiency.
- Maneuver, ground effect, and Mach number each change the polar.
- The model is validated on a known aircraft, compared with aircraft of your class, and carried with a margin.
:::

## Drag due to lift

:::{math}
:label: eq-polar
C_D = C_{D_{min}} + K\left(C_L - C_{L_{minD}}\right)^{2}, \qquad K = \frac{1}{\pi\,AR\,e}
:::

:::{figure} figures/induced-factor.svg
:label: fig-induced-factor
:alt: Induced drag factor delta against taper ratio for aspect ratios 4, 8, 12, and 16. Every curve is high at low taper, falls to a minimum near a taper ratio of 0.35, and rises again toward a taper ratio of 1. The curves for higher aspect ratios lie above the lower ones; at a taper ratio of 1, delta runs from about 0.03 at aspect ratio 4 to about 0.13 at aspect ratio 16.
:width: 80%

The induced drag factor of an unswept, untwisted wing. Computed with lifting-line theory; after Gudmundsson (2022), Figure 9-75.
:::

- $C_{D_{min}}$ occurs at $C_{L_{minD}}$. With $C_{L_{minD}}$ = 0 it equals $C_{D_0}$, the form the SR22 example uses.
- Wing alone, from theory: $e = 1/(1+\delta)$.
- Whole aircraft: $e$ of 0.70 to 0.85 is typical.
- Raymer, straight wing, $AR > 3$ (Gudmundsson 2022, Eq. 9-129): $e = 1.78\,(1-0.045\,AR^{0.68}) - 0.64$.
- Raymer, $\Lambda_{LE} > 30°$ and $AR < 10$ (Gudmundsson 2022, Eq. 9-130): $e = 4.61\,(1-0.045\,AR^{0.68})(\cos\Lambda_{LE})^{0.15} - 3.1$.

## Worked example: Cirrus SR22 polar

:::{table} The SR22 at the cruise condition of the build-up, computed with the equations of this lecture.
:label: tbl-sr22-polar

| Quantity | Value |
| --- | ---: |
| Weight | 2,750 lb |
| Dynamic pressure, $q$ | 91.6 lb/ft² |
| $C_L = W/(qS)$ | 0.207 |
| $e$, Raymer, $AR$ 10 (Gudmundsson 2022, Example 9-4) | 0.7566 |
| $K = 1/(\pi\,AR\,e)$ | 0.0421 |
| $C_{D_i} = K\,C_L^{2}$ | 0.0018 |
| $C_D = C_{D_0} + C_{D_i}$ | 0.0280 |
| Drag, $C_D\,q\,S$ | 371 lb |

:::

:::{figure} figures/sr22-polar.svg
:label: fig-sr22-polar
:alt: The SR22 polar, lift coefficient against drag coefficient, starting at a drag coefficient of 0.0262 at zero lift. A marker near the bottom shows cruise at 313 feet per second, with a lift coefficient of 0.207 and a lift-to-drag ratio of 7.4. A dashed line from the origin touches the curve at a lift coefficient of 0.79, where the lift-to-drag ratio reaches its maximum of 15.1.
:width: 75%

The SR22 polar, with the cruise point and the maximum lift-to-drag ratio. Computed.
:::

At cruise speed, parasite drag is 94% of the total. $(L/D)_{max}$ is at $C_L$ = 0.79.

## The polar at high lift

:::{math}
:label: eq-maneuver-cl
C_L = \frac{n\,W}{q\,S}
:::

:::{figure} figures/polar-break.svg
:label: fig-polar-break
:alt: Lift coefficient against drag coefficient. A solid curve and a dashed parabola coincide up to a lift coefficient of 0.5, marked the break lift coefficient. Above it the solid curve bends to much higher drag than the parabola; an arrow between the two is labeled separation adds drag.
:width: 75%

The polar leaves the parabola at the break $C_L$. Schematic, after Nicolai and Carichner (2010), Figure 2.17, which shows the F-4C at Mach 0.8.
:::

- The polar is parabolic up to the break $C_L$. Above it, separation adds drag.
- In a sustained turn, thrust equals drag at the $C_L$ of {eq}`eq-maneuver-cl`.
- Check it against the break $C_L$ and against $C_{L_{max}}$ at the flight Mach number.

:::{admonition} Navy Jet Trainer
:class: navy

Sustained +4.0 g (T) and +6.0 g (O) at 15,000 ft, at MTOW less 50% fuel. Where does that $C_L$ sit on your polar?
:::

## Ground effect

:::{math}
:label: eq-ground-effect
C_{D_i}^{\,IGE} = \Phi_L^{2}\,\Phi_D\,C_{D_i}^{\,OGE}, \qquad \Phi_D = \frac{33\,(h/b)^{1.5}}{1+33\,(h/b)^{1.5}}
:::

:::{figure} figures/ground-effect.svg
:label: fig-ground-effect
:alt: Ground influence coefficient against height over span from 0 to 1.5. The drag influence coefficient from Hoerner rises from zero at the ground through about 0.92 at a height of half a span and approaches 1. The lift influence coefficient is 1.05 below half a span and 1 above it.
:width: 75%

The ground influence coefficients. Computed from Hoerner's relation; after Gudmundsson (2022), Figure 9-74; Eqs. 9-113 and 9-119.
:::

- {term}`Ground effect` depends on $h$, the height of the aerodynamic center of the {term}`mean geometric chord` above the ground.
- In the absence of better data, $\Phi_L$ = 1.05 for $h/b < 0.5$, and 1 otherwise.
- The effect is noticeable below one span.

:::{admonition} Navy Jet Trainer
:class: navy

The takeoff and landing polars apply in ground effect near the runway. Wing height sets $h/b$.
:::

## Compressibility drag

A spline models the drag rise from $M_{crit}$ up to $M_{maxD}$, the Mach number where it reaches $\Delta C_{D_{max}}$ (Gudmundsson 2022, Eqs. 16-108 to 16-110):

:::{math}
:label: eq-compressibility
C_{D_c} = \frac{\Delta C_{D_{max}}}{2}\left[1+\tanh\,(A\,M + B)\right]
:::

:::{math}
:label: eq-compressibility-constants
A = \frac{2a}{M_{maxD}-M_{crit}}, \qquad B = -a - A\,M_{crit}, \qquad a = \tanh^{-1}\!\left(1-\frac{0.0002}{\Delta C_{D_{max}}}\right)
:::

:::{table} Token values of $M_{maxD}$ and $\Delta C_{D_{max}}$ for a clean wing, $M_{maxD}$ approximate. Selected rows of Gudmundsson (2022), Table 16-9.
:label: tbl-compressibility

| Wing, clean | $M_{maxD}$ | $\Delta C_{D_{max}}$ |
| --- | ---: | ---: |
| Straight | 1.10 | 0.055 |
| $\Lambda_{c/4}$ = 34° | 1.25 | 0.030 |
| $\Lambda_{c/4}$ = 45° | 1.65 | 0.020 |

:::

:::{figure} figures/compressibility.svg
:label: fig-compressibility
:alt: Two plots of compressibility drag against Mach number for a straight wing and wings swept 34 and 45 degrees at the quarter chord. Left, each curve ends at its table value: 0.055 at Mach 1.10, 0.030 at Mach 1.25, and 0.020 at Mach 1.65. Right, a close view from Mach 0.6 to 1.0 with drag up to 0.004: each curve leaves zero just after a dot at its critical Mach number, the straight wing first and steepest.
:width: 100%

The spline {eq}`eq-compressibility` with the values of {numref}`tbl-compressibility` and invented $M_{crit}$ of 0.70, 0.76, and 0.82, valid up to $M_{maxD}$. Computed; after Gudmundsson (2022), Figures 16-37 and 16-39.
:::

:::{admonition} Navy Jet Trainer
:class: navy

$M_{crit}$ comes from the Korn relation in [Lecture 5](../lecture-05/wing-geometry-and-lift.md). Check the drag rise at Mach 0.78 and Mach 0.90.
:::

## Three polars

:::{table} The three configurations the RFP asks for.
:label: tbl-three-polars

| Polar | Configuration |
| --- | --- |
| Cruise | Clean |
| Takeoff | Takeoff flaps, gear down |
| Landing | Landing flaps, gear down |

:::

:::{figure} figures/flap-polar.svg
:label: fig-flap-polar
:alt: Section drag coefficient against section lift coefficient with the flap up and down. The flap-up curve has a low minimum drag near zero lift. The flap-down curve has a higher minimum, at a higher lift coefficient, and lies farther to the right. The curves cross near a lift coefficient of 1, and above that the flap-down curve has the lower drag.
:width: 80%

Section data: what a flap does to the polar. Schematic, after Gudmundsson (2022), Figure 8-59.
:::

- Flaps raise the minimum drag and move it toward higher $C_L$.
- Gear and flaps add $C_{D_0}$. The span efficiency changes with the flap setting.
- Trim drag is 1 to 2% of the total in cruise (Gudmundsson 2022, Section 16.4.1). Add it once the tail is sized.

:::{admonition} Navy Jet Trainer
:class: navy

The RFP requires drag polars for the cruise, takeoff, and landing configurations. The flap increments come from [Lecture 6](../lecture-06/high-lift-wing-and-field.md). The gear increment comes from [Lecture 7, part 1](parasite-drag.md).
:::

## Check against existing aircraft

:::{math}
:label: eq-ldmax
\left(\frac{L}{D}\right)_{max} = \frac{1}{2\sqrt{C_{D_0}\,K}}
:::

This form holds for $C_{L_{minD}}$ = 0.

:::{table} Representative subsonic $C_{D_0}$ by aircraft class. Selected rows of Nicolai and Carichner (2010), Table 5.2.
:label: tbl-cd0-class

| Aircraft class | Subsonic $C_{D_0}$ |
| --- | ---: |
| High-subsonic jet transport | 0.014 to 0.020 |
| Supersonic fighter | 0.014 to 0.022 |
| Large turboprop | 0.018 to 0.024 |
| Small single-engine propeller, retractable gear | 0.022 to 0.030 |
| Small single-engine propeller, fixed gear | 0.026 to 0.040 |

:::

:::{figure} figures/ldmax-vs-ar.svg
:label: fig-ldmax
:alt: Maximum lift-to-drag ratio against subsonic Mach number. Six nearly flat lines, higher at higher aspect ratio: about 9 at aspect ratio 2, 11 at 3, 13 at 4, 16 at 6, 19 at 8, and 23 at 10. Three aircraft are marked: the U-2S near 25, the L-1011 near 17, and the F-16C near 11.
:width: 70%

Maximum lift-to-drag ratio of cruise aircraft, subsonic range. Values read from Nicolai and Carichner (2010), Figure 5.3, which continues to Mach 5.
:::

:::{iframe} ../quickcheck/polar-point.html
:label: qc-polar-point
:width: 100%

Quick check: a point on the polar from {eq}`eq-polar`, and the maximum lift-to-drag ratio from {eq}`eq-ldmax`. Shuffle gives new values; the solution shows the steps.
:::

:::{admonition} Navy Jet Trainer
:class: navy

Compare your build-up with aircraft of your class before the polar enters the sizing code.
:::

## Solvers agree on lift, not on drag

:::{figure} figures/solver-compare.svg
:label: fig-solver-compare
:alt: Two plots against angle of attack from 0 to 5 degrees for three solvers on one wing and tail: an MDO code, XFLR5, and OpenVSP. Left, the lift coefficient lines nearly coincide, reaching about 0.57 at 5 degrees. Right, the drag coefficient curves separate: at 5 degrees the MDO code reaches 0.0158, XFLR5 0.0140, and OpenVSP 0.0134.
:width: 100%

One wing and tail, three solvers: a multidisciplinary design optimization (MDO) code, XFLR5, and OpenVSP. Values at 0° and 5° from Silva et al. (2021), Table 1; the drag between them read from their Figure 17.
:::

:::{table} The three solvers at 5° angle of attack. Silva et al. (2021), Table 1.
:label: tbl-solver-compare

| $\alpha$ = 5° | MDO code | XFLR5 | OpenVSP |
| --- | ---: | ---: | ---: |
| $C_L$ | 0.5752 | 0.5692 | 0.5692 |
| $C_D$ | 0.0158 | 0.0140 | 0.0134 |

:::

- At 5°, lift agrees within about 1% and drag differs by up to 18%. At 0°, drag differs by up to 21%.
- Validate your code on a known aircraft.
- Carry a margin, and update the model as the design matures.

## This week

1. Write the build-up code. Reproduce the SR22 case of [Lecture 7, part 1](parasite-drag.md): $C_{D_0}$ = 0.0262.
2. Run the build-up on your aircraft. Take the wetted areas from the loft and state the transition point.
3. Compute the span efficiency, $K$, and the cruise polar. Compare them with aircraft of your class.
4. Compute the drag rise at the maximum operating Mach number.

:::{tip}
The takeoff and landing polars need the flap increments from [Lecture 6](../lecture-06/high-lift-wing-and-field.md) and the gear increment from [Lecture 7, part 1](parasite-drag.md). [](../assignments/a04.md), Deliverable 5, asks for the build-up by component and the polars. [](../assignments/a05.md), Deliverable 1, then states the polar of each configuration your segments fly.
:::

:::{important} Summary
- Parasite drag is built up by component from skin friction, form, interference, and the miscellaneous items.
- Induced drag is set by the aspect ratio and the span efficiency. Maneuver, ground effect, and Mach number each change the polar.
- The model is validated on a known aircraft, compared with aircraft of your class, and carried with a margin.
:::

:::{exercise} For discussion
:label: ex-drag

At cruise speed the SR22 flies well below its $(L/D)_{max}$, and parasite drag is 94% of the total. Take your aircraft at Mach 0.78 and 25,000 ft, at the ASORT wing loading. Where does the cruise $C_L$ sit against the $C_L$ of $(L/D)_{max}$, and which term of the polar would you work on first?
:::

:::{seealso} Reading
Gudmundsson (2022), Chapter 16, and Nicolai and Carichner (2010), Chapter 2. In class, build the cruise, takeoff, and landing polars for your configuration. [Lecture 8](../lecture-08/engine-selection.md) covers propulsion: the engine class, the thrust and fuel-flow models, and the inlet.
:::

## Quiz

:::{iframe} ../quickcheck/quiz-lecture-07.html
:label: quiz-lecture-07
:width: 100%

Quiz on Lecture 7: eight questions, one at a time, with the explanation after each answer. It is not graded and nothing is recorded.
:::

## References

- Gudmundsson, S., *General Aviation Aircraft Design: Applied Methods and Procedures*, 2nd ed., Butterworth-Heinemann, 2022. Chapters 8, 9, and 16.
- Nicolai, L. M., and Carichner, G. E., *Fundamentals of Aircraft and Airship Design, Volume 1: Aircraft Design*, AIAA Education Series, 2010. Chapters 2 and 5.
- Raymer, D. P., *Aircraft Design: A Conceptual Approach*, 6th ed., AIAA, 2018. Chapter 12.
- Shevell, R. S., *Fundamentals of Flight*, 2nd ed., Prentice Hall, 1989.
- Silva, H. L., Resende, G. J., Neto, R. M. C., Carvalho, A. R. D., Gil, A. A., Cruz, M. A. A., and Guimarães, T. A. M., "A multidisciplinary design optimization for conceptual design of hybrid-electric aircraft," *Structural and Multidisciplinary Optimization*, Vol. 64, 2021, pp. 3505-3526.
- AIAA 2026-27 Undergraduate Team Aircraft Design Competition RFP, *Design of a Navy Jet Training Aircraft*; see [](../navy-rfp/navy-rfp.md).
