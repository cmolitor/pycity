__author__ = 'Sonja Kolen'

from bes_agent import BesAgent
import random

class UncoordAgent(BesAgent):
    def __init__(self, message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=None):
        """
        class UncoordAgent inherits from class BesAgent (and SmartBes)
        constructor of UncoordAgent
        :param stepSize: size of time slot in seconds [s]
        :param TER1: ratio between thermal and electrical power for primary heating system: for EH/HP > 0, COP; for CHP < 0, sigma; for gas boiler = 0;
        :param TER2: ratio between thermal and electrical power for secondary heating system: for EH/HP > 0, COP; for CHP < 0, sigma; for gas boiler = 0
        :param RSC: ratio of storage capacity to  energy output of heater in one hour (3600s); e.g. Pthnom = 10kW and ratioStorageCap = 3 means storage capacity of 30kWh
        :param sizingMethod: share of thermal energy demand which can be covered by main heater; 1: all, < 1: there might be situations that the thermal demand power is higher then the nominal power of the heater
        :param iApartments: number of apartments within the building
        :param sqm: sqm per apartment [m^2]
        :param specDemandTh: specific thermal demand per sqm and year [kWh/(m^2 a)]
        :param ID: ID used for identification of each agent in communication network
        :param solutionPoolIntensity: solution pool intensity of cplex solver (1-4)
        :param absGap: absolute gap to optimal solution accepted by the cplex solver
        :param envirmt: the environment for the UncoordAgent
        :return:
        """
        super(UncoordAgent, self).__init__(message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=envirmt)

    #########################################################
    ############ MESSAGING and NETWORK FUNCTIONS ############
    #########################################################

    def messageHandler(self):
        """
        processes incoming messages, for UncoordAgent no messages to process
        :return:
        """

        return 0

    #########################################################
    ##### UNCOORDINATED SCHEDULE SELECTION FUNCTIONS ########
    #########################################################

    def initUncoordScheduleSelection(self):
        """
        initialize Uncoordinated Schedule Selection Algorithm
        -> init pseudo random number generator
        :return:
        """
        random.seed()
        return

    def startUncoordScheduleSelection(self, fromTime, toTime):
        """
        calc schedule pool and select a random schedule from the pool
        :param fromTime: start time
        :param toTime: end time
        :return:
        """
        #calc schedule pool
        self.calcSchedulePool(fromTime, toTime)
        self.calcScheduleConsumptionCurves()

        if len(self.schedules) > 1: # more than one schedule calculated
            #choose a random schedule out of the pool
            idx = random.randint(0, len(self.schedules)-1)
            self.chosenScheduleIndex = idx

        else: # only one schedule calculated
            self.chosenScheduleIndex = 0

        self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
        self.EConsumptionChosenSchedule = self.EConsumptionScheduleCurves[self.chosenScheduleIndex]
        self.setStateModlvl(self.chosenSchedule[-1])
        self.setSOC(self.SOCEnd[self.chosenScheduleIndex])