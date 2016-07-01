# coding=utf-8
__author__ = 'Christoph Molitor'

# todo: timestep:30min (adjust data), maybe modlvl = 2, surchargeload as discrete houses
import numpy as np
import xlwt
from time import *
import os
import multiprocessing as mp

from building.environment import Environment
from clustersizeanalysis.cluster_cplex import Cluster
from building.bes import Bes

# List of investigated horizons
listHorizon = list()
listHorizon.append(1.0)
listHorizon.append(1.25)
listHorizon.append(1.5)
listHorizon.append(1.75)
listHorizon.append(2.0)

listRSC = list()
listRSC.append(1.0)
listRSC.append(2.0)
listRSC.append(3.0)
listRSC.append(4.0)
listRSC.append(5.0)


def calcScenario(factorHorizon, _RSC):
    # for r in range(0, len(listRSC)):
    stepSize = 900
    startTime = 86400 * 0  # 1814400
    endTime = 86400 * 365
    horizon = int(86400 * factorHorizon)  # horizon for scheduling
    interval = 86400  # interval for scheduling

    nDays = (endTime-startTime)/86400

    # General building data
    RSC = _RSC  # listRSC[r]  # Relative Storage Capacity (RSC)
    iApartments = 1
    specDemandTh = 166.0
    sqm = 150

    #Heating system parameters; TER (Thermal-electric ratio)
    TER_HP = -2.32  # Values for Dimplex LA 12TU (http://www.dimplex.de/pdf/de/produktattribute/produkt_1725609_extern_egd.pdf)
    TER_CHP = 2.3
    sizingMethod = "Bivalent"

    # Sizing of electro-thermal heating system:
    # Sizing of CHP due to Maximum Rectangle Method (MRM). Sources:
    #   [1] D. Haeseldonckx, L. Peeters, L. Helsen, und W. D’haeseleer,
    #       „The impact of thermal storage on the operational behaviour of residential CHP facilities and the overall CO2 emissions“,
    #       Renewable and Sustainable Energy Reviews, Bd. 11, Nr. 6, S. 1227–1243, Aug. 2007.
    sizingMethod_CHP = -1  # MRM


    # Sizing of HP to cover 98% of the annual thermal energy demand. Sources:
    #   [1] "Bivalente Wärmepumpen-Systeme." Bundesindustrieverband Deutschland Haus-, Energie- und Umwelttechnik e.V., Mar-2014.
    #   [2]“Planungshandbuch Wärmepumpen.” Viessmann Werke, 2011.
    sizingMethod_HP = -2

    maxNBES = 10

    environment1 = Environment(100, stepSize)

    # create folder for simulation results
    lt = localtime()
    scenario_name = "{}{:02d}{:02d}-{:02d}{:02d}_{}_RES-{}_RSC-{}_Hrzn-{}_stepsize-{}".format(lt[0],
                                                                                              lt[1],
                                                                                              lt[2],
                                                                                              lt[3],
                                                                                              lt[4],
                                                                                              sizingMethod,
                                                                                              environment1.getShareRES(),
                                                                                              RSC,
                                                                                              float(horizon)/interval,
                                                                                              stepSize)
    dirResults = "_results_LP/{}".format(scenario_name)
    if not os.path.exists(dirResults):
        os.makedirs(dirResults)

    dirScript = os.path.dirname(__file__)
    dirAbsResults = dirScript + "/" + dirResults

    # construct multi-dimensional array for storing the simulation results
    result = -np.ones((maxNBES + 1, maxNBES + 1, (endTime-startTime)/interval, 5))
    result_annual = -np.ones((maxNBES + 1, maxNBES + 1, 2))

    for sCHP in range(0, maxNBES + 1):
        if sCHP == 0:  # Exclude point 0/0
            startHP = 1
        else:
            startHP = 0

        for sHP in range(startHP, maxNBES - sCHP + 1):
            # Create new clean cluster
            cluster1 = Cluster(dirAbsResults, environment1, horizon, stepSize, interval)

            # Add CHP BES to the cluster
            for c in range(0, sCHP):
                besCHP = Bes(stepSize=stepSize, TER1=TER_CHP, TER2=0.0, RSC=RSC, sizingMethod=sizingMethod_CHP, iApartments=iApartments, sqm=sqm, specDemandTh=specDemandTh, envrnmt=environment1)
                cluster1.addMember(besCHP)
            # Add HP BES to the cluster
            for h in range(0, sHP):
                besHP = Bes(stepSize=stepSize, TER1=TER_HP, TER2=-1.0, RSC=RSC, sizingMethod=sizingMethod_HP, iApartments=iApartments, sqm=sqm, specDemandTh=specDemandTh, envrnmt=environment1)
                # print("pth1:", bes1.getNominalThermalPower())
                cluster1.addMember(besHP)

            _shareSurchargeLoad = (maxNBES - float(sCHP + sHP))/(sCHP + sHP) * 100
            # print("Term: {}".format(_shareSurchargeLoad))
            cluster1.setSurchargeLoad(_shareSurchargeLoad)  # has to be called after all bes are added

            cluster1.setTypeOptimization("LP")

            for time in range(startTime, endTime, interval):
                print("Scenario (Start time: {}; #BES: {}; #CHP: {}; #HP: {}; SurchargeLoad: {}; "
                      "Annual Electrical Consumption (BES): {}; Annual Electrical Consumption (all): {}"
                      .format(time, cluster1.getNumberOfMembers(), sCHP, sHP, cluster1.getSurchargeLoad(),
                              cluster1.getAnnualElectricityConsumption(1), cluster1.getAnnualElectricityConsumption(0)))

                (ratioMaxEnergy, ratioMaxPower, relGap, avgRemainder, avgFluctuations) = cluster1.calcSchedules(time)

                print("_____________________________________________________________________________________")
                print("ratioMaxFluc: {}".format(ratioMaxEnergy))
                print("ratioMaxPower: {}".format(ratioMaxPower))
                print("Gap: {}".format(relGap))  # gap >= 0: real gap value; gap == -1: optimal solution found during presolve; gap == -2: Relaxations
                print("avgRemainder: {}".format(avgRemainder))
                print("avgFluctuations: {}".format(avgFluctuations))
                print("_____________________________________________________________________________________")

                result[sCHP, sHP, (time-startTime)/interval, 0] = ratioMaxEnergy
                result[sCHP, sHP, (time-startTime)/interval, 1] = ratioMaxPower
                result[sCHP, sHP, (time-startTime)/interval, 2] = relGap
                result[sCHP, sHP, (time-startTime)/interval, 3] = avgRemainder
                result[sCHP, sHP, (time-startTime)/interval, 4] = avgFluctuations

                # In the first iteration, the values are still initialized with -1, thus set them to 0
                if result_annual[sCHP, sHP, 0] < 0:
                    result_annual[sCHP, sHP, 0] = 0
                if result_annual[sCHP, sHP, 1] < 0:
                    result_annual[sCHP, sHP, 1] = 0
                #Create the sum of ratioMaxFluc for the whole year
                result_annual[sCHP, sHP, 0] = result_annual[sCHP, sHP, 0] + ratioMaxEnergy
                result_annual[sCHP, sHP, 1] = result_annual[sCHP, sHP, 1] + ratioMaxPower
            print("_____________________________________________________________________________________")
        print("_____________________________________________________________________________________")


    # Write results to files

    # Write results to Excel sheet
    # create Excel workbook and worksheets for saving the simulation results
    wb = xlwt.Workbook()

    # list of worksheets
    listws = list()
    listws.append(wb.add_sheet("ratioMaxEnergy", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("ratioMaxPower", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("relGap", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("avgRemainder", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("avgFluctuations", cell_overwrite_ok=True))

    for time in range(startTime, endTime, interval):
        ztime = (time-startTime)/interval
        # write column description and column labels
        for i in range(0, len(listws)):
            listws[i].write(0 + ztime*(maxNBES + 4), 0, "Time: {}".format(time))
            listws[i].write(0 + ztime*(maxNBES + 4), 2, "#HP")
            for sHP in range(0, maxNBES+1):
                listws[i].write(1 + ztime*(maxNBES + 4), 2 + sHP, sHP)
            # write row description and row labels
            listws[i].write(2 + ztime*(maxNBES + 4), 0, "#CHP")

            # write real simulation results
            for sCHP in range(0, maxNBES + 1):
                listws[i].write(2 + ztime*(maxNBES + 4) + sCHP, 1, sCHP)
                if sCHP == 0:  # Exclude point 0/0
                    startHP = 1
                else:
                    startHP = 0

                for sHP in range(startHP, maxNBES - sCHP + 1):
                    listws[i].write(2 + ztime*(maxNBES + 4) + sCHP, 2 + sHP, result[sCHP, sHP, ztime, i])


    # Write the sum of ratioMaxFluc for the whole year to Excel
    ws = wb.add_sheet("ratioMaxEnergy_Annual", cell_overwrite_ok=True)
    ws.write(0, 0, nDays)
    ws.write(2, 0, "#CHP")
    ws.write(0, 2, "#HP")

    for sHP in range(0, maxNBES + 1):
        ws.write(1, 2 + sHP, sHP)

    for sCHP in range(0, maxNBES + 1):
        ws.write(2 + sCHP, 1, sCHP)
        if sCHP == 0:  # Exclude point 0/0
            startHP = 1
        else:
            startHP = 0

        for sHP in range(startHP, maxNBES - sCHP + 1):
            ws.write(2 + sCHP, 2 + sHP, result_annual[sCHP, sHP, 0]/nDays)

    # Write the sum of ratioMaxFluc for the whole year to Excel
    ws = wb.add_sheet("ratioMaxPower_Annual", cell_overwrite_ok=True)
    ws.write(0, 0, nDays)
    ws.write(2, 0, "#CHP")
    ws.write(0, 2, "#HP")

    for sHP in range(0, maxNBES + 1):
        ws.write(1, 2 + sHP, sHP)

    for sCHP in range(0, maxNBES + 1):
        ws.write(2 + sCHP, 1, sCHP)
        if sCHP == 0:  # Exclude point 0/0
            startHP = 1
        else:
            startHP = 0

        for sHP in range(startHP, maxNBES - sCHP + 1):
            ws.write(2 + sCHP, 2 + sHP, result_annual[sCHP, sHP, 1]/nDays)

    # Excel needs a different filename as Excel can open only files with a path length of 218 characters
    excel_file_name = "results"
    print(dirAbsResults)
    print(excel_file_name)
    wbname = "{}/{}.xls".format(dirAbsResults, excel_file_name)
    wb.save(wbname)

    np.save("{}/results.npy".format(dirAbsResults), result)
    np.save("{}/results_annual.npy".format(dirAbsResults), result_annual)

    # plot3Dbars.plot3Dbars(result[:, :, 0].T, arrNumberBes, arrSurchargeLoad)

def calcScenarioHelper(_args):
    print("_args: ", _args)
    calcScenario(*_args)

if __name__ == '__main__':
    matScenarios = np.asarray([[(listHorizon[x], listRSC[y]) for x in range(0, len(listHorizon))] for y in range(0, len(listRSC))])
    _shape = np.shape(matScenarios)
    listScenarios = matScenarios.reshape((_shape[0] * _shape[1], _shape[2]))

    # w/o parallelization
    # calcScenarioHelper(listScenarios[0])

    pool = mp.Pool()  # processes=len(listHorizon)
    pool.map_async(calcScenarioHelper, [listScenarios[x] for x in range(0, len(listScenarios))])
    pool.close()
    pool.join()