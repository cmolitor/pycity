__author__ = 'Annika Wierichs'

import numpy as np

from buildingControl.smartbes import SmartBes


class FlexSmartBes(SmartBes):  # subclass inherits from class Bes
    def __init__(self, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, objFcn=1, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4):
        """
        constructor of FlexSmartBes

        sign of CHP and HP data:
                El. NomPower    Th. NomPower    TER1
        CHP:    -               -               +
        HP:     +               -               -

        general info regarding indexing:
        e.g.:   index       012345678
                ---------------------
                MODLVL		001110010
                switchOn	_01000010
                switchOff	_00001001
                ETHStorage	XXXXXXXXX
                PTHStorage	_XXXXXXXX

                index       _01234567
                ---------------------
                demand/gen
                curves      _XXXXXXXX
        """

        super(FlexSmartBes, self).__init__(stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, objFcn, solPoolAbsGap, solPoolRelGap, solPoolIntensity)

        self.flexibility = -1               # flexibility for current parameters



    def calcFlexibility(self):
        """
        calculates flexibility of current set of schedules:
            1. get flexibility of each time step: minimum (0) if same MODLVL in all schedules; maximum (1) if half MODLVLs equal 1, and half MODLVLs equal 0; adjusted for odd numbers of schedules.
            2. sum up flexibility-values of all time steps & divide by number of time steps.
            3. multiply this by number of schedules
        :return: flexibility value
        """

        # don't consider different schedules for backup heater if it's a gas boiler
        if self.getTER2() is 0:
            consideredSchedules = self.getUniquePrimarySchedules()
            noOfSchedules = len(consideredSchedules)
        else:
            consideredSchedules = self.getSchedules()
            noOfSchedules = len(consideredSchedules)

        # zero flexibility if no thermal storage or if only one schedule available
        if self.getTER1() == 0 or noOfSchedules == 1:
            # print "Gas boiler, no schedules."
            self.flexibility = 0
            self.flexibilityInclNomPower = 0
            return self.flexibility

        # no schedules calculated?
        if noOfSchedules is 0:
            print "\nFlexibility Calculation: No schedules available for this BES."
            self.flexibility = 0
            return -1

        steps = len(self.schedules[0])
        added = [float(0.0) for x in range(steps)]

        for t in range(steps):  # for each time step
            for s in range(noOfSchedules):    # sum up MODLVLs
                added[t] += float(consideredSchedules[s][t])
            if float(added[t])/float(noOfSchedules) > 0.5:    # if more ones than zeros for this time step
                if noOfSchedules % 2 == 0: added[t] = 1 - float(added[t])/float(noOfSchedules)  # if even no. of schedules
                else: added[t] = float(noOfSchedules - added[t]) / float(noOfSchedules-1)       # if uneven no. of schedules
            else:
                if noOfSchedules % 2 == 0: added[t] = float(added[t])/float(noOfSchedules)
                else: added[t] = float(added[t])/float(noOfSchedules-1)
            added[t] *= 2   # multiply by 2, so maximum flexibility for a time step will be 1

        flexibility = sum(added)/float(steps) * noOfSchedules     # add up flexibilities of time steps, divide by number of time steps, multiply by no. of schedules
        self.flexibility = flexibility
        # for debugging
        # print '%.2f' % self.getNominalElectricalPower1(), ' - %.3f' % flexibility    # for debugging
        # if self.getTER2() is 0:
        #     print noOfSchedules, "of", self.getNoOfSchedules(), "schedules considered"

        return flexibility


    def getFlexibility(self):
        """
        :return: current flexibility
        """
        return self.flexibility

    def getNoOfUniquePrimarySchedules(self):
        if self.getNoOfSchedules() is 0:
            return 0
        counter = 1
        for s in range(1, self.getNoOfSchedules()):
            if not (self.schedules[s] in self.schedules[0:s]):
                counter += 1
        return counter

    def getUniquePrimarySchedules(self):
        if self.getNoOfSchedules() is 0:
            return list()
        priSchedules = list()
        priSchedules.append(self.schedules[0])
        for s in range(1, self.getNoOfSchedules()):
            if not (self.schedules[s] in self.schedules[0:s]):
                priSchedules.append(self.schedules[s])
        return priSchedules

    @staticmethod
    def calcFlexibilityTest():
        """
        for testing purposes: check your own set of schedules and see if flexibility makes sense.
        calculates flexibility of a current isolated set of schedules:
            1. get flexibility of each time step: minimum (0) if same MODLVL in all schedules; maximum (1) if half MODLVLs equal 1, and half MODLVLs equal 0; adjusted for odd numbers of schedules.
            2. sum up flexibility-values of all time steps & divide by number of time steps.
            3. multiply this by number of schedules
        :return: flexibility
        """

        # define some example schedules here!
        sa = ["" for x in range(10)]
        sa[0] = "0011000000"
        sa[1] = "1100001110"
        sa[2] = "1110000000"
        sa[3] = "0000001110"
        sa[4] = "1000011110"
        sa[5] = "0011011000"
        sa[6] = "1100011000"
        sa[7] = "0000011110"
        sa[8] = "0000000010"
        sa[9] = "0110011110"

        # for debugging
        for r in range(9):
            steps = len(sa[0])
            noS = len(sa) - r
            added = [float(0.0) for x in range(steps)]

            # zero flexibility if only one schedule possible
            if noS == 1: return 0

            for i in range(steps):  # for each time step
                for s in range(noS):    # sum up MODLVLs
                    added[i] += float(sa[s][i])
                if float(added[i])/float(noS) > 0.5:    # if more ones than zeros for this time step
                    if noS % 2 == 0: added[i] = 1 - float(added[i])/float(noS)  # if even no. of schedules
                    else: added[i] = float(noS - added[i]) / float(noS-1)       # if uneven no. of schedules
                else:
                    if noS % 2 == 0: added[i] = float(added[i])/float(noS)
                    else: added[i] = float(added[i])/float(noS-1)
                added[i] *= 2   # multiply by 2, so maximum flexibility for a time step will be 1

            flexibility = sum(added)/float(steps) * noS     # add up flexibilities of time steps, divide by number of time steps, multiply by no. of schedules
            print 'No of schedules: %.0f' % noS, '- Flexibility: %.3f' % flexibility    # for debugging

        return flexibility
