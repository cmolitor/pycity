__author__ = 'Annika Wierichs'


from building.pvsystem import PVSystem
from building.environment import Environment
from city.cluster import Cluster
from buildingControl.smartbes import SmartBes
import os


horizon = 86400
stepSize = 3600
startingH = 120

fromTime = startingH * horizon
toTime = fromTime + horizon - stepSize

env = Environment(50, stepSize)

# CHP
# bes = SmartBes(stepSize, TER1= 2.3, TER2= 0, RSC=3.0, sizingMethod=-1, iApartments=1, sqm=150, specDemandTh=166, env=env , objFcn=2, solPoolAbsGap=0, solPoolRelGap=0.0, solPoolIntensity=4)
# HP
bes = SmartBes(stepSize=stepSize, TER1=-2.3, TER2=-1, RSC=3.0, sizingMethod=-2, iApartments=3, sqm=150, specDemandTh=166, env=env , objFcn=2, solPoolAbsGap=0, solPoolRelGap=0.0, solPoolIntensity=4)

bes.addPVSystem(PVSystem(env, 8000))

bes.calcOptimalSchedule(fromTime, toTime)
