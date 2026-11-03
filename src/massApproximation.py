import json
import numpy as np
from types import SimpleNamespace

def isa_density(h, rho_0):
   return rho_0 * (1 - 2.25577e-5 * h) ** 4.2559

def hook(d):
    return SimpleNamespace(**{k: v[0] if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})

def approximateMass():
    with open("parameters.json") as f:
        par = json.load(f, object_hook=hook)

    with open("reference_aircraft.json") as f:
        ref = json.load(f, object_hook=hook)

def getRequiredTotalDistance():
    cruiseDistance = 100.0 # in NM
    reserveDistance = 5.0 # as in requirements
    diversionDistance = 50.0 # as in requirements
    loiterDistance = 85.0 # at cruise speed for 30 mins (very conservative estimate)
    taxiAndTakeOffDistance = 30.77 # taken from reference aircraft, which has ~30% of cruise fuel for this section of the mission
    climbDistance = 46.15 # taken from reference arcraft, which has ~45% of cruise fuel for this section of the mission, very conservative
    descentAndLandingDistance = 21.79 # taken from reference arcraft, which has ~20% of cruise fuel for this section of the mission

    return cruiseDistance + reserveDistance + diversionDistance + loiterDistance + taxiAndTakeOffDistance + climbDistance + descentAndLandingDistance
    
# at upper limit for cell density, you get 350Wh/kg
# to get preliminary estimate for energy efficiency, calibration method is used

def getBatteryPackMass():
    flightSpeedRef = 102.9 # cruise speed in m/s
    tsfcRef = 2.833*10**(-5) * 0.46 # conversion to kg/(s*N)
    energyDensityRef = 42.8*10**6 # joule/kg
    totalFuelMassRef = 339.0 # kg
    batteryPackEnergyDensity = 350.0 # from requirements
    etaEl =  0.75 # assumption

    etaRef = flightSpeedRef / (tsfcRef * energyDensityRef) # fuel efficiency of ref aircraft
    totalEnergyRef = totalFuelMassRef*energyDensityRef*etaRef*2.778*10**(-4) # convert to Wh
    
    return totalEnergyRef / etaEl / batteryPackEnergyDensity
print(getBatteryPackMass())
