__author__ = 'christoph'

from building.bes import Bes
from building.environment import Environment
import numpy as np
import matplotlib.pyplot as plt

stepSize = 1800

testEnv = Environment(50, stepSize)
testBes = Bes(stepSize=stepSize, TER1=-2.32, TER2=0, RSC=3, sizingMethod=-2, iApartments=1, sqm=146, specDemandTh=160, envrnmt=testEnv)
#testBes = Bes(stepSize=stepSize, TER1=2.3, TER2=0, RSC=3, sizingMethod=-1, iApartments=1, sqm=146, specDemandTh=160, envrnmt=testEnv)
#testBes = Bes(stepSize=stepSize, TER1=0, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=146, specDemandTh=160, envrnmt=testEnv)

print(testBes.getNominalThermalPower1())
print(testBes.getNominalThermalPower2())
print(testBes.getNominalElectricalPower1())
print("TER1dyn", testBes.TER1dyn)
print("TER1dyn", testBes.getTER1(0, 365*24*3600)[1, :])
print("ThermalPower1", testBes.getThermalPower1(0, 365*24*3600)[1, :])

