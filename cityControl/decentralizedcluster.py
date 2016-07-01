__author__ = 'Anni'

import numpy as np
from city.cluster import Cluster
import sys
from time import *

class DecentralizedCluster(Cluster):
    def __init__(self, dirAbsResults, environment, horizon, stepSize, interval):
        
        super(DecentralizedCluster, self).__init__(dirAbsResults, environment, horizon, stepSize, interval)

    def assignSelectedSchedulesFromPool(self):
        """
        assign the selected schedules from solution pools and the EoD values (ModLvl 1 & SoC)
        :return:
        """

        listBesPri = self.getBESs(typeHeater='primary')
        # assign schedule data (SMARTBESs)
        for b in range(len(listBesPri)):
            iSelectedSchedule = listBesPri[b].getPoolChosenScheduleIndex()
            # set schedules
            listBesPri[b].setSchedule(listBesPri[b].getPoolSchedules()[iSelectedSchedule])          # set schedule
            listBesPri[b].setScheduleSec(listBesPri[b].getPoolSchedulesSec()[iSelectedSchedule])    # set secondary schedule
            # MODLVL 1 EoD
            listBesPri[b].setStateModlvl(listBesPri[b].getSchedule()[self.iSteps])                  # set current modulation level
            # state of charge EoD (and avoid possible infeasibility)
            end_SOC = listBesPri[b].getPoolETHStorage()[iSelectedSchedule, self.iSteps] / listBesPri[b].getStorageCapacity()
            if end_SOC <= listBesPri[b].getSOCmin():
                end_SOC = listBesPri[b].getSOCmin()
            elif end_SOC >= listBesPri[b].getSOCmax():
                end_SOC = listBesPri[b].getSOCmax()
            listBesPri[b].setSOC(end_SOC)


    def PIDA(self, fromTime):
        """
        Parallel Iterative Desync Algorithm
        ...consisting of multiple 'executions of IDA', which in turn consist of several 'iterations' (= all BESs in
        cluster find their current best schedule once). Iterations consist of single 'steps' (= one BES finding its
        current optimal schedule) --> keep in mind when reading comments!
        :return: performance measure
        """

        # set up variables
        listBesPri = self.getBESs("primary")
        noMem = len(listBesPri)
        toTimeH = fromTime + (self.hSteps - 1) * self.stepSize
        fluctuations = self.getFluctuationsCurve(fromTime, toTimeH)

        peakToValleyPerformances = np.zeros(noMem)      # stores performance for each execution of IDA

        # calculate schedule pools & reset for PIDA
        for bes in listBesPri:
            bes.calcSchedulePool(fromTime, toTimeH)

        # for debugging
        # for bes in listBesPri:
        #     print "\nSolutions: %d" % bes.getPoolNoOfSchedules(), "\tObjFcn:", bes.getObjFcn()
        #     for s in range(bes.getPoolNoOfSchedules()):
        #         for t in range(len(bes.poolSchedules[0])):
        #             print '%1.0f' % int(round(bes.poolSchedules[s, t])),
        #             sys.stdout.softspace = 0
        #         print "\tOptimized Value:", bes.poolOptimizedValues[s]

        messagesSent = 0

        # PIDA
        # --------------------------------------------------------------------------------------------------------------

        # use each BES in the cluster as a starting point for IDA and select the execution achieving best performance
        for iStartingBes in range(noMem):
            # SINGLE IDA EXECUTION
            # ----------------------------------------------------------------------------------------------------------
            peakToValleys = np.zeros(noMem)     # stores peak to valley values for each step of IDA
            tempRemainder = fluctuations        # stores temporary remainder for each step of IDA

            # reset all BESs for upcoming fresh execution of IDA
            for bes in listBesPri:
                bes.resetForDesync(self.hSteps)

            # for debugging
            # print "\n\n------------------- Starting with BES No.", iStartingBes, "now. -------------------"
            b = iStartingBes        # set the initial value of iterator 'b' to starting BES index of this IDA execution
            noOfIt = 0              # keeps track of iterations within this IDA execution
            while True:
                # if at least one iteration has occured AND peak to valley value has not improved any further (-> local optimum), break from while
                if noOfIt > 0 and peakToValleys[b] - np.finfo(np.float32).eps <= peakToValleys[b-1] <= peakToValleys[b] + np.finfo(np.float32).eps:     # 64 bit: np.finfo(float).eps
                    # for debugging
                    # print "\nSelected schedules (Last Iteration:", noOfIt, ")"
                    # for bb in range(b):
                    #     print "%3.3d" % listBesPri[bb].getPoolChosenScheduleIndex(), "\t",

                    break

                # pass current temporary remainder to BES b for it to find its optimal schedule & save new temporary remainder
                tempRemainder = listBesPri[b].findBestSchedule(tempRemainder)
                # calculate and save peak to valley value
                peakToValleys[b] = np.max(tempRemainder) - np.min(tempRemainder)

                b += 1
                # if current iteration of IDA has finished, reset b to zero
                if b == noMem:
                    # for debugging
                    # print "\nSelected schedules (Iteration:", noOfIt, ")"
                    # for bes in listBesPri:
                    #     print "%3.3d" % bes.getPoolChosenScheduleIndex(), "\t",

                    noOfIt += 1
                    b = 0
            # ----------------------------------------------------------------------------------------------------------
            # END SINGLE IDA EXECUTION

            messagesSent += noOfIt * noMem + b - iStartingBes
            if b < iStartingBes:
                messagesSent += noMem

            # save peak to valley performance
            peakToValleyPerformances[iStartingBes] = peakToValleys[b]

            # for debugging
            # print "\n\nPerformance (Horizon):", self.calcPerformanceMeasure(tempRemainder, fluctuations)


        # --------------------------------------------------------------------------------------------------------------
        # END PIDA

        # now find IDA execution that achieved best peak to valley performance
        iBestIDAExecution = np.argmin(peakToValleyPerformances)

        # for debugging
        # print "\n\n--------------------------\nBest IDA Execution starting with BES No.", iBestIDAExecution

        # SINGLE IDA EXECUTION (BEST PERFORMANCE)
        # --------------------------------------------------------------------------------------------------------------
        peakToValleys = np.zeros(noMem)     # stores peak to valley values for each step of IDA
        tempRemainder = fluctuations        # stores temporary remainder for each step of IDA

        # reset all BESs for upcoming fresh execution of IDA
        for bes in listBesPri:
            bes.resetForDesync(self.hSteps)

        b = iBestIDAExecution     # set the initial value of iterator 'b' to starting BES index of this IDA execution
        noOfIt = 0          # keeps track of iterations within this IDA execution
        while True:
            # if at least one iteration has occured AND peak to valley value has not improved any further (-> local optimum), break from while
            if noOfIt > 0 and peakToValleys[b] - np.finfo(np.float32).eps <= peakToValleys[b-1] <= peakToValleys[b] + np.finfo(np.float32).eps:     # 64 bit: np.finfo(float).eps
                break

            # pass current temporary remainder to BES b for it to find its optimal schedule & save new temporary remainder
            tempRemainder = listBesPri[b].findBestSchedule(tempRemainder)
            # calculate and save peak to valley value
            peakToValleys[b] = np.max(tempRemainder) - np.min(tempRemainder)

            b += 1
            # if current iteration of IDA has finished, reset b to zero
            if b == noMem:
                noOfIt += 1
                b = 0
        # --------------------------------------------------------------------------------------------------------------
        # END SINGLE IDA EXECUTION (BEST PERFORMANCE)

        messagesSent += noOfIt * noMem + b - iBestIDAExecution
        if b < iBestIDAExecution:
            messagesSent += noMem

        # assign values to BESs (schedules 1 & 2, SoC EoD, ModLvl1 EoD) and cluster (remainder)
        self.assignSelectedSchedulesFromPool()
        self.remainder = tempRemainder[:self.iSteps]

        performance = self.calcPerformanceMeasure(self.remainder, fluctuations[:self.iSteps])

        return performance, messagesSent

    def SIDA(self, fromTime):
        """
        Sorted Iterative Desync Algorithm
        :param fromTime:
        :return:
        """

        # sort primary heater BESs by their nominal power (descending order)
        self.sortPrimaryHeatersByNomElPower()

        # call IDA
        perf, mess = self.IDA(fromTime)

        return perf, mess


    def IDA(self, fromTime):
        """
        Iterative Desync Algorithm
        :return: performance measure
        """

        # set up variables
        listBesPri = self.getBESs("primary")
        noMem = len(listBesPri)
        toTimeH = fromTime + (self.hSteps - 1) * self.stepSize
        fluctuations = self.getFluctuationsCurve(fromTime, toTimeH)

        # temporary remainder in between individual steps of IDA
        tempRemainder = fluctuations
        # peak to valley values corresponding to temporary remainders
        peakToValleys = np.zeros(noMem)

        timer = time()

        # calculate schedule pools & reset for desync
        for bes in listBesPri:
            bes.calcSchedulePool(fromTime, toTimeH)
            bes.resetForDesync(self.hSteps)

        # for debugging
        for bes in listBesPri:
            print "\nSolutions: %d" % bes.getPoolNoOfSchedules(), "\tObjFcn:", bes.getObjFcn()
            for s in range(bes.getPoolNoOfSchedules()):
                for t in range(len(bes.poolSchedules[0])):
                    print '%1.0f' % int(round(bes.poolSchedules[s, t])),
                    sys.stdout.softspace = 0
                print "\tOptimized Value:", bes.poolOptimizedValues[s]

        # for debugging
        print "\nCalculation of all Solution Pools:", time() - timer
        # for debugging
        timer = time()

        b = 0
        noOfIt = 0
        while True:
            if noOfIt > 0 and peakToValleys[b] - np.finfo(np.float32).eps <= peakToValleys[b-1] <= peakToValleys[b] + np.finfo(np.float32).eps:     # 64 bit: np.finfo(float).eps
                # for debugging
                print "\nSelected schedules (Last Iteration:", noOfIt, ")"
                for bb in range(b):
                    print "%3.3d" % listBesPri[bb].getPoolChosenScheduleIndex(), "\t",
                print "\n\nEPS 32:", np.finfo(np.float32).eps, "\tEPS 64:", np.finfo(float).eps

                break

            tempRemainder = listBesPri[b].findBestSchedule(tempRemainder)
            peakToValleys[b] = np.max(tempRemainder) - np.min(tempRemainder)

            b += 1
            if b == noMem:
                # for debugging
                print "\nSelected schedules (Iteration:", noOfIt, ")"
                for bes in listBesPri:
                    print "%3.3d" % bes.getPoolChosenScheduleIndex(), "\t",

                noOfIt += 1
                b = 0

        # for debugging
        print "No of full iterations:", noOfIt
        print "\nIDA Execution time:", time() - timer, "\n\n"

        # assign values to BESs (schedules 1 & 2, SoC EoD, ModLvl1 EoD) and cluster (remainder)
        self.assignSelectedSchedulesFromPool()
        self.remainder = tempRemainder[:self.iSteps]

        performance = self.calcPerformanceMeasure(self.remainder, fluctuations[:self.iSteps])
        messagesSent = noOfIt * noMem + b

        return performance, messagesSent
