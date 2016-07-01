__author__ = 'Anni'


import numpy as np
from city.cluster import Cluster
from buildingControl.smartbes import SmartBes
import cplex


class CentralizedCluster(Cluster):
    def __init__(self, dirAbsResults, environment, horizon, stepSize, interval):

        super(CentralizedCluster, self).__init__(dirAbsResults, environment, horizon, stepSize, interval)

        self.c = cplex.Cplex()      # cplex MIP model container

        # decision variables' names for global optimization problem
        self.dv_MODLVL1 = []
        self.dv_MODLVL2 = []
        self.dv_EThStorage = []
        self.dv_PThStorage = []
        self.dv_remainder = []
        self.dv_remainderMin = []
        self.dv_remainderMax = []
        # (objFcn = 1)
        self.dv_switchOn = []
        self.dv_switchOff = []
        self.dv_switchSum = []
        # (objFcn = 2)
        self.dv_EElGrid = []
        self.dv_EElGridDmnd = []
        self.dv_EElGridFeed = []
        self.dv_EElGridDmndOrFeedSum = []

    def runLclOptimization(self, fromTime):
        """
        run local optimizations for each BES to find upper bounds for decision variables of global optimization
        (i. e. minimized number of switching events or minimized demand (CHP) / feed (HP)).
        the value of the locally optimized variable is saved in smartbes and can be accessed later -> createCplexModel()
        :param fromTime: from time in seconds
        """

        toTimeH = fromTime + (self.hSteps - 1) * self.stepSize

        listBesPri = self.getBESs(typeHeater="primary")
        noBesPri = len(listBesPri)

        # run local optimization for each BES
        for b in range(noBesPri):
            listBesPri[b].calcOptimalSchedule(fromTime, toTimeH)

    def createGlobalCplexModel(self, fromTime):
        """
        creates the global cplex MIP model (c), including global decision variables and constraints

        1.  create empty cplex model & set sense (minimize)
        2.  define python variables needed to define the MIP
        3.  define energy/power curves needed to define the MIP

        4.  define all global decision variables
            (B: number of BESs / T: number of time steps incl. dummy time step t=0 for previous day):

            dv_MODLVL1, dv_MODLVL2                          (B x T)
            dv_EThStorage, dv_PThStorage                    (B x T)
            dv_remainder                                    (T)
            dv_remainderMin, dv_remainderMax                (1)                     <<< globally minimized/maximized
                                                                                        for CHPs: demand, for HPs: feed
        5.  define all global constraints needed for all BESs

        :param fromTime: fromTime in seconds
        """

        # ==============================================================================================================
        # cplex model
        # ==============================================================================================================

        # create empty Model
        self.c = cplex.Cplex()
        self.c.objective.set_sense(self.c.objective.sense.minimize)


        # ==============================================================================================================
        # py-variables
        # ==============================================================================================================

        toTime = fromTime + (self.hSteps - 1) * self.stepSize

        rangeHorizonFrom1 = range(1, self.hSteps+1)         # step array (1,2 ... 24)
        rangeHorizonFrom0 = range(0, self.hSteps+1)         # dummy    (0,1,2 ... 24)

        # number & list of primary heaters
        noBesPri = self.getNumberOfMembers(typeHeater="primary")
        rangeBesPri = range(noBesPri)
        listBesPri = self.getBESs(typeHeater="primary")


        # ==============================================================================================================
        # curves
        # ==============================================================================================================

        # curves needed to define MIP including a dummy-zero for t=0 to simplify iterations later
        # matrix: "number of primary heaters" x "time steps+1"
        # use second row of all curve-matrices as first row contains time and second row contains actual values

        # cluster values:
        _fluctuationsCurve = np.append([0], self.getFluctuationsCurve(fromTime, toTime))
        _flucMin = np.min(_fluctuationsCurve[1:])
        _flucMax = np.max(_fluctuationsCurve[1:])

        # BES values:
        _thermalPowerCurves1 = np.zeros((noBesPri, self.hSteps+1))
        _thermalPowerCurves2 = np.zeros((noBesPri, self.hSteps+1))
        _thermalDemandCurves = np.zeros((noBesPri, self.hSteps+1))

        for b in rangeBesPri:
            _thermalPowerCurves1[b] = np.append([0], listBesPri[b].getThermalPower1(fromTime, toTime)[1, :])
            _thermalPowerCurves2[b] = np.append([0], listBesPri[b].getThermalPower2(fromTime, toTime)[1, :])
            _thermalDemandCurves[b] = np.append([0], listBesPri[b].getThermalDemandCurve(fromTime, toTime)[1, :])


        # ==============================================================================================================
        # decision variables
        # ==============================================================================================================

        # modulation level 1: on=1, off=0
        # --------------------------------------------------------------------------------------------------------------

        self.dv_MODLVL1 = [['dv_MODLVL1_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri]
        for b in rangeBesPri:
            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_MODLVL1[b][t]],
                                lb = [0],
                                ub = [listBesPri[b].getModlvls1()],
                                types = [self.c.variables.type.integer])

        # modulation level 2: on=1, off=0
        # --------------------------------------------------------------------------------------------------------------

        self.dv_MODLVL2 = [['dv_MODLVL2_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri]

        typeMODLVLSec = list()
        lbMODLVLSec = np.zeros(noBesPri)
        allowHeater2 = np.zeros((noBesPri, self.hSteps+1))
        # find variable types & bounds of secondary heater's schedule for each BES
        for b in rangeBesPri:
            if listBesPri[b].getTER2() == 0:     # gas boiler
                typeMODLVLSec.append(self.c.variables.type.semi_continuous)
                lbMODLVLSec[b] = 0.2
            elif listBesPri[b].getTER2() < 0:    # electric boiler
                typeMODLVLSec.append(self.c.variables.type.binary)
                lbMODLVLSec[b] = 0
            else:
                print "TER2 doesn't make sense."
                return -1

            # allow secondary heater to only run whenever thermal demand exceeds thermal energy provided by pr. heater
            for t in rangeHorizonFrom0:
                if _thermalDemandCurves[b, t] > abs(_thermalPowerCurves1[b, t] * self.stepSize):
                    allowHeater2[b, t] = 1.0
                else:
                    allowHeater2[b, t] = 0.0

        # finally add variables
        for bb in rangeBesPri:
            for tt in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_MODLVL2[bb][tt]],
                                lb = [allowHeater2[bb, tt] * lbMODLVLSec[bb]],
                                ub = [allowHeater2[bb, tt]],
                                types = [typeMODLVLSec[bb]])

        # energy stored in thermal storage
        # --------------------------------------------------------------------------------------------------------------

		self.dv_EThStorage = [['dv_EThStorage_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri]
        for b in rangeBesPri:
            # get relevant data on storage for current BES to set bounds
            B_storMin = listBesPri[b].getSOCmin() * listBesPri[b].getStorageCapacity()
            B_storMax = listBesPri[b].getSOCmax() * listBesPri[b].getStorageCapacity()

            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_EThStorage[b][t]],
                                lb = [B_storMin],
                                ub = [B_storMax],
                                types = [self.c.variables.type.continuous])

        # power flow into thermal storage (positive when thermal power flows into device)
        # --------------------------------------------------------------------------------------------------------------

        self.dv_PThStorage = [['dv_PThStorage_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri]
        for b in rangeBesPri:
            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_PThStorage[b][t]],
                                lb = [- _thermalDemandCurves[b][t] / self.hSteps],                  # lb = negative thermal *power* demand at time t
                                ub = [- _thermalPowerCurves1[b][t] - _thermalPowerCurves2[b][t]],   # ub = combined thermal power of both heaters (curves are negative. assuming no thermal demand to define upper bound)
                                types = [self.c.variables.type.continuous])

        # remainder
        # --------------------------------------------------------------------------------------------------------------

        # find the maximum generation and maximum load that might be added to fluctuations curve by heating systems
        _maxGenerationFromHS = 0
        _maxLoadFromHS = 0
        for b in rangeBesPri:
            B_PelNom1 = listBesPri[b].getNominalElectricalPower1()
            B_PelNom2 = listBesPri[b].getNominalElectricalPower2()
            if B_PelNom1 < 0:
                _maxGenerationFromHS += B_PelNom1 * self.stepSize
            else:
                _maxLoadFromHS += B_PelNom1 * self.stepSize

            if B_PelNom2 < 0:
                _maxGenerationFromHS += B_PelNom2 * self.stepSize
            else:
                _maxLoadFromHS += B_PelNom2 * self.stepSize

        # remainder
        self.dv_remainder = ['dv_remainder_' + str(t) for t in rangeHorizonFrom0]
        for t in rangeHorizonFrom0:
            self.c.variables.add(names = [self.dv_remainder[t]],
                            lb = [_flucMin + _maxGenerationFromHS],
                            ub = [_flucMax + _maxLoadFromHS],
                            types = [self.c.variables.type.continuous])

        # minimum remainder
        self.dv_remainderMin = "dv_remainderMin"
        self.c.variables.add(obj = [-1], names = [self.dv_remainderMin],      # !!! global objective: to be maximized
                        lb = [_flucMin + _maxGenerationFromHS],
                        ub = [_flucMax + _maxLoadFromHS],
                        types = [self.c.variables.type.continuous])

        # maximum remainder
        self.dv_remainderMax = "dv_remainderMax"
        self.c.variables.add(obj = [1], names = [self.dv_remainderMax],       # !!! global objective: to be minimized
                        lb = [_flucMin + _maxGenerationFromHS],
                        ub = [_flucMax + _maxLoadFromHS],
                        types = [self.c.variables.type.continuous])


        # ==============================================================================================================
        # constraints
        # ==============================================================================================================

        for b in rangeBesPri:

            # constraints for time step t = 0
            # ----------------------------------------------------------------------------------------------------------

            # check if SOC has floating point issues & correct if necessary
            if listBesPri[b].getSOC() > listBesPri[b].getSOCmax():
                listBesPri[b].setSOC(listBesPri[b].getSOCmax())
            elif listBesPri[b].getSOC() < listBesPri[b].getSOCmin():
                listBesPri[b].setSOC(listBesPri[b].getSOCmin())

            # ModLvl at time (t=0) = MODLVLini
            thevars = [self.dv_MODLVL1[b][0]]
            coeffs  = [1]
            self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                     senses = ["E"], rhs = [round(listBesPri[b].getStateModlvl())])

            # energy in storage at time t=0 = SoCini * storageCapThermal
            thevars = [self.dv_EThStorage[b][0]]
            coeffs  = [1]
            self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                     senses = ["E"], rhs = [listBesPri[b].getSOC() * listBesPri[b].getStorageCapacity()])


            # constraints for all further time steps t > 0
            # ----------------------------------------------------------------------------------------------------------

            for t in rangeHorizonFrom1:

                # Restrict the secondary heater to operate only when the primary heater is already running
                thevars = [self.dv_MODLVL1[b][t], self.dv_MODLVL2[b][t]]
                coeffs  = [1, -1]
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                         senses = ["G"], rhs = [0])

                # energy in storage at time t = energy at time (t-1) + (stepSize * PTHStorage[t])
                thevars = [self.dv_EThStorage[b][t], self.dv_EThStorage[b][t-1], self.dv_PThStorage[b][t]]
                coeffs  = [1, -1, -self.stepSize]
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                         senses = ["E"], rhs = [0])

                # thermal energy produced by main & backup device (dynamic thermal power!) = thermal demand + thermal energy that is stored in thermal storage
                thevars = [self.dv_MODLVL1[b][t], self.dv_MODLVL2[b][t], self.dv_PThStorage[b][t]]
                coeffs  = [-_thermalPowerCurves1[b][t] * self.stepSize / listBesPri[b].getModlvls1(), -_thermalPowerCurves2[b][t] * self.stepSize, -self.stepSize]
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                         senses = ["E"], rhs = [_thermalDemandCurves[b][t]])

        # constraints for remainder at times t and min/max remainder
        # --------------------------------------------------------------------------------------------------------------

        for t in rangeHorizonFrom1:

            # remainder at any time t >= minRemainder
            thevars = [self.dv_remainder[t], self.dv_remainderMin]
            coeffs = [1, -1]
            self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                     senses = ["G"], rhs = [0])

            # remainder at any time t <= maxRemainder
            thevars = [self.dv_remainder[t], self.dv_remainderMax]
            coeffs = [1, -1]
            self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                     senses = ["L"], rhs = [0])

            # remainder = fluctuations + electrical load/generation by all heating devices for all time steps t
            thevars = [self.dv_remainder[t]]
            coeff = [1]
            for b in rangeBesPri:
                thevars.append(self.dv_MODLVL1[b][t])
                thevars.append(self.dv_MODLVL2[b][t])
                coeff.append(-listBesPri[b].getNominalElectricalPower1() / listBesPri[b].getModlvls1() * self.stepSize)
                coeff.append(-listBesPri[b].getNominalElectricalPower2() * self.stepSize)
            self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeff)],
                                     senses = ["E"], rhs = [_fluctuationsCurve[t]])

    def addLclOptimizationsToCplexModel(self, fromTime):
        """
        method adds decision variables and constraints to the cplex MIP model (c) that are needed if the global
        optimization also considers BESs' local objectives

        1.  define python variables needed to define the MIP components needed for local optimization
        2.  define energy/power curves needed to define the MIP

        3.  define all decision variables needed for local optimization
            (B: number of BESs / T: number of time steps incl. dummy time step t=0 for previous day):

            a) decision variables for BESs with objFcn = 1
                dv_switchOn, dv_switchOff                   (B_objFcn_1 x T)
                dv_switchSum                                (B_objFcn_1)            <<< locally minimized

            b) decision variables for BESs with objFcn = 2:
                dv_EElGrid                                  (B_objFcn_2 x T)
                dv_EElGridDmnd, dv_EElGridFeed              (B_objFcn_2 x T)
                dv_EElGridDmndOrFeedSum                     (B_objFcn_2)            <<< locally minimized
                                                                                        for CHPs: demand, for HPs: feed

        5.  define all constraints needed for local optimization
            b) define constraints for BESs with objFcn = 1
            c) define constraints for BESs with objFcn = 2

        :param fromTime: fromTime in seconds
        """


        # ==============================================================================================================
        # py-variables
        # ==============================================================================================================

        toTimeH = fromTime + (self.hSteps - 1) * self.stepSize

        rangeHorizonFrom1 = range(1, self.hSteps+1)         # step array (1,2 ... 24)
        rangeHorizonFrom0 = range(0, self.hSteps+1)         # dummy    (0,1,2 ... 24)

        # number & list of primary heaters
        noBesPri = self.getNumberOfMembers(typeHeater="primary")
        rangeBesPri = range(noBesPri)
        listBesPri = self.getBESs(typeHeater="primary")
        noBesPri_beforeObjFcn2 = len([listBesPri[b] for b in rangeBesPri if listBesPri[b].getObjFcn() is 1])
        rangeBesPri_objFcn1 = range(noBesPri_beforeObjFcn2)
        rangeBesPri_objFcn2 = range(noBesPri_beforeObjFcn2, len(listBesPri))



        # ==============================================================================================================
        # curves
        # ==============================================================================================================

        # curves needed to define MIP components needed for local optimization including a dummy-zero for t=0 to
        # simplify iterations later

        # BES values:
        _onSitePVGenerationCurves = np.zeros((noBesPri, self.hSteps+1))
        _electricalDemandCurves = np.zeros((noBesPri, self.hSteps+1))

        for b in rangeBesPri:
            _onSitePVGenerationCurves[b] = np.append([0], listBesPri[b].getOnSitePVGenerationCurve(fromTime, toTimeH)[1, :])
            _electricalDemandCurves[b] = np.append([0], listBesPri[b].getElectricalDemandCurve(fromTime, toTimeH)[1, :])


        # ==============================================================================================================
        # decision variables
        # ==============================================================================================================

        # objFcn = 1
        # ==============================================================================================================

        # switching primary heater to on (1 if switched on from time t-1 to t, dummy for 0)
        # ------------------------------------------------------------------------------------------------------

        self.dv_switchOn = [['dv_switchOn_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri_objFcn1]
        for b in rangeBesPri_objFcn1:
            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_switchOn[b][t]],
                                lb = [0],
                                ub = [1],
                                types = [self.c.variables.type.binary])

        # switching primary heater to off (1 if switched off from time t-1 to t, dummy for 0)
        # ------------------------------------------------------------------------------------------------------

        self.dv_switchOff = [['dv_switchOff_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri_objFcn1]
        for b in rangeBesPri_objFcn1:
            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_switchOff[b][t]],
                                lb = [0],
                                ub = [1],
                                types = [self.c.variables.type.binary])

        # sum of switching events in switchOn and switchOff
        # ------------------------------------------------------------------------------------------------------

        # todo: find out about optimized value! check this for absGap = 0.
        self.dv_switchSum = ['dv_switchOff_' + str(b) for b in rangeBesPri_objFcn1]
        for b in rangeBesPri_objFcn1:
            self.c.variables.add(names = [self.dv_switchSum[b]],
                            lb = [0],
                            ub = [listBesPri[b].getOptimizedCriterionValue() + listBesPri[b].getSolPoolAbsGap()],             # !!! this sets the upper bound to the minimum switching sum achieved by the local optimization !!!
                            types = [self.c.variables.type.integer])


        # objFcn = 2
        # ==============================================================================================================

        # define decision variables' names & add to problem later as multiple variables use the same bounds
        self.dv_EElGrid = [['dv_EElGrid_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri_objFcn2]
        self.dv_EElGridDmnd = [['dv_EElGridDmnd_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri_objFcn2]
        self.dv_EElGridFeed = [['dv_EElGridFeed_' + str(b) + '_' + str(t) for t in rangeHorizonFrom0] for b in rangeBesPri_objFcn2]
        self.dv_EElGridDmndOrFeedSum = ['dv_EElGridDmndOrFeedSum_' + str(b) for b in rangeBesPri_objFcn2]

        for b in rangeBesPri_objFcn2:
            # calculate bounds for multiple EElGrid variables
            minEELGrid = _electricalDemandCurves[b] + _onSitePVGenerationCurves[b] - self.stepSize * abs(listBesPri[b].getNominalElectricalPower1()) - self.stepSize * abs(listBesPri[b].getNominalElectricalPower2())
            maxEELGrid = _electricalDemandCurves[b] + _onSitePVGenerationCurves[b] + self.stepSize * abs(listBesPri[b].getNominalElectricalPower1()) + self.stepSize * abs(listBesPri[b].getNominalElectricalPower2())
            minEELGrid[0] = 0
            maxEELGrid[0] = 0
            # if maximum EELGrid is < 0 or minimum EELGrid is > 0, define proper upper bounds for feed & dmnd variables
            dmndUB = [ maxEELGrid[t] if maxEELGrid[t] > 0 else 0.0 for t in rangeHorizonFrom0]
            feedUB = [-minEELGrid[t] if minEELGrid[t] < 0 else 0.0 for t in rangeHorizonFrom0]

            # energy demand from / feed into grid
            # ----------------------------------------------------------------------------------------------------------
            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_EElGrid[b-noBesPri_beforeObjFcn2][t]],
                                lb = [minEELGrid[t]],
                                ub = [maxEELGrid[t]],
                                types = [self.c.variables.type.continuous])

            # energy demand from grid
            # ----------------------------------------------------------------------------------------------------------
            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_EElGridDmnd[b-noBesPri_beforeObjFcn2][t]],
                                lb = [0],
                                ub = [dmndUB[t]],
                                types = [self.c.variables.type.continuous])

            # energy feed into grid
            # ----------------------------------------------------------------------------------------------------------
            for t in rangeHorizonFrom0:
                self.c.variables.add(names = [self.dv_EElGridFeed[b-noBesPri_beforeObjFcn2][t]],
                                lb = [0],
                                ub = [feedUB[t]],
                                types = [self.c.variables.type.continuous])

            # demand or feed sum, depending on type of heater (CHP or HP), to be minimized
            # ----------------------------------------------------------------------------------------------------------
            self.c.variables.add(names = [self.dv_EElGridDmndOrFeedSum[b-noBesPri_beforeObjFcn2]],
                            lb = [0],
                            ub = [listBesPri[b].getOptimizedCriterionValue() + listBesPri[b].calcAbsGap(fromTime, toTimeH, solveFirst=False)],  # !!! this sets the upper bound to the local optimization value + relative gap
                            types = [self.c.variables.type.continuous])




        # ==============================================================================================================
        # constraints
        # ==============================================================================================================

        # objFcn = 1
        # ==============================================================================================================

        for b in rangeBesPri_objFcn1:

            # sum of switching events: switchSum = sum(switchOn) + sum(switchOff)
            thevars = []
            for t in rangeHorizonFrom1:
                thevars.append(self.dv_switchOn [b][t])
                thevars.append(self.dv_switchOff[b][t])
            thevars.append(self.dv_switchSum[b])
            coeffs = [1]*2*self.hSteps
            coeffs.append(-1)
            self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)], senses = ["E"], rhs = [0])


            # constraints for all further time steps t > 0
            # ----------------------------------------------------------------------------------------------------------

            for t in rangeHorizonFrom1:

                # sync switchOn/Off and MODLVL
                thevars = [self.dv_MODLVL1[b][t], self.dv_MODLVL1[b][t-1], self.dv_switchOn[b][t], self.dv_switchOff[b][t]]
                coeffs  = [1,-1,-1, 1]
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                         senses = ["E"], rhs = [0])

                # sync switchOn & switchOff
                thevars = [self.dv_switchOn[b][t], self.dv_switchOff[b][t]]
                coeffs  = [1, 1]
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                         senses = ["L"], rhs = [1])


        # objFcn = 2
        # ==============================================================================================================

        for b in rangeBesPri_objFcn2:

            if listBesPri[b].getNominalElectricalPower1() > 0:       # HP
                # define sum of energy feed into grid
                coeffs = [1] * self.hSteps
                coeffs.append(-1)
                thevars = []
                for t in rangeHorizonFrom1:
                    thevars.append(self.dv_EElGridFeed[b-noBesPri_beforeObjFcn2][t])
                thevars.append(self.dv_EElGridDmndOrFeedSum[b-noBesPri_beforeObjFcn2])
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)], senses = ["E"], rhs = [0])

            elif listBesPri[b].getNominalElectricalPower1() < 0:     # CHP
                # define sum of energy demand from grid
                coeffs = [1] * self.hSteps
                coeffs.append(-1)
                thevars = []
                for t in rangeHorizonFrom1:
                    thevars.append(self.dv_EElGridDmnd[b-noBesPri_beforeObjFcn2][t])
                thevars.append(self.dv_EElGridDmndOrFeedSum[b-noBesPri_beforeObjFcn2])
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)], senses = ["E"], rhs = [0])

            # constraints for all further time steps t > 0
            # ----------------------------------------------------------------------------------------------------------

            for t in rangeHorizonFrom1:

                # energy demand from grid =     electrical demand
                #                           +   energy consumed by primary heating device (negative for CHP)
                #                           +   energy consumed by secondary heating device (positive for HP, zero for CHP)
                #                           -   solar energy from on site generation
                thevars = [self.dv_EElGrid[b-noBesPri_beforeObjFcn2][t], self.dv_MODLVL1[b][t], self.dv_MODLVL2[b][t]]
                coeffs = [1, -listBesPri[b].getNominalElectricalPower1() * self.stepSize / listBesPri[b].getModlvls1(), -listBesPri[b].getNominalElectricalPower2() * self.stepSize]
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                         senses = ["E"], rhs = [_electricalDemandCurves[b][t] + _onSitePVGenerationCurves[b][t]])

                # EELGrid = EELGrid_Dmnd - EELGrid_Feed
                thevars = [self.dv_EElGrid[b-noBesPri_beforeObjFcn2][t], self.dv_EElGridDmnd[b-noBesPri_beforeObjFcn2][t], self.dv_EElGridFeed[b-noBesPri_beforeObjFcn2][t]]
                coeffs = [1, -1, 1]
                self.c.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars, coeffs)],
                                         senses = ["E"], rhs = [0])

    def addMIPStartValues(self):
        """
        add start values to cplex MIP problem to provide optimizer with a first feasible solution to start with, thus
        reducing run time. start values are taken from the local optimization that must have been run earlier for each
        BES
        """

        listBesPri = self.getBESs(typeHeater='primary')
        noBesPri = self.getNumberOfMembers(typeHeater = 'primary')

        startValNames = list()
        startVals = list()

        print("noBesPri", noBesPri)
        print("listBesPri", len(listBesPri))
        print("dv_MODLVL1: ", len(self.dv_MODLVL1))
        print("range(self.hSteps+1): ", range(self.hSteps+1))

        for b in range(noBesPri):
            for t in range(1, self.hSteps+1):  # t starting from 0 to avoid reset of MODLVLini
                startValNames.append(self.dv_MODLVL1[b][t])
                #startValNames.append(self.dv_MODLVL2[b][t])
                startVals.append(int(round(listBesPri[b].getLocallyOptimalSchedule()[t])))
                #startVals.append(listBesPri[b].getLocallyOptimalScheduleSec()[t])

        self.c.MIP_starts.add(cplex.SparsePair(ind = startValNames, val = startVals), self.c.MIP_starts.effort_level.solve_MIP)

    def setCplexSolverParameters(self):
        """
        set cplex's solver parameters, such as time limit, number of threads, log streams, etc.
        """

        # logs
        # --------------------------------------------------------------------------------------------------------------

        # self.c.set_results_stream("logfile.res")
        # self.c.set_error_stream("logfile.err")
        # self.c.set_warning_stream("logfile.war")
        # self.c.set_log_stream("logfile.log")

        # solver limits
        # --------------------------------------------------------------------------------------------------------------

        self.c.parameters.timelimit.set(300.0)
        self.c.parameters.tune.timelimit.set(100.0)


        # self.c.parameters.dettimelimit.set(600000)
        # self.c.parameters.threads.set(4)
        # # self.c.parameters.mip.limits.treememory.set(2000)
        # # self.c.parameters.workmem.set(128)
        #
        # # self.c.setVerbosity(self, 3)
        # self.c.parameters.mip.tolerances.mipgap.set(0.1)
        # self.c.parameters.emphasis.mip.set(2)  # 2: optimality
        # # self.c.parameters.mip.strategy.dive(2)
        # self.c.parameters.mip.strategy.dive.set(2)
        # self.c.parameters.mip.strategy.file.set(3)

        # self.c.parameters.write_file("cpxParameters1.txt")
        # _test = self.c.parameters.get_changed()
        # print _test
        self.c.parameters.tune_problem()
        self.c.parameters.write_file("cpxParameters2.txt")

    def assignLocalSolution(self, fromTime):
        """
        assign the locally optimal solutions to all BESs and assign the respective remainder to cluster
        :return:
        """

        listBesPri = self.getBESs(typeHeater='primary')

        #print("self.iSteps: ", self.iSteps)

        # assign schedule data (SMARTBESs)
        for b in range(len(listBesPri)):
            #print("Schedule: ", np.asarray(listBesPri[b].getLocallyOptimalSchedule()).astype(np.int))
            # set schedules
            listBesPri[b].setSchedule(listBesPri[b].getLocallyOptimalSchedule())            # set schedule
            listBesPri[b].setScheduleSec(listBesPri[b].getLocallyOptimalScheduleSec())      # set secondary schedule
            # MODLVL 1 EoD
            listBesPri[b].setStateModlvl(listBesPri[b].getSchedule()[self.iSteps])          # set current modulation level
            # set current state of charge (and avoid possible infeasibility)
            end_SOC = listBesPri[b].c.solution.get_values(listBesPri[b].ETHStorage)[self.iSteps] / listBesPri[b].getStorageCapacity()
            if end_SOC <= listBesPri[b].getSOCmin():
                end_SOC = listBesPri[b].getSOCmin()
            elif end_SOC >= listBesPri[b].getSOCmax():
                end_SOC = listBesPri[b].getSOCmax()
            listBesPri[b].setSOC(end_SOC)
            #print("listBesPri[b].getStateModlvl: ", listBesPri[b].getStateModlvl())

        # calculate and assign resulting remainder based on locally optimal schedules
        self.assignRemainderAfterLocalOptimization(fromTime)

    def assignGlobalSolution(self):
        """
        assign cplex's global solution to both the cluster and all its comprised BESs
        """

        listBesPri = self.getBESs(typeHeater='primary')
        sol = self.c.solution

        # assign remainder (CLUSTER)
        self.remainder = sol.get_values(self.dv_remainder[1:][0:self.iSteps])   # assign remainder for interval only

        # assign schedule data (SMARTBESs)
        for b in range(len(listBesPri)):
            # schedules 1 & 2
            listBesPri[b].setSchedule(sol.get_values(self.dv_MODLVL1[b]))
            listBesPri[b].setScheduleSec(sol.get_values(self.dv_MODLVL2[b]))
            # MODLVL 1
            listBesPri[b].setStateModlvl(sol.get_values(self.dv_MODLVL1[b][self.iSteps]))
            # SOC (correct if floating point issues occuring)
            end_SOC = sol.get_values(self.dv_EThStorage[b][self.iSteps]) / listBesPri[b].getStorageCapacity()
            if end_SOC <= listBesPri[b].getSOCmin():
                end_SOC = listBesPri[b].getSOCmin()
            elif end_SOC >= listBesPri[b].getSOCmax():
                end_SOC = listBesPri[b].getSOCmax()
            listBesPri[b].setSOC(end_SOC)

    def calcSchedules(self, fromTime, globalCoordination=True, localOptimization=True):
        """
        MAIN METHOD FOR CENTRALIZED CLUSTER

        runs the entire optimization process, including prior local optimizations for all BESs to define upper
        bounds for locally optimized values, creating all decision variables and constraints, adding start values to
        MIP, setting cplex solver parameters, solving the MIP, assigning respective values to BESs and cluster itself
        and calculating the achieved performance in fluctuations reduction

        :param algorithm: fromTime
        :param fromTime: fromTime
        :return: achieved performance
        """

        if globalCoordination == False and localOptimization == False:
            print "no optimization chosen. returning from *calcSchedules()*"
            return

        toTimeI = fromTime + (self.iSteps - 1) * self.stepSize

        # LOCAL ONLY
        # --------------------------------------------------------------------------------------------------------------
        if globalCoordination == False and localOptimization == True:

            # run local optimization for each BES and assign solutions
            self.runLclOptimization(fromTime)

            # assign the locally calculated schedules etc. to BESs and assign the resulting remainder to cluster
            self.assignLocalSolution(fromTime)


        # GLOBAL
        # --------------------------------------------------------------------------------------------------------------
        if globalCoordination == True:

            # optimize locally for each BES to create MIP start values and to create upper bounds for global MIP (only for local optimization)
            self.runLclOptimization(fromTime)

            # sort heaters by their respective objFcn for correct iterations & ranges (required for global coordination)
            self.sortPrimaryHeatersByObjFcn()

            # create global cplex optimization model (decision variables & constraints)
            self.createGlobalCplexModel(fromTime)


        # GLOBAL + LOCAL
        # --------------------------------------------------------------------------------------------------------------
        if globalCoordination == True and localOptimization == True:

            # add further decision variables & constraints to global MIP to consider local objectives
            self.addLclOptimizationsToCplexModel(fromTime)


        # GLOBAL cont'd
        # --------------------------------------------------------------------------------------------------------------
        if globalCoordination == True:

            # add local solutions to global MIP as start values
            self.addMIPStartValues()

            # set cplex's solver parameters for the global MIP (e.g. time limit, number of threads, log streams...)
            self.setCplexSolverParameters()

            # solve the global MIP
            self.c.solve()

            # debug
            _status = self.c.solution.get_status()
            x = 0
            print("Status solver: {}".format(_status))

            # solution status: http://eaton.math.rpi.edu/cplex90html/refcallablelibrary/html/optim.cplex.solutionstatus/group.html
            if _status == 108:
                self.c.write(fromTime + ".lp")
                self.c.MIP_starts.write(fromTime + ".mst")
                exit()
                # x = x + 1
                # print("Additional iteration: {}".format(x + 1))
                # print("Status: {}".format(_status))
                # _timelimit = min(x * 900.0, 3600.0)
                # self.c.parameters.timelimit.set(_timelimit)
                # self.c.solve()
                # _status = self.c.solution.get_status()

            # assign the solution to BES-objects and to cluster-object
            self.assignGlobalSolution()


        # --------------------------------------------------------------------------------------------------------------
        # calculate performance measure
        # --------------------------------------------------------------------------------------------------------------

        performance = self.calcPerformanceMeasure(self.remainder, self.getFluctuationsCurve(fromTime, toTimeI), criterion='RPV')

        return performance





