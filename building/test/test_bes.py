__author__ = 'cmo'
import numpy as np
from building.bes import Bes
from building.environment import Environment

# sign of CHP and HP data:
#         El. NomPower    Th. NomPower    TERx
# CHP:    -               -               +
# HP:     +               -               -
# EH:     +               -               -
# """
stepSize = 3600
testEnv = Environment(50, stepSize)

testBES = Bes(stepSize=stepSize, TER1=2.3, TER2=0, RSC=3, sizingMethod=0.98, iApartments=1, sqm=146, specDemandTh=160, envrnmt=testEnv)
#testBES = Bes(stepSize=stepSize, TER1=-2.3, TER2=-1, RSC=3, sizingMethod=-2, iApartments=1, sqm=146, specDemandTh=160, envrnmt=testEnv)

dynCOP = testBES.getTER1(0, 365*24*3600)
np.save("dynCOP.npy", dynCOP)
print(dynCOP)

exit()

#print("Type: {}".format(isinstance(testBES, Bes)))
#productionAll = testBES.getThermalDemandCurve(0, 365*24*3600)[1, :]
#productionAll = productionAll[:]/3600.0
#production1 = [min(productionAll[x], -testBES.getNominalThermalPower1()) for x in range(0, len(productionAll))]

#print("All: ", sum(productionAll)/1000)
#print("All_: {}".format(testBES.getAnnualThermalDemand()))
#print("HS1: ", sum(production1)/1000)

#print "ratioEnergy: ", sum(production1)/sum(productionAll)
#print "ratioPower: ", testBES.getNominalThermalPower1()/(testBES.getNominalThermalPower1()+testBES.getNominalThermalPower2())

# print("AnnualElectricalDemand: {}".format(testBES.getAnnualElectricalDemand()))
# print("AnnualThermalDemand: {}".format(testBES.getAnnualThermalDemand()))
# print("TER of primary heater: {}".format(testBES.getTER1(0, 86400)))
# print("TER of secondary heater: {}".format(testBES.getTER2(0, 86400)))
# print("Nominal thermal power (primary): {}".format(testBES.getNominalThermalPower1()))
# print("Nominal thermal power (secondary): {}".format(testBES.getNominalThermalPower2()))
# print("Nominal electrical power (primary): {}".format(testBES.getNominalElectricalPower1()))
# print("Nominal electrical power (secondary): {}".format(testBES.getNominalElectricalPower2()))
# print("SOC: {}".format(testBES.getSOC()))
# testBES.setSOC(0.7)
# print("SOC: {}".format(testBES.getSOC()))
# print("StorageCapacity: {}".format(testBES.getStorageCapacity()))
# print("Minimum runtime1: {}".format(testBES.getMinRuntime1()))
# print("Minimum runtime2: {}".format(testBES.getMinRuntime2()))
# print("Thermal demand : {}".format(np.max(testBES.getThermalDemandCurve(0, 365*24*3600)[1,:])))
# print("Thermal power : {}".format(np.max(testBES.getThermalPower1(0, 365*24*3600)[1,:])))
# print("Thermal power : {}".format(np.min(testBES.getThermalPower1(0, 365*24*3600)[1,:])))

Tamb = np.array([253.15, 258.15, 266.15, 275.15, 280.15, 283.15, 288.15, 293.15])
# Tamb = Tamb + 273.15
A2Wx_COP = 4.7
TsourceAx = 2 + 273.15
TsinkWy = 15 + 273.15
print(testBES.calcHPdynCOP(Tamb,A2Wx_COP))