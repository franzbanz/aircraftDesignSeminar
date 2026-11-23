import json
from pathlib import Path
import re
import numpy as np
from types import SimpleNamespace

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_json(path: Path):
    content = path.read_text(encoding="utf-8")
    pattern = re.compile(r'("(?:\\.|[^"\\])*")|(/\*[\s\S]*?\*/)|(//[^\r\n]*)')
    cleaned = pattern.sub(lambda m: m.group(1) if m.group(1) else "", content)
    cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
    return json.loads(cleaned, object_hook=hook)


def hook(d):
    return SimpleNamespace(**{k: v[0] if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})

def getTotalMass():
    with open("parameters.json") as f:
        par = json.load(f, object_hook=hook)
    ref = _load_json(_CONFIG_DIR / "reference_aircraft.json")
    with open("battery_aircraft.json") as f:
        bat = json.load(f, object_hook=hook)

    # parameters
    pax = par.payload.numberOfPassengers
    payloadMass = pax * par.payload.weightPerPassenger
    batteryPackEnergyDensity = par.battery.cellEnergyDensityMax / par.battery.cellToPackFactorMin

    # ref aircraft
    mtowRef = ref.mass.takeOffMassMax
    ldRef = ref.aerodynamics.liftToDragRatioCruise
    fuelMassRef = ref.fuel.total
    flightSpeedRef = ref.mission.cruiseSpeedTAS * 0.5144 # convert to SI
    tsfcRef = ref.propulsion.tsfcCruise * 2.833 * 10 ** (-5) # convert to SI
    energyDensityRef = ref.fuel.energyDensity * 10 ** 6 # convert to SI

    # electric aircraft
    emptyMass = bat.mass.mwe
    etaEl = bat.assumptions.electricFuelEfficiency
    ldBat = bat.aerodynamics.liftToDragRatioCruise

    # get initial battery mass estimate
    etaRef = flightSpeedRef / (tsfcRef * energyDensityRef) # fuel efficiency of ref aircraft
    totalEnergyRef = fuelMassRef * energyDensityRef * etaRef * 2.778 * 10 ** (-4) # convert to Wh
    batteryMass = totalEnergyRef / etaEl / batteryPackEnergyDensity # initial guess for battery mass

    # use average weight over course of mission of ref aircraft, batteries stay same mass
    massAvgRef = mtowRef - 0.5 * fuelMassRef
    fixedMass = emptyMass + payloadMass
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
    print(f"Payload mass:                      {payloadMass:.2f} kg")
    print(f"Battery mass:                      {batteryMass:.2f} kg")
    print(f"TOTAL MASS:                        {batteryMass + fixedMass:.2f} kg")
    print("")

    return batteryMass + fixedMass
