import json
import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace

def hook(d):
    return SimpleNamespace(**{k: v[0] if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})

def isa_density(h):
   return rho_0 * (1 - 2.25577e-5 * h) ** 4.2559

def generate_sizing_diagram():
    with open("parameters.json") as f:
        par = json.load(f, object_hook=hook)

    with open("reference_aircraft.json") as f:
        ref = json.load(f, object_hook=hook)

    k_TO = ref.assumptions.kTakeOff
    v_S_Max = ref.assumptions.maxStallSpeed
    l_A = ref.assumptions.obstacleClearance
    A = ref.assumptions.reverseThrustFactorA
    gamma_Min_Oei = ref.assumptions.minClimbGradient
    m_Climb_Ratio = ref.assumptions.massClimbRatio
    oswald_E = ref.assumptions.oswaldFactor
    f_Over_Fcr = ref.assumptions.maxThrustOverCruiseThrustRatio
    m_Cr_Ratio = ref.assumptions.maxMassOverCruiseMassRatio
    mlw_Ratio = ref.assumptions.maxMassOverLandingMassRatio
    g = par.mission.gravity
    m0_ref = ref.mass.takeOffMassMax
    S_ref = ref.dimensions.wingArea
    b = ref.dimensions.wingspan
    n_eng = int(ref.propulsion.numberOfEngines)
    e_cruise = ref.aerodynamics.liftToDragRatioCruise
    h_Cruise = ref.performance.cruiseAltitude
    ca_Max_To = ref.assumptions.maxTakeOffLiftCoefficient
    ca_Max_L = ref.aerodynamics.maxLandingLiftCoefficient
    s_Tofl = par.performance.takeOffFieldLengthMax
    l_Ldg = par.performance.landingFieldLengthMax
    rho_0 = par.performance.takeOffDensity
    field_Elevation = par.performance.takeOffAltitude
    v_Cruise = par.performance.cruiseSpeedMin * 0.5144

    Lambda = b**2 / S_ref                                # (A.1) aspect ratio
    cW0 = np.pi * Lambda * oswald_E / (4 * e_cruise**2)  # from E_max = 0.5*sqrt(pi*Lambda*e/cW0)
    eps = 1 / e_cruise                                   # (A.2) eps = CW/CA
    sigma = isa_density(field_Elevation) / rho_0         # 1, because start at standard density
    rho_cr = isa_density(h_Cruise)                       # density at cruise height
    q_cr = 0.5 * rho_cr * V_CRUISE**2                    # dynamic pressure
    x = np.linspace(50, 450, 800)                        # m0/S in kg/m^2, needed for plotting everything

    # (G.2) stall speed vertical line
    x_stall = ca_Max_L * rho_0 / (2 * g) * v_S_Max**2

    # (F.8) takeoff field length line through origin
    y_to = k_TO / (ca_Max_To * sigma * s_Tofl) * x

    # (H.2) OEI climb gradient horizontal line
    y_climb = m_Climb_Ratio * n_eng / (n_eng - 1) * (gamma_Min_Oei + eps) * np.ones_like(x)

    # (I.1) cruise curve
    y_cruise = f_Over_Fcr * (cW0 * q_cr / (x * g) + x * g / (q_cr * np.pi * Lambda * oswald_E) * m_Cr_Ratio**2)

    # (K.6) landing distance vertical line
    x_landing = mlw_Ratio * (l_Ldg - l_A) * sigma * ca_Max_L / (0.51 * A * g)

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

# def get_design_point():
#     TODO
#     return
