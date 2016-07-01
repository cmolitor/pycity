# coding=utf-8
__author__ = 'Christoph Molitor'


# todo: timestep:30min (adjust data), maybe modlvl = 2, surchargeload as discrete houses
import numpy as np
import xlwt
from time import *
import os
import fractions as frac
import multiprocessing as mp
import sys

from building.environment import Environment
from clustersizeanalysis.cluster_cplex import Cluster
from building.bes import Bes

stepSize = 900
minRuntime1 = stepSize * 1
startTime = 86400 * 0  # 1814400 # 5270400  #
endTime = 86400 * 365
horizon = int(86400 + minRuntime1 - stepSize)  # horizon for scheduling
interval = 86400  # interval for scheduling


nDays = (endTime-startTime)/86400

# General building data
RSC = 3.0
iApartments = 1
# 166 kWh/m2/a seem a good value however different values found
# According to Endenergieverbrauch im deutschen Wohngebäudebestand, Zusatzauswertung zur Studie
# "Wohnungsbau in Deutschland - 2011, Modernisierung oder Bestandsersatz"
# it is around 200kWh/sqm/a for 1 and 2 apartment buildings
specDemandTh = 166.0

# 150 sqm per apartment has to be adjusted to 128.5 sqm according to
# Statistisches Bundesamt, Fachserie 15, Sonderheft 1, EVS 2013, Hochrechnung
# 146sqm according to F. Schröder, M. Greller, V. Hundt, B. Mundry, and O. Papert, “Universelle Energiekennzahlen für Deutschland,”
# Bauphysik, vol. 31, no. 6, pp. 393–402, Dec. 2009.
sqm = 146.0

#Heating system parameters; TER (Thermal-electric ratio)
TER_HP = -2.32  # Values for Dimplex LA 12TU (http://www.dimplex.de/pdf/de/produktattribute/produkt_1725609_extern_egd.pdf)
TER_CHP = 2.3
sizingMethod = "Bivalent"

# Sizing of electro-thermal heating system:
# Sizing of CHP due to Maximum Rectangle Method (MRM). Sources:
#   [1] D. Haeseldonckx, L. Peeters, L. Helsen, und W. D’haeseleer,
#       „The impact of thermal storage on the operational behaviour of residential CHP facilities and the overall CO2 emissions“,
#       Renewable and Sustainable Energy Review, Bd. 11, Nr. 6, S. 1227–1243, Aug. 2007.
sizingMethod_CHP = -1  # MRM


# Sizing of HP to cover 98% of the annual thermal energy demand. Sources:
#   [1] "Bivalente Wärmepumpen-Systeme." Bundesindustrieverband Deutschland Haus-, Energie- und Umwelttechnik e.V., Mar-2014.
#   [2]“Planungshandbuch Wärmepumpen.” Viessmann Werke, 2011.
sizingMethod_HP = -2

sizingMethod_NETH = 1.0

# scenario = [[shareCHP1 shareHP1] [shareCHP2 shareHP2].....]
sharesETHs = np.matrix('20 20; 40 20; 60 20; 40 40; 20 60; 20 40')
sharesETHs = np.matrix('20 40')
#sharesETHs = np.matrix('50 50')
maxNBes = 50
#maxNBes = 2

environment1 = Environment(0.0, stepSize)

def calcScenario(_args, iScenario, counts, dirAbsResults):
    _result = np.zeros(((endTime-startTime)/interval, 5))
    _result_annual = np.zeros(2)

    nCHPs = _args[0]
    nHPs = _args[1]
    nNETHs = _args[2]

    # Create new clean cluster
    cluster1 = Cluster(dirAbsResults, environment1, horizon, stepSize, interval)
    # Add CHP BESs to the cluster
    for i in range(0, nCHPs):
        besCHP = Bes(stepSize=stepSize, TER1=TER_CHP, TER2=0.0, RSC=RSC, sizingMethod=sizingMethod_CHP, iApartments=iApartments, sqm=sqm, specDemandTh=specDemandTh, envrnmt=environment1)
        #besCHP.setMinRuntime1(minRuntime1)
        cluster1.addMember(besCHP)

    # Add HP BESs to the cluster
    for i in range(0, nHPs):
        besHP = Bes(stepSize=stepSize, TER1=TER_HP, TER2=-1.0, RSC=RSC, sizingMethod=sizingMethod_HP, iApartments=iApartments, sqm=sqm, specDemandTh=specDemandTh, envrnmt=environment1)
        #besHP.setMinRuntime1(minRuntime1)
        # print("pth1:", bes1.getNominalThermalPower())
        cluster1.addMember(besHP)

    # Add non TEH BESs to the cluster
    for i in range(0, nNETHs):
        besNETH = Bes(stepSize=stepSize, TER1=0.0, TER2=0.0, RSC=RSC, sizingMethod=1, iApartments=iApartments, sqm=sqm, specDemandTh=specDemandTh, envrnmt=environment1)
        # print("pth1:", bes1.getNominalThermalPower())
        cluster1.addMember(besNETH)

    cluster1.setTypeOptimization("MIP")

    for time in range(startTime, endTime, interval):
        message = "Scenario (Start time: {}; #BES: {}; nHPs: {}; nCHPs: {}; Annual Electrical Consumption (BES): {}; Annual Electrical Consumption (all): {}".format(time, cluster1.getNumberOfMembers(), nHPs, nCHPs, cluster1.getAnnualElectricityConsumption(1), cluster1.getAnnualElectricityConsumption(0))
        print(message)
        (ratioMaxEnergy, ratioMaxPower, relGap, avgRemainder, avgFluctuations) = cluster1.calcSchedules(time)

        print("ratioMaxFluc: {}".format(ratioMaxEnergy))
        print("ratioMaxPower: {}".format(ratioMaxPower))
        print("Gap: {}".format(relGap))  # gap >= 0: real gap value; gap == -1: optimal solution found during presolve; gap == -2: Relaxations
        print("avgRemainder: {}".format(avgRemainder))
        print("avgFluctuations: {}".format(avgFluctuations))

        print("_____________________________________________________________________________________")
        _result[(time-startTime)/interval, 0] = ratioMaxEnergy
        _result[(time-startTime)/interval, 1] = ratioMaxPower
        _result[(time-startTime)/interval, 2] = relGap
        _result[(time-startTime)/interval, 3] = avgRemainder
        _result[(time-startTime)/interval, 4] = avgFluctuations

        # print _result[(time-startTime)/interval, 0]
        # print _result[(time-startTime)/interval, 1]
        # print _result[(time-startTime)/interval, 2]
        # print _result[(time-startTime)/interval, 3]
        # print _result[(time-startTime)/interval, 4]

        #Create the sum of ratioMaxFluc for the whole year
        _result_annual[0] = _result_annual[0] + ratioMaxEnergy
        _result_annual[1] = _result_annual[1] + ratioMaxPower
    print("_____________________________________________________________________________________")

    return (iScenario, counts, _result, _result_annual)



def calcScenarioHelper(_args, shares, counts):
    _result = np.zeros(((endTime-startTime)/interval, 5))
    _result_annual = np.zeros(2)
    return (shares, counts, _result, _result_annual)

def log_result(_args):
    iScenario = _args[0]
    counts = _args[1]
    _result = _args[2]
    _result_annual = _args[3]
    #print("Scenario(log_result): {} finished".format(iScenario))
    #print "logfile", _result, _result_annual, len(lstResults[iScenario][0,0,:])
    for iResult in range(0, len(lstResults[iScenario][0,0,:])):
        lstResults[iScenario][counts,:,iResult] = _result[:, iResult]

    for iResult in range(0, len(lstResults[iScenario][0,0,:])):
        lstResultsAnnual[iScenario][counts,:] = _result_annual[:]

def writeResults2Logfile(Scenario, dirAbsResults, scenario_name, _result, _result_annual):
    # Write results to Excel sheet
    # create Excel workbook and worksheets for saving the simulation results
    # print dirAbsResults
    #print("Scenario(writeResults2Logfile): {} finished".format(iScenario))
    wb = xlwt.Workbook()

    # _result = lstResults[iScenario2]
    # _result_annual = lstResultsAnnual[iScenario2]

    # list of worksheets
    listws = list()
    listws.append(wb.add_sheet("ratioMaxEnergy", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("ratioMaxPower", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("relGap", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("avgRemainder", cell_overwrite_ok=True))
    listws.append(wb.add_sheet("avgFluctuations", cell_overwrite_ok=True))

    # counts = len(lstResults[iScenario][:,0,0])
    # write column description and column labels
    for i in range(0, len(listws)):
        listws[i].write(0, 1, "nBES")
        listws[i].write(1, 0, "Time")
        for iSimRun in range(0, Scenario.shape[0]):
            listws[i].write(1, 1 + iSimRun, sum(Scenario[iSimRun]))
            # listws[i].write(1, 1 + iSimRun, (iSimRun + 1) * min_nBES)

        for time in range(startTime, endTime, interval):
            ztime = (time-startTime)/interval
            listws[i].write(2 + ztime, 0, ztime)

            for iSimRun in range(0, Scenario.shape[0]):
                listws[i].write(2 + ztime, 1 + iSimRun, _result[iSimRun, ztime, i])

    # Write the sum of ratioMaxEnergy for the whole year to Excel
    ws = wb.add_sheet("ratioMaxEnergy_Annual", cell_overwrite_ok=True)
    ws.write(0, 1, "nBES")

    for iSimRun in range(0, Scenario.shape[0]):
        ws.write(1, 1 + iSimRun, sum(Scenario[iSimRun]))
        ws.write(2, 1 + iSimRun, _result_annual[iSimRun, 0])

    # Write the sum of ratioMaxFluc for the whole year to Excel
    ws = wb.add_sheet("ratioMaxPower_Annual", cell_overwrite_ok=True)
    ws.write(0, 1, "nBES")

    for iSimRun in range(0, Scenario.shape[0]):
        ws.write(1, 1 + iSimRun, sum(Scenario[iSimRun]))
        ws.write(2, 1 + iSimRun, _result_annual[iSimRun, 1])

    # Excel needs a different filename as Excel can open only files with a path length of 218 characters
    excel_file_name = "results"
    wbname = "{}/{}.xls".format(dirAbsResults, excel_file_name)
    wb.save(wbname)

    #print "iScenario: {}, path: {}, filename: {}".format(iScenario, dirAbsResults, scenario_name)
    #np.save("{}/{}.npy".format(dirAbsResults, scenario_name), _result)
    #np.save("{}/{}_annual.npy".format(dirAbsResults, scenario_name), _result_annual)
    np.save("{}/results.npy".format(dirAbsResults), _result)
    np.save("{}/results_annual.npy".format(dirAbsResults), _result_annual)

# Not implemented yet, the idea is to have a function which create a data structure with all data belonging to a scenario
# def createScenario(shareCHPs, shareHPs, LCM=None):
#     shareNETHs = 100 - shareHPs - shareCHPs
#
#     divisor = frac.gcd(frac.gcd(shareCHPs, shareHPs),shareNETHs)
#     min_nCHPs = shareCHPs/divisor
#     min_nHPs = shareHPs/divisor
#     min_nNETHs = shareNETHs/divisor
#     min_nBES = min_nCHPs + min_nHPs + min_nNETHs


def main():
    lstScenarios = list()
    lstScenarioNames = list()
    lstScenarioResultPath = list()
    lstMin_nBES = list()

    factors = np.array([1, 2, 4, 7, 10])

    for ls in range(0, len(sharesETHs)):
        shareCHPs = sharesETHs[ls, 0]
        shareHPs = sharesETHs[ls, 1]
        shareNETHs = 100 - shareHPs - shareCHPs

        divisor = frac.gcd(frac.gcd(shareCHPs, shareHPs),shareNETHs)
        min_nCHPs = shareCHPs/divisor
        min_nHPs = shareHPs/divisor
        min_nNETHs = shareNETHs/divisor
        min_nBES = min_nCHPs + min_nHPs + min_nNETHs
        lstMin_nBES.append(min_nBES)

        # print min_nCHPs, min_nHPs, min_nNETHs, min_nBES
        scenario = np.array([[min_nCHPs * factors[x], min_nHPs * factors[x], min_nNETHs * factors[x]] for x in range(0, len(factors))]) # int(maxNBes/min_nBES)

        #scenario = np.array([[1, 1, 0],[2, 2, 0],[3, 3, 0],[5, 5, 0], [7, 7, 0],[10, 10, 0],[16, 16, 0],[25, 25, 0]])
        #scenario = np.array([[10, 10, 0]])

        print("Scenario: {}".format(scenario))

        counts = scenario.shape[0]

         # construct multi-dimensional array for storing the simulation results
        _result = np.zeros((counts, (endTime-startTime)/interval, 5))
        _result_annual = np.zeros((counts, 2))

        # Shared lists/memory
        lstResults.append(_result)
        lstResultsAnnual.append(_result_annual)
        lstScenarios.append(scenario)

        # create folder for simulation results
        lt = localtime()
        scenario_name = "{}{:02d}{:02d}-{:02d}{:02d}_{}_RES-{}_RSC-{}_Hrzn-{}_shareHPs-{}_shareCHPs-{}_step-{}".format(lt[0], lt[1], lt[2], lt[3], lt[4], sizingMethod, int(environment1.getShareRES()), int(RSC), int(float(horizon)/interval), shareHPs, shareCHPs, stepSize)
        if minRuntime1 > stepSize:
            scenario_name = scenario_name + "_minRT"

        dirResults = "_results_MIP/{}".format(scenario_name)
        if not os.path.exists(dirResults):
            os.makedirs(dirResults)
            np.save(dirResults + "/scenario.npy", scenario)

        dirScript = os.path.dirname(__file__)
        dirAbsResults = dirScript + "/" + dirResults
        lstScenarioNames.append(scenario_name)
        lstScenarioResultPath.append(dirAbsResults)

        # w/o parallelization
        # calcScenario(lstScenarios[0][0], 0, 0, lstScenarioResultPath[0])

    nCpus = mp.cpu_count()  # count logical CPU cores (including hyperthreading)
    print("# of CPU cores: ", nCpus)
    pool = mp.Pool(nCpus/4)  # processes=len(listHorizon)
    for iScenario in range(0, len(lstScenarios)):
        for counts in range(0, len(lstScenarios[0])):
            #pool.apply_async(calcScenarioHelper, [listScenarios[shares][counts], shares, counts], callback = log_result)
            pool.apply_async(calcScenario,
                             [lstScenarios[iScenario][counts],
                              iScenario,
                              counts,
                              lstScenarioResultPath[iScenario]],
                             callback = log_result)
    pool.close()
    pool.join()

    print("Waiting for all processes to finish...")

    #print lstResults
    #print lstResultsAnnual

    for iScenario in range(0, len(lstScenarios)):
        # print lstScenarioResultPath[iScenario]
        writeResults2Logfile(lstScenarios[iScenario], lstScenarioResultPath[iScenario], lstScenarioNames[iScenario], lstResults[iScenario], lstResultsAnnual[iScenario])

if __name__ == '__main__':
    lstResults = list()
    lstResultsAnnual = list()
    main()
    print "The end"