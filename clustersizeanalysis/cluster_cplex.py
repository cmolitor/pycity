__author__ = 'Christoph Molitor'

import os
import cplex
import numpy as np
import math

from building.electricalload import ElectricalLoad
from toolbox import arrToOplStr as arrTOS


class Cluster(object):
    """
    A cluster is a container for a number of building energy systems. A cluster is part of an environment
    which provides for example  weather information.
    """

    def __init__(self, dirAbsResults, environment, horizon, stepSize, interval):
        """
        Constructor of cluster
        :param environment: instance of the environment in which the cluster will be included
        :param horizon: time period (s) for which the schedules are calculated (e.g. 1 day ahead = 86400s)
        :param stepSize: time period (s) of the individual time step
        :param interval: time period (s) after new schedules are calculates (interval <= horizon)
        """
        self.script_dir = os.path.dirname(__file__)
        self.dirAbsResults = dirAbsResults

        self.horizon = horizon  # in seconds
        self.stepSize = stepSize  # in seconds
        self.interval = interval  # in seconds
        self.hSteps = horizon / stepSize
        self.iSteps = interval / stepSize
        self.listBes = list()
        self.environment = environment
        self.surchargeLoad = ElectricalLoad(0, self.stepSize)  # ElectricalLoad(0)  # create dummy electrical surcharge load, update later
        self.surchargeShare = 0
        self.typeOptimization = "MIP"
        # print("I am the constructor of a cluster")

    def addMember(self, Bes):
        """
        Method to add BES to the cluster
        :param Bes: BES which will be added to the cluster
        """
        self.listBes.append(Bes)
        # print(self.listBES)

    def getNumberOfMembers(self):
        return len(self.listBes)
        # print(self.listBES)

    def getNumberOfPrimaryHeaters(self, typeHeater):
        _iHP = 0
        _iCHP = 0
        if typeHeater == "HP":
            for b in range(0,self.getNumberOfMembers()):
                if self.listBes[b].getTER1() < 0:  # HP
                    _iHP = _iHP + 1
            return _iHP
        elif typeHeater == "CHP":
            for b in range(0,self.getNumberOfMembers()):
                if self.listBes[b].getTER1() > 0:  # CHP
                    _iCHP = _iCHP + 1
            return _iCHP
        else:  # type not found
            return -1

    def setSurchargeLoad(self, share):  # share in percent
        self.surchargeShare = share
        self.surchargeLoad = ElectricalLoad(float(share) / 100 * self.getAnnualElectricityConsumption(1), self.stepSize)
        # print("self.surchargeLoad:", self.surchargeLoad)
        # return 0

    def setTypeOptimization(self, typeOptimization):
        if typeOptimization == "LP" or "MIP":
            self.typeOptimization = typeOptimization
            return 0
        else:
            return -1

    def getSurchargeLoad(self):
        return self.surchargeLoad.getAnnualElectricalDemand()

    def getTypeOptimization(self):
        return self.typeOptimization

    def getAnnualElectricityConsumption(self, type):  # type: 0: all; 1: only electro thermal BES
        """
        does awesome stuff
        :param type:
        :return: annual electrical demand :rtype: int
        """
        _demandelectrical_annual = 0
        for x in range(0, len(self.listBes)):
            _demandelectrical_annual += self.listBes[x].getAnnualElectricalDemand()
        if type == 0:
            _demandelectrical_annual += self.surchargeLoad.getAnnualElectricalDemand()
        return _demandelectrical_annual

    def getElectricalDemandCurve(self, fromTime, toTime):
        """
        Returns the electrical demand curve for a given time period
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: multi dimensional array (2x time period); first column: time; second column: values
        """
        _electricalDemandCurve = self.listBes[0].getElectricalDemandCurve(fromTime, toTime)
        for x in range(1, len(self.listBes)):
            _electricalDemandCurve[1, :] += self.listBes[x].getElectricalDemandCurve(fromTime, toTime)[1, :]
        _electricalDemandCurve[1, :] += self.surchargeLoad.getElectricalDemandCurve(fromTime, toTime)[1, :]
        return _electricalDemandCurve

    def getRenewableGenerationCurve(self, fromTime, toTime):
        _AnnualEnergyDemand = self.getAnnualElectricityConsumption(0)
        # print("_AnnualEnergyDemand:", _AnnualEnergyDemand)
        return self.environment.getRenewableGenerationCurve(fromTime, toTime, _AnnualEnergyDemand)

    def getFluctuationsCurve(self, fromTime, toTime):
        print("fromTime: ", fromTime, "; toTime: ", toTime)
        _RES = self.getRenewableGenerationCurve(fromTime, toTime)
        #print("_RES", _RES.shape)
        _Load = self.getElectricalDemandCurve(fromTime, toTime)
        #print("_Load: ", _Load.shape)
        return _RES[1, :] + _Load[1, :]

    def calcSchedules(self, fromTime):
        """
        Method to calculate the schedules for each BES in the cluster.
        :param fromTime: start time; the scheduling is done for the time period fromTime + Horizon
        :return: :rtype: returns the results in a matrix
        """

        # =========================================================================
        # Model
        # =========================================================================
        cpx = cplex.Cplex()
        cpx.objective.set_sense(cpx.objective.sense.minimize)

        # =========================================================================
        # Variables
        # =========================================================================
        nBES = self.getNumberOfMembers()
        rangeBES = range(0, nBES)
        nSteps = self.hSteps            # number of steps within horizon
        rangeHorizon1 = range(1, nSteps + 1)  # hour array
        rangeHorizon0 = range(0, nSteps + 1)  # dummy
        stepSize = self.stepSize

        toTime = fromTime + (self.hSteps - 1) * stepSize

        # Initialization of fluctuations in this way to simply iterations later
        Fluctuations = [0 for x in rangeHorizon0]
        Fluctuations[1:] = self.getFluctuationsCurve(fromTime, toTime)

        # =========================================================================
        # Decision variables
        # =========================================================================
        dvModlvl1 = [[0 for x in rangeHorizon0] for x in rangeBES]
        dbgModlvl1 = [[0 for x in rangeHorizon0] for x in rangeBES]
        dvModlvl2 = [[0 for x in rangeHorizon0] for x in rangeBES]

        _typeOptimization = self.getTypeOptimization()

        for b in rangeBES:
            # The modulation level (modlvl) as decision variable gets a different type and different allowed range
            # depending on the type of optimization problem (MIP or LP) and as well as depending on the type of
            # secondary heater.
            # The model is described in detail by the following table:
            #
            #               |   |Primary heater                    |  Secondary Heater
            # =================================================================================
            # CHP system    |   | CHP                              | Gas boiler
            # ---------------------------------------------------------------------------------
            #               |LP | continuous: 0 - ModLvls (e.g. 1) | continuous: 0 - 1
            #               |MIP| integer: 0, ModLvls              | semi-continuous: 0.2 - 1.0
            # =================================================================================
            # HP system     |   | HP                               | Electric boiler
            # ---------------------------------------------------------------------------------
            #               |LP | continuous: 0 - ModLvls          | continuous: 0 - 1
            #               |MIP| integer: 0, ModLvls              | integer: 0, 1
            #
            # If the problem is solved as LP, all heaters (primary and secondary) can modulate continuously.
            # If the problem is solved as MIP, the type of the decision variable is differentiate following the
            # following argumentation:
            # CHP system have often a gas boiler as secondary heater as a connection to the gas grid is required in
            # any case for the CHP. Gas boilers can modulate quite well in a wide range. Here: 0.2 -1.0 ([1]).
            # HP systems have typically an electrical secondary heater. This electrical heater can not modulate and
            # can only be operated on or off.
            #
            # In order to restrict the operation of the secondary heater, the secondary heater can only be turned on if
            # the primary heater is running (see constraints with name "RestrictSecondaryHeater").
            # Furthermore, the secondary heater can operate only when the thermal demand
            # at time slot t is higher then the nominal thermal power of the primary heater (implemented by variable
            # _enableHeater2).
            # Sources:
            # [1] Buderus, "Buderus Gas-Brennwertkessel Leistungsbereich: 2,7 bis 40 kW",
            #     Bd. Einfach komfortabel modernisieren, 2012.

            if _typeOptimization == "MIP":
                _typeDvModlvl1 = [cpx.variables.type.integer]
                if self.listBes[b].getTER2() == 0:
                    _typeDvModlvl2 = [cpx.variables.type.semi_continuous]
                    _lbModlvl2 = 0.2
                    _ubModlvl2 = 1.0
                elif self.listBes[b].getTER2() < 0:
                    _typeDvModlvl2 = [cpx.variables.type.integer]
                    _lbModlvl2 = 0
                    _ubModlvl2 = 1
                else:
                    print("Something wrong with the type of the decision variable dvModlvl - 1")
                    return -1
            elif _typeOptimization == "LP":
                _typeDvModlvl1 = [cpx.variables.type.continuous]
                _typeDvModlvl2 = [cpx.variables.type.continuous]
                _lbModlvl2 = 0
                _ubModlvl2 = 1

            else: # fallback
                print("Something wrong with the type of the decision variable dvModlvl - 2")
                return -1

            _thermaldemandcurve  = [0 for x in rangeHorizon0]
            _thermaldemandcurve[1:] = self.listBes[b].getThermalDemandCurve(fromTime, toTime)[1, :]

            _ThermalPower1 = [0 for x in rangeHorizon0]
            _ThermalPower1[1:] = self.listBes[b].getThermalPower1(fromTime, toTime)[1, :]
            for s in rangeHorizon0:
                if abs(_thermaldemandcurve[s]) > abs(_ThermalPower1[s] * self.stepSize):
                    _enableHeater2 = 1.0
                else:
                    _enableHeater2 = 0.0

                # print _thermaldemandcurve[s], self.listBes[b].getNominalThermalPower1() * self.stepSize, _enableHeater2

                dvModlvlName = "MODLVL1_" + str(b) + "_" + str(s)
                dvModlvl1[b][s] = dvModlvlName
                cpx.variables.add(names = [dvModlvlName],
                                       lb = [0],
                                       ub = [self.listBes[b].getModlvls1()],
                                       types = _typeDvModlvl1)

                dvModlvlName = "MODLVL2_" + str(b) + "_" + str(s)
                dvModlvl2[b][s] = dvModlvlName
                cpx.variables.add(names = [dvModlvlName],
                                       lb = [_lbModlvl2 * _enableHeater2],
                                       ub = [_ubModlvl2 * _enableHeater2],
                                       types = _typeDvModlvl2)

        # Variables to indicate switching events of primary heater (1)
        if _typeOptimization == "MIP":
            swtchOn1 = [[0 for x in rangeHorizon0] for x in rangeBES]
            swtchOff1 = [[0 for x in rangeHorizon0] for x in rangeBES]
            for b in rangeBES:
                for s in rangeHorizon0:
                    swtchOnName = "switchOn1_" + str(b) + "_" + str(s)
                    swtchOn1[b][s] = swtchOnName
                    swtchOffName = "switchOff1_" + str(b) + "_" + str(s)
                    swtchOff1[b][s] = swtchOffName

                    cpx.variables.add(names=[swtchOnName],
                                      lb=[0],
                                      ub=[1],
                                      types=[cpx.variables.type.integer])
                    cpx.variables.add(names=[swtchOffName],
                                      lb=[0],
                                      ub=[1],
                                      types=[cpx.variables.type.integer])


            # Variables to indicate switching events of secondary heater (2)
            swtchOn2 = [[0 for x in rangeHorizon0] for x in rangeBES]
            swtchOff2 = [[0 for x in rangeHorizon0] for x in rangeBES]
            for b in rangeBES:
                for s in rangeHorizon0:
                    swtchOnName = "switchOn2_" + str(b) + "_" + str(s)
                    swtchOn2[b][s] = swtchOnName
                    swtchOffName = "switchOff2_" + str(b) + "_" + str(s)
                    swtchOff2[b][s] = swtchOffName

                    cpx.variables.add(names=[swtchOnName],
                                      lb=[0],
                                      ub=[1],
                                      types=[cpx.variables.type.integer])
                    cpx.variables.add(names=[swtchOffName],
                                      lb=[0],
                                      ub=[1],
                                      types=[cpx.variables.type.integer])

            # number of switching events as sum of swtchOn and swtchOff of primary heater (1)
            swtchCount1 = [0 for x in rangeBES]
            for b in rangeBES:
                swtchCountName = "switchCount1_" + str(b)
                swtchCount1[b] = swtchCountName
                cpx.variables.add(names=[swtchCountName],
                                  lb=[0],
                                  ub=[len(rangeHorizon0)],
                                  types=[cpx.variables.type.integer])

            # number of switching events as sum of swtchOn and swtchOff of secondary heater (2)
            swtchCount2 = [0 for x in rangeBES]
            for b in rangeBES:
                swtchCountName = "switchCount2_" + str(b)
                swtchCount2[b] = swtchCountName
                cpx.variables.add(names=[swtchCountName],
                                  lb=[0],
                                  ub=[len(rangeHorizon0)],
                                  types=[cpx.variables.type.integer])

        # stored thermal energy
        ETHStorage = [[0 for x in rangeHorizon0] for x in rangeBES]
        for b in rangeBES:
            for s in rangeHorizon0:
                ETHStorageName = "ETHStorage_" + str(b) + "_" + str(s)
                ETHStorage[b][s] = ETHStorageName
                cpx.variables.add(names = [ETHStorageName],
                        lb = [self.listBes[b].getStorageCapacity() * self.listBes[b].getSOCmin()],
                        ub = [self.listBes[b].getStorageCapacity() * self.listBes[b].getSOCmax()],
                        types = [cpx.variables.type.continuous])

        # power flow into storage at time=s
        PTHStorage = [[0 for x in rangeHorizon0] for x in rangeBES]
        for b in rangeBES:
            _thermaldemandcurve = [0 for x in rangeHorizon0]
            _thermaldemandcurve[1:] = self.listBes[b].getThermalDemandCurve(fromTime, toTime)[1, :]
            _thermalPower1 = [0 for x in rangeHorizon0]
            _thermalPower1[1:] = self.listBes[b].getThermalPower1(fromTime, toTime)[1, :]
            _thermalPower2 = [0 for x in rangeHorizon0]
            _thermalPower2[1:] = self.listBes[b].getThermalPower2(fromTime, toTime)[1, :]

            #_thermalPower2[1:] = self.listBes[b].getNominalThermalPower2() * np.ones_like(_thermalPower2[1:])
            for s in rangeHorizon1:
                #print("lb: ", -_thermaldemandcurve[s]/stepSize, "; ub: ", -(_thermalPower1[s] + _thermalPower2[s]))
                #print("lb: ", math.floor(-_thermaldemandcurve[s]/stepSize), "; ub: ", math.ceil(-(_thermalPower1[s] + _thermalPower2[s])))
                PTHStorageName = "PTHStorage_" + str(b) + "_" + str(s)
                PTHStorage[b][s] = PTHStorageName
                cpx.variables.add(names=[PTHStorageName],
                                  lb=[math.floor(-_thermaldemandcurve[s]/stepSize)],
                                  ub=[math.ceil(-(_thermalPower1[s] + _thermalPower2[s]))],
                                  types=[cpx.variables.type.continuous])

        # Remainder
        _minFluc = min(Fluctuations[1:])
        _maxFluc = max(Fluctuations[1:])

        _maxGeneration = 0
        _maxLoad = 0
        for b in rangeBES:
            _PelNom1 = self.listBes[b].getNominalElectricalPower1()
            _PelNom2 = self.listBes[b].getNominalElectricalPower2()
            if _PelNom1 < 0:
                _maxGeneration = _maxGeneration + _PelNom1 * stepSize
            else:
                _maxLoad = _maxLoad + _PelNom1 * stepSize

            if _PelNom2 < 0:
                _maxGeneration = _maxGeneration + _PelNom2 * stepSize
            else:
                _maxLoad = _maxLoad + _PelNom2 * stepSize


        varsRemainder = [0 for x in rangeHorizon0]  # not necessary to use rangeHorizon0 but for convenience during later iterations
        for s in rangeHorizon1:
            RemainderName = "Remainder_" + str(s)
            varsRemainder[s] = RemainderName
            cpx.variables.add(names = [RemainderName],
                                   lb = [_minFluc + _maxGeneration],
                                   ub = [_maxFluc + _maxLoad],
                                   types = [cpx.variables.type.continuous])

        # minRemainder
        minRemainder = "minRemainder"
        cpx.variables.add(obj =[-1], names = [minRemainder], lb = [_minFluc + _maxGeneration], ub = [_maxFluc + _maxLoad], types = [cpx.variables.type.continuous])

        # maxRemainder
        maxRemainder = "maxRemainder"
        cpx.variables.add(obj = [1], names = [maxRemainder], lb = [_minFluc + _maxGeneration], ub = [_maxFluc + _maxLoad], types = [cpx.variables.type.continuous])
        #cplModel.variables.add(obj = [1], names = [maxRemainder], ub = [-2000000], types = [cplModel.variables.type.continuous])

        # =========================================================================
        # Constraints
        # =========================================================================
        for s in rangeHorizon1:
            # constraint: Remainder:
            thevars = [varsRemainder[s], minRemainder]
            cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, -1])], senses = ["G"], rhs = [0], names=["minRemainder_" + str(s)])
            thevars = [varsRemainder[s], maxRemainder]
            cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1, -1])], senses = ["L"], rhs = [0], names=["maxRemainder_" + str(s)])

            # constraint: Electrical energy balance
            # Equation: Remainder(t) - sum[b of BES](Pel(b,t) * modlvl(b,t) == Fluctuations(t)
            thevars = [varsRemainder[s]]
            coeff = [1]
            for b in rangeBES:
                thevars.append(dvModlvl1[b][s])
                thevars.append(dvModlvl2[b][s])
                coeff.append(-self.listBes[b].getNominalElectricalPower1()/self.listBes[b].getModlvls1() * stepSize)
                coeff.append(-self.listBes[b].getNominalElectricalPower2() * stepSize)
            cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeff)], senses = ["E"], rhs = [Fluctuations[s]], names=["ElecBalance_" + str(s)])

        for b in rangeBES:
            _thermaldemandcurve  = [0 for x in rangeHorizon0]
            _thermaldemandcurve[1:] = self.listBes[b].getThermalDemandCurve(fromTime, toTime)[1, :]

            _ThermalPower1 = [0 for x in rangeHorizon0]
            _ThermalPower1[1:] = self.listBes[b].getThermalPower1(fromTime, toTime)[1, :]
            _ThermalPower2 = [0 for x in rangeHorizon0]
            _ThermalPower2[1:] = self.listBes[b].getThermalPower2(fromTime, toTime)[1, :]

            #print("_ThermalPower1[1:]: ",_ThermalPower1[1:])
            #print("_ThermalPower2[1:]: ", _ThermalPower2[1:])
            #print("_thermaldemandcurve[1:]: ", _thermaldemandcurve[1:])

            for s in rangeHorizon1:
                # Limitation due to storage size
                thevars = [ETHStorage[b][s]]
                cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                                senses = ["G"], rhs = [self.listBes[b].getSOCmin() * self.listBes[b].getStorageCapacity()],
                                                names=["SoCmin_" + str(b) + "_" + str(s)])
                cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                                senses = ["L"], rhs = [self.listBes[b].getSOCmax() * self.listBes[b].getStorageCapacity()],
                                                names=["SoCmax_" + str(b) + "_" + str(s)])

                # Thermal energy balance in storage
                # Equation: EthStorage(b, t) - EthStorage(b, t-1) - PthStorage(b,t) * stepSize == 0
                thevars = [ETHStorage[b][s], ETHStorage[b][s-1], PTHStorage[b][s]]
                cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1,-1,-stepSize])],
                                                senses = ["E"],
                                                rhs = [0],
                                                names=["ThermalStorageBalance_" + str(b) + "_" + str(s)])

                # Thermal energy balance
                # Equation: -modlvl(b, t) * PthNom(b) * stepSize - PthStorage(b, t) * stepSize == PthDemand
                thevars = [dvModlvl1[b][s], dvModlvl2[b][s], PTHStorage[b][s]]
                thecoeffs = [-_ThermalPower1[s] * self.stepSize, -_ThermalPower2[s] * stepSize, -stepSize]
                cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, thecoeffs)],
                                                senses = ["E"],
                                                rhs = [_thermaldemandcurve[s]],
                                                names=["ThermalBalance_" + str(b) + "_" + str(s)])

                # Restrict the secondary heater to operate only when the primary heater is already running
                thevars = [dvModlvl2[b][s], dvModlvl1[b][s]]
                thecoeffs = [1, -1]
                cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, thecoeffs)],
                                                senses = ["L"],
                                                rhs = [0],
                                                names=["RestrictSecondaryHeater" + str(b) + "_" + str(s)])

                # Constraints regarding switching of primary heater
                if _typeOptimization == "MIP":
                    thevars = [dvModlvl1[b][s], dvModlvl1[b][s-1], swtchOn1[b][s], swtchOff1[b][s]]
                    cpx.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1, -1, -1, 1])],
                                               senses=["E"],
                                               rhs=[0],
                                               names=["SwitchingBalance_"+str(b)+"_"+str(s)])

                    thevars = [swtchOn1[b][s], swtchOff1[b][s]]
                    cpx.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1, 1])],
                                              senses=["L"],
                                              rhs=[1],
                                              names=["SwitchingSum_"+str(b)+"_"+str(s)])

                    # Consider minimum runtime
                    # Remark: this works only properly at the beginning of a scheduling interval (e.g. day) if
                    # the minimum runtime is two consecutive steps as only the switching event in the last time step
                    # of the previous day is stored and can be considered
                    # Equation: Modlvl(t) >= swtchOn(t) + swtchOn(t-1) + swtchOn(t-2)
                    _minRunSteps = int(math.ceil(self.listBes[b].getMinRuntime1()/self.stepSize))
                    if _minRunSteps > 2.0:
                        print("Possibly not correct results; Check comments in code")
                    thevars = [dvModlvl1[b][s]]
                    thecoeffs = [1]
                    for z in range(0, _minRunSteps):
                        thevars.append(swtchOn1[b][s-z])
                        thecoeffs.append(-1)
                    cpx.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, thecoeffs)],
                                               senses=["G"],
                                               rhs=[0],
                                               names=["Minimum_runtime"+str(b)+"_"+str(s)])

            # MODLVL at time t=0 = MODLVLini
            thevars = [dvModlvl1[b][0]]
            cpx.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1])],
                                       senses=["E"],
                                       rhs=[self.listBes[b].getStateModlvl()])

            if _typeOptimization == "MIP":
                # swtchOn1 at time t=0
                #print("self.listBes[b].getSwtchOn1EOD(): ", self.listBes[b].getSwtchOn1EOD())
                thevars = [swtchOn1[b][0]]
                cpx.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1])],
                                           senses=["E"],
                                           rhs=[self.listBes[b].getSwtchOn1EOD()])

                # swtchOff1 at time t=0
                thevars = [swtchOff1[b][0]]
                cpx.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1])],
                                           senses=["E"],
                                           rhs=[self.listBes[b].getSwtchOff1EOD()])

            # Initializing the SOC of the storage
            thevars = [ETHStorage[b][0]]
            cpx.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, [1])],
                                            senses = ["E"],
                                            rhs = [self.listBes[b].getSOC() * self.listBes[b].getStorageCapacity()])

        # =========================================================================
        # Solve
        # =========================================================================
        # set time limit
        cpx.parameters.timelimit.set(900.0)

        #cpx.setVerbosity(self, 3)
        # set relative gap
        if _typeOptimization == "MIP":
            cpx.parameters.mip.tolerances.mipgap.set(0.1)
            #cpx.parameters.mip.strategy.dive(2)
            cpx.parameters.emphasis.mip.set(2)  # 2: optimality
            cpx.parameters.mip.strategy.dive.set(2)
            #cpx.parameters.mip.strategy.file.set(3)
            cpx.parameters.threads.set(4)
        #cpx.parameters.mip.limits.treememory.set(2000)
        #cpx.parameters.workmem.set(128)
        _logfile = self.dirAbsResults + "/logfile_Buildings-" + str(int(self.getNumberOfMembers()+self.getNumberOfMembers()*self.surchargeShare/100)) \
                     + "_HPs-" + str(self.getNumberOfPrimaryHeaters("HP")) + "_CHPs-" + str(self.getNumberOfPrimaryHeaters("CHP"))

        cpx.set_results_stream(_logfile + "_t-" + str(fromTime) +  ".res")
        cpx.set_error_stream(_logfile + "_t-" + str(fromTime) + ".err")
        cpx.set_warning_stream(_logfile + "_t-" + str(fromTime) + ".war")
        cpx.set_log_stream(_logfile + "_t-" + str(fromTime) + ".log")
        cpx.solve()

        _status = cpx.solution.get_status()
        x = 0

        # solution status: http://eaton.math.rpi.edu/cplex90html/refcallablelibrary/html/optim.cplex.solutionstatus/group.html
        while _status == 108:
            x = x + 1
            print("Additional iteration: {}".format(x + 1))
            print("Status: {}".format(_status))
            _timelimit = min(x * 900.0, 3600.0)
            cpx.parameters.timelimit.set(_timelimit)
            cpx.solve()
            _status = cpx.solution.get_status()

        # for x in xrange(0,4):
        #     _status = cpx.solution.get_status()
        #     if _status == 108:
        #         print("Additional iteration: {}".format(x + 1))
        #         cpx.solve()
        #     else:
        #         break

        # =========================================================================
        # Extract results
        # =========================================================================
        sol = cpx.solution
        #print sol.quality_metric.objective_gap
        if _typeOptimization == "MIP":
            relGap = sol.MIP.get_mip_relative_gap()
        else:
            relGap = 0.0

        #print sol.get_integer_quality()
        #print sol.get_status()

        Remainder = [0 for x in rangeHorizon0]
        Remainder[1:] = sol.get_values([varsRemainder[s] for s in rangeHorizon1])

        # Extract SOC and modlvl at the end of the interval and assign them to the specific BES, thus the values can serve as
        # start values for the next scheduling period
        _EthStorage = sol.get_values([ETHStorage[b][self.iSteps] for b in rangeBES])
        _Modlvl1 = sol.get_values([dvModlvl1[b][self.iSteps] for b in rangeBES])

        if _typeOptimization == "MIP":
            _swtchOn1 = sol.get_values([swtchOn1[b][self.iSteps] for b in rangeBES])
            _swtchOff1 = sol.get_values([swtchOff1[b][self.iSteps] for b in rangeBES])

        # for debugging; best with one BES as it prints SOC and modlvl .. only for first BES
        bDebugMode = 0
        if _typeOptimization == "MIP":
            if bDebugMode == 1:
                b = 0  # select BES
                if fromTime > -1:
                    print("s swtchOn swtchOff ModLvl1 ModLvl2 Pel1 Pel2 Pth1 Pth2 SoC PthStorage PthDemand Remainder Fluctuations")
                for s in rangeHorizon0:
                    _dgbModlvl1 = sol.get_values([dvModlvl1[b][s] for b in rangeBES])
                    _dbgModlvl2 = sol.get_values([dvModlvl2[b][s] for b in rangeBES])
                    _swtchOn1 = sol.get_values([swtchOn1[b][s] for b in rangeBES])
                    _swtchOff1 = sol.get_values([swtchOff1[b][s] for b in rangeBES])
                    _PthStorage = sol.get_values([PTHStorage[b][s] for b in rangeBES])
                    _EthStorage = sol.get_values([ETHStorage[b][s] for b in rangeBES])
                    _Remainder = sol.get_values(varsRemainder[s])
                    _ThermalPower1 = [0 for x in rangeHorizon0]
                    _ThermalPower1[1:] = self.listBes[b].getThermalPower1(fromTime, toTime)[1, :]
                    print "{} {} {} {} {} {} {} {} {} {} {} {} {} {}".format(s, int(_dgbModlvl1[0]),
                                                                    int(_swtchOn1[0]),
                                                                    int(_swtchOff1[0]),
                                                                    int(_dbgModlvl2[0]),
                                                                    _dgbModlvl1[0] / self.listBes[b].getModlvls1() * self.listBes[b].getNominalElectricalPower1(),
                                                                    _dbgModlvl2[0] * self.listBes[b].getNominalElectricalPower2(),
                                                                    _dgbModlvl1[0] * _ThermalPower1[s],
                                                                    _dbgModlvl2[0] * self.listBes[b].getNominalThermalPower2(),
                                                                    _EthStorage[0] / self.listBes[b].getStorageCapacity(),
                                                                    _PthStorage[0],
                                                                    _thermaldemandcurve[s] / self.stepSize,
                                                                    _Remainder,
                                                                    Fluctuations[s])

            if bDebugMode == 2:
                for s in rangeHorizon1:
                    _dgbModlvl1 = sol.get_values([dvModlvl1[b][s] for b in rangeBES])
                    _dbgModlvl1 = sol.get_values([dbgModlvl1[b][s] for b in rangeBES])
                    _swtchOn1 = sol.get_values([swtchOn1[b][s] for b in rangeBES])
                    _swtchOff1 = sol.get_values([swtchOff1[b][s] for b in rangeBES])
                    # for b in rangeBES:
                    print("{} {} {} {}".format([int(_dgbModlvl1[b]) for b in rangeBES], [int(_swtchOn1[b]) for b in rangeBES], [int(_swtchOff1[b]) for b in rangeBES], [_dbgModlvl1[b] for b in rangeBES]))

        # store state variables of BES
        for b in rangeBES:
            newSOC = _EthStorage[b]/self.listBes[b].getStorageCapacity()
            # print "pre newSoc: ", b, " ", newSOC, "oldSoC: ", self.listBes[b].getSOC()
            if newSOC <= self.listBes[b].getSOCmin():
                # print "smaller"
                newSOC = self.listBes[b].getSOCmin()
            elif newSOC >= self.listBes[b].getSOCmax():
                # print "bigger"
                newSOC = self.listBes[b].getSOCmax()
            #else:
                # print "else"

            # print "after newSoc: ", b, " ", newSOC, "oldSoC: ", self.listBes[b].getSOC()

            # Store BES states
            self.listBes[b].setSOC(newSOC)
            self.listBes[b].setStateModlvl(_Modlvl1[b])
            if _typeOptimization == "MIP":
                self.listBes[b].setSwtchOn1EOD(int(round(_swtchOn1[b])))
                self.listBes[b].setSwtchOff1EOD(int(round(_swtchOff1[b])))

        (maxEnergyRemainder, maxEnergyFluctuations, deltaRemainder, deltaFluctuations, avgRemainder, avgFluctuations) \
            = self._calcPerformanceMeasure(Remainder[1:], Fluctuations[1:], fromTime)

        ratioMaxEnergy = maxEnergyRemainder/maxEnergyFluctuations
        ratioMaxPower = deltaRemainder/deltaFluctuations

        return (ratioMaxEnergy, ratioMaxPower, relGap, avgRemainder, avgFluctuations)

    def _calcPerformanceMeasure(self, Remainder, Fluctuations, fromTime):
        """
        Method calculates the performance measure the following way:
        (Remainder^max - Remainder^min)/(Fluctuations^max - Fluctuations^min)
        :param remainder:
        :param fluctuations:
        :param fromTime:
        :return: performance measure, aggregated energy of remainder, aggregated energy of fluctuations
        """
        avgRemainder = np.mean(Remainder)
        shiftedRemainder = [(Remainder[x]-avgRemainder) for x in range(0, len(Remainder))]
        cumsumShiftedRemainder = np.cumsum(shiftedRemainder)
        maxEnergyRemainder = max(abs(cumsumShiftedRemainder))
        deltaRemainder = np.max(Remainder) - np.min(Remainder)

        avgFluctuations = np.mean(Fluctuations)
        shiftedFluctuations = [(Fluctuations[x]-avgFluctuations) for x in range(0, len(Fluctuations))]
        cumsumFluctuations = np.cumsum(shiftedFluctuations)
        maxEnergyFluctuations = max(abs(cumsumFluctuations))
        deltaFluctuations = np.max(Fluctuations) - np.min(Fluctuations)

        # for s in range(0, len(Remainder)):
        #     print Remainder[s], Fluctuations[s], avgRemainder, avgFluctuations, cumsumShiftedRemainder[s], cumsumFluctuations[s]

        logfile_name = self.dirAbsResults + "/logfile_Buildings-" + str(int(self.getNumberOfMembers()+self.getNumberOfMembers()*self.surchargeShare/100)) \
                       + "_HPs-" + str(self.getNumberOfPrimaryHeaters("HP")) + "_CHPs-" + str(self.getNumberOfPrimaryHeaters("CHP")) + ".txt"
        if not os.path.isfile(logfile_name):
            logfile = open(logfile_name, "a")
            logfile.write("Time,Remainder,Fluctuations,avgRemainder,avgFluctuations,cumsumShiftedRemainder,cumsumFluctuations\n")
            logfile.close()

        logfile = open(logfile_name, "a")
        for s in range(0, self.iSteps):
            logfile.write("{},{},{},{},{},{},{}\n".format(fromTime + s * self.stepSize,Remainder[s], Fluctuations[s],
                                                          avgRemainder, avgFluctuations, cumsumShiftedRemainder[s], cumsumFluctuations[s]))
        logfile.close()

        return (maxEnergyRemainder, maxEnergyFluctuations, deltaRemainder, deltaFluctuations, avgRemainder, avgFluctuations)