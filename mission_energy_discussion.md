# Mission Energy & Fuel Fraction Transfer: Kerosene (Do 228) to Battery-Electric Aircraft

This document summarizes our methodology for transferring the mission fuel breakdown of the reference aircraft (**Dornier 228**) into electrical battery energy ($\text{kWh}$) and battery mass ($\text{kg}$) for our 19-passenger battery-electric aircraft.

---

## 1. Reference Aircraft Data (Dornier 228 – 100 NM Reference Mission)

For the $100\text{ NM}$ ($185.2\text{ km}$) reference mission, the Do 228 starts at a mission take-off mass of **$5950\text{ kg}$** ($\text{ZFM} = 5600\text{ kg} + 350\text{ kg}$ total fuel, below structural $\text{MTOM}_{\text{ref}} = 6400\text{ kg}$):
- **Reference Mission Start Mass ($m_{\text{ref,0}}$):** $5950\text{ kg}$
- **Cruise Speed ($v_{\text{cruise}}$):** $200\text{ kts} = 102.89\text{ m/s}$
- **Cruise Altitude ($h_{\text{cruise}}$):** $10\,000\text{ ft} = 3048\text{ m}$
- **Cruise Lift-to-Drag Ratio ($(L/D)_{\text{cruise}}$):** $12.1$
- **Thrust Specific Fuel Consumption ($\text{TSFC}$):** $0.46\text{ lb/(h}\cdot\text{lbf)} = 1.3025 \times 10^{-5}\text{ kg/(N}\cdot\text{s)}$
- **Kerosene Specific Energy ($e_{\text{fuel}}$):** $42.8\text{ MJ/kg} = 11.89\text{ kWh/kg}$

| Phase | Segment | Reference Fuel $m_{\text{fuel,ref}}$ | Start Mass $m_{\text{start,ref}}$ | Average Mass $\bar{m}_{\text{ref}}$ | Mass Fraction $M_{\text{ff},i}$ |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **1** | Taxi-out (5 min) & Take-off | $24\text{ kg}$ | $5950\text{ kg}$ | $5938.0\text{ kg}$ | $0.99597$ |
| **2** | Climb (to $10\,000\text{ ft}$ & $200\text{ kts}$) | $36\text{ kg}$ | $5926\text{ kg}$ | $5908.0\text{ kg}$ | $0.99393$ |
| **3** | Cruise ($100\text{ NM}$ total stage length) | $78\text{ kg}$ | $5890\text{ kg}$ | $5851.0\text{ kg}$ | $0.98676$ |
| **4** | Descent | $9\text{ kg}$ | $5812\text{ kg}$ | $5807.5\text{ kg}$ | $0.99845$ |
| **5** | Approach, Landing & Taxi-in (4 min) | $17\text{ kg}$ | $5803\text{ kg}$ | $5794.5\text{ kg}$ | $0.99707$ |
| **1–5** | **Trip Total** | **$164\text{ kg}$** | **$5950\text{ kg}$** | – | **$0.97244$** |
| **6** | **Reserve** (5% route + 30 min loiter + 50 NM) | **$186\text{ kg}$** | **$5786\text{ kg}$** | **$5693.0\text{ kg}$** | **$0.96785$** |
| **1–6** | **Mission Total (Trip + Reserve)** | **$350\text{ kg}$** | **$5950\text{ kg}$** | – | **$0.94118$** |

---

## 2. General Transfer Methodology: Kerosene to Electric Energy

To transfer a segment's fuel mass $m_{\text{fuel,ref},i}$ to the battery-electric aircraft (illustrated below for $\text{MTOM} = 7500\text{ kg}$ and electric powertrain efficiency $\eta_{\text{el}} = 85\,\%$), two main physical factors are applied:

### 2.1 Reference Turboprop Propulsion Efficiency ($\eta_{\text{ref}}$)
Only a fraction of the chemical energy in kerosene is converted into useful propulsive work at the propeller. Using the reference cruise speed and $\text{TSFC}$:

$$\eta_{\text{ref}} = \frac{v_{\text{cruise}}}{\text{TSFC}_{\text{SI}} \cdot e_{\text{fuel}}} = \frac{102.89\text{ m/s}}{1.3025 \times 10^{-5}\text{ kg/(N}\cdot\text{s)} \cdot 42.8 \times 10^6\text{ J/kg}} = \mathbf{18.46\,\%}$$

The useful propulsive energy of segment $i$ on the reference aircraft is therefore:

$$E_{\text{prop,ref},i} = m_{\text{fuel,ref},i} \cdot e_{\text{fuel}} \cdot \eta_{\text{ref}}$$

### 2.2 Constant Mass of the Battery-Electric Aircraft ($\text{MTOM} / \bar{m}_{\text{ref},i}$)
While the Do 228 becomes lighter throughout the flight as fuel is burned ($\bar{m}_{\text{ref}}$ drops from $5938\text{ kg}$ at take-off down to $5693\text{ kg}$ during reserve), the battery-electric aircraft remains at **constant $\text{MTOM}$** from take-off to landing ($\text{MTOM} = \text{MLM} = \text{MZFM}$).

Consequently, later mission phases (Descent, Approach & Landing, Reserve) require relatively more lift and propulsive energy on the electric aircraft. Each segment is therefore scaled by the ratio of $\text{MTOM}$ to the reference aircraft's instantaneous average segment mass $\bar{m}_{\text{ref},i}$:

$$E_{\text{el,new},i} = \frac{E_{\text{prop,ref},i}}{\eta_{\text{el}}} \cdot \frac{\text{MTOM}}{\bar{m}_{\text{ref},i}}$$

---

## 3. En-Route Analysis: Climb, Cruise, and Descent via Breguet

A key question is how to decouple **Climb**, **Cruise**, and **Descent** when using the analytical electric range equation for cruise:

$$E_{\text{el,cruise}}(R) = \frac{\text{MTOM} \cdot g \cdot R}{\eta_{\text{el}} \cdot (L/D)}$$

### 3.1 Equivalent Breguet Range of Each Airborne Phase
Using the Breguet range equation for the Do 228 with the range factor

$$K = \frac{v_{\text{cruise}}}{g \cdot \text{TSFC}_{\text{SI}}} \cdot \left(\frac{L}{D}\right)_{\text{cruise}} = 9743.1\text{ km} \,\, (5260.9\text{ NM}),$$

we can calculate the equivalent horizontal cruise distance $R_i = K \cdot \ln(m_{\text{start},i} / m_{\text{end},i})$ represented by the fuel burned in **Climb**, **Cruise**, and **Descent**:

| Airborne Phase | Ref. Fuel | Mass Change ($m_{\text{start}} \to m_{\text{end}}$) | Equivalent Breguet Distance $R_i$ | Scaled Electric Energy ($\text{MTOM} = 7500\text{ kg}$) |
| :--- | :---: | :---: | :---: | :---: |
| **2. Climb** | $36\text{ kg}$ | $5926 \to 5890\text{ kg}$ | $59.4\text{ km}$ ($32.1\text{ NM}$) | $118.0\text{ kWh}$ |
| **3. Cruise** | $78\text{ kg}$ | $5890 \to 5812\text{ kg}$ | $129.9\text{ km}$ ($70.1\text{ NM}$) | $258.1\text{ kWh}$ |
| **4. Descent** | $9\text{ kg}$ | $5812 \to 5803\text{ kg}$ | $15.1\text{ km}$ ($8.1\text{ NM}$) | $30.0\text{ kWh}$ |
| **Sum (Climb + Cruise + Descent)** | **$123\text{ kg}$** | **$5926 \to 5803\text{ kg}$** | **$204.4\text{ km}$ ($110.35\text{ NM}$)** | **$406.1\text{ kWh}$** |
| *Analytical Cruise Formula for full $100\text{ NM}$* | – | *Constant $7500\text{ kg}$* | *$185.2\text{ km}$ ($100.0\text{ NM}$)* | *$368.0\text{ kWh}$* |

### 3.2 Two Key Insights from the Breguet Breakdown

1. **Why "Cruise ($78\text{ kg}$)" covers $70.1\text{ NM}$ ($129.9\text{ km}$):**  
   In the Do 228 reference mission, $100\text{ NM}$ ($185.2\text{ km}$) is the **total stage length** from take-off to landing. Roughly $29.9\text{ NM}$ ($55.3\text{ km}$) of horizontal distance is traveled during **Climb** (to $10\,000\text{ ft}$) and **Descent** (from $10\,000\text{ ft}$), leaving $70.1\text{ NM}$ ($129.9\text{ km}$) of level cruise flight.

2. **Net Overhead of Climb & Descent ($+10.35\,\%$ / $+38.1\text{ kWh}$):**  
   The combined Climb + Cruise + Descent fuel ($123\text{ kg}$) corresponds to an equivalent Breguet cruise distance of **$110.35\text{ NM}$ ($204.4\text{ km}$)** — i.e., **$+10.35\,\%$ ($+19.2\text{ km}$)** more than a flat $100\text{ NM}$ ($185.2\text{ km}$) cruise flight ($406.1\text{ kWh}$ vs. $368.0\text{ kWh}$).

---

## 4. Physical Explanation of the $+38.1\text{ kWh}$ ($+10.35\,\%$) Climb & Descent Overhead

Lifting $\text{MTOM} = 7500\text{ kg}$ to $h_{\text{cruise}} = 3048\text{ m}$ requires $\Delta E_{\text{el,pot}} = \frac{\text{MTOM} \cdot g \cdot h_{\text{cruise}}}{\eta_{\text{el}}} = \mathbf{73.3\text{ kWh}}$ of potential energy, plus $\Delta E_{\text{el,kin}} = \frac{\frac{1}{2}\text{MTOM}(v_{\text{cruise}}^2 - v_{\text{TO}}^2)}{\eta_{\text{el}}} = \mathbf{9.4\text{ kWh}}$ of kinetic energy (total $\approx 82.7\text{ kWh}$ on top of horizontal drag).

During **Descent**, gravity recovers roughly **$44.6\text{ kWh}$** of that potential energy as the aircraft glides down over $\sim 15\text{ NM}$, leaving a **net Climb + Descent energy overhead of $38.1\text{ kWh}$** ($10.35\,\%$ of the $100\text{ NM}$ reference cruise energy) due to:
- the kinetic energy dissipated during landing ($\approx 9.4\text{ kWh}$), and
- lower aerodynamic/propulsive efficiency during steep climb and throttled descent ($\approx 28.7\text{ kWh}$).

---

## 5. Implemented Approach in `src/fuel_fractions.py`

Based on the Breguet analysis above, our implementation in `src/fuel_fractions.py` decouples the horizontal mission distance from climb and descent as follows:
1. **Horizontal Distance (`calc_cruise_energy`):** Computed analytically via $E_{\text{el,cruise}} = \frac{\text{MTOM} \cdot g \cdot R_{\text{target}}}{\eta_{\text{el}} \cdot (L/D)}$ over the full target mission range $R_{\text{target}}$ ($368.0\text{ kWh}$ for $100\text{ NM} = 185.2\text{ km}$).
2. **Net Climb & Descent Overhead (`calc_climb_and_descent_energy`):** Computes the exact Breguet overhead factor $\frac{R_{\text{Breguet,Climb+Cruise+Descent}} - R_{\text{ref}}}{R_{\text{ref}}} = \mathbf{10.34\,\%}$ and multiplies it by the $100\text{ NM}$ reference cruise energy ($0.1034 \cdot 368.0\text{ kWh} = \mathbf{38.1\text{ kWh}}$).

| Segment | Ref. Fuel ($m_0 = 5950\text{ kg}$) | Electric Energy ($\text{MTOM} = 7500\text{ kg}$) | Battery Mass (Cell, $420\text{ Wh/kg}$) | Battery Mass (Pack, Factor $1.2$) |
| :--- | :---: | :---: | :---: | :---: |
| **1. Taxi-out & Take-off** | $24.0\text{ kg}$ | $78.3\text{ kWh}$ | $186.3\text{ kg}$ | $223.6\text{ kg}$ |
| **2. Cruise ($185.2\text{ km}$)** | $78.0\text{ kg}$ | $368.0\text{ kWh}$ | $876.2\text{ kg}$ | $1051.5\text{ kg}$ |
| **3. Climb & Descent ($+10.3\%$ Ref.)** | $45.0\text{ kg}$ | $38.1\text{ kWh}$ | $90.6\text{ kg}$ | $108.8\text{ kg}$ |
| **4. Approach, Landing & Taxi-in** | $17.0\text{ kg}$ | $56.8\text{ kWh}$ | $135.2\text{ kg}$ | $162.3\text{ kg}$ |
| **TRIP TOTAL (Phases 1–5)** | **$164.0\text{ kg}$** | **$541.1\text{ kWh}$** | **$1288.4\text{ kg}$** | **$1546.1\text{ kg}$** |
| **6. Reserve (5% + 30 min + 50 NM)** | **$186.0\text{ kg}$** | **$632.5\text{ kWh}$** | **$1506.1\text{ kg}$** | **$1807.3\text{ kg}$** |
| **MISSION TOTAL (Trip + Reserve)** | **$350.0\text{ kg}$** | **$1173.7\text{ kWh}$** | **$2794.5\text{ kg}$** | **$3353.4\text{ kg}$** |

---

## 6. Why Kerosene-Based Scaling Overestimates Reserve and Ground Energy

When scaling the Do 228 fuel masses directly with the cruise efficiency ($\eta_{\text{ref}} = 18.46\,\%$), the resulting battery mass ($2.7\text{–}3.3\text{ t}$) is artificially inflated in two flight regimes where gas turbines suffer from severe off-design inefficiencies that do **not** apply to electric propulsion:

### 6.1 Reserve Breakdown & Part-Load $\text{TSFC}$ Degradation in Loiter

Using our analytical Breguet functions (`src/breguet.py`) with the given reference parameters ($m_{\text{start,res}} = 5786\text{ kg}$, $(L/D)_{\text{cruise}} = 12.1$, $(L/D)_{\text{loiter}} = 15.7$, $\text{TSFC} = 0.46\text{ lb/(h}\cdot\text{lbf)}$), the three reserve components of the Do 228 evaluate to:
1. **5% Route Reserve:** $0.05 \cdot 164\text{ kg} = \mathbf{8.2\text{ kg}}$
2. **30 min Loiter (Breguet endurance at $(L/D)_{\text{loiter}} = 15.7$):** $\mathbf{84.1\text{ kg}}$
3. **50 NM Diversion (Breguet range at $(L/D)_{\text{cruise}} = 12.1$):** $\mathbf{54.7\text{ kg}}$
- **Analytical Reserve Total:** **$147.1\text{ kg}$** (vs. **$186.0\text{ kg}$** in the Do 228 datasheet).

**Why does the Do 228 datasheet specify $186.0\text{ kg}$ instead of $147.1\text{ kg}$ ($+26.5\,\%$)?**
- **Turboprop Part-Load $\text{TSFC}$ Penalty in Loiter:** During low-speed loiter, required shaft power drops to $\sim 30\text{–}40\,\%$ of rated power. In gas turbines, lower compressor pressure ratios and turbine inlet temperatures at part load degrade specific fuel consumption ($\text{SFC}$ / $\text{TSFC}$) by **$+20\text{ to }+35\,\%$** (*Raymer, Aircraft Design: A Conceptual Approach, Ch. 13*). By contrast, an electric motor and inverter maintain a nearly constant efficiency of $\eta_{\text{el}} \approx 85\text{–}90\,\%$ down to $20\,\%$ load.
- **Loiter Airspeed ($v_{\text{loiter}}$):** In the electric Breguet endurance formula,
  $$E_{\text{el,loiter}} = \frac{v_{\text{loiter}} \cdot t_{\text{loiter}} \cdot g \cdot \text{MTOM}}{\eta_{\text{el}} \cdot (L/D)_{\text{loiter}}},$$
  required energy scales linearly with loiter speed $v_{\text{loiter}}$. Evaluating loiter at minimum cruise speed ($170\text{ kt} \rightarrow 276.4\text{ kWh}$ at $\text{MTOM} = 8600\text{ kg}$) rather than best-endurance speed ($v_{\text{loiter}} \approx 110\text{ kt} \rightarrow 178.8\text{ kWh}$) overestimates loiter energy by **$\approx 98\text{ kWh}$** ($\approx 280\text{ kg}$ battery pack mass).

---

### 6.2 Ground Operations (Taxi-out & Taxi-in) – Literature Sources & Physical Energy Demand

In the Do 228 table, **Phase 1 (5 min Taxi-out & Take-off: $24\text{ kg}$)** and **Phase 5 (Approach, Landing & 4 min Taxi-in: $17\text{ kg}$)** consume $41\text{ kg}$ of kerosene. Scaling these $41\text{ kg}$ with the cruise efficiency ($\eta_{\text{ref}} = 18.46\,\%$) yields **$154.8\text{ kWh}$** (at $\text{MTOM} = 8600\text{ kg}$) — more than half of the entire $100\text{ NM}$ cruise energy!

In reality, a turboprop burns most of this fuel to sustain **ground idle** during 9 minutes of taxiing (where propulsive efficiency is $< 2\,\%$, not $18.46\,\%$), whereas an electric drivetrain draws zero power when stationary and only overcomes rolling resistance while taxiing.

Two standard aerospace references allow a realistic estimation of ground and take-off energy:

#### Source A: ICAO LTO Cycle (*ICAO Annex 16, Vol. II* / FAA & EASA Engine Emissions Databank)
The standard Landing and Take-Off (LTO) cycle defines engine power settings relative to maximum take-off power $P_{\text{TO}}$ ($2 \times 580\text{ kW} = 1160\text{ kW}$ for Do 228, or $\approx 1445\text{ kW}$ scaled to $\text{MTOM} = 8600\text{ kg}$):
- **Taxi / Ground Idle:** **$7\,\%$ of $P_{\text{TO}}$** ($\approx 101\text{ kW}$ shaft power)
  - **5 min Taxi-out:** $E_{\text{el,taxi-out}} = \frac{0.07 \cdot P_{\text{TO}} \cdot (5/60\text{ h})}{\eta_{\text{el}}} \approx \mathbf{10.0\text{ kWh}}$
  - **4 min Taxi-in:** $E_{\text{el,taxi-in}} = \frac{0.07 \cdot P_{\text{TO}} \cdot (4/60\text{ h})}{\eta_{\text{el}}} \approx \mathbf{8.0\text{ kWh}}$
- **Take-Off Run & Initial Climb:** **$100\,\%$ of $P_{\text{TO}}$ for $0.7\text{ min}$ ($42\text{ s}$)**
  - **Take-off:** $E_{\text{el,TO}} = \frac{1.00 \cdot P_{\text{TO}} \cdot (0.7/60\text{ h})}{\eta_{\text{el}}} \approx \mathbf{19.8\text{ kWh}}$
- **Total Phase 1 (5 min Taxi-out + Take-off) via ICAO LTO:** **$10.0 + 19.8 = \mathbf{29.8\text{ kWh}}$** (instead of **$89.7\text{ kWh}$** from kerosene scaling!).

#### Source B: Rolling Resistance Physics (*Torenbeek: Synthesis of Subsonic Airplane Design*; *Gudmundsson: General Aviation Aircraft Design, Ch. 17*)
Using a rolling friction coefficient on paved runways of $\mu_{\text{roll}} = 0.02\text{–}0.03$ and a taxi speed of $v_{\text{taxi}} = 15\text{–}20\text{ kt}$ ($\approx 8.5\text{ m/s}$) at $\text{MTOM} = 8600\text{ kg}$:

$$P_{\text{mech,taxi}} = \mu_{\text{roll}} \cdot \text{MTOM} \cdot g \cdot v_{\text{taxi}} = 0.025 \cdot 8600\text{ kg} \cdot 9.81\text{ m/s}^2 \cdot 8.5\text{ m/s} = \mathbf{17.9\text{ kW}}$$

Even assuming a low propeller efficiency at taxi speed ($\eta_{P,\text{taxi}} \approx 0.30$) and $\eta_{\text{el}} = 0.85$, the electrical taxi power is $P_{\text{el,taxi}} \approx 70\text{ kW}$, resulting in **$5.8\text{ kWh}$** for 5 min Taxi-out and **$4.7\text{ kWh}$** for 4 min Taxi-in — confirming the ICAO LTO estimate and saving **$\sim 110\text{–}120\text{ kWh}$** ($\approx 310\text{–}340\text{ kg}$ battery pack mass).

