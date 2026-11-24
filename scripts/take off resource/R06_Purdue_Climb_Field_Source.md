---
title: "Performance, part 2: Climb and field performance"
short_title: Climb and field performance
---

This is the second part of Lecture 11, *Performance Assessment*. It covers the steady climb, the speeds for the best angle and the best rate, the takeoff speeds, the ground run and its integration, the balanced and critical field lengths, the landing, and the effect of altitude, temperature, and weight on the ground run. The equations of motion and the symbols are in [](level-flight-and-range.md).

:::{note} What to take from this lecture
- The climb angle follows $T - D$ and the rate of climb follows $V\,(T - D)$. Compute both with the engine deck; the closed forms are a check.
- The takeoff speeds follow from the stall speed, the control with an engine out, and the tail-strike angle, with the factors of MIL-STD-3013B.
- Field lengths come from integrating the ground run at the altitude, the temperature, and the weight of the requirement.
:::

## Steady climb

The forces are those of {numref}`fig-eom-climb` in [part 1](level-flight-and-range.md). In a steady climb the force equations of {eq}`eq-perf-climb` become

:::{math}
:label: eq-climb-balance
T\cos\varepsilon - D - W\sin\gamma = 0, \qquad T\sin\varepsilon + L - W\cos\gamma = 0
:::

With $\varepsilon \approx 0$ and $\cos\gamma \approx 1$:

:::{math}
:label: eq-climb-angle-rate
\sin\gamma = \frac{T - D}{W} \approx \frac{T}{W} - \frac{1}{L/D}, \qquad
V_v = V\sin\gamma = \frac{V\,(T - D)}{W}
:::

At a steady true airspeed the rate of climb $V_v$ equals the specific excess power $P_s$. A climb at a constant calibrated airspeed gains true airspeed with altitude, and part of $P_s$ goes into that acceleration:

:::{math}
:label: eq-climb-accel-factor
V_v = \frac{P_s}{1 + \dfrac{V}{g}\dfrac{dV}{dh}}
:::

At 250 KCAS in the standard atmosphere the denominator is 1.08 at sea level, 1.13 at 15,000 ft, and 1.19 at 25,000 ft.

- The angle matters for obstacle clearance and noise. The rate matters for the time to altitude.
- With the thrust along the flight path, $\sin\gamma = (T - D)/W$ holds at any angle. The drag in it is computed at $L = W\cos\gamma$. Taking $L = W$ is close below about 15°; a jet trainer at low altitude can climb more steeply, so iterate on $\gamma$ as in {numref}`fig-climb-learjet`.

## Best angle and best rate

For a jet with a thrust that does not change with speed (Gudmundsson 2022, Chapter 19):

:::{math}
:label: eq-best-angle
\sin\gamma_{max} = \frac{T}{W} - \frac{1}{(L/D)_{max}}, \qquad V_X \approx V_{md}
:::

:::{math}
:label: eq-best-rate
V_Y = \sqrt{\frac{(T/W)\,(W/S)}{3\,\rho\,C_{D_0}}\left[1+\sqrt{1+\frac{3}{(L/D)^2_{max}\,(T/W)^2}}\right]}
:::

- For the Learjet 45 at sea level, 20,000 lb, and $T$ = 4,635 lb, $\gamma_{max}$ = 9.62° and $V_X$ = 174 KCAS (Gudmundsson 2022, Example 19-7), and {eq}`eq-best-rate` gives $V_Y$ = 278 KCAS.
- Include the compressibility drag in $C_{D_0}$ when $V_Y$ is high.
- In the Mattingly model the thrust rises with Mach number at low altitude. Compute the rate of climb against speed with the engine deck and take its maximum.

:::{admonition} Navy Jet Trainer
:class: navy

The training flight climbs at 250 KCAS. How does that speed compare with your $V_Y$ at each altitude of the climb?
:::

## A published jet: Learjet 45 climb

:::{figure} figures/climb-learjet.svg
:label: fig-climb-learjet
:alt: Two panels against calibrated airspeed at sea level from 110 to 380 knots, each with two curves: thrust held at 4,635 pounds, and the military thrust, which rises with speed. Left, rate of climb. With constant thrust it rises from 1,540 feet per minute to a peak of 3,874 at 278 knots, marked V Y, and falls to 2,790. With the military thrust it peaks at 4,180 feet per minute at 327 knots. Right, climb angle. With constant thrust it peaks at 9.7 degrees at 174 knots, marked V X, and falls to 4.2 degrees. With the military thrust it peaks at 9.1 degrees at 192 knots.
:width: 100%

Rate of climb and climb angle of the Learjet 45, a published example, at 20,000 lb and sea level, with the thrust held at 4,635 lb and with the military thrust of the Mattingly model. The lift is $W\cos\gamma$, so $\gamma_{max}$ is 9.7° against 9.62° from the closed form. Computed; inputs from Gudmundsson (2022), Table 17-8 and Examples 19-1, 19-4, and 19-7.
:::

- With the thrust of the Mattingly model in place of the constant 4,635 lb, $V_Y$ moves from 278 to 327 KCAS and the best rate of climb is 8% higher.
- The top of the curve is flat. Fly the speed the mission states.
- Example 19-4 of Gudmundsson (2022) iterates $V_Y$ to 281 KCAS: it updates $T$ but ignores $dT/dV$. The maximum of the computed curve is at 327 KCAS.

:::{admonition} Navy Jet Trainer
:class: navy

Plot the rate of climb and the climb angle with your engine deck. How far is each maximum from its closed form?
:::

## Takeoff speeds

:::{figure} figures/takeoff-speeds.svg
:label: fig-takeoff-speeds
:alt: A runway seen from the side with a jet trainer at three points of the takeoff: at rest at brake release, rotating with the nose wheel off the runway, and climbing past the obstacle height, h with the subscript obst. A dashed line traces its path along the runway and up after liftoff. Marks along the runway give the speeds in order: V equals zero at brake release, the stall speed V S 1, the minimum control speed V m c, the decision speed V 1, the rotation speed V R, the minimum unstick speed V M U, the liftoff speed V L O F, and the takeoff safety speed V 2 at the obstacle height.
:width: 100%

The speeds along the takeoff. Schematic, after Gudmundsson (2022), Figure 18-4.
:::

:::{table} The takeoff speeds.
:label: tbl-takeoff-speeds

| Speed | Definition |
| --- | --- |
| $V_{mc}$ | Minimum control speed with the critical engine failed; aircraft with two or more engines |
| $V_1$ | Decision speed. Below it, stop on the runway; above it, continue with an engine out |
| $V_R$ | Rotation speed. The pilot starts to raise the nose |
| $V_{MU}$ | Minimum unstick speed, at the tail-strike angle |
| $V_{LOF}$ | Liftoff speed |
| $V_2$ | Takeoff safety speed, at the obstacle height |

:::

:::{admonition} Navy Jet Trainer
:class: navy

The RFP cites MIL-STD-3013B for these speeds. Which of them apply to your number of engines?
:::

## Computing the takeoff speeds

:::{table} How each takeoff speed is computed. After Gudmundsson (2022), Eq. 18-18 and Sections 13.3.1, 18.1.3, 18.2.6, and 18.3.5; the minimum control speed after Nelson (1998), Chapter 2.
:label: tbl-takeoff-speed-relations

| Speed | Relation | Notes |
| --- | --- | --- |
| Stall, takeoff configuration | $V_{S1} = \sqrt{2W/(\rho\,S\,C_{L_{max}})}$ | Power off |
| Minimum control, two or more engines | $V_{mc}$: see {eq}`eq-vmc` | Full rudder against the failed engine, with a bank of 5° or less. $T$ is the thrust of the live engine at $V_{mc}$: iterate. This is {eq}`eq-engine-out` of [Lecture 10](../lecture-10/lateral-and-controls.md), solved for the speed |
| Decision, two or more engines | $V_1$: $S_{stop} = S_{go} = S_{BFL}$ | The stop and go distances of {numref}`fig-balanced-field`; no closed form. The engine fails at $V_{EF}$, a reaction time earlier |
| Rotation and liftoff | $V_R = V_{LOF} = 1.1\,V_{S1}$ | An assumption of Gudmundsson (2022), Eq. 18-18. Large aircraft rotate 3 s before liftoff |
| Minimum unstick | $V_{MU} = \sqrt{2W/(\rho\,S\,C_{L,TS})}$ | $C_{L,TS}$ is the lift coefficient at the tail-strike angle in ground effect, at most $C_{L_{max}}$. Lift only, with no thrust term |
| Takeoff safety, at the obstacle | $V_2 \ge 1.20\,V_{S1}$ | With two or more engines, also above $V_{mc}$, as in [Lecture 10](../lecture-10/lateral-and-controls.md). The climb at $V_2$ must hold the required gradient |

:::

The minimum control speed is

:::{math}
:label: eq-vmc
V_{mc} = \sqrt{\frac{2\,(T + D_{dead})\,y_e}{\rho\,S\,b\,\lvert C_{n\delta_r}\rvert\,\delta_{r,max}}}
:::

Every speed comes from the polar of the sizing code, your landing gear, and your tail.

## Takeoff speed rules

:::{table} The speed rules of MIL-STD-3013 (2003 issue), Sections 3.2, 3.2.3, and 3.2.4. The RFP cites revision B. The factors on the approach and touchdown speeds are in {numref}`tbl-reference-speeds` of Lecture 6. $V_S$ here is the $V_{S1}$ of {numref}`tbl-takeoff-speed-relations`.
:label: tbl-takeoff-speed-rules

| Speed | MIL-STD-3013 |
| --- | --- |
| $V_S$ | Power off (Section 3.2.3) |
| $V_{mc}$ | No factor |
| $V_1$ | Set by the engine-failure speed of the critical field length |
| $V_R$ | No factor |
| $V_{LOF}$ | Liftoff at $1.10\,V_S$ (Section 3.2.3) |
| $V_2$ | $1.20\,V_S$ at 50 ft (Section 3.2.4) |

:::

:::{admonition} Navy Jet Trainer
:class: navy

The RFP cites MIL-STD-3013B for the speed and distance definitions; [Lecture 6](../lecture-06/high-lift-devices.md) lists the distances. Do the factors of revision B match the 2003 issue quoted here?
:::

## The ground run

Along the runway, with the rolling friction on the weight the wheels carry:

:::{math}
:label: eq-ground-run
\frac{W}{g}\frac{dV}{dt} = T - D - \mu\,(W - L) - W\sin\theta_r
:::

- $L$ and $D$ come from the takeoff polar in [ground effect](../lecture-07/drag-polar.md), at the angle of attack of the ground run.
- $T$ comes from the engine deck at the pressure altitude and the temperature of the runway. It varies along the run.
- $\theta_r$ is the runway slope, positive uphill. The equation is the form for a small slope.
- Once $L > W$, the friction term is zero.

:::{table} Rolling and braking friction coefficients. Selected rows of Gudmundsson (2022), Table 18-4.
:label: tbl-friction

| Surface | $\mu$, rolling | $\mu_B$, braking |
| --- | ---: | ---: |
| Dry asphalt or concrete | 0.03 to 0.05 | 0.3 to 0.5 |
| Wet asphalt or concrete | 0.05 | 0.15 to 0.3 |
| Icy asphalt or concrete | 0.02 | 0.06 to 0.10 |
| Hard turf | 0.05 | 0.4 |

:::

:::{admonition} Navy Jet Trainer
:class: navy

The MIL-STD-3013 distances assume a dry, hard runway. Which values of $\mu$ and $\mu_B$ do you use, and what is their source?
:::

## Integrating the ground run

Integrate {eq}`eq-ground-run` in steps of $\Delta t$ = 0.25 s (Gudmundsson 2022, Eqs. 18-14 to 18-17):

1. $q_i = \tfrac{1}{2}\rho V_{i-1}^2$, then $T_i$, $L_i$, and $D_i$.
2. $a_i = \dfrac{g}{W}\left[T_i - D_i - \mu\,(W - L_i)\right]$.
3. $V_i = V_{i-1} + a_i\,\Delta t$.
4. $S_i = S_{i-1} + V_{i-1}\,\Delta t + \tfrac{1}{2}a_i\,\Delta t^2$.
5. Repeat until $V_i \ge V_R$.

A closed form uses the average acceleration, taken at $V_R/\sqrt{2}$ (Gudmundsson 2022, Eq. 18-22):

:::{math}
:label: eq-ground-run-average
S_G = \frac{V_R^2}{2\,\bar a}
:::

:::{figure} figures/ground-run.svg
:label: fig-ground-run
:alt: Calibrated airspeed against ground distance from brake release. Two curves lie on top of each other: the step-by-step integration and the estimate with the average acceleration. They rise steeply at first, pass about 58 knots at 500 feet and 100 knots at 1,500 feet, and reach the rotation speed, 122 knots, marked by a dotted line, at 2,246 feet. The integration takes 21.5 seconds.
:width: 80%

The ground run of the Learjet 45, a published example (Gudmundsson 2022, Example 18-5): 21,500 lb at sea level, $T$ = 7,000 lb, $C_L$ = 0.90, $C_D$ = 0.045, $\mu$ = 0.02, and $V_R$ = 206.7 ft/s as printed (the inputs give 206.3). Integrated in steps of 0.25 s, and estimated with the average acceleration. Computed.
:::

Both methods give 2,246 ft, because the thrust is constant.

Gudmundsson's procedure runs the integration to $V_{LOF}$; his Example 18-5 stops at $V_R$, as here. The example's $\mu$ = 0.02 is below the dry-runway range of {numref}`tbl-friction`.

The rotation, the transition, and the climb to the obstacle follow the ground run. They are in [Lecture 6](../lecture-06/high-lift-wing-and-field.md).

:::{admonition} Navy Jet Trainer
:class: navy

Integrate the ground run with your engine deck. How far apart are the two methods with your deck?
:::

## Balanced and critical field length

:::{prf:definition} Balanced field length
:label: def-balanced-field-length

The {term}`balanced field length` is the runway length at which, after an engine failure at the engine-failure speed, the distance to continue the takeoff to the obstacle height equals the distance to stop. The {term}`critical field length` of MIL-STD-3013B balances the distance to lift off against the distance to stop ({numref}`tbl-milstd-distances` of Lecture 6).
:::

:::{figure} figures/balanced-field.svg
:label: fig-balanced-field
:alt: Airspeed against distance from brake release. A solid curve, all engines, rises from zero through the decision speed V 1 to the liftoff speed V L O F. A dot on it marks the engine failure at V E F and the decision at V 1. Two branches leave the dot. The continue branch, with an engine out, rises more slowly than the all-engines curve and reaches the takeoff safety speed V 2. The stop branch, with brakes, falls to zero speed. Both branches end at the same distance, the balanced field length, shown as a runway bar under the axis.
:width: 75%

The continue and stop branches of the balanced field length. Schematic, after Gudmundsson (2022), Figures 18-16 and 18-17.
:::

An estimate for aircraft with two or more engines (Gudmundsson 2022, Eq. 18-33, after Torenbeek 1982), in feet:

:::{math}
:label: eq-balanced-field
S_{BFL} = \frac{0.863}{1+2.3\,\Delta\gamma_2}\left(\frac{W/S}{\rho\,g\,C_{L_2}} + h_{obst}\right)\left(2.7 + \frac{1}{\bar T/W - \mu'}\right) + \frac{655}{\sqrt{\sigma}}
:::

- $\Delta\gamma_2 = \gamma_2 - \gamma_{2,min}$ in radians, with $\gamma_2 = \sin^{-1}[(T_{OEI} - D_2)/W]$ the climb angle at $V_2$ with one engine failed and $\gamma_{2,min}$ = 0.024 for a twin.
- $C_{L_2}$ is the lift coefficient at $V_2$, and $h_{obst}$ is the obstacle height, 50 ft in the example.
- $\mu' = 0.01\,C_{L_{max}} + 0.02$, with $C_{L_{max}}$ of the takeoff configuration.
- $\bar T = 0.75\,T_{TO}\,(5 + BPR)/(4 + BPR)$ is the mean thrust, with $T_{TO}$ the maximum static thrust of all engines and $BPR$ the bypass ratio.
- $\rho$ is in slug/ft³ and $\sigma$ is the density ratio.

For the Learjet 45 the estimate gives 5,587 ft against a published 5,500 ft (Gudmundsson 2022, Example 18-9).

:::{admonition} Navy Jet Trainer
:class: navy

The RFP sets the critical field length at 6,000 ft and cites MIL-STD-3013B. With one engine, what follows an engine failure on the runway? With two, where is your $V_1$?
:::

## Altitude, temperature, and weight

:::{figure} figures/takeoff-altitude-weight.svg
:label: fig-takeoff-altitude-weight
:alt: Two panels of pressure altitude, from sea level to 10,000 feet, against ground run. Left, three temperatures at 21,500 pounds. On a standard day the ground run grows from 2,209 feet at sea level to 4,530 feet at 10,000 feet. At 10,000 feet the line for standard minus 20 degrees Celsius is about 7 percent shorter and the line for standard plus 20 degrees Celsius about 7 percent longer. Right, three weights on a standard day. At sea level the ground run is 1,527 feet at 18,000 pounds, 1,900 feet at 20,000 pounds, and 2,209 feet at 21,500 pounds. At 10,000 feet it is 3,108, 3,884, and 4,530 feet. A note reads: ground run grows as weight to the power 2.1 at sea level.
:width: 100%

Ground run of the Learjet 45, a published example, from sea level to 10,000 ft pressure altitude: three temperatures at 21,500 lb, and three weights at ISA. Integrated to $V_R = 1.1\,V_{S1}$ with the maximum thrust of the Mattingly model at the pressure altitude and temperature of the runway. Computed; inputs from Gudmundsson (2022), Table 17-8 and Example 18-5.
:::

- From sea level to 10,000 ft, $S_G$ grows from 2,209 to 4,530 ft, a factor of 2.05. The 2,209 ft differs from the 2,246 ft of {numref}`fig-ground-run` because the thrust model and $V_R$ differ.
- A day 20 °C above standard adds 7% at 10,000 ft.
- Here $S_G \propto W^{2.1}$.

:::{admonition} Navy Jet Trainer
:class: navy

The RFP field lengths are at 5,000 ft density altitude. How much longer is your ground run there than at sea level?
:::

## Landing

In the braking roll:

:::{math}
:label: eq-landing-roll
\frac{W}{g}\frac{dV}{dt} = -\left[\mu_B\,(W - L) + D - T\right]
:::

- $T$ is the idle thrust, or negative with thrust reversers.
- $D$ comes from the landing polar, plus spoilers or speed brakes.
- Spoilers dump the lift. The brakes need weight on the wheels.
- The air distance and the flare are in [Lecture 6](../lecture-06/high-lift-wing-and-field.md). Integrate the braking roll as for the takeoff.

The source is Gudmundsson (2022), Eqs. 23-1 and 23-8 to 23-16.

:::{admonition} Navy Jet Trainer
:class: navy

The RFP asks for a landing distance of 5,000 ft at MLW and 5,000 ft density altitude, with full-stop FCLP and no carrier suitability. What is your MLW, and how much fuel does it include?
:::

:::{seealso}
Continue with [](maneuver-and-vn.md): energy height and specific excess power, turns, the turn-rate chart, the flight envelope, the load factor of each maneuver, and the maneuver V-n diagram. The references for the three parts are at the end of that page.
:::
