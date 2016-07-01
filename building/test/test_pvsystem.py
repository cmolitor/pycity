__author__ = 'Annika Wierichs'

# quickly check if smartbes is working properly

from city.database import DataBase
from building.pvsystem import PVSystem
from building.environment import Environment
from city.cluster import Cluster
from time import *
import os

horizon = 86400
stepSize = 3600
startingH = 201

env = Environment(50, stepSize)

nBES = 1
listBes = DataBase.createRandomFlexSmartBuildings(nBES, stepSize, pseudorandom = True, randomSeed = 1, objFcn=1, solPoolAbsGap=2, solPoolRelGap=0.1)

fromTime = startingH * horizon
toTime = fromTime + horizon - stepSize

# create folder for simulation results etc.
dirResults = "testingOnly"
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

cl = Cluster(dirAbsResults, env, horizon, stepSize, horizon)

# add pvs & calc schedules:
for bes in listBes:
    cl.addMember(bes)

for bes in listBes:
    print("RES: ")
    print(cl.getRenewableGenerationCurve(fromTime, toTime)[1, :])
    bes.addPVSystem(PVSystem(env, stepSize, 30))
    print(max(bes.getOnSitePVGenerationCurve(fromTime, toTime)[1,:])/3600000)
    bes.setObjFcn(2)


    bes.calcSchedulePool(fromTime, toTime)
