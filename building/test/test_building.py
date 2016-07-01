__author__ = 'Christoph Molitor'

from building.building import Building

iApartments = 1
specDemandTh = 166.0
sqm = 150.0
stepSize = 3600

testBuilding = Building(iApartments, sqm, specDemandTh, stepSize)

print("Annual thermal demand: {} kWh".format(testBuilding.getAnnualThermalDemand()))
print("Thermal demand curve: {} Wh".format(testBuilding.getThermalDemandCurve(0, 365*24*3600)))
print("Annual electrical demand: {} kWh".format(testBuilding.getAnnualElectricalDemand()))
print("Electrical demand curve: {} Wh".format(testBuilding.getElectricalDemandCurve(0, 365*24*3600)))

