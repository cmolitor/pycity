__author__ = 'Christoph Molitor'

from building.apartment import Apartment

timeSlot = 3600

testApartment = Apartment(1, 146, 166, timeSlot)
print("Annual thermal demand: {} kWh".format(testApartment.getAnnualThermalDemand()))
print("Thermal demand curve: {} Ws".format(testApartment.getThermalDemandCurve(0, 365*24*3600)))
print("Annual electrical demand: {} kWh".format(testApartment.getAnnualElectricalDemand()))
print("Electrical demand curve: {} Ws".format(testApartment.getElectricalDemandCurve(0, 365*24*3600)))
