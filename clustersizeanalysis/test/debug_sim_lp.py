__author__ = 'cmo'

import numpy as np
import xlwt
from time import *
import os

from building.environment import Environment
from clustersizeanalysis.cluster_cplex import Cluster
from building.bes import Bes

# List of investigated horizons
listHorizon = list()
#listHorizon.append(1.0)
#listHorizon.append(1.25)
#listHorizon.append(1.5)
#listHorizon.append(1.75)
listHorizon.append(2.0)

listRSC = list()
#listRSC.append(1.0)
#listRSC.append(2.0)
#listRSC.append(3.0)
#listRSC.append(4.0)
listRSC.append(5.0)

for hz in range(0, len(listHorizon)):
    for r in range(0, len(listRSC)):
        stepSize = 3600  # todo: not tested with other stepsize
        startTime = 2678400  # 1814400
        endTime = startTime + 86400 * 2
        horizon = int(86400 * listHorizon[hz])  # horizon for scheduling
        interval = 86400  # interval for scheduling

        nDays = (endTime-startTime)/86400

        # General building data
        RSC = listRSC[r]  # Relative Storage Capacity (RSC)
        iApartments = 1
        specDemandTh = 166.0
        sqm = 150

        #Heating system parameters; TER (Thermal-electric ratio)
        TER_HP = -3.0
        TER_CHP = 2.3
        sizingMethod = "Bivalent"

        # Sizing of electro-thermal heating system:
        # Sizing of CHP due to Maximum Rectangle Method (MRM). Sources:
        #   [1] D. Haeseldonckx, L. Peeters, L. Helsen, und W. D'haeseleer,
        #       "The impact of thermal storage on the operational behaviour of residential CHP facilities and the overall CO2 emissions",
        #       Renewable and Sustainable Energy Reviews, Bd. 11, Nr. 6, S. 1227-1243, Aug. 2007.
        sizingMethod_CHP = -1  # MRM


        # Sizing of HP to cover 98% of the annual thermal energy demand. Sources:
        #   [1] "Bivalente Waermepumpen-Systeme." Bundesindustrieverband Deutschland Haus-, Energie- und Umwelttechnik e.V., Mar-2014.
        #   [2] "Planungshandbuch Waermepumpen." Viessmann Werke, 2011.
        sizingMethod_HP = 0.98

        maxNBES = 10

        environment1 = Environment(0, stepSize)

        # create folder for simulation results
        lt = localtime()
        scenario_name = "{}{:02d}{:02d}-{:02d}{:02d}_SizingHS-{}_RES-{}_RSC-{}_Hrzn-{}".format(lt[0], lt[1], lt[2], lt[3], lt[4], sizingMethod, environment1.getShareRES(), RSC, float(horizon)/interval)
        dirResults = "_results_LP/{}".format(scenario_name)
        if not os.path.exists(dirResults):
            os.makedirs(dirResults)

        dirScript = os.path.dirname(__file__)
        dirAbsResults = dirScript + "/" + dirResults

        cluster1 = Cluster(dirAbsResults, environment1, horizon, stepSize, interval)

        # Add CHP BES to the cluster
        sCHP = 6
        for c in range(0, sCHP):
            besCHP = Bes(stepSize=stepSize, TER1=TER_CHP, TER2=0.0, RSC=RSC, sizingMethod=sizingMethod_CHP, iApartments=iApartments, sqm=sqm, specDemandTh=specDemandTh)
            cluster1.addMember(besCHP)

        # Add HP BES to the cluster
        sHP = 4
        for h in range(0, sHP):
            besHP = Bes(stepSize=stepSize, TER1=TER_HP, TER2=-1.0, RSC=RSC, sizingMethod=sizingMethod_HP, iApartments=iApartments, sqm=sqm, specDemandTh=specDemandTh)
            # print("pth1:", bes1.getNominalThermalPower())
            cluster1.addMember(besHP)

        _shareSurchargeLoad = (maxNBES - float(sCHP + sHP))/(sCHP + sHP) * 100
        # print("Term: {}".format(_shareSurchargeLoad))
        cluster1.setSurchargeLoad(_shareSurchargeLoad)  # has to be called after all bes are added

        cluster1.setTypeOptimization("LP")

        for time in range(startTime, endTime, interval):
            (ratioMaxEnergy, ratioMaxPower, relGap, avgRemainder, avgFluctuations, HSBackupEnergy) = cluster1.calcSchedules(time)

            print("ratioMaxFluc: {}".format(ratioMaxEnergy))
            print("ratioMaxPower: {}".format(ratioMaxPower))
            print("Gap: {}".format(relGap))  # gap >= 0: real gap value; gap == -1: optimal solution found during presolve; gap == -2: Relaxations
            print("HSBackupEnergy: {}".format(HSBackupEnergy))