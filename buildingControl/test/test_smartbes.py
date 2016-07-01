__author__ = 'Annika Wierichs'


from city.database import DataBase
from building.pvsystem import PVSystem
from building.environment import Environment
from city.cluster import Cluster
from buildingControl.smartbes import SmartBes
import os


horizon = 86400
stepSize = 1800
startingH = 1

env = Environment(50, stepSize)
#listBes = DataBase.createRandomFlexSmartBuildings(5, stepSize, objFcn=1, solPoolAbsGap=2)

listBes = list()
listBes.append(SmartBes(stepSize,-2.3, -1.0, 3.0, -2, 1, 150, 166, env, objFcn=1, solPoolAbsGap=1, solPoolRelGap=0.2, solPoolIntensity=4))

fromTime = startingH * horizon
toTime = fromTime + horizon - stepSize

# create folder for simulation results etc.
dirResults = "testingOnly"
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

listBes[0].calcSchedulePool(fromTime, toTime)

cl = Cluster(dirAbsResults, env, horizon, stepSize, horizon)

# add pvs & calc schedules:
for bes in listBes:
    cl.addMember(bes)

# for bes in listBes:
#     bes.addPVSystem(PVSystem(env, 30, stepSize))


#for bes in listBes:
#    print bes.calcResultOfOptimizedCriterion(fromTime, toTime)

