__author__ = 'Annika Wierichs'

import os
import numpy as np


class Cluster(object):
    """
    container for number of BES
    """

    def __init__(self, dirAbsResults, environment, horizon, stepSize, interval):
        """
        Constructor of cluster
        :param environment: instance of the environment in which the cluster will be included
        :param horizon: time period (s) for which the schedules are calculated (e.g. 1 day ahead = 86400s)
        :param stepSize: time period (s) of the individual time step
        :param interval: time period (s) after which new schedules are calculated (interval <= horizon)
        """
        self.script_dir = os.path.dirname(__file__)
        self.dirAbsResults = dirAbsResults

        self.horizon = horizon  # in seconds
        self.stepSize = stepSize  # in seconds
        self.interval = interval  # in seconds
        self.hSteps = horizon / stepSize
        self.iSteps = interval / stepSize

        self.listBes = list()
        self.listBesPrimary = list()
        self.listBesCHP = list()
        self.listBesHP = list()
        self.listBesGB = list()
        self.environment = environment

        self.remainder = []

    def chooseSchedulesRandomly(self, fromTime, criterion='energy'):
        """
        method only evaluates but does not actually choose schedules in BES classes
        :param fromTime: from time
        :param criterion: criterion to be used in evaluation through performance measure
        :return:
        """

        toTime = fromTime + (self.hSteps - 1) * self.stepSize
        flucCurve = self.getFluctuationsCurve(fromTime, toTime)
        remainder = flucCurve

        for b in range(self.getNumberOfMembers()):
            if self.listBes[b].getTER1() is not 0:
                schedulePri = self.listBes[b].getSchedules()[0]

                scheduleSec = self.listBes[b].getSchedulesSec()[0]
                loadPri = [float(self.listBes[b].getNominalElectricalPower1() * schedulePri[t]/self.listBes[b].getModlvls1() * self.stepSize) for t in range(len(schedulePri))]
                loadSec = [float(self.listBes[b].getNominalElectricalPower2() * scheduleSec[t] * self.stepSize) for t in range(len(scheduleSec))]
                remainder = [remainder[t] + loadPri[t] for t in range(len(remainder))]
                remainder = [remainder[t] + loadSec[t] for t in range(len(remainder))]

        performance = self.calcPerformanceMeasure(remainder, flucCurve, criterion)
        return performance

    def addMember(self, SmartBes):
        """
        Method to add SmartBes to the cluster
        :param SmartBes: BES which will be added to the cluster
        """
        self.listBes.append(SmartBes)
        if SmartBes.getTER1() > 0:      # CHP
            self.listBesCHP.append(SmartBes)
            self.listBesPrimary.append(SmartBes)
        elif SmartBes.getTER1() < 0:    # HP
            self.listBesHP.append(SmartBes)
            self.listBesPrimary.append(SmartBes)
        else:                           # gas boiler
            self.listBesGB.append(SmartBes)

    def deleteMember(self, SmartBes):
        """
        Method deletes given member-BES from cluster
        :param SmartBes: BES to be deleted from cluster
        """
        self.listBes.remove(SmartBes)
        if SmartBes.getTER1() > 0:      # CHP
            self.listBesCHP.remove(SmartBes)
            self.listBesPrimary.remove(SmartBes)
        elif SmartBes.getTER1() < 0:    # HP
            self.listBesHP.remove(SmartBes)
            self.listBesPrimary.remove(SmartBes)
        else:                           # gas boiler
            self.listBesGB.remove(SmartBes)

    def assignRemainderAfterLocalOptimization(self, fromTime):
        toTimeI = fromTime + (self.iSteps - 1) * self.stepSize

        # remainder = fluctuations + load added by heating systems in cluster
        self.remainder = self.getFluctuationsCurve(fromTime, toTimeI)
        # add each heating system's load to current curve (use [1:0] to avoid dummy modlvl at t=0)
        for bes in self.getBESs(typeHeater="primary"):
            #print np.array(bes.getSchedule()[1:]) * bes.getNominalElectricalPower1() / bes.getModlvls1() * self.stepSize
            self.remainder += np.array(bes.getSchedule()[1:self.iSteps+1])    * bes.getNominalElectricalPower1() / bes.getModlvls1() * self.stepSize \
                            + np.array(bes.getScheduleSec()[1:self.iSteps+1]) * bes.getNominalElectricalPower2()                     * self.stepSize


    @staticmethod
    def calcPerformanceMeasure(Remainder, Fluctuations, criterion='RPV'):
        """
        Method calculates the performance measure the following way:
        (Remainder^max - Remainder^min)/(Fluctuations^max - Fluctuations^min)
        :param Remainder: current remainder array
        :param Fluctuations: current fluctuations curve array
        :return: performance measures: ratioMaxEnergy, ratioMaxPower
        """

        if criterion is 'RPV':
            deltaRemainder = np.max(Remainder) - np.min(Remainder)
            deltaFluctuations = np.max(Fluctuations) - np.min(Fluctuations)

            ratio = deltaRemainder / deltaFluctuations

        # elif criterion is 'energy':
        #     avgRemainder = np.mean(Remainder)
        #     shiftedRemainder = [(Remainder[x]-avgRemainder) for x in range(0, len(Remainder))]
        #     cumsumShiftedRemainder = np.cumsum(shiftedRemainder)
        #     maxEnergyRemainder = max(abs(cumsumShiftedRemainder))
        #
        #     avgFluctuations = np.mean(Fluctuations)
        #     shiftedFluctuations = [(Fluctuations[x]-avgFluctuations) for x in range(0, len(Fluctuations))]
        #     cumsumFluctuations = np.cumsum(shiftedFluctuations)
        #     maxEnergyFluctuations = max(abs(cumsumFluctuations))
        #
        #     ratio = maxEnergyRemainder / maxEnergyFluctuations

        return ratio

    def getNumberOfMembers(self, typeHeater = "all"):
        """
        :param typeHeater: "HP", "CHP", "GB", "primary" or "all"
        :return: list of BESs
        """
        if typeHeater == "CHP":
            return len(self.listBesCHP)
        elif typeHeater == "HP":
            return len(self.listBesHP)
        elif typeHeater == "GB":
            return len(self.listBesGB)
        elif typeHeater == "all":
            return len(self.listBes)
        elif typeHeater == "primary":
            return len(self.listBesPrimary)
        else:  # type not found
            print "in cluster.getNumberOfMembers: type of heater not found, returning -1."
            return -1

    def getSumOfNomElecPower(self, typeHeater):
        """
        :param typeHeater: "HP", "CHP" or "all"
        :return: Accumulated nominal power of specified BES's (for "all": using absolute values / for "CHP": result will be negative)
        """
        _npCHP = 0
        _npHP = 0
        _npAll = 0
        if typeHeater == "CHP":
            for b in range(self.getNumberOfMembers()):
                if self.listBes[b].getTER1() > 0:   # CHP
                    _npCHP += self.listBes[b].getNominalElectricalPower1()
            return _npCHP
        elif typeHeater == "HP":
            for b in range(self.getNumberOfMembers()):
                if self.listBes[b].getTER1() < 0:   # HP
                    _npHP += self.listBes[b].getNominalElectricalPower1()
            return _npHP
        elif typeHeater == "all":
            for b in range(self.getNumberOfMembers()):
                if self.listBes[b].getTER1() != 0:   # no GB
                    _npAll += abs(self.listBes[b].getNominalElectricalPower1())
            return _npAll
        else:  # type not found
            return -1

    def getRemainder(self):
        """
        :return: remainder after BESs have chosen their optimal schedules
        """
        return self.remainder

    def getAnnualElectricityConsumption(self):
        """
        adds up annual energy consumption of all BES in cluster
        :param type:
        :return: annual electrical demand :rtype: int
        """
        _demandelectrical_annual = 0
        for x in range(0, len(self.listBes)):
            _demandelectrical_annual += self.listBes[x].getAnnualElectricalDemand()
        return _demandelectrical_annual

    def getElectricalDemandCurve(self, fromTime, toTime):
        """
        Returns the electrical demand curve of the cluster for a given time period
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: multi dimensional array (2x time period); first column: time; second column: values
        """
        _electricalDemandCurve = self.listBes[0].getElectricalDemandCurve(fromTime, toTime)
        for x in range(1, len(self.listBes)):
            _electricalDemandCurve[1, :] += self.listBes[x].getElectricalDemandCurve(fromTime, toTime)[1, :]
        return _electricalDemandCurve

    def getRenewableGenerationCurve(self, fromTime, toTime):
        """
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: renewable generation curve for cluster
        """
        _AnnualEnergyDemand = self.getAnnualElectricityConsumption()
        return self.environment.getRenewableGenerationCurve(fromTime, toTime, _AnnualEnergyDemand)

    def getFluctuationsCurve(self, fromTime, toTime):
        """
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: resulting curve (electrical demand minus energy covered by RG) that will be flattened (1 x time period)
        """
        _RES = self.getRenewableGenerationCurve(fromTime, toTime)
        _Load = self.getElectricalDemandCurve(fromTime, toTime)
        return _RES[1, :] + _Load[1, :]

    def getBESs(self, typeHeater="all"):

        """
        :param typeHeater: "HP", "CHP", "GB", "primary" or "all"
        :return: list of BESs
        """
        if typeHeater == "CHP":
            return self.listBesCHP
        elif typeHeater == "HP":
            return self.listBesHP
        elif typeHeater == "GB":
            return self.listBesGB
        elif typeHeater == "all":
            return self.listBes
        elif typeHeater == "primary":
            return self.listBesPrimary
        else:  # type not found
            print "in cluster.getBESs: type of heater not found, returning -1."
            return -1

    def sortPrimaryHeatersByObjFcn(self):
        self.listBesPrimary.sort(key = lambda smartbes: smartbes.getObjFcn())

    def sortPrimaryHeatersByNomElPower(self):
        self.listBesPrimary.sort(key = lambda smartbes: abs(smartbes.getNominalElectricalPower1()), reverse=True)
