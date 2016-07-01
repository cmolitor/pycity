__author__ = 'cmo'


from time import *
import os
import sys
import numpy as np

from building.environment import Environment
from city.database import DataBase
from cityControl.centralizedcluster import CentralizedCluster

# todo: set cplex parameters in central cluster
# todo: choose exact scenario configurations (which combinations?)



# ======================================================================================================================
# Scenario configuration
# ======================================================================================================================

# Algorithm configuration
stepSize = 900
horizon = 86400 * 2  # 86400 * 2
interval = 86400
startI = 0  # start interval # 0 # 31+29+31  # 31+29+31+30+31+30
stopI = 2  # stop interval # 31 # 31+29+31+30 # 31+29+31+30+31+30+31

globalCoordination = True      # False
localOptimization = False    # False
randomSeed = 2
specialTest = False

# Cluster configuration
shareHS_arr = np.array((20, 20))  # HP, CHP in %
shareRES = 50  # 20, 50
sizeCluster = 50  # 40, 60, 80, 100
gblObj = "RPV"  # minimize Peak to Valley

# BES configuration
RSC = 3  # 3, 5, 7
switchingAbsGap = 2 * 2
feedOrDmndRelGap = 0.2


# ======================================================================================================================
# Setup variables & directories
# ======================================================================================================================

stepsPerDay = interval / stepSize
noDays = stopI - startI

# create scenario name string
scenarioName = "startI-" + str(startI) + "_stopI-" + str(stopI) + "_stepSize-" + str(stepSize) + "_shareRES-" + str(shareRES) + "_clusterSize-" + str(sizeCluster) + "_RSC-" + str(RSC) + "_"
if globalCoordination:
    scenarioName += "G"
if localOptimization:
    scenarioName += "L"

scenarioName += "_Seed-" + str(randomSeed)

# create folder for simulation results
lt = localtime()
dirResults = "results/{}-{:02d}-{:02d}_{:02d}-{:02d}_{}".format(lt[0], lt[1], lt[2], lt[3], lt[4], scenarioName)
if not os.path.exists(dirResults):
    os.makedirs(dirResults)
dirScript = os.path.dirname(__file__)
dirAbsResults = dirScript + "/" + dirResults

# create Environment
env = Environment(shareRES, stepSize)
# create cluster
cluster = CentralizedCluster(dirAbsResults, env, horizon, stepSize, interval)
# create BESs


if specialTest == True:
    _sizeCluster = sizeCluster
    sizeCluster = 50

listBESs = DataBase.createRandomBESs(sizeCluster, shareHS_arr, env, stepSize, RSC,
                                     solPoolAbsGap=switchingAbsGap,
                                     solPoolRelGap=feedOrDmndRelGap,
                                     solPoolIntensity=4,
                                     pseudorandom=True,
                                     randomSeed=randomSeed,
                                     sqm=0, specDemandTh=166, iApartments=1,
                                     lclPV=False)

if specialTest == True:
    listBESs2 = list()
    for l in range(0, _sizeCluster/sizeCluster):
        listBESs2 += listBESs

    listBESs = listBESs2
    sizeCluster = _sizeCluster


# add BESs to cluster
for bes in listBESs:
    cluster.addMember(bes)

# ======================================================================================================================
# create containers & files for logging
# ======================================================================================================================

# create empty numpy arrays
_scenario       = np.zeros((sizeCluster, 6))                # for each BES: TER1, TER2, iAp, sqmPerAp, specDmnd, annualPVGen
_performances   = np.zeros((noDays, 2))                     # performances for each day (RPV)
_fluctuations   = np.zeros((2, noDays * stepsPerDay))       # fluctuations for all days
_remainders     = np.zeros((2, noDays * stepsPerDay))       # remainder after coordination/optimization for all days
_fluctuations[0, :] = range(stepsPerDay*stepSize*startI, stepsPerDay*stepSize*(stopI), stepSize)     # time in sec
_remainders[0, :]   = range(stepsPerDay*stepSize*startI, stepsPerDay*stepSize*(stopI), stepSize)     # time in sec

for b in range(len(listBESs)):
    _scenario[b, 0] = listBESs[b].getTER1()                             # TER 1
    _scenario[b, 1] = listBESs[b].getTER2()                             # TER 2
    _scenario[b, 2] = listBESs[b].iApartments                           # no of apartments
    _scenario[b, 3] = listBESs[b].listApartments[0].sqm                 # sqm per apartment
    _scenario[b, 4] = listBESs[b].listApartments[0].specDemandTh        # specific thermal demand [kWh/(sqm a)]
    _scenario[b, 5] = listBESs[b].getAnnualPVGeneration()               # annual generation from pv system [kWh], zero if no pv system installed
# save the scenario
np.save("{}/scenario.npy".format(dirResults), _scenario)
np.savetxt("{}/scenario.txt".format(dirResults), _scenario, header="TER 1, TER 2, no of apartments, sqm per apartment, specific thermal demand [kWh/(sqm a)], annual local pv generation [kWh]")

# general log file
logfile_name = dirResults + "/generalLog.txt"
logfile = open(logfile_name, mode="a")
logfile.write("SIMULATION:\nstep size: {}\nglobal coordination: {}\nlocal optimization: {}\nrandom seed: {}\nshare HS each: {}\nshare RES: {}\ncluster size: {}\nRSC: {}\nHorizon: {}\nInterval: {}\n".format(stepSize, globalCoordination, localOptimization, randomSeed, shareHS_arr[0], shareRES, sizeCluster, RSC, horizon, interval))
logfile.close()

# ======================================================================================================================
# run full year simulation
# ======================================================================================================================


for h in range(startI, stopI):

    fromTime = h * interval
    toTimeH = fromTime + horizon - stepSize
    toTimeI = fromTime + interval - stepSize

    print("=========================================")
    print("from time: ", fromTime, "to time: ", toTimeH)
    print("=========================================")

    # run optimization
    # ==================================================================================================================

    _performances[h-startI, 1] = cluster.calcSchedules(fromTime, globalCoordination=globalCoordination, localOptimization=localOptimization)
    _performances[h-startI, 0] = h

    # Logging
    # ==================================================================================================================

    # save fluctuations & remainder
    _fluctuations[1, (h-startI)*stepsPerDay : (h-startI+1)*stepsPerDay]   = cluster.getFluctuationsCurve(fromTime, toTimeI)
    _remainders[1, (h-startI)*stepsPerDay : (h-startI+1)*stepsPerDay]     = cluster.getRemainder()

    # replace existing arrays for every new day
    np.save("{}/performances.npy".format(dirResults), _performances)
    np.save("{}/fluctuations.npy".format(dirResults), _fluctuations)
    np.save("{}/remainders.npy".format(dirResults), _remainders)
    # also log in txt files
    np.savetxt("{}/performances.txt".format(dirResults), _performances)
    np.savetxt("{}/fluctuations.txt".format(dirResults), _fluctuations)
    np.savetxt("{}/remainders.txt".format(dirResults), _remainders)

    # general log file
    logfile = open(logfile_name, mode='a')
    logfile.write("\nDAY: {}\n".format(h))
    logfile.write("\tPerformance: {}\n".format(_performances[h-startI,:]))
    # todo: anything else? schedules? objfcn? local & global optima? ...
    logfile.close()

os.rename(dirResults, dirResults + "_FINAL")