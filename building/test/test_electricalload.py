__author__ = 'Christoph Molitor'

from building.electricalload import ElectricalLoad

test = ElectricalLoad(1000, 900)

print("ElectricalDemandCurve: {}".format(test.getElectricalDemandCurve(0, 365*24*3600)))
print("ElectricalDemand: {}".format(test.getAnnualElectricalDemand()))