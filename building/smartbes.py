__author__ = 'Annika Wierichs'

import cplex
import sys
import numpy as np
from bes import Bes


class SmartBes(Bes):  # subclass inherits from class Bes
    def __init__(self, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, objFcn=1, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4, env=None):
        """
        constructor of SmartBes

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

        super(SmartBes, self).__init__(stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, envrnmt=env)

        self.chosenScheduleIndex = -1       # index of currently chosen schedule
        self.chosenSchedule = []            # array containing currently chosen schedule
        self.schedules = list()             # array containing schedules
        self.schedulesSec = list()          # array containing schedules for backup/secondary heater
        self.SOCEnd = list()                # array containing resulting state of charge of thermal storage at the end of the horizon for all possible schedules

        self.noOfSchedules = -1             # current no. of schedules
        self.objFcn = objFcn
        self.solPoolAbsGap = solPoolAbsGap
        self.solPoolRelGap = solPoolRelGap
        self.solPoolIntensity = solPoolIntensity

        self.flexibility = -1               # flexibility for current parameters, needed for ring search in subclass    # todo: clean up (move to other class)

    def getChosenScheduleIndex(self):
        return self.chosenScheduleIndex

    def setChosenScheduleIndex(self, index):
        self.chosenScheduleIndex = index

    def getObjFcn(self):
        return self.objFcn

    def setObjFcn(self, objFcn):
        self.objFcn = objFcn

    def getSolPoolAbsGap(self):
        return self.solPoolAbsGap

    def setSolPoolAbsGap(self, absGap):
        self.solPoolAbsGap = absGap

    def getSolPoolRelGap(self):
        return self.solPoolRelGap

    def setSolPoolRelGap(self, RelGap):
        self.solPoolRelGap = RelGap

    def getSolPoolIntensity(self):
        return self.solPoolIntensity

    def setSolPoolIntensity(self, solPoolIntensity):
        self.solPoolIntensity = solPoolIntensity

    def getSchedules(self):
        return self.schedules

    def getSchedulesSec(self):
        return self.schedulesSec

    def getSOCEnd(self):
        return self.SOCEnd

    def getNoOfSchedules(self):
        """
        :return: no. of current schedules available in solution pool
        """
        return self.noOfSchedules

    def getChosenSchedule(self):
        """
        :return: currently chosen schedule
        """
        return self.chosenSchedule

    def calcSchedulePool(self, fromTime, toTime):
        """
        method creates optimized schedules for given timeframe.
        e.g.:   MODLVL		001110010
                switchOn	_01000010
                switchOff	_00001001
                ETHStorage	XXXXXXXXX
                PTHStorage	_XXXXXXXX

        :param fromTime: start time [s]
        :param toTime: end time [s]
        :param objectiveFcn: sets the criterion that will be optimized; 1: minimize switching events (used gap: absGap)
        :param absGap: absolute gap between best solution and worst solution returned (e.g. if best solution has 4 switching events, worst will have 7 for absGap=3)
        :param relGap: relative gap between best solution and worst solution returned (e.g. solutions can be 30% worse than best solution for relGap=0.3)
        :return: array [no. solutions x no. timesteps]; resulting schedules (0,1... for each timestep in each sol.)
        """

        # gas boiler? no calculation.
        if self.getTER1() == 0:
            self.schedules = []
            self.noOfSchedules = 0
            return []

        # create empty Model
        c = cplex.Cplex()
        c.set_log_stream(None)
        c.set_results_stream(None)
        c.objective.set_sense(c.objective.sense.minimize)

        # todo: add these possible parameters
        #c.parameters.timelimit.set(2e-1)              # sets a time limit to solution pool calculation
        #c.parameters.mip.limits.populate.set(30)      # limits number of solutions
        c.parameters.mip.pool.absgap.set(self.solPoolAbsGap)
        c.parameters.mip.pool.intensity.set(self.solPoolIntensity)  # parameters may be: 1 - 4 (low to high time/memory consumption)
        #c.parameters.threads.set(1) # limit threads to 1 thread (no cplex parallelization)


        # py-variables

        timeSteps = (toTime-fromTime)/self.stepSize + 1   # no. of steps (e.g. hours)
        rangeHorizonFrom1 = range(1, timeSteps+1)         # step array (1,2 ... 24)
        rangeHorizonFrom0 = range(0, timeSteps+1)         # dummy    (0,1,2 ... 24)


        # decision variables

        # modulation level: on=1, off=0
        MODLVL = []
        for s in rangeHorizonFrom0:
            MODLVLName = "MODLVL_"+str(s)
            MODLVL.append(MODLVLName)
        c.variables.add(obj = [0] * len(MODLVL), names = MODLVL,
                        lb = [0] * len(MODLVL), ub = [self.getModlvls1()] * len(MODLVL),
                        types = [c.variables.type.integer] * len(MODLVL))

        # modulation level of secondary heater
        if self.getTER2() == 0:     # gas boiler
            typeMODLVLSec = c.variables.type.semi_continuous
            lbMODLVLSec = 0.2
        elif self.getTER2() < 0:    # electric boiler
            typeMODLVLSec = c.variables.type.binary
            lbMODLVLSec = 0
        else:
            print "TER2 doesn't make sense."
            return -1

        thermalDemand  = [0 for x in rangeHorizonFrom0]
        thermalDemand[1:] = self.getThermalDemandCurve(fromTime, toTime)[1, :]
        _ThermalPower1 = np.append([0], self.getThermalPower1(fromTime, toTime)[1, :])
        allowHeater2 = [0 for x in rangeHorizonFrom0]
        for s in rangeHorizonFrom0:
            #if thermalDemand[s] > abs(self.getNominalThermalPower1() * self.stepSize):
            if thermalDemand[s] > abs(_ThermalPower1[s] * self.stepSize):
                allowHeater2[s] = 1.0
            else:
                allowHeater2[s] = 0.0

        MODLVLSec = []
        for s in rangeHorizonFrom0:
            MODLVLSecName = "MODLVLSec_"+str(s)
            MODLVLSec.append(MODLVLSecName)
        c.variables.add(obj = [0] * len(MODLVLSec), names = MODLVLSec,
                        lb = [allowHeater2[s] * lbMODLVLSec for s in rangeHorizonFrom0], ub = allowHeater2,
                        types = [typeMODLVLSec] * len(MODLVLSec))

        # stored thermal energy
        ETHStorage = []
        for s in rangeHorizonFrom0:
            ETHStorageName = "ETHStorage_"+str(s)
            ETHStorage.append(ETHStorageName)
        c.variables.add(obj = [0] * len(ETHStorage), names = ETHStorage,
                        lb = [self.getSOCmin()*self.getStorageCapacity()] * len(ETHStorage), ub = [self.getSOCmax()*self.getStorageCapacity()] * len(ETHStorage),
                        types = [c.variables.type.continuous] * len(ETHStorage))

        # power flow into thermal storage at time=s. (Positive when thermal power flows into device)
        PTHStorage = []
        thermalDemand = self.getThermalDemandCurve(fromTime, toTime)
        maxThermalPowerDemand = max(thermalDemand[1])/self.stepSize
        _ThermalPower1 = np.append([0], self.getThermalPower1(fromTime, toTime)[1,:])
        _ThermalPower2 = np.append([0], self.getThermalPower2(fromTime, toTime)[1,:])
        for s in rangeHorizonFrom0:
            PTHStorageName = "PTHStorage_"+str(s)
            PTHStorage.append(PTHStorageName)
        c.variables.add(obj = [0] * len(PTHStorage), names = PTHStorage,
                        lb = np.append([0], [-maxThermalPowerDemand] * (len(PTHStorage)-1) ),
                        ub = - (_ThermalPower1 + _ThermalPower2),
                        types = [c.variables.type.continuous] * len(PTHStorage))
                        #lb = [-maxThermalPowerDemand] * len(PTHStorage),
                        #lb = [-maxThermalPowerDemand] * (len(PTHStorage)-1),
                        #ub = [-self.getNominalThermalPower1()] * len(PTHStorage),
                        #ub = -(_ThermalPower1+_ThermalPower2),
                        #types = [c.variables.type.continuous] * len(PTHStorage))

        # 1 if switched on from time t-1 to t (not def. for t=0)
        switchOn = []
        for s in rangeHorizonFrom0:
            switchOnName = "switchOn_"+str(s)
            switchOn.append(switchOnName)
        c.variables.add(obj = [0] * len(switchOn), names = switchOn,
                        lb = [0] * len(switchOn), ub = [1] * len(switchOn),
                        types = [c.variables.type.binary] * len(switchOn))

        # 1 if switched off from time t-1 to t (not def. for t=0)
        switchOff = []
        for s in rangeHorizonFrom0:
            switchOffName = "switchOff_"+str(s)
            switchOff.append(switchOffName)
        c.variables.add(obj = [0] * len(switchOff), names = switchOff,
                        lb = [0] * len(switchOff), ub = [1] * len(switchOff),
                        types = [c.variables.type.binary] * len(switchOff))

        # sum of switching events in switchOn and switchOff. to be minimized.
        switchSum = ["switch_Sum"]
        c.variables.add(obj = [1], names = switchSum,
                        lb = [0], ub = [timeSteps],
                        types = [c.variables.type.integer])


        # constraints

        for t in rangeHorizonFrom1:
            # sync switchOn/Off and MODLVL
            thevars = [MODLVL[t], MODLVL[t-1], switchOn[t], switchOff[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-1, 1])],
                                     senses = ["E"], rhs = [0])
            thevars = [switchOn[t], switchOff[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, 1])],
                                     senses = ["L"], rhs = [1])
            # Restrict the secondary heater to operate only when the primary heater is already running
            thevars = [MODLVLSec[t], MODLVL[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [-1,1])],
                                       senses = ["G"], rhs = [0] )
            # SoCmin <= energy in storage <= SoCmax
            thevars = [ETHStorage[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                     senses = ["G"], rhs = [self.getSOCmin()*self.getStorageCapacity()])
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                     senses = ["L"], rhs = [self.getSOCmax()*self.getStorageCapacity()])
            # energy in storage at time t = energy at time (t-1) + (stepSize * PTHStorage[t])
            thevars = [ETHStorage[t], ETHStorage[t-1], PTHStorage[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-self.stepSize])],
                                     senses = ["E"], rhs = [0])
            # thermal energy produced by main & backup device = thermal demand + thermal energy that is stored in thermal storage
            thevars = [MODLVL[t], MODLVLSec[t], PTHStorage[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [-self.getThermalPower1(fromTime, toTime)[1, t-1] * self.stepSize / self.getModlvls1(), -self.getThermalPower2(fromTime, toTime)[1, t-1] * self.stepSize, -self.stepSize])],
                                     senses = ["E"], rhs = [thermalDemand[1][t-1]])

        # MODLVL at time t=0 = MODLVLini
        thevars = [MODLVL[0]]
        c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                 senses = ["E"], rhs = [round(self.getStateModlvl())])

        # energy in storage at time t=0 = SoCini * storageCapThermal
        if self.getSOC() > self.getSOCmax():
            self.setSOC(self.getSOCmax())
        elif self.getSOC() < self.getSOCmin():
            self.setSOC(self.getSOCmin())
        thevars = [ETHStorage[0]]
        c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                 senses = ["E"], rhs = [self.getSOC() * self.getStorageCapacity()])

        # sum of switching events: switchSum (which is targeted by cplex's objective function [minimizing]) = sum(switchOn) + sum(switchOff)
        sumCoeffs = [1]*2*timeSteps
        sumCoeffs.append(-1)
        thevars = []
        for i in rangeHorizonFrom1:
            thevars.append(switchOn[i])
            thevars.append(switchOff[i])
        thevars.append(switchSum[0])
        c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, sumCoeffs)], senses = ["E"], rhs = [0])

        # solve problem

        pool = c.populate_solution_pool()
        noSol = c.solution.pool.get_num()

        # create and return optimized schedule-array

        self.chosenSchedule = []
        self.chosenScheduleIndex = -1
        self.flexibility = -1
        self.schedules = list()         # create empty multi dim array for schedules
        self.schedulesSec = list()      # create empty multi dim array for schedules
        self.SOCEnd = list()            # create empty array for SOCs
        for n in range(noSol):
            self.schedules.append(c.solution.pool.get_values(n, MODLVL))
            self.schedulesSec.append(c.solution.pool.get_values(n, MODLVLSec))
            self.SOCEnd.append(float(float(c.solution.pool.get_values(n, ETHStorage[-1])) / self.getStorageCapacity()))

        self.noOfSchedules = len(self.schedules)


    def calcSchedulePoolTest(self, fromTime, toTime):
        """
        method creates optimized schedules for given timeframe.
        e.g.:   MODLVL		001110010
                switchOn	_01000010
                switchOff	_00001001
                ETHStorage	XXXXXXXXX
                PTHStorage	_XXXXXXXX

        :param fromTime: start time [s]
        :param toTime: end time [s]
        :param objectiveFcn: sets the criterion that will be optimized; 1: minimize switching events (used gap: absGap)
        :param absGap: absolute gap between best solution and worst solution returned (e.g. if best solution has 4 switching events, worst will have 7 for absGap=3)
        :param relGap: relative gap between best solution and worst solution returned (e.g. solutions can be 30% worse than best solution for relGap=0.3)
        :return: array [no. solutions x no. timesteps]; resulting schedules (0,1... for each timestep in each sol.)
        """

        # todo: add pv system stuff to objective fcn 1

        # gas boiler? no calculation.
        if self.getTER1() == 0:
            self.schedules = []
            self.noOfSchedules = 0
            return []

        # create empty Model
        c = cplex.Cplex()
        c.set_log_stream(None)
        c.set_results_stream(None)
        c.objective.set_sense(c.objective.sense.minimize)

        # todo: add these possible parameters
        #c.parameters.timelimit.set(2e-1)              # sets a time limit to solution pool calculation
        #c.parameters.mip.limits.populate.set(30)      # limits number of solutions
        if self.objFcn is 1:
            c.parameters.mip.pool.absgap.set(self.solPoolAbsGap)
        else:
            c.parameters.mip.pool.relgap.set(self.solPoolRelGap)

        c.parameters.mip.pool.intensity.set(self.solPoolIntensity)  # parameters may be: 1 - 4 (low to high time/memory consumption)
        #c.parameters.threads.set(1) # limit threads to 1 thread (no cplex parallelization)


        # py-variables

        timeSteps = (toTime-fromTime)/self.stepSize + 1   # no. of steps (e.g. hours)
        rangeHorizonFrom1 = range(1, timeSteps+1)         # step array (1,2 ... 24)
        rangeHorizonFrom0 = range(0, timeSteps+1)         # dummy    (0,1,2 ... 24)
        if self.getObjFcn() is 2:
            solarGenerationCurve = self.getOnSitePVGenerationCurve(fromTime, toTime)


        # decision variables

        # modulation level: on=1, off=0
        MODLVL = []
        for s in rangeHorizonFrom0:
            MODLVLName = "MODLVL_"+str(s)
            MODLVL.append(MODLVLName)
        c.variables.add(obj = [0] * len(MODLVL), names = MODLVL,
                        lb = [0] * len(MODLVL), ub = [self.getModlvls1()] * len(MODLVL),
                        types = [c.variables.type.integer] * len(MODLVL))

        # modulation level of secondary heater
        if self.getTER2() == 0:     # gas boiler
            typeMODLVLSec = c.variables.type.semi_continuous
            lbMODLVLSec = 0.2
        elif self.getTER2() < 0:    # electric boiler
            typeMODLVLSec = c.variables.type.binary
            lbMODLVLSec = 0
        else:
            print "TER2 doesn't make sense."
            return -1

        thermalDemand  = [0 for x in rangeHorizonFrom0]
        thermalDemand[1:] = self.getThermalDemandCurve(fromTime, toTime)[1, :]
        allowHeater2 = [0 for x in rangeHorizonFrom0]
        for s in rangeHorizonFrom0:
            if thermalDemand[s] > abs(self.getNominalThermalPower1() * self.stepSize):
                allowHeater2[s] = 1.0
            else:
                allowHeater2[s] = 0.0

        MODLVLSec = []
        for s in rangeHorizonFrom0:
            MODLVLSecName = "MODLVLSec_"+str(s)
            MODLVLSec.append(MODLVLSecName)
        c.variables.add(obj = [0] * len(MODLVLSec), names = MODLVLSec,
                        lb = [allowHeater2[s] * lbMODLVLSec for s in rangeHorizonFrom0], ub = allowHeater2,
                        types = [typeMODLVLSec] * len(MODLVLSec))

        # stored thermal energy
        ETHStorage = []
        for s in rangeHorizonFrom0:
            ETHStorageName = "ETHStorage_"+str(s)
            ETHStorage.append(ETHStorageName)
        c.variables.add(obj = [0] * len(ETHStorage), names = ETHStorage,
                        lb = [self.getSOCmin()*self.getStorageCapacity()] * len(ETHStorage), ub = [self.getSOCmax()*self.getStorageCapacity()] * len(ETHStorage),
                        types = [c.variables.type.continuous] * len(ETHStorage))

        # power flow into thermal storage at time=s. (Positive when thermal power flows into device)
        PTHStorage = []
        thermalDemand = self.getThermalDemandCurve(fromTime, toTime)
        maxThermalPowerDemand = max(thermalDemand[1])/self.stepSize
        for s in rangeHorizonFrom0:
            PTHStorageName = "PTHStorage_"+str(s)
            PTHStorage.append(PTHStorageName)
        c.variables.add(obj = [0] * len(PTHStorage), names = PTHStorage,
                        lb = [-maxThermalPowerDemand] * len(PTHStorage),
                        ub = [-self.getNominalThermalPower1()] * len(PTHStorage),
                        types = [c.variables.type.continuous] * len(PTHStorage))

        if self.getObjFcn() is 1:
            # 1 if switched on from time t-1 to t (not def. for t=0)
            switchOn = []
            for s in rangeHorizonFrom0:
                switchOnName = "switchOn_"+str(s)
                switchOn.append(switchOnName)
            c.variables.add(obj = [0] * len(switchOn), names = switchOn,
                            lb = [0] * len(switchOn), ub = [1] * len(switchOn),
                            types = [c.variables.type.binary] * len(switchOn))

            # 1 if switched off from time t-1 to t (not def. for t=0)
            switchOff = []
            for s in rangeHorizonFrom0:
                switchOffName = "switchOff_"+str(s)
                switchOff.append(switchOffName)
            c.variables.add(obj = [0] * len(switchOff), names = switchOff,
                            lb = [0] * len(switchOff), ub = [1] * len(switchOff),
                            types = [c.variables.type.binary] * len(switchOff))

            # sum of switching events in switchOn and switchOff. to be minimized.
            switchSum = ["switch_Sum"]
            c.variables.add(obj = [1], names = switchSum,
                            lb = [0], ub = [timeSteps],
                            types = [c.variables.type.integer])

        elif self.getObjFcn() is 2:
            # electrical demand from grid
            EELDemandFromGrid = []
            electricalDemand = self.getElectricalDemandCurve(fromTime, toTime)
            maxDemandFromGrid = np.max(electricalDemand[1] - solarGenerationCurve[1] + self.stepSize * abs(self.getNominalElectricalPower1()))		# todo: array sizes?
            minDemandFromGrid = np.min(electricalDemand[1] - solarGenerationCurve[1] - self.stepSize * abs(self.getNominalElectricalPower1()))
            for s in rangeHorizonFrom0:
                EELDemandFromGridName = "EELDemandFromGrid_"+str(s)
                EELDemandFromGrid.append(EELDemandFromGridName)
            c.variables.add(obj = [0] * len(EELDemandFromGrid), names = EELDemandFromGrid,
                            lb = [minDemandFromGrid] * len(EELDemandFromGrid),
                            ub = [maxDemandFromGrid] * len(EELDemandFromGrid),
                            types = [c.variables.type.continuous] * len(EELDemandFromGrid))

            # overall electrical energy needed from grid during timeframe - to be minimized!
            EELDemandFromGridSum = ["EELDemandFromGrid_Sum"]
            maxDemandFromGridSum = np.sum(electricalDemand[1] - solarGenerationCurve[1] + self.stepSize * abs(self.getNominalElectricalPower1()))		# todo: array sizes?
            minDemandFromGridSum = np.sum(electricalDemand[1] - solarGenerationCurve[1] - self.stepSize * abs(self.getNominalElectricalPower1()))
            c.variables.add(obj = [1], names = EELDemandFromGridSum,
                            lb = [minDemandFromGridSum], ub = [maxDemandFromGridSum],
                            types = [c.variables.type.continuous])


        # constraints

        for t in rangeHorizonFrom1:
            if self.getObjFcn() is 1:
                # sync switchOn/Off and MODLVL
                thevars = [MODLVL[t], MODLVL[t-1], switchOn[t], switchOff[t]]
                c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-1, 1])],
                                         senses = ["E"], rhs = [0])
                thevars = [switchOn[t], switchOff[t]]
                c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, 1])],
                                         senses = ["L"], rhs = [1])

            elif self.getObjFcn() is 2:
                # energy demand from grid =     electrical demand
                #                           +   energy consumed by primary heating device (negative for CHP)
                #                           +   energy consumed by secondary heating device (positive for HP, zero for CHP)
                #                           -   solar energy from on site generation
                thevars = [EELDemandFromGrid[t], MODLVL[t], MODLVLSec[t]]
                c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, -self.getNominalElectricalPower1() * self.stepSize / self.getModlvls1(), -self.getNominalElectricalPower2() * self.stepSize / self.getModlvls2() ])],
                                         senses = ["E"], rhs = [electricalDemand[1][t-1] - solarGenerationCurve[1][t-1]])


            # Restrict the secondary heater to operate only when the primary heater is already running
            thevars = [MODLVLSec[t], MODLVL[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [-1,1])],
                                       senses = ["G"], rhs = [0] )
            # SoCmin <= energy in storage <= SoCmax
            thevars = [ETHStorage[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                     senses = ["G"], rhs = [self.getSOCmin()*self.getStorageCapacity()])
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                     senses = ["L"], rhs = [self.getSOCmax()*self.getStorageCapacity()])
            # energy in storage at time t = energy at time (t-1) + (stepSize * PTHStorage[t])
            thevars = [ETHStorage[t], ETHStorage[t-1], PTHStorage[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-self.stepSize])],
                                     senses = ["E"], rhs = [0])
            # thermal energy produced by main & backup device = thermal demand + thermal energy that is stored in thermal storage
            thevars = [MODLVL[t], MODLVLSec[t], PTHStorage[t]]
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [-self.getThermalPower1(fromTime, toTime)[1, t-1] * self.stepSize / self.getModlvls1(), -self.getThermalPower2(fromTime, toTime)[1, t-1] * self.stepSize, -self.stepSize])],
            #c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [-self.getNominalThermalPower1() * self.stepSize / self.getModlvls1(), -self.getNominalThermalPower2() * self.stepSize, -self.stepSize])],
                                     senses = ["E"], rhs = [thermalDemand[1][t-1]])

        # MODLVL at time t=0 = MODLVLini
        thevars = [MODLVL[0]]
        c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                 senses = ["E"], rhs = [round(self.getStateModlvl())])

        # energy in storage at time t=0 = SoCini * storageCapThermal
        if self.getSOC() > self.getSOCmax():
            self.setSOC(self.getSOCmax())
        elif self.getSOC() < self.getSOCmin():
            self.setSOC(self.getSOCmin())
        thevars = [ETHStorage[0]]
        c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                 senses = ["E"], rhs = [self.getSOC() * self.getStorageCapacity()])

        if self.getObjFcn() is 1:
            # sum of switching events: switchSum (which is targeted by cplex's objective function [minimizing]) = sum(switchOn) + sum(switchOff)
            sumCoeffs = [1]*2*timeSteps
            sumCoeffs.append(-1)
            thevars = []
            for i in rangeHorizonFrom1:
                thevars.append(switchOn[i])
                thevars.append(switchOff[i])
            thevars.append(switchSum[0])
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, sumCoeffs)], senses = ["E"], rhs = [0])

        elif self.getObjFcn() is 2:
            # sum of consumed energy taken from grid
            sumCoeffs = [1]*timeSteps
            sumCoeffs.append(-1)
            thevars = []
            for i in rangeHorizonFrom1:
                thevars.append(EELDemandFromGrid[i])
            thevars.append(EELDemandFromGridSum[0])
            c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, sumCoeffs)], senses = ["E"], rhs = [0])


        # solve problem

        pool = c.populate_solution_pool()
        noSol = c.solution.pool.get_num()

        # create and return optimized schedule-array

        self.chosenSchedule = []
        self.chosenScheduleIndex = -1
        self.flexibility = -1
        self.schedules = list()         # create empty multi dim array for schedules
        self.schedulesSec = list()      # create empty multi dim array for schedules
        self.SOCEnd = list()            # create empty array for SOCs
        for n in range(noSol):
            self.schedules.append(c.solution.pool.get_values(n, MODLVL))
            self.schedulesSec.append(c.solution.pool.get_values(n, MODLVLSec))
            self.SOCEnd.append(float(float(c.solution.pool.get_values(n, ETHStorage)[-1]) / float(self.getStorageCapacity())))

        self.noOfSchedules = len(self.schedules)

        # for debugging
        # print "\nSolutions (Number: %d)" % self.noOfSchedules
        # print "Nom. th Power:", self.getNominalThermalPower1()
        # print "Stor Cap:", self.getStorageCapacity()
        # print "StorIni", self.getSOC()
        # print "Thermal demand: ", self.getThermalDemandCurve(fromTime, toTime)[1]
        # for n in range(self.noOfSchedules):
        #     for j in rangeHorizonFrom0:
        #         print '%.0f' % abs(self.schedules[n][j]),
        #         sys.stdout.softspace = 0
        #     print " End:", self.getSOCEnd()[n]
        #     # for j in rangeHorizonFrom0:
        #     #     print '%.0f' % abs(self.schedulesSec[n][j]),
        #     #     sys.stdout.softspace = 0
        #     # print "\n"
        # print solarGenerationCurve
