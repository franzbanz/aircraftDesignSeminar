
import json
import math
from types import SimpleNamespace


def hook(d):
    return SimpleNamespace(**{k: v[0] if isinstance(v, list) and len(v) == 2 else v
                              for k, v in d.items()})

def getSkinFrictionCoefficient(reynoldsNumber, machNumber):
    cf = 0.455 / (math.log10(reynoldsNumber) ** 2.58)
    if machNumber > 0.3:
        cf /= (1 + 0.144 * machNumber ** 2) ** 0.65
    return cf

def getTotalDrag():
    with open("parameters.json") as f:
        par = json.load(f, object_hook=hook)
    with open("battery_aircraft.json") as f:
        bat = json.load(f, object_hook=hook)

    # aircraft geometry
    sRef = bat.dimensions.wingArea
    lFus = bat.dimensions.fuselageLength
    widthFus = bat.dimensions.fuselageWidth
    heightFus = bat.dimensions.fuselageHeight

    # fuselage parameters
    cfeq = bat.aerodynamics.drag.EquivalentDragParameter
    ifFus = bat.aerodynamics.drag.fuselageInterfereceParameter
    kFus = 4 # for rectengular cross-sections (see FE1)
    aTopFus = lFus * widthFus  # replace with CAD value
    aSideFus = lFus * heightFus  # replace with CAD value
    dFus = math.sqrt(widthFus * heightFus)

    # cruise conditions
    flightSpeed = par.performance.cruiseSpeedMin * 0.5144
    cruiseAltitude = bat.performance.cruiseAltitude * 0.3048
    machNumberInput = bat.performance.cruiseMachNumber
    rhoInput = par.performance.takeOffDensity
    muInput = par.performance.dynamicViscosity * 10 ** (-6)

    # atmosphere
    useISA = True
    t0 = 288.15
    p0 = 101325
    g = 9.80665
    rAir = 287.05
    lapseRate = 0.0065
    gamma = 1.4
    muRef = 1.716 * 10 ** (-5)
    tRef = 273.15
    sutherlandConstant = 110.4

    # interference components: enter CAD and FEI values
    interferenceComponents = [
        {"name": "Wing", "length": None, "wettedArea": None, "FF": None, "IF": None},
        {"name": "Horizontal tail", "length": None, "wettedArea": None, "FF": None, "IF": None},
        {"name": "Vertical tail", "length": None, "wettedArea": None, "FF": None, "IF": None},
        {"name": "Engine nacelles", "length": None, "wettedArea": None, "FF": None, "IF": None},
        {"name": "Engine pylons", "length": None, "wettedArea": None, "FF": None, "IF": None}
    ]

    cwTrim = 0.0

    # cruise atmosphere
    if useISA:
        temperature = t0 - lapseRate * cruiseAltitude
        pressure = p0 * (temperature / t0) ** (g / (rAir * lapseRate))
        rho = pressure / (rAir * temperature)
        mu = muRef * (temperature / tRef) ** 1.5 * (
            (tRef + sutherlandConstant) / (temperature + sutherlandConstant)
        )
    else:
        rho = rhoInput
        mu = muInput
        temperature = t0

    machNumber = flightSpeed / math.sqrt(gamma * rAir * temperature)
    q = 0.5 * rho * flightSpeed ** 2

    # 1. fuselage drag
    sWetFus = kFus * (aTopFus + aSideFus) / 2
    cw0FusEquivalent = cfeq * sWetFus / sRef

    reFus = rho * flightSpeed * lFus / mu
    cfFus = getSkinFrictionCoefficient(reFus, machNumber)

    finenessRatio = lFus / dFus
    ffFus = 1 + 60 / finenessRatio ** 3 + finenessRatio / 400

    cw0Fus = cfFus * ffFus * ifFus * sWetFus / sRef
    dragFus = cw0Fus * q * sRef

    # 2. interference drag
    deltaCw0Int = 0
    componentResults = []
    missingComponents = []

    for component in interferenceComponents:
        length = component["length"]
        sWet = component["wettedArea"]
        ff = component["FF"]
        interf = component["IF"]

        if any(v is None for v in [length, sWet, ff, interf]):
            missingComponents.append(component["name"])
            continue

        re = rho * flightSpeed * length / mu
        cf = getSkinFrictionCoefficient(re, machNumber)

        deltaCw0 = cf * ff * (interf - 1) * sWet / sRef
        deltaCw0Int += deltaCw0

        componentResults.append((component["name"], deltaCw0))

    dragInt = deltaCw0Int * q * sRef

    # 3. trim drag
    dragTrim = cwTrim * q * sRef

    # 4. total remaining drag
    cwRemaining = cw0Fus + deltaCw0Int + cwTrim
    dragRemaining = dragFus + dragInt + dragTrim

    # output
    print("")
    print("FUSELAGE DRAG")
    print(f"Fuselage wetted area:               {sWetFus:.2f} m^2")
    print(f"Reynolds number:                    {reFus:.3e}")
    print(f"Skin friction coefficient:          {cfFus:.6f}")
    print(f"Form factor:                        {ffFus:.4f}")
    print(f"Interference factor:                {ifFus:.2f}")
    print(f"Cw0 equivalent method:              {cw0FusEquivalent:.6f}")
    print(f"Cw0 detailed method:                {cw0Fus:.6f}")
    print(f"Fuselage drag:                      {dragFus:.2f} N")

    print("")
    print("INTERFERENCE DRAG")
    for name, value in componentResults:
        print(f"{name}:                          {value:.6f}")

    print(f"Total interference coefficient:    {deltaCw0Int:.6f}")
    print(f"Interference drag:                  {dragInt:.2f} N")

    if missingComponents:
        print(f"Missing component data:             {', '.join(missingComponents)}")

    print("")
    print("TRIM DRAG")
    print(f"Trim drag coefficient:              {cwTrim:.6f}")
    print(f"Trim drag:                          {dragTrim:.2f} N")

    print("")
    print("TOTAL REMAINING DRAG")
    print(f"Fuselage drag coefficient:          {cw0Fus:.6f}")
    print(f"Interference coefficient:           {deltaCw0Int:.6f}")
    print(f"Trim drag coefficient:              {cwTrim:.6f}")
    print(f"TOTAL DRAG COEFFICIENT:              {cwRemaining:.6f}")
    print(f"TOTAL DRAG FORCE:                    {dragRemaining:.2f} N")
    print("")

    return {
        "fuselageDragCoefficient": cw0Fus,
        "interferenceDragCoefficient": deltaCw0Int,
        "trimDragCoefficient": cwTrim,
        "totalRemainingDragCoefficient": cwRemaining,
        "totalRemainingDragForce": dragRemaining
    }
