import json
import numpy as np
import matplotlib.pyplot as plt

K_TO = 2.45            # (F.8) m^3/kg, because of 2 engines
V_S_MAX = 113 / 3.6    # (G.1) m/s, directly from CS-23

L_A = 183.0            # (K.5) m, obstacle clearance distance
A = 1.0        # 

GAMMA_MIN_OEI = 0.015  # (CS 23.67 b) %, minimum gradient of climb, one engine inoperative
M_CLIMB_RATIO = 1.0    # m_climb / m0

OSWALD_E = 0.8         # assumption, could be false
F_OVER_FCR = 4.0       # (I.1)
M_CR_RATIO = 1.0       # no mass loss in flight
MLW_RATIO = 1.0        # no mass loss in flight

g = 9.81

with open("reference_aircraft.json", "r") as file1:
    ref = json.load(file1)
with open("parameters.json", "r") as file2:
    par = json.load(file2)

m0_ref = ref["mass"]["takeOffMassMax"][0]
S_ref = ref["dimensions"]["wingArea"][0]
b = ref["dimensions"]["wingspan"][0]
n_eng = int(ref["propulsion"]["numberOfEngines"][0])
E_cruise = ref["aerodynamics"]["liftToDragRatioCruise"][0]
H_CRUISE = ref["performance"]["cruiseAltitude"][0]
CA_max_TO = ref["assumptions"]["maxTakeOffLiftCoefficient"][0]
CA_max_L = ref["aerodynamics"]["maxLandingLiftCoefficient"][0]
S_TOFL = par["performance"]["takeOffFieldLengthMax"][0]
L_LDG = par["performance"]["landingFieldLengthMax"][0]
RHO0 = par["performance"]["takeOffDensity"][0]
FIELD_ELEVATION = par["performance"]["takeOffAltitude"][0]
V_CRUISE = par["performance"]["cruiseSpeedMin"][0] * 0.5144

def isa_density(h):
   return RHO0 * (1 - 2.25577e-5 * h) ** 4.2559

Lambda = b**2 / S_ref                                # (A.1) aspect ratio
CW0 = np.pi * Lambda * OSWALD_E / (4 * E_cruise**2)  # from E_max = 0.5*sqrt(pi*Lambda*e/CW0)
eps = 1 / E_cruise                                   # (A.2) eps = CW/CA
sigma = isa_density(FIELD_ELEVATION) / RHO0
rho_cr = isa_density(H_CRUISE)
q_cr = 0.5 * rho_cr * V_CRUISE**2                    # dynamic pressure
x = np.linspace(50, 450, 800)                        # m0/S in kg/m^2, needed for plotting everything

# (G.2) stall speed vertical line
x_stall = CA_max_L * RHO0 / (2 * g) * V_S_MAX**2

# (F.8) takeoff field length line through origin
y_to = K_TO / (CA_max_TO * sigma * S_TOFL) * x

# (H.2) OEI climb gradient horizontal line
y_climb = M_CLIMB_RATIO * n_eng / (n_eng - 1) * (GAMMA_MIN_OEI + eps) * np.ones_like(x)

# (I.1) cruise curve
y_cruise = F_OVER_FCR * (CW0 * q_cr / (x * g) + x * g / (q_cr * np.pi * Lambda * OSWALD_E) * M_CR_RATIO**2)

# (K.6) landing distance vertical line
x_landing = MLW_RATIO * (L_LDG - L_A) * sigma * CA_max_L / (0.51 * A * g)

# plot
fig, ax = plt.subplots(figsize=(9, 6))
ax.axvline(x_stall, color="red", ls="--", label="Überziehgeschwindigkeit (G.2)")
ax.plot(x, y_to, label="Startstrecke (F.8)")
ax.plot(x, y_climb, label="Steiggradient OEI (H.2)")
ax.plot(x, y_cruise, label="Reiseflug (I.1)")
ax.axvline(x_landing, color="purple", ls="--", label="Landestrecke (K.6)")

ax.set_xlim(x[0], x[-1])
ax.set_ylim(0, 0.6)
ax.set_xlabel(r"$m_0/S$ in kg m$^{-2}$")
ax.set_ylabel(r"$F/(m_0\cdot g)$ (–)")
ax.set_title("Entwurfsdiagramm")
ax.grid(alpha=0.3)
ax.legend(fontsize=8, loc="upper left")
plt.tight_layout()
plt.show()
