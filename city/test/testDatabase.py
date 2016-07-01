__author__ = 'cmo'

import numpy as np
from city.database import DataBase
from building.environment import Environment

# Algorithm configuration
stepSize = 900
horizon = 86400 * 1  # 86400 * 2
interval = 86400
startI = 0  # start interval
stopI = 31  # stop interval

randomSeed = 1
algorithm = "IDA"  # IDA, PIDA, SIDA

# Cluster configuration
shareHS_arr = np.array((20,20)) # HP, CHP in %
shareRES = 50  # 20, 50
sizeCluster = 50  # 40, 60, 80, 100
gblObj = "RPV"  # minimize Peak to Valley

# BES configuration
RSC = 3  # 3, 5, 7
switchingAbsGap = 2
feedOrDmndRelGap = 0.2

env = Environment(shareRES, stepSize)

listBESs = DataBase.createRandomBESs(sizeCluster, shareHS_arr, env, stepSize, RSC, solPoolAbsGap=switchingAbsGap,
                                     solPoolRelGap=feedOrDmndRelGap,
                                     solPoolIntensity=4,
                                     pseudorandom=True,
                                     randomSeed=randomSeed,
                                     sqm=0, specDemandTh=166, iApartments=1)
# add BESs to cluster

_scenario       = np.zeros((sizeCluster, 6))

for b in range(len(listBESs)):
    _scenario[b, 0] = listBESs[b].getTER1()                             # TER 1
    _scenario[b, 1] = listBESs[b].getTER2()                             # TER 2
    _scenario[b, 2] = listBESs[b].iApartments                           # no of apartments
    _scenario[b, 3] = listBESs[b].listApartments[0].sqm                 # sqm per apartment
    _scenario[b, 4] = listBESs[b].listApartments[0].specDemandTh        # specific thermal demand [kWh/(sqm a)]
    _scenario[b, 5] = listBESs[b].getAnnualPVGeneration()               # annual generation from pv system [kWh], zero if no pv system installed
# save the scenario
np.save("scenario.npy", _scenario)
np.savetxt("scenario.txt", _scenario, header="TER 1, TER 2, no of apartments, sqm per apartment, specific thermal demand [kWh/(sqm a)], annual local pv generation [kWh]")
