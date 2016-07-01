__author__ = 'Annika Wierichs'

#import cplex
import sys
import numpy as np
import xlwt
from building.besagent import BesAgent

import aiomas
import asyncio


class SmartBesAgent(BesAgent):  # subclass inherits from class Bes
    def __init__(self, container, name, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, env=None, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4):
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

        super(SmartBesAgent, self).__init__(container, name, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, env)

        # todo: choose objFcn

        # if self.PVSystem is None:
        #     self.objFcn = 1
        # else:
        #     self.objFcn = 2

        if self.getNominalElectricalPower1() > 0:   # HP
            self.objFcn = 1
        else:                                       # CHP
            self.objFcn = 2

        # self.c = cplex.Cplex()      # cplex MIP model container

        self.solPoolAbsGap = solPoolAbsGap
        self.solPoolRelGap = solPoolRelGap
        self.solPoolIntensity = solPoolIntensity

        self.schedule = []
        self.scheduleSec = []

        # DECENTRALIZED:
        # variable definitions for solution pool

        self.poolChosenScheduleIndex = -1       # index of currently chosen schedule
        self.poolSchedules = np.array([])            # array containing schedules
        self.poolSchedulesSec = np.array([])          # array containing schedules for backup/secondary heater
        self.poolETHStorage = np.array([])               # array containing resulting state of charge of thermal storage at the end of the horizon for all possible schedules
        self.poolNoOfSchedules = -1             # current no. of schedules
        self.poolOptimizedValues = np.array([])

        # self.poolFlexibility = -1               # flexibility for current parameters, needed for ring search in subclass    # todo: clean up (move to other class)

        self.previousDesyncIterationLoad = np.array([])   # to temporarily save previously added load
        self.previousDesyncIterationBest = -1    # to temporarily save result for previously chosen best schedule

        # CENTRALIZED:
        # variable definitions for local optimization creating only one solution
        self.optimizedCriterionValue = -1
        self.locallyOptimalSchedule = []
        self.locallyOptimalScheduleSec = []

        # decision variables' names (to retrieve solutions from within another function)
        self.MODLVL = []
        self.MODLVLSec = []
        self.ETHStorage = []
        self.PTHStorage = []

        self.switchOn = []
        self.switchOff = []
        self.switchSum = []

        self.EELGrid = []
        self.EELGrid_Dmnd = []
        self.EELGrid_Feed = []
        self.EELGrid_FeedOrDmnd_Sum = []
        self.EELGrid_FeedOrDmnd_Sum = []

    @asyncio.coroutine
    def run(self, addr):
        """The agent's "main" function."""
        remote_agent = yield from self.container.connect(addr)
        ret = yield from remote_agent.service(42)
        print('%s got %s from %s' % (self.name, ret, addr))

    @aiomas.expose
    def service(self, value):
        """Exposed function that can be called by remote agents."""
        return value




    # def setMatchingObjFcn(self, fromTime, toTime):
    #     """
    #     sets the matching objFcn for HPs, depeding on electrical feed
    #     :param fromTime: from time in sec
    #     :param toTime: to time in sec
    #     """
    #
    #     # if BES is a HP and is also equipped with a pv system...
    #     if self.getNominalElectricalPower1() > 0 and self.PVSystem is not None:
    #         # get electrical demand from grid (pv generation subtracted)
    #         extElecDmnd = np.array(self.getExternalElectricalDemandCurve(fromTime, toTime)[1, :])
    #         # if pv system generates more electrical energy than required to cover electrical demand at any time t, use objFcn 2
    #         if np.any(extElecDmnd < 0):
    #             self.setObjFcn(2)
    #         else:
    #             self.setObjFcn(1)
    #
    # def createCplexModel(self, fromTime, toTime):
    #     # create empty Model
    #     self.c = cplex.Cplex()
    #     #self.c.set_log_stream(None)
    #     #self.c.set_results_stream(None)
    #
    #     self.c.objective.set_sense(self.c.objective.sense.minimize)
    #
    #     self.c.parameters.mip.pool.replace.set(2)
    #     self.c.parameters.timelimit.set(5)                  # sets a time limit to calculation
    #     self.c.parameters.mip.limits.populate.set(100)      # limits number of solutions
    #
    #     self.c.parameters.mip.pool.intensity.set(self.solPoolIntensity)  # parameters may be: 1 - 4 (low to high time/memory consumption)
    #
    #     if self.objFcn is 1:
    #         self.c.parameters.mip.pool.absgap.set(self.getSolPoolAbsGap())
    #     elif self.objFcn is 2:
    #         self.c.parameters.mip.pool.relgap.set(self.getSolPoolRelGap())
    #
    #     #self.c.parameters.threads.set(1) # limit threads to 1 thread (no cplex parallelization)
    #
    #
    #     # py-variables
    #
    #     timeSteps = (toTime-fromTime)/self.stepSize + 1   # no. of steps (e.g. hours)
    #     rangeHorizonFrom1 = range(1, timeSteps+1)         # step array (1,2 ... 24)
    #     rangeHorizonFrom0 = range(0, timeSteps+1)         # dummy    (0,1,2 ... 24)
    #     thermalPowerCurve1 = self.getThermalPower1(fromTime, toTime)[1, :]
    #     thermalPowerCurve2 = self.getThermalPower2(fromTime, toTime)[1, :]
    #     if self.getObjFcn() is 2:
    #         onSitePVGenerationCurve = self.getOnSitePVGenerationCurve(fromTime, toTime)
    #
    #     # decision variables
    #
    #     # modulation level: on=1, off=0
    #     self.MODLVL = []
    #     for s in rangeHorizonFrom0:
    #         MODLVLName = "MODLVL_"+str(s)
    #         self.MODLVL.append(MODLVLName)
    #     self.c.variables.add(obj = [0] * len(self.MODLVL), names = self.MODLVL,
    #                     lb = [0] * len(self.MODLVL), ub = [self.getModlvls1()] * len(self.MODLVL),
    #                     types = [self.c.variables.type.integer] * len(self.MODLVL))
    #
    #     # modulation level of secondary heater
    #     if self.getTER2() == 0:     # gas boiler
    #         typeMODLVLSec = self.c.variables.type.semi_continuous
    #         lbMODLVLSec = 0.2
    #     elif self.getTER2() < 0:    # electric boiler
    #         typeMODLVLSec = self.c.variables.type.binary
    #         lbMODLVLSec = 0
    #     else:
    #         print("TER2 doesn't make sense.")
    #         return -1
    #
    #     thermalDemand  = [0 for x in rangeHorizonFrom0]
    #     thermalDemand[1:] = self.getThermalDemandCurve(fromTime, toTime)[1, :]
    #     _ThermalPower1 = np.append([0], self.getThermalPower1(fromTime, toTime)[1, :])
    #     allowHeater2 = [0 for x in rangeHorizonFrom0]
    #     for s in rangeHorizonFrom0:
    #         # print("fromTime: ", fromTime, "toTime: ", toTime ,"s: ", s, "rangeHorizonFrom0: ", len(rangeHorizonFrom0))
    #         if thermalDemand[s] > abs(_ThermalPower1[s] * self.stepSize):
    #             allowHeater2[s] = 1.0
    #         else:
    #             allowHeater2[s] = 0.0
    #
    #     self.MODLVLSec = []
    #     for s in rangeHorizonFrom0:
    #         MODLVLSecName = "MODLVLSec_"+str(s)
    #         self.MODLVLSec.append(MODLVLSecName)
    #     self.c.variables.add(obj = [0] * len(self.MODLVLSec), names = self.MODLVLSec,
    #                     lb = [allowHeater2[s] * lbMODLVLSec for s in rangeHorizonFrom0], ub = allowHeater2,
    #                     types = [typeMODLVLSec] * len(self.MODLVLSec))
    #
    #     # stored thermal energy
    #     self.ETHStorage = []
    #     for s in rangeHorizonFrom0:
    #         ETHStorageName = "ETHStorage_"+str(s)
    #         self.ETHStorage.append(ETHStorageName)
    #     self.c.variables.add(obj = [0] * len(self.ETHStorage), names = self.ETHStorage,
    #                     lb = [self.getSOCmin()*self.getStorageCapacity()] * len(self.ETHStorage),
    #                     ub = [self.getSOCmax()*self.getStorageCapacity()] * len(self.ETHStorage),
    #                     types = [self.c.variables.type.continuous] * len(self.ETHStorage))
    #
    #     # power flow into thermal storage at time=s. (Positive when thermal power flows into device)
    #     self.PTHStorage = []
    #     _ThermalPower1 = np.append([0], self.getThermalPower1(fromTime, toTime)[1,:])
    #     _ThermalPower2 = np.append([0], self.getThermalPower2(fromTime, toTime)[1,:])
    #     thermalDemand = self.getThermalDemandCurve(fromTime, toTime)
    #     maxThermalPowerDemand = max(thermalDemand[1])/self.stepSize
    #     for s in rangeHorizonFrom0:
    #         PTHStorageName = "PTHStorage_"+str(s)
    #         self.PTHStorage.append(PTHStorageName)
    #     self.c.variables.add(obj = [0] * len(self.PTHStorage), names = self.PTHStorage,
    #                     lb = np.append([0], [-maxThermalPowerDemand] * (len(self.PTHStorage)-1) ),
    #                     ub = - (_ThermalPower1 + _ThermalPower2),
    #                     types = [self.c.variables.type.continuous] * len(self.PTHStorage))
    #
    #     # =============================================================
    #     # Objectives
    #     # =============================================================
    #
    #     if self.getObjFcn() is 1:
    #         # 1 if switched on from time t-1 to t (not def. for t=0)
    #         self.switchOn = []
    #         for s in rangeHorizonFrom0:
    #             switchOnName = "switchOn_"+str(s)
    #             self.switchOn.append(switchOnName)
    #         self.c.variables.add(obj = [0] * len(self.switchOn), names = self.switchOn,
    #                         lb = [0] * len(self.switchOn), ub = [1] * len(self.switchOn),
    #                         types = [self.c.variables.type.binary] * len(self.switchOn))
    #
    #         # 1 if switched off from time t-1 to t (not def. for t=0)
    #         self.switchOff = []
    #         for s in rangeHorizonFrom0:
    #             switchOffName = "switchOff_"+str(s)
    #             self.switchOff.append(switchOffName)
    #         self.c.variables.add(obj = [0] * len(self.switchOff), names = self.switchOff,
    #                         lb = [0] * len(self.switchOff), ub = [1] * len(self.switchOff),
    #                         types = [self.c.variables.type.binary] * len(self.switchOff))
    #
    #         # sum of switching events in switchOn and switchOff. to be minimized.
    #         self.switchSum = ["switch_Sum"]
    #         self.c.variables.add(obj = [1], names = self.switchSum,
    #                         lb = [0], ub = [timeSteps],
    #                         types = [self.c.variables.type.integer])
    #
    #     elif self.getObjFcn() is 2:
    #
    #         # calculate bounds
    #         electricalDemand = self.getElectricalDemandCurve(fromTime, toTime)
    #         minEELGrid = electricalDemand[1] + onSitePVGenerationCurve[1] - self.stepSize * abs(self.getNominalElectricalPower1()) - self.stepSize * abs(self.getNominalElectricalPower2())
    #         maxEELGrid = electricalDemand[1] + onSitePVGenerationCurve[1] + self.stepSize * abs(self.getNominalElectricalPower1()) + self.stepSize * abs(self.getNominalElectricalPower2())
    #         minEELGrid = np.append([0], minEELGrid)
    #         maxEELGrid = np.append([0], maxEELGrid)
    #
    #         # if maximum EELGrid is < 0 or minimum EELGrid is > 0, define proper upper bounds for feed & dmnd variables
    #         dmndUB = [ maxEELGrid[t] if maxEELGrid[t] > 0 else 0 for t in rangeHorizonFrom0]
    #         feedUB = [-minEELGrid[t] if minEELGrid[t] < 0 else 0 for t in rangeHorizonFrom0]
    #         # also define a proper upper bound for feed sum variable
    #         dmndSumUB = np.sum(dmndUB)
    #         feedSumUB = np.sum(feedUB)
    #
    #         # overall electrical demand from / feed into grid
    #         self.EELGrid = []
    #         for s in rangeHorizonFrom0:
    #             EELGridName = "EELGrid_"+str(s)
    #             self.EELGrid.append(EELGridName)
    #         self.c.variables.add(obj = [0] * len(self.EELGrid), names = self.EELGrid,
    #                         lb = minEELGrid,
    #                         ub = maxEELGrid,
    #                         types = [self.c.variables.type.continuous] * len(self.EELGrid))
    #
    #         # electrical demand from grid
    #         self.EELGrid_Dmnd = []
    #         for s in rangeHorizonFrom0:
    #             EELGrid_DmndName = "EELGrid_Dmnd_"+str(s)
    #             self.EELGrid_Dmnd.append(EELGrid_DmndName)
    #         self.c.variables.add(obj = [0] * len(self.EELGrid_Dmnd), names = self.EELGrid_Dmnd,
    #                         lb = [0] * len(self.EELGrid_Dmnd),
    #                         ub = dmndUB,
    #                         types = [self.c.variables.type.continuous] * len(self.EELGrid_Dmnd))
    #
    #         # electrical feed into grid
    #         self.EELGrid_Feed = []
    #         for s in rangeHorizonFrom0:
    #             EELGrid_FeedName = "EELGrid_Feed_"+str(s)
    #             self.EELGrid_Feed.append(EELGrid_FeedName)
    #         self.c.variables.add(obj = [0] * len(self.EELGrid_Feed), names = self.EELGrid_Feed,
    #                         lb = [0] * len(self.EELGrid_Feed),
    #                         ub = feedUB,
    #                         types = [self.c.variables.type.continuous] * len(self.EELGrid_Feed))
    #
    #         if self.getNominalElectricalPower1() > 0:
    #             # for HPs: sum of overall energy feed into grid --> to be minimized!
    #             self.EELGrid_FeedOrDmnd_Sum = ["EELGrid_FeedOrDmnd_Sum"]
    #             self.c.variables.add(obj = [1], names = self.EELGrid_FeedOrDmnd_Sum,
    #                             lb = [0],
    #                             ub = [feedSumUB],
    #                             types = [self.c.variables.type.continuous])
    #
    #         elif self.getNominalElectricalPower1() < 0:
    #             # for CHPs: sum of overall energy demand from grid --> to be minimized!
    #             self.EELGrid_FeedOrDmnd_Sum = ["EELGrid_FeedOrDmnd_Sum"]
    #             self.c.variables.add(obj = [1], names = self.EELGrid_FeedOrDmnd_Sum,
    #                             lb = [0],
    #                             ub = [dmndSumUB],
    #                             types = [self.c.variables.type.continuous])
    #
    #
    #     # =============================================================
    #     # Constraints
    #     # =============================================================
    #
    #     for t in rangeHorizonFrom1:
    #         if self.getObjFcn() is 1:
    #             # sync switchOn/Off and MODLVL
    #             thevars = [self.MODLVL[t], self.MODLVL[t-1], self.switchOn[t], self.switchOff[t]]
    #             self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-1, 1])],
    #                                      senses = ["E"], rhs = [0])
    #             thevars = [self.switchOn[t], self.switchOff[t]]
    #             self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, 1])],
    #                                      senses = ["L"], rhs = [1])
    #
    #         # Electrical energy balance
    #         elif self.getObjFcn() is 2:
    #             # energy demand from grid =     electrical demand
    #             #                           +   energy consumed by primary heating device (negative for CHP)
    #             #                           +   energy consumed by secondary heating device (positive for HP, zero for CHP)
    #             #                           -   solar energy from on site generation
    #             thevars = [self.EELGrid[t], self.MODLVL[t], self.MODLVLSec[t]]
    #             self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, -self.getNominalElectricalPower1() * self.stepSize / self.getModlvls1(), -self.getNominalElectricalPower2() * self.stepSize ])],
    #                                      senses = ["E"], rhs = [electricalDemand[1][t-1] + onSitePVGenerationCurve[1][t-1]])
    #
    #             # EELGrid = EELGrid_Dmnd - EELGrid_Feed (for all time steps t)
    #             thevars = [self.EELGrid[t], self.EELGrid_Dmnd[t], self.EELGrid_Feed[t]]
    #             self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, -1, 1])],
    #                                      senses = ["E"], rhs = [0])
    #
    #
    #         # Restrict the secondary heater to operate only when the primary heater is already running
    #         thevars = [self.MODLVLSec[t], self.MODLVL[t]]
    #         self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [-1,1])],
    #                                    senses = ["G"], rhs = [0] )
    #         # SoCmin <= energy in storage <= SoCmax
    #         # thevars = [self.ETHStorage[t]]
    #         # self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
    #         #                          senses = ["G"], rhs = [self.getSOCmin()*self.getStorageCapacity()])
    #         # self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
    #         #                          senses = ["L"], rhs = [self.getSOCmax()*self.getStorageCapacity()])
    #         # energy in storage at time t = energy at time (t-1) + (stepSize * PTHStorage[t])
    #         thevars = [self.ETHStorage[t], self.ETHStorage[t-1], self.PTHStorage[t]]
    #         self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-self.stepSize])],
    #                                  senses = ["E"], rhs = [0])
    #         # thermal energy produced by main & backup device (dynamic thermal power!) = thermal demand + thermal energy that is stored in thermal storage
    #         thevars = [self.MODLVL[t], self.MODLVLSec[t], self.PTHStorage[t]]
    #         self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [-thermalPowerCurve1[t-1] * self.stepSize / self.getModlvls1(), -thermalPowerCurve2[t-1] * self.stepSize, -self.stepSize])],
    #                                  senses = ["E"], rhs = [thermalDemand[1][t-1]])
    #
    #     # MODLVL at time t=0 = MODLVLini
    #     thevars = [self.MODLVL[0]]
    #     self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
    #                              senses = ["E"], rhs = [round(self.getStateModlvl())])
    #
    #     # energy in storage at time t=0 = SoCini * storageCapThermal
    #     if self.getSOC() > self.getSOCmax():
    #         self.setSOC(self.getSOCmax())
    #     elif self.getSOC() < self.getSOCmin():
    #         self.setSOC(self.getSOCmin())
    #     thevars = [self.ETHStorage[0]]
    #     self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
    #                              senses = ["E"], rhs = [self.getSOC() * self.getStorageCapacity()])
    #
    #     if self.getObjFcn() is 1:
    #
    #         # sum of switching events: switchSum (which is targeted by cplex's objective function [minimizing]) = sum(switchOn) + sum(switchOff)
    #         sumCoeffs = [1]*2*timeSteps
    #         sumCoeffs.append(-1)
    #         thevars = []
    #         for i in rangeHorizonFrom1:
    #             thevars.append(self.switchOn[i])
    #             thevars.append(self.switchOff[i])
    #         thevars.append(self.switchSum[0])
    #         self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, sumCoeffs)], senses = ["E"], rhs = [0])
    #
    #     elif self.getObjFcn() is 2:
    #
    #         if self.getNominalElectricalPower1() > 0:
    #             # for HPs: define sum of energy feed into grid
    #             sumCoeffs = [1]*timeSteps
    #             sumCoeffs.append(-1)
    #             thevars = []
    #             for i in rangeHorizonFrom1:
    #                 thevars.append(self.EELGrid_Feed[i])
    #             thevars.append(self.EELGrid_FeedOrDmnd_Sum[0])
    #             self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, sumCoeffs)], senses = ["E"], rhs = [0])
    #
    #         elif self.getNominalElectricalPower1() < 0:
    #             # for CHPs: define sum of energy demand from grid
    #             sumCoeffs = [1]*timeSteps
    #             sumCoeffs.append(-1)
    #             thevars = []
    #             for i in rangeHorizonFrom1:
    #                 thevars.append(self.EELGrid_Dmnd[i])
    #             thevars.append(self.EELGrid_FeedOrDmnd_Sum[0])
    #             self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, sumCoeffs)], senses = ["E"], rhs = [0])
    #
    #
    #     if self.getObjFcn() is 1:
    #         optimizedCriterion = self.switchSum
    #     elif self.getObjFcn() is 2:
    #         optimizedCriterion = self.EELGrid_FeedOrDmnd_Sum
    #
    #     return optimizedCriterion
    #
    # # ==================================================================================================================
    # # methods for centralized coordination algorithms
    # # ==================================================================================================================
    #
    # def calcOptimalSchedule(self, fromTime, toTime):
    #
    #     # gas boiler? no calculation.
    #     if self.getTER1() == 0:
    #         return []
    #
    #     # for HPs, decide which objFcn to use for this time frame
    #     self.setMatchingObjFcn(fromTime, toTime)
    #
    #     # request the name of the optimized DV
    #     optimizedCriterion = self.createCplexModel(fromTime, toTime)
    #
    #     # Restrict threads to 1
    #     self.c.parameters.threads.set(1)
    #
    #     # solve problem
    #     self.c.parameters.dettimelimit.set(10000.0)
    #     self.c.solve()
    #
    #     # set locally optimal schedules (this does not set the real operation schedule variable "schedule"/"scheduleSec")
    #     self.setLocallyOptimalSchedule(self.c.solution.get_values(self.MODLVL))
    #     self.setLocallyOptimalScheduleSec(self.c.solution.get_values(self.MODLVLSec))
    #
    #     self.optimizedCriterionValue = self.c.solution.get_values(optimizedCriterion)[0]
    #     if self.optimizedCriterionValue < 0:
    #         self.optimizedCriterionValue = 0
    #
    #     # for debugging
    #     # for j in range(len(self.poolChosenSchedule)):
    #     #     print '%.0f' % abs(self.poolChosenSchedule[j]),
    #     # print "Optimal schedule calculation"
    #     # print "Nom. th Power:", self.getNominalThermalPower1(), "\tStor Cap:", self.getStorageCapacity(), "SOC End:", self.getSOC(),
    #     # print "Thermal demand: ", self.getThermalDemandCurve(fromTime, toTime)[1]
    #     # for n in range(self.poolNoOfSchedules):
    #     #     for j in rangeHorizonFrom0:
    #     #         print '%.0f' % abs(self.poolSchedules[n][j]),
    #     #         sys.stdout.softspace = 0
    #     #     print " End:", self.getSOCEnd()[n]
    #     #     # for j in rangeHorizonFrom0:
    #     #     #     print '%.0f' % abs(self.poolSchedulesSec[n][j]),
    #     #     #     sys.stdout.softspace = 0
    #     #     # print "\n"
    #
    # def verifyOptimizationInExcel(self, fromTime, toTime, c):
    #     """
    #     method creates and saves an excel sheet for the optimization (for either of the two ocjFcns)
    #     :param fromTime: from time in seconds
    #     :param toTime: to time in seconds
    #     :param c: cplex model (to retrieve solutions)
    #     :return: nothing (excel sheet will be saved to "excelVerificationObjFcn2" folder)
    #     """
    #     if self.getNominalElectricalPower1() is 0:
    #         return -1
    #
    #     # set file name
    #     if self.getNominalElectricalPower1() > 0:
    #         fileName = 'HP-day-' + str(fromTime / 86400)
    #     else:
    #         fileName = 'CHP-day-' + str(fromTime / 86400)
    #
    #     # set up excel worksheet
    #     wb = xlwt.Workbook()
    #     ws = wb.add_sheet("test", cell_overwrite_ok=True)
    #
    #     for iC in range(20):
    #         ws.col(iC).width = 256*15
    #
    #     decimal_style = xlwt.XFStyle()
    #     decimal_style.num_format_str = '#,##0.00'
    #
    #
    #     _columnCounter = 0
    #
    #     # time
    #     _time = range(fromTime, toTime+self.stepSize, self.stepSize)
    #     ws.write(0, _columnCounter, "Time")
    #     for iR in range(len(_time)):
    #         ws.write(iR+2, _columnCounter, _time[iR])
    #
    #     # nominal power 1
    #     _nomElPower1 = self.getNominalElectricalPower1()
    #     _storCap = self.getStorageCapacity()
    #     ws.write(len(_time)+5, _columnCounter, "Nom El Power 1:")
    #     ws.write(len(_time)+6, _columnCounter, "Storage Cap:")
    #     _columnCounter += 1
    #
    #
    #     # MODLVL
    #     _modlvl = self.c.solution.get_values(self.MODLVL)
    #     ws.write(0, _columnCounter, "MODLVL")
    #     for iR in range(len(_modlvl)):
    #         ws.write(iR+1, _columnCounter, _modlvl[iR])
    #
    #     ws.write(len(_time)+5, _columnCounter, _nomElPower1, decimal_style)
    #     ws.write(len(_time)+6, _columnCounter, _storCap, decimal_style)
    #     _columnCounter += 1
    #
    #     # MODLVLSec
    #     _modlvlsec = self.c.solution.get_values(self.MODLVLSec)
    #     ws.write(0, _columnCounter, "MODLVLSec")
    #     for iR in range(len(_modlvlsec)):
    #         ws.write(iR+1, _columnCounter, _modlvlsec[iR])
    #     _columnCounter += 1
    #
    #     # ETHStorage
    #     _ethstorage = self.c.solution.get_values(self.ETHStorage)
    #     ws.write(0, _columnCounter, "ETHStorage")
    #     for iR in range(len(_ethstorage)):
    #         ws.write(iR+1, _columnCounter, _ethstorage[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     # PTHStorage
    #     _pthstorage = self.c.solution.get_values(self.PTHStorage)
    #     ws.write(0, _columnCounter, "PTHStorage")
    #     for iR in range(len(_pthstorage)):
    #         ws.write(iR+1, _columnCounter, _pthstorage[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     if self.objFcn is 1:
    #
    #         # switchOn
    #         _switchon = self.c.solution.get_values(self.switchOn)
    #         ws.write(0, _columnCounter, "switchOn")
    #         for iR in range(len(_switchon)):
    #             ws.write(iR+1, _columnCounter, _switchon[iR])
    #         _columnCounter += 1
    #
    #         # switchOff
    #         _switchoff = self.c.solution.get_values(self.switchOff)
    #         ws.write(0, _columnCounter, "switchOff")
    #         for iR in range(len(_switchoff)):
    #             ws.write(iR+1, _columnCounter, _switchoff[iR])
    #         _columnCounter += 1
    #
    #         # switchSum (same column as MODLVL)
    #         _switchsum = self.c.solution.get_values(self.switchSum)
    #         ws.write(len(_switchoff)+2, 1, _switchsum[0])
    #
    #     elif self.objFcn is 2:
    #
    #         # EELGrid
    #         _eelgrid = self.c.solution.get_values(self.EELGrid)
    #         ws.write(0, _columnCounter, "EELGrid")
    #         for iR in range(len(_eelgrid)):
    #             ws.write(iR+1, _columnCounter, _eelgrid[iR], decimal_style)
    #         _columnCounter += 1
    #
    #         # EELGrid_Dmnd
    #         _eelgriddmnd = self.c.solution.get_values(self.EELGrid_Dmnd)
    #         ws.write(0, _columnCounter, "EELGrid_Dmnd")
    #         for iR in range(len(_eelgriddmnd)):
    #             ws.write(iR+1, _columnCounter, _eelgriddmnd[iR], decimal_style)
    #         _columnCounter += 1
    #
    #         # EELGrid_Feed
    #         _eelgridfeed = self.c.solution.get_values(self.EELGrid_Feed)
    #         ws.write(0, _columnCounter, "EELGrid_Feed")
    #         for iR in range(len(_eelgridfeed)):
    #             ws.write(iR+1, _columnCounter, _eelgridfeed[iR], decimal_style)
    #
    #         if self.getNominalElectricalPower1() > 0:
    #             # HP: EELGrid_Feed_Sum
    #             _eelgridfeedsum = self.c.solution.get_values(self.EELGrid_FeedOrDmnd_Sum)
    #             ws.write(len(_eelgrid)+4, _columnCounter, _eelgridfeedsum[0], decimal_style)
    #
    #         elif self.getNominalElectricalPower1() < 0:
    #             # CHP: EELGrid_Dmnd_Sum
    #             _eelgriddmndsum = self.c.solution.get_values(self.EELGrid_FeedOrDmnd_Sum)
    #             ws.write(len(_eelgrid)+4, _columnCounter-1, _eelgriddmndsum[0], decimal_style)
    #
    #         _columnCounter += 1
    #
    #     # thermalDemand
    #     _thermaldemand = self.getThermalDemandCurve(fromTime, toTime)[1, :]
    #     ws.write(0, _columnCounter, "thermalDemand")
    #     for iR in range(len(_thermaldemand)):
    #         ws.write(iR+2, _columnCounter, _thermaldemand[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     # thermalPower1
    #     _thermalpower1 = self.getThermalPower1(fromTime, toTime)[1, :]
    #     ws.write(0, _columnCounter, "thermalPower1")
    #     for iR in range(len(_thermalpower1)):
    #         ws.write(iR+2, _columnCounter, _thermalpower1[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     # thermalPower2
    #     _thermalpower2 = self.getThermalPower2(fromTime, toTime)[1, :]
    #     ws.write(0, _columnCounter, "thermalPower2")
    #     for iR in range(len(_thermalpower2)):
    #         ws.write(iR+2, _columnCounter, _thermalpower2[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     # electricalDemand
    #     _electricaldemand = self.getElectricalDemandCurve(fromTime, toTime)[1, :]
    #     ws.write(0, _columnCounter, "electricalDemand")
    #     for iR in range(len(_electricaldemand)):
    #         ws.write(iR+2, _columnCounter, _electricaldemand[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     # onSitePVGeneration
    #     _onsitepvgeneration = self.getOnSitePVGenerationCurve(fromTime, toTime)[1, :]
    #     ws.write(0, _columnCounter, "onSitePVGen")
    #     for iR in range(len(_onsitepvgeneration)):
    #         ws.write(iR+2, _columnCounter, _onsitepvgeneration[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     # additional info for graph creation
    #
    #     # electrical demand less pv generation
    #     _elecdmndlesspv = _electricaldemand + _onsitepvgeneration
    #     ws.write(0, _columnCounter, "elecDmndLessPV")
    #     for iR in range(len(_elecdmndlesspv)):
    #         ws.write(iR+2, _columnCounter, _elecdmndlesspv[iR], decimal_style)
    #     _columnCounter += 1
    #
    #     # energy consumed/produced by primary & secondary heater
    #     _hsenergy = np.array(_modlvl[1:]) * self.getNominalElectricalPower1() * self.stepSize + np.array(_modlvlsec[1:]) * self.getNominalElectricalPower2() * self.stepSize
    #     print(_hsenergy)
    #     ws.write(0, _columnCounter, "HSEnergy")
    #     for iR in range(len(_hsenergy)):
    #         ws.write(iR+2, _columnCounter, _hsenergy[iR], decimal_style)
    #     _columnCounter += 1
    #
    #
    #
    #     # wb.save('tempTest/' + fileName + '.xls')
    #     wb.save('excelVerificationObjFcn2/' + fileName + '.xls')
    #
    # # ==================================================================================================================
    # # methods for decentralized coordination algorithms
    # # ==================================================================================================================
    #
    # def calcAbsGap(self, fromTime, toTimeH, solveFirst):
    #     """
    #     calculate absolute gap of solution pool (calculations needed for objFcn 2)
    #     :param fromTime: from time in sec
    #     :param toTimeH: to time in sec
    #     :return:
    #     """
    #     # set solution pool values
    #     if self.objFcn is 1:
    #         return self.getSolPoolAbsGap()
    #     elif self.objFcn is 2:
    #         if solveFirst is True:
    #             # run optimization once so that the optimized criterion value is calculated for this time frame
    #             self.calcOptimalSchedule(fromTime, toTimeH)
    #         # calculate local fluctuations curve (Dmnd - PV generation)
    #         lclFluctuationsCurve = self.getElectricalDemandCurve(fromTime, toTimeH) + self.getOnSitePVGenerationCurve(fromTime, toTimeH)  # PV is negative
    #         # HP
    #         if self.getNominalElectricalPower1() > 0:
    #             # feed only: sum of energy FEED (= negative demand) into grid, not including DEMAND from grid
    #             lclFlucFeedOnly = np.abs(np.sum(np.where(lclFluctuationsCurve < 0, lclFluctuationsCurve, 0)))       # abs to get positive value
    #             # optimal reduction in energy feed into grid: amount of energy by which the feed into grid can be reduced by scheduling the HP optimally
    #             optimalFeedReduction = lclFlucFeedOnly - self.getOptimizedCriterionValue()
    #             # find abs gap by calculating *relGap* (e.g. 20 %) of the optimal feed reduction
    #             feedAbsGap = optimalFeedReduction * self.getSolPoolRelGap()
    #             # finally set solution pool value
    #             #print "\n\nFeed Abs Gap:", feedAbsGap, "\nOptimal Feed Reduction:", optimalFeedReduction, "\nOptimal (minimized) Feed into Grid:", self.getOptimizedCriterionValue()
    #             return feedAbsGap
    #         # CHP
    #         else:
    #             # demand only: sum of energy DEMAND from grid, not including FEED into grid (= negative demand)
    #             lclFlucDmndOnly = np.sum(np.where(lclFluctuationsCurve > 0, lclFluctuationsCurve, 0))
    #             # optimal reduction in energy demand from grid: amount of energy by which the demand from grid can be reduced by scheduling the CHP optimally
    #             optimalDmndReduction = lclFlucDmndOnly - self.getOptimizedCriterionValue()
    #             # find abs gap by calculating *relGap* (e.g. 20 %) of the optimal demand reduction
    #             dmndAbsGap = optimalDmndReduction * self.getSolPoolRelGap()
    #             # finally set solution pool value
    #             #print "\n\nDemand Abs Gap:", dmndAbsGap, "\nOptimal Demand Reduction:", optimalDmndReduction, "\nOptimal (minimized) Demand from Grid:", self.getOptimizedCriterionValue()
    #             return dmndAbsGap
    #
    # def calcSchedulePool(self, fromTime, toTimeH):
    #     """
    #     method creates optimized schedules for given timeframe.
    #     e.g.:   MODLVL		001110010
    #             switchOn	_01000010
    #             switchOff	_00001001
    #             ETHStorage	XXXXXXXXX
    #             PTHStorage	_XXXXXXXX
    #
    #     :param fromTime: start time [s]
    #     :param toTimeH: end time [s]
    #     """
    #
    #     # gas boiler? no calculation.
    #     if self.getTER1() == 0:
    #         self.poolSchedules = []
    #         self.poolNoOfSchedules = 0
    #         return []
    #
    #     self.setMatchingObjFcn(fromTime, toTimeH)
    #
    #     # request some of the variable name strings from function
    #     optimizedCriterion = self.createCplexModel(fromTime, toTimeH)
    #
    #     absGap = self.calcAbsGap(fromTime, toTimeH, solveFirst=True)
    #     absGap = max((absGap, 0))
    #     print("absGap to set:", absGap, "getNominalThermalPower1: ", self.getNominalThermalPower1())
    #     self.c.parameters.mip.pool.absgap.set(absGap)
    #
    #     # Restrict threads to 1
    #     self.c.parameters.threads.set(1)
    #
    #     # solve problem
    #     self.c.populate_solution_pool()
    #     self.poolNoOfSchedules = self.c.solution.pool.get_num()
    #
    #     hSteps = (toTimeH-fromTime)/self.stepSize + 1
    #
    #     # create and return optimized schedule-array
    #     self.poolChosenSchedule = np.zeros(hSteps)
    #     self.poolChosenScheduleIndex = -1
    #     self.poolSchedules = np.zeros((self.poolNoOfSchedules, hSteps+1))
    #     self.poolSchedulesSec = np.zeros((self.poolNoOfSchedules, hSteps+1))
    #     self.poolETHStorage = np.zeros((self.poolNoOfSchedules, hSteps+1))
    #     self.poolOptimizedValues = np.zeros(self.poolNoOfSchedules)
    #     for s in range(self.poolNoOfSchedules):
    #         self.poolSchedules[s] = self.c.solution.pool.get_values(s, self.MODLVL)
    #         self.poolSchedulesSec[s] = self.c.solution.pool.get_values(s, self.MODLVLSec)
    #         self.poolETHStorage[s] = self.c.solution.pool.get_values(s, self.ETHStorage)
    #         self.poolOptimizedValues[s] = self.c.solution.pool.get_values(s, optimizedCriterion)[0]
    #
    # def resetForDesync(self, steps):
    #     """
    #     resets previousLoad data for a new ring search
    #     :param steps: number of time steps
    #     :return:
    #     """
    #     self.previousDesyncIterationLoad = np.zeros(steps)
    #     self.previousDesyncIterationBest = -1
    #
    # def findBestSchedule(self, fluctuationsCurve):
    #     """
    #     finds optimal schedule from schedule pool to flatten given current fluctuations curve
    #     :param fluctuationsCurve: fluctuation curve that will be flattened
    #     :param criterion: criterion used to choose best schedule - 'power' or 'energy'
    #     :return: resulting fluctuations curve after best bes-generation and -load has been added (1 x time period, e.g. 1 x 24) & info if schedule has been changed during this iteration
    #     """
    #
    #     if self.getTER1() == 0: # gas boiler
    #         print("GB does not have any schedules")
    #         return fluctuationsCurve
    #     if self.getPoolNoOfSchedules() == 0:    # no schedules, error!
    #         return fluctuationsCurve
    #
    #     # setup variables
    #     noSch = self.getPoolNoOfSchedules()
    #     remainder = np.zeros((noSch, len(fluctuationsCurve)))
    #
    #     # revert changes made by previously chosen schedule
    #     fluctuationsCurveCurrent = np.array(fluctuationsCurve) - np.array(self.previousDesyncIterationLoad)
    #
    #     # calculate remainder for each possible schedule from solution pool
    #     for s in range(noSch):
    #         remainder[s, :] = fluctuationsCurveCurrent + self.poolSchedules[s, 1:]    * self.getNominalElectricalPower1() * self.stepSize / self.getModlvls1() \
    #                                                    + self.poolSchedulesSec[s, 1:] * self.getNominalElectricalPower2() * self.stepSize
    #
    #     # find the remainder with best RPV performance and choose respective schedule from solution pool
    #     iBest = np.argmin([(np.max(remainder[s]) - np.min(remainder[s])) for s in range(remainder.shape[0])])
    #     self.poolChosenScheduleIndex = iBest
    #
    #     # make sure that a new schedule will only be selected if results are actually better (thus avoiding endless loop)
    #     # if self.previousDesyncIterationBest != -1 and self.previousDesyncIterationBest <= best:     # if at least one iteration has occurred and results aren't better...
    #     #     # print self.poolChosenScheduleIndex, "\t",   # for debugging
    #     #     return remainder[self.poolChosenScheduleIndex], 0   # ...return previous remainder and zero flag since schedule hasn't changed
    #
    #     # save the load/generation that the selected schedule adds to the fluctuations curve (to possibly subtract it in next desync iteration)
    #     self.previousDesyncIterationLoad = self.poolSchedules[iBest, 1:]    * self.getNominalElectricalPower1() * self.stepSize / self.getModlvls1() \
    #                                      + self.poolSchedulesSec[iBest, 1:] * self.getNominalElectricalPower2() * self.stepSize
    #
    #
    #     return remainder[self.poolChosenScheduleIndex]


    # ==================================================================================================================
    # getters & setters
    # ==================================================================================================================

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

    # ------------

    def getPoolChosenScheduleIndex(self):
        return self.poolChosenScheduleIndex
    def setPoolChosenScheduleIndex(self, newVal):
        self.poolChosenScheduleIndex = newVal

    def getPoolSchedules(self):
        return self.poolSchedules
    def setPoolSchedules(self, newVal):
        self.poolSchedules = newVal

    def getPoolSchedulesSec(self):
        return self.poolSchedulesSec
    def setPoolSchedulesSec(self, newVal):
        self.poolSchedulesSec = newVal

    def getPoolETHStorage(self):
        return self.poolETHStorage
    def setPoolETHStorage(self, newVal):
        self.poolETHStorage = newVal

    def getPoolNoOfSchedules(self):
        return self.poolNoOfSchedules
    def setPoolNoOfSchedules(self, newVal):
        self.poolNoOfSchedules = newVal

    # -------------

    def getOptimizedCriterionValue(self):
        return self.optimizedCriterionValue
    def setOptimizedCriterionValue(self, newVal):
        self.optimizedCriterionValue = newVal

    def getLocallyOptimalSchedule(self):
        return self.locallyOptimalSchedule
    def setLocallyOptimalSchedule(self, newVal):
        self.locallyOptimalSchedule = newVal

    def getLocallyOptimalScheduleSec(self):
        return self.locallyOptimalScheduleSec
    def setLocallyOptimalScheduleSec(self, newVal):
        self.locallyOptimalScheduleSec = newVal

    # -------------

    def getSchedule(self):
        return self.schedule
    def setSchedule(self, newVal):
        self.schedule = newVal

    def getScheduleSec(self):
        return self.scheduleSec
    def setScheduleSec(self, newVal):
        self.scheduleSec = newVal
