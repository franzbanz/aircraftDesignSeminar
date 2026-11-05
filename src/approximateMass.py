import json
import numpy as np
from types import SimpleNamespace
from data import load_constraints, load_reference_aircraft

def hook(d):
    return SimpleNamespace(**{k: v[0] if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})

def getTotalMass():
    constraints = load_constraints()
    ref = load_reference_aircraft()
    with open("battery_aircraft.json") as f:
        bat = json.load(f, object_hook=hook)

    # constraints
    pax = constraints.payload.numberOfPassengers
    personalMass = pax * constraints.payload.weightPerPassenger
    payloadMass = pax * constraints.payload.maxStructuralPayloadPerPassenger
    batteryPackEnergyDensity = constraints.battery.cellEnergyDensityMax / constraints.battery.cellToPackFactorMin

    # ref aircraft
    mtowRef = ref.mass.takeOffMassMax
    ldRef = ref.aerodynamics.liftToDragRatioCruise
    fuelMassRef = ref.fuel.total
    flightSpeedRef = ref.performance.cruiseSpeedTAS * 0.5144 # convert to SI
    tsfcRef = ref.propulsion.tsfcCruise * 2.833 * 10 ** (-5) # convert to SI
    energyDensityRef = ref.fuel.energyDensity * 10 ** 6 # convert to SI

    # electric aircraft
    emptyMass = getattr(getattr(bat, chr(109)+chr(97)+chr(115)+chr(115), None), chr(109)+chr(119)+chr(101), ref.mass.mwe)
    etaEl = bat.assumptions.electricFuelEfficiency
    ldBat = bat.aerodynamics.liftToDragRatioCruise

    # get initial battery mass estimate
    etaRef = flightSpeedRef / (tsfcRef * energyDensityRef) # fuel efficiency of ref aircraft
    totalEnergyRef = fuelMassRef * energyDensityRef * etaRef * 2.778 * 10 ** (-4) # convert to Wh
    batteryMass = totalEnergyRef / etaEl / batteryPackEnergyDensity # initial guess for battery mass

    # use average weight over course of mission of ref aircraft, batteries stay same mass
    massAvgRef = mtowRef - 0.5 * fuelMassRef
    fixedMass = emptyMass + payloadMass + personalMass
    # scaling factor and iteration
    for i in range(100):
        massTotal = fixedMass + batteryMass
        scale = (massTotal / massAvgRef) * (ldRef / ldBat)
        batteryMassNew = totalEnergyRef * scale / etaEl / batteryPackEnergyDensity
        if abs(batteryMassNew - batteryMass) < 0.1:
            break
        batteryMass = batteryMassNew

    print("")    
    print(f"Lift to drag ratio:                {ldBat:.2f}")
    print(f"Scaling factor:                    {scale:.2f}")
    print(f"Battery energy pack density:       {batteryPackEnergyDensity:.2f} Wh/kg")
    print(f"Electric propulsion efficiency:    {100 * etaEl:.2f} %")
    print(f"Empty mass:                        {emptyMass:.2f} kg")
    print(f"Payload mass:                      {payloadMass + personalMass:.2f} kg")
    print(f"Battery mass:                      {batteryMass:.2f} kg")
    print(f"TOTAL MASS:                        {batteryMass + fixedMass:.2f} kg")
    print("")

    return batteryMass + fixedMass

if __name__ == "__main__":
    getTotalMass()