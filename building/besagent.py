__author__ = 'Christoph Molitor'

import numpy as np
import math
from building.buildingagent import BuildingAgent

class BesAgent(BuildingAgent):  # subclass inherits from class Building
    def __init__(self, container, name, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, envrnmt=None):
        """
        Constructor of Bes (Building Energy System)
        :param stepSize: size of time slot in seconds [s]
        :param TER1: ratio between thermal and electrical power of primary heater: for EH/HP < 0, COP; for CHP > 0, sigma; for gas boiler = 0;
        :param TER2: ratio between thermal and electrical power of secondary heater: for EH/HP < 0, COP; for CHP > 0, sigma; for gas boiler = 0;
        :param RSC: ratio of storage capacity to  energy output of heater in one hour (3600s); e.g. Pthnom = 10kW and ratioStorageCap = 3 means storage capacity of 30kWh
        :param sizingMethod: share of thermal energy demand which can be covered by main heater; 1: all, < 1: there might be situations that the thermal demand power is higher then the nominal power of the heater
        :param iApartments: number of apartments within the building
        :param sqm: sqm per apartment [m^2]
        :param specDemandTh: specific thermal demand per sqm and year [kWh/(m^2 a)]
        :param envrnmt: environment where BES is located and which contains ambient data

        sign of CHP and HP data:
                El. NomPower    Th. NomPower    TERx
        CHP:    -               -               +
        HP:     +               -               -
        EH:     +               -               -
        """
        super(BesAgent, self).__init__(container, name, iApartments, sqm, specDemandTh, stepSize)
        self.stepSize = stepSize  # in seconds
        self.TER1 = TER1  # < 0: EH/HP; > 0: CHP; == 0: gas boiler; numerical value is also the COP
        self.TER2 = TER2  # < 0: EH/HP; > 0: CHP; == 0: gas boiler; numerical value is also the COP
        self.storageCap = 0  # in Ws
        self.sizingMethod = sizingMethod
        self.pthnom1 = 0  # Nominal thermal power of primary thermal generator [W]
        self.pthnom2 = 0  # Nominal thermal power of secondary heater [W]
        self.pelnom1 = 0  # Nominal electrical power of primary thermal heater [W]
        self.pelnom2 = 0  # Nominal electrical power of secondary thermal heater [W]
        self.SOC = 0.5  # state of charge of the internal storage (e.g. water tank)
        self.modlvls1 = 1  # 1 means that device can be on or off; 2 means: 50% on, 100% on or off, ...
        self.stateModlvl = 0  # variable to store a state of the modlvl;
            # useful to save the state at the end of a scheduling interval and
            # use it as start value for the next scheduling horizon
        self.swtchOn1EOD = 0  # switch on vent at end of day
        self.swtchOff1EOD = 0  # switch off vent at end of day
        self.SOCmin = 0.0
        self.SOCmax = 1.0
        self.minRuntime1 = self.stepSize  # Minimum runtime of primary heater; here initialized as stepSize thus no impact
        self.minRuntime2 = self.stepSize  # Minimum runtime of secondary heater; here initialized as stepSize thus no impact

        self.environment = envrnmt
        self.TER1dyn = 0

        # Parameters for HP
        self.bivalence_temperature = 273.15 - 5.0
        self.HP_A2W55_COP = -self.TER1
        self.HP_A2W55_Tsource = 273.15 + 2
        self.HP_A2W55_Tsink = 273.15 + 55
        # Values for Dimplex LA 12TU (http://www.dimplex.de/pdf/de/produktattribute/produkt_1725609_extern_egd.pdf)
        # Tsource   Flow Temperature (Heat power/COP)
        #           W35             W45             W55
        # A-20	    4,89 kW/1,91	4,70 kW/1,48	4,50 kW/1,20
        # A-15	    5,87 kW/2,28	5,70 kW/1,77	5,50 kW/1,45
        # A-7	    7,60 kW/3,00	7,35 kW/2,30	7,17 kW/1,88
        # A2	    9,60 kW/3,70	9,10 kW/2,84	8,80 kW/2,32
        # A7	    11,40 kW/4,30	10,85 kW/3,42	9,80 kW/2,50
        # A10	    11,70 kW/4,60	11,20 kW/3,53	10,60 kW/2,75
        # A12	    12,20 kW/4,78	11,40 kW/3,56	10,90 kW/2,87
        # A20	    13,60 kW/5,33	12,80 kW/4,06	12,39 kW/3,30

        # calculate dimension of heating system
        self.sizeHeatingSystem(self.sizingMethod)

        # calculate storage size depending on nominal power of heating system
        self.setStorageCapacity(RSC)

        self.PVSystem = None

    def sizeHeatingSystem(self, sizingMethod):
        #get thermal demand curve for the whole building
        # unit of thermal demand curve: Ws
        _ThermalDemandCurve = self.getThermalDemandCurve(0, 366 * 24 * 60 * 60)  # from beginning to end of year (here 2012: leap year)

        # Calculate load duration curve which is needed to define the nominal thermal power of the heating system of each device later on
        _LoadDuration_thermal = np.sort(_ThermalDemandCurve, axis=1)  # sorts both columns ascending
        # print("_LoadDuration_thermal: {}".format(_LoadDuration_thermal))
        LoadDuration_thermal = np.zeros((4, _LoadDuration_thermal.shape[1]))
        # print("bes1:", LoadDuration_thermal)
        LoadDuration_thermal[0, :] = _LoadDuration_thermal[0, :]
        # print("bes2:", LoadDuration_thermal)
        LoadDuration_thermal[1, :] = _LoadDuration_thermal[1, :]
        # print("bes3:", LoadDuration_thermal)
        LoadDuration_thermal[2, :] = _LoadDuration_thermal.cumsum(1)[1, :]
        # print("bes4:", LoadDuration_thermal)

        # Calculate curve to derive the maximum rectangle
        _LoadDuration_thermal_reverse = _LoadDuration_thermal[1, :]
        _LoadDuration_thermal_reverse = _LoadDuration_thermal_reverse[::-1]  # reverting
        LoadDuration_thermal[3, :] =_LoadDuration_thermal_reverse * _LoadDuration_thermal[0, :]
        # print("bes5:", LoadDuration_thermal)

        #for tr in range (0, len(LoadDuration_thermal[1, :])):
        #    print LoadDuration_thermal[0, tr], LoadDuration_thermal[1, tr], LoadDuration_thermal[2, tr],  LoadDuration_thermal[3, tr]

        # print("MRM:", LoadDuration_thermal)
        #print("max MRM:", max(LoadDuration_thermal[3, :]))

        if sizingMethod > 0:
            # Derive the nominal power of the main thermal generator and an optional backup heater depending on sqm and specific thermal demand
            search = 0
            i = -1
            LoadDuration_thermal_0_max = LoadDuration_thermal[0, :].max()
            LoadDuration_thermal_2_max = LoadDuration_thermal[2, :].max()
            while search < 1:
                i += 1
                # term1 is the energy which can be covered by sizing the thermal power of the device the same as the current value the load duration curve
                term1 = LoadDuration_thermal[2, i] + LoadDuration_thermal[1, i]/self.stepSize * (LoadDuration_thermal_0_max - LoadDuration_thermal[0, i])
                # term2 represents the amount of energy which can be covered by a device with the defined coverage rate
                term2 = sizingMethod * LoadDuration_thermal_2_max
                # print term1, term2
                if term1 >= term2:
                    search = 1
                    self.pthnom1 = -np.ceil(LoadDuration_thermal[1, i])/self.stepSize  # thermal generator: negative sign
                    # calculate nominal electrical power of primary heater

            if self.getTER1() != 0:
                self.pelnom1 = self.pthnom1/self.getTER1()
            else:
                self.pelnom1 = 0

            # size Backup Heater
            self.pthnom2 = -np.ceil(max(LoadDuration_thermal[1, :])/self.stepSize + self.pthnom1)  # thermal generator: negative sign

            # store TER for each time step; this is not needed for CHP systems but to be compatible on a higher level with HP systems
            _TER1dyn = np.zeros_like(LoadDuration_thermal[0, :]) + self.getTER1()
            self.TER1dyn = np.vstack((LoadDuration_thermal[0, :], _TER1dyn))

        elif sizingMethod == -1:
            # CAREFUL: here only used for CHP systems
            # sizeHS == -1: apply maximum rectangle method for sizing the primary heater according to:
            # D. Haeseldonckx, L. Peeters, L. Helsen, and W. D'haeseleer, "The impact of thermal storage on the operational
            # behaviour of residential CHP facilities and the overall CO2 emissions," Renewable and Sustainable Energy Reviews,
            # vol. 11, no. 6, pp. 1227-1243, Aug. 2007.

            index =  (np.where(LoadDuration_thermal[3, :] ==  max(LoadDuration_thermal[3, :])))[0]
            self.pthnom1 = -(_LoadDuration_thermal_reverse[index]/self.stepSize)[0]

            # calculate nominal electrical power of primary heater
            if self.getTER1() != 0:
                self.pelnom1 = self.pthnom1/self.getTER1()
            else:
                self.pelnom1 = 0

            # size Backup Heater
            self.pthnom2 = -np.ceil(max(LoadDuration_thermal[1, :])/self.stepSize + self.pthnom1)  # thermal generator: negative sign

            # store TER for each time step; this is not needed for CHP systems but to be compatible on a higher level with HP systems
            _TER1dyn = np.zeros_like(LoadDuration_thermal[0, :]) + self.getTER1()
            _TER1dyn = _TER1dyn * self.getTER1()/abs(self.getTER1())
            self.TER1dyn = np.vstack((LoadDuration_thermal[0, :], _TER1dyn))

        # print self.pthnom
        elif sizingMethod == -2:
            # here sizing of heat pump systems
            if self.environment is None:
                print("Environment of BEs not set. No dimensioning of HP possible")
                return -1
            Tamb = self.environment.getTemperatureCurve(0, 366 * 24 * 60 * 60)

            # Sort ambient temperature and heatdemand: Assumption: 100% negative correlation between both
            sort_temperature = np.sort(Tamb[1, :])
            sort_heatdemand = np.flipud(LoadDuration_thermal[1, :])

            # Find all values that correspond with the bivalence temperature
            min_index = np.argmax(sort_temperature >= self.bivalence_temperature)
            max_index = np.argmin(sort_temperature <= self.bivalence_temperature)

            # Extract the bivalence heat demand
            hd_bivalence = np.mean(sort_heatdemand[min_index:max_index])/self.stepSize

            # Get the COP at the bivalence and minimum temperature
            Tamb_min = np.min(sort_temperature)
            _COP = self.calcHPdynCOP(np.array([self.bivalence_temperature, Tamb_min]),
                                              self.HP_A2W55_COP,
                                              self.HP_A2W55_Tsource,
                                              self.HP_A2W55_Tsink)
            COP_bivalence = _COP[0]
            COP_min = _COP[1]
            # print("COP_bivalence", COP_bivalence)
            # print("COP_min", COP_min)

            # Compute the electricity consumption of the HP unit.
            # Assumption: Constant electricity consumption of the HP
            self.pelnom1 = hd_bivalence/COP_bivalence
            self.pthnom1 = -math.ceil(self.pelnom1 * self.HP_A2W55_COP / 100.0) * 100.0  # some rounding

            # Thermal output of heat pump at lowest temperature
            pthmin1 = self.pelnom1 * COP_min
            # print("pthmin1", pthmin1)

            # get maximal thermal demand of the time period
            pth_demand_max = np.max(LoadDuration_thermal[1, :])/self.stepSize
            # print("pth_demand_max", pth_demand_max)

            # calculate power of secondary heater in order to cover missing thermal power at lowest temperature
            self.pthnom2 = -(pth_demand_max-pthmin1) * 1.1  # overdimensioning by 10%

            _TER1dyn = self.calcHPdynCOP(Tamb[1, :], self.HP_A2W55_COP, self.HP_A2W55_Tsource, self.HP_A2W55_Tsink)
            _TER1dyn = _TER1dyn * self.getTER1()/abs(self.getTER1())
            self.TER1dyn = np.vstack((Tamb[0, :], _TER1dyn))
        else:
            print("Sizing of HS did not work well")
            return -1

        # calculate nominal electrical power of secondary heater
        if self.getTER2() != 0:
            self.pelnom2 = self.pthnom2/self.getTER2()
        else:
            self.pelnom2 = 0

        # print("Pthnom1:", self.pthnom1)
        # print("Pthnom2:", self.pthnom2)
        #print("Pelnom1:", self.pelnom1)
        #print("Pelnom2:", self.pelnom2)

    def calcHeatingCurve(self, Tamb, m=0.33, set_room=293.15, set_ambient=263.15, set_flow=273.15+55, set_return=273.15+45):
        """ This function is a straight-forward implementation of the heatingCurve
            algorithm of the EBC Modelica library (Cities.Supply.BaseClasses.heatingCurve)
        The parameters are:
            ambient_temperature: Temperature time series in K
                (Note: ambient_temperature should be a 1-dimensional numpy-array)
            m:                   Heater characteristic. Normally: 0.25 <= m <= 0.40
            set_room:            Room's set temperature in K
            set_ambient:         Nominal ambient temperature in K
            set_flow:            Nominal heater flow temperature in K
            set_return:          Nominal heater return temperature in K
        """

        # Determine design room excess temperature
        dTmN = (set_flow + set_return)/2 - set_room

        # Calculate design temperature spread of heating system
        dTN = set_flow - set_return

        # Compute load situation of heating system (parameter phi)
        phi = np.zeros_like(Tamb)
        phi[Tamb <= set_room] = (set_room - Tamb[Tamb <= set_room]) / (set_room - set_ambient)

        # Compute flow temperature according to heating curve
        flow_temp = np.power(phi, 1/(1 + m))*dTmN + 0.5*phi*dTN + set_room

        return flow_temp

    def calcHPdynCOP(self, Tamb, COP_AxWy=2.32, TsourceAx=2+273.15, TsinkWy=55+273.15):
        """
        Calculates the COP of air source HPs depending on source temperature and sink temperature. The sink temperature
        depends also on the source (ambient) temperature as a lower ambient temperature requires higher flow (sink) temperatures.
        :param Tamb: numpy array of ambient temperature
        :param COP_AxWy: COP value from data sheet of HP; e.g. COP_A2W35 means at 2 degrees C source temperature and 35 degrees C
        flow temperature
        :param TsourceAx: Source temperature according to COP_AxWy; e.g. in case COP_A2W35: 2 degree C
        :param TsinkWy: Sink temperature according to COP_AxWy; e.g. in case COP_A2W35: 35 degree C
        :return: numpy array of dynamic COP; same length like input array of Tamb
        """

        # calculation of qualityGrade of HP according to:
        # A. Schaefer, P. Baumanns, and A. Moser, "Modeling heat pumps as combined heat and power plants in energy generation planning,"
        # in Energytech, 2012 IEEE, 2012, pp. 1-6.
        _qualityGrade = COP_AxWy * (TsinkWy - TsourceAx)/TsinkWy

        # print("_qualityGrade", _qualityGrade)

        # get sink temperature
        Tsink_dyn = self.calcHeatingCurve(Tamb)

        # set lower limit of sink temperature and add offset (here: 5K) due to temperature drop at heat exchanger
        Tsink_dyn = Tsink_dyn + 5.0  # offset

        # set source temperature to ambient temperature and substract offset due to temperature drop at heat exchanger
        Tsource_dyn = Tamb - 5.0

        # limit source temperature
        Tsource_dyn[Tsource_dyn > (273.15+20)] = 273.15 + 20

        # calculate dynamic COP(Tsink, Tsource)
        COP_dyn = _qualityGrade * Tsink_dyn/(Tsink_dyn-Tsource_dyn)

        # limit COP to a value; here from data sheet
        COP_dyn[COP_dyn > 5.33] = 5.33

        # out = np.vstack((Tamb, Tsink_dyn, Tsource_dyn, COP_dyn))
        # np.savetxt("out.txt", out.T)
        return COP_dyn


    def getTER1(self, fromTime=0, toTime=0):
        """
        return thermal electrical ratio of primary heater
        :return: ratio between thermal and electrical power: for EH/HP < 0, COP; for CHP > 0, sigma; for gas boiler = 0;
        """
        if fromTime == 0 and toTime == 0:
            return self.TER1
        else:  # if time variant TER
            indFrom = min((np.asarray(np.where(self.TER1dyn[0, :] >= fromTime)))[0, :])
            indTo = max((np.asarray(np.where(self.TER1dyn[0, :] <= toTime)))[0, :]) + 1
            ret = np.zeros((2, indTo-indFrom))
            ret[0, :] = self.TER1dyn[0, indFrom:indTo]
            ret[1, :] = self.TER1dyn[1, indFrom:indTo]  # scale SLP to actual consumption
            #print("dynTER1:", ret, ret.shape)
            return ret

    def getTER2(self, fromTime=0, toTime=0):
        """
        return thermal electrical ratio of secondary heater
        :return: ratio between thermal and electrical power: for EH/HP < 0, COP; for CHP > 0, sigma; for gas boiler = 0;
        """
        if fromTime == 0 and toTime == 0:
            return self.TER2
        else:  # if time variant TER
            _time = np.arange(fromTime, toTime+self.stepSize, self.stepSize)
            ret = np.zeros((2, len(_time)))
            ret[0, :] = _time
            ret[1, :] = self.TER2 * np.ones_like(ret[0, :])
            #print("dynTER2:", ret, ret.shape)
            return ret

    def getNominalThermalPower1(self):
        """
        :return: pthnom: nominal thermal power of main heating device
        """
        return self.pthnom1

    def getNominalThermalPower2(self):
        """
        :return: pthnombackup: nominal thermal power of backup heating device
        """
        return self.pthnom2

    def getThermalPower1(self, fromTime, toTime):
        """
        return the maximum thermal output power of the primary heater in the defined time period
        :param: fromTime: start time of time period
        :param: toTime: end time of time period
        :return: Pth: thermal power output of primary heater
        """
        _TERdyn = self.getTER1(fromTime, toTime)
        Pth = np.zeros_like(_TERdyn)
        Pth[0, :] = _TERdyn[0, :]
        if self.getTER1() != 0:
            Pth[1, :] = _TERdyn[1, :] * self.getNominalElectricalPower1()
        else:
            Pth[1, :] = Pth[1, :] + self.getNominalThermalPower1()
        # print("SLPscaling:", self.scalingSLPth)
        return Pth

    def getThermalPower2(self, fromTime, toTime):
        """
        return the maximum thermal output power of the primary heater in the defined time period
        :param: fromTime: start time of time period
        :param: toTime: end time of time period
        :return: Pth: thermal power output of primary heater
        """
        _TERdyn = self.getTER2(fromTime, toTime)
        Pth = np.zeros_like(_TERdyn)
        Pth[0, :] = _TERdyn[0, :]
        if self.getTER2() != 0:
            Pth[1, :] = _TERdyn[1, :] * self.getNominalElectricalPower2()
        else:
            Pth[1, :] = Pth[1, :] + self.getNominalThermalPower2()
        # print("SLPscaling:", self.scalingSLPth)
        return Pth

    def getStorageCapacity(self):
        """
        :return: storage capacity [Ws]
        """
        return self.storageCap

    def getSOC(self):
        """
        :return: SOC: current state of charge (SOC)
        """
        return self.SOC

    def getSOCmin(self):
        """
        :return: SOCmin: minimal allowed value of SOC
        """
        return self.SOCmin

    def getSOCmax(self):
        """
        :return: SOCmax: maximum allowed value of SOC
        """
        return self.SOCmax

    def getModlvls1(self):
        """
        :return: modlvls: number of possible modulation levels (on state)
        """
        return self.modlvls1

    def getStateModlvl(self):
        """
        :return: stateModlvl: stored current modlvl
        """
        return self.stateModlvl

    def getNominalElectricalPower1(self):
        return self.pelnom1

    def getNominalElectricalPower2(self):
        return self.pelnom2

    def setSOC(self, SOC):
        """
        :param SOC: state of charge (SOC), 0<=SOC<=1
        """
        self.SOC = SOC

    def setSOCmin(self, SOCmin):
        """
        :param SOCmin: minimum allowed value of SOC
        """
        self.SOCmin = SOCmin

    def setSOCmax(self, SOCmax):
        """
        :param SOCmax: maximum allowed value of SOC
        """
        self.SOCmax = SOCmax

    def setModlvls(self, modlvls):
        """
        :param modlvls: number of possible modulation levels (on state)
        """
        self.modlvls1 = modlvls

    def setStateModlvl(self, modlvl):
        """
        :param modlvl: current modlvl which should be stored
        """
        self.stateModlvl = modlvl

    def setStorageCapacity(self, ratioStorageCap):
        """
        :param ratioStorageCap: ratio of storage capacity to  energy output of heater in one hour (3600s); e.g. Pthnom = 10kW and ratioStorageCap = 3 means storage capacity of 30kWh
        """
        self.storageCap = float(ratioStorageCap) * abs(self.pthnom1) * 3600

    def setMinRuntime1(self, minRuntime):
        """
        set minimum runtime of primary heater
        :param minRuntime: minimum runtime in seconds
        """
        self.minRuntime1 = minRuntime

    def setMinRuntime2(self, minRuntime):
        """
        set minimum runtime of secondary heater
        :param minRuntime: minimum runtime in seconds
        """
        self.minRuntime2 = minRuntime

    def getMinRuntime1(self):
        """
        get minimum runtime of primary heater
        """
        return self.minRuntime1

    def getMinRuntime2(self):
        """
        get minimum runtime of secondary heater
        """
        return self.minRuntime2

    def getSwtchOn1EOD(self):
        """
        get switch on event at end of day of primary heater
        """
        return self.swtchOn1EOD

    def getSwtchOff1EOD(self):
        """
        get switch off event at end of day of primary heater
        """
        return self.swtchOff1EOD

    def setSwtchOn1EOD(self, swtchOn):
        """
        set switch on event at end of day of primary heater
        """
        self.swtchOn1EOD = int(round(swtchOn))

    def setSwtchOff1EOD(self, swtchOff):
        """
        set switch off event at end of day of primary heater
        """
        self.swtchOff1EOD = int(round(swtchOff))

    def setEnvironment(self, env):
        self.environment = env

    def addPVSystem(self, PVSys):
        """
        adds a PV system to the BES or replaces the one in place (then printing a warning, though)
        :param PVSys: pv system to be added
        """
        if self.PVSystem is not None:
            print("Warning: Replacing an existing PV system.")
        self.PVSystem = PVSys

    def deletePVSystem(self):
        if self.PVSystem is None:
            print("BES does not hold a PV-System anyway.")
            return
        self.PVSystem.deletePVSystemFromEnvironment()
        self.PVSystem = None

    def getExternalElectricalDemandCurve(self, fromTime, toTime):
        """
        calculates the external electrical energy demand curve.
        external electrical demand = electrical demand + solar generation (negative values)
        :param fromTime: from time in seconds
        :param toTime: to time in seconds
        :return: [2 x steps] array of time (in sec) and external electrical demand (in Ws)
        """

        extElecDmnd = self.getElectricalDemandCurve(fromTime, toTime)                   # set up time values & electrical demand
        extElecDmnd[1, :] += self.getOnSitePVGenerationCurve(fromTime, toTime)[1, :]    # add solar generation (negative values) to electrical demand, leave time values

        return extElecDmnd

    def getOnSitePVGenerationCurve(self, fromTime, toTime):
        """
        if there is no pv system installed, an array containing zeros is returned.
        :return: 2 x n array of on site solar energy production over the course of the given time frame [sec, Ws]
        """
        timeSteps = (toTime-fromTime)/self.stepSize + 1   # no. of steps (e.g. hours)

        if self.PVSystem is None:
            timeArray = np.arange(fromTime, toTime+self.stepSize, self.stepSize)
            return np.vstack((timeArray, np.zeros(timeSteps)))
        else:
            return self.PVSystem.getGenerationCurve(fromTime, toTime)

    def getAnnualPVGeneration(self):
        if self.PVSystem is None:
            return 0
        else:
            return self.PVSystem.getAnnualGeneration()