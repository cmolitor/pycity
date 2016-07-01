__author__ = 'Sonja Kolen'

from bes_agent import BesAgent
import copy

class MulticastAgent(BesAgent):
    def __init__(self, message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=None):
        """
        class MulticastAgent inherits from class BesAgent (and SmartBes)
        constructor of MulticastAgent
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
        :param envirmt: the environment for the MulticastAgent
        :return:
        """
        super(MulticastAgent, self).__init__(message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=envirmt)

        # Variables used for multicast-based coordination algorithm
        self.origins = []                               # list of known origin BES for incoming remainder curves
        self.overall_min = 0                            # overall minimum
        self.overall_max_path_length= 0                 # saves overall maximal path length
        self.min_path = []                              # saves path corresponding to current minimum
        self.min_path_schedules = []                    # saves path_schedules corresponding to current minimum
        self.pathLengths = []                           # list of arrived path lengths
        self.globalMin = []                             # saves global minimal value
        self.globalMinSchedIdx = []                     # saves index of schedule that led to global min


    #########################################################
    ############ MESSAGING and NETWORK FUNCTIONS ############
    #########################################################

    def messageHandler(self):
        """
        processes incoming messages
        :return:
        """
        # all received messages will be processed
        while len(self.ReceiveMessageBuffer) > 0:
            msg = self.ReceiveMessageBuffer.popleft()
            self.MsgReceiveCount += 1
            self.MsgReceiveCount_interval += 1
            type = msg.getType()

            if type == 70:
                self.messageHandler_MulticastBasedCoordination(msg)      #remainder multicast optimization

        return 0

    #########################################################
    ################### GETTER FUNCTIONS ####################
    #########################################################

    def get_min_path(self):
        max_path_length = max(self.pathLengths)

        criterion_max_path_length = []
        origins_max_path_length = []
        for c in range(len(self.pathLengths)):
            if self.pathLengths[c] == max_path_length:
                criterion_max_path_length.append(self.globalMin[c])
                origins_max_path_length.append(self.origins[c])

        min_criterion = min(criterion_max_path_length)

        #find index
        for m in range(len(criterion_max_path_length)):
            if criterion_max_path_length[m] == min_criterion:
                break

        for s in range(len(self.origins)):
            if self.origins[s] == origins_max_path_length[m]:
                break
        return [self.min_path[s], self.min_path_schedules[s]]

    #########################################################
    ####### MULTICAST-BASED COORDINATION FUNCTIONS ##########
    #########################################################

    def initCoordination(self, fromTime, toTime, fluct, criterion_type):
        """
        initialize remainder multicast optimization (needs to be called for each BES
        participating in the optimization procedure
        :param fromTime: start time
        :param toTime: end time
        :param fluct: fluctuation curve
        :param criterion_type: type of optimization criterion, either 'maxmindiff' or 'absremainder'
        :return:
        """
        #reset
        self.MsgReceiveCount_interval = 0
        self.MsgSendCount_interval = 0
        self.origins = []
        self.pathLengths = []
        self.globalMin = []
        self.globalMinSchedIdx = []
        self.overall_min = 0
        self.overall_max_path_length = 0
        self.min_path = []
        self.min_path_schedules = []
        self.chosenSchedule = []
        self.schedules = []
        self.EConsumptionChosenSchedule = []
        self.chosenScheduleIndex = -1


        #save data
        self.fromTime = fromTime
        self.toTime = toTime
        self.noOfTimesteps = (self.toTime - self.fromTime) / self.stepSize + 1
        self.EFluctuationCurve = fluct
        self.OPTcriterion = criterion_type

        self.overall_max_path_length = 0
        if self.OPTcriterion == 'maxmindiff':
            self.overall_min = max(self.EFluctuationCurve) - min(self.EFluctuationCurve)
        elif self.OPTcriterion == 'absremainder':
            self.overall_min = 0
            for a in range(len(self.EFluctuationCurve)):
                self.overall_min += abs(self.EFluctuationCurve[a])

        #self.globalMin = [max(self.EFluctuationCurve) - min(self.EFluctuationCurve)


        #calc schedule pool and schedule load curves
        if not self.isGasBoiler():
            self.calcSchedulePool(fromTime, toTime)
            self.calcScheduleConsumptionCurves()
        return

    def startCoordination(self):
        """
        start remainder multicast optimization
        :return:
        """
        if not self.isGasBoiler():

            self.log_message('ID {0}: Start of Remainder Multicast Optimization'.format(self.CommID))
            #select initial schedule
            #print len(self.EFluctuationCurve)
            self.selectBestSchedule(self.EFluctuationCurve)

            #calc remainder
            remainder = [0 for i in range(len(self.EFluctuationCurve))]
            for t in range(len(self.EFluctuationCurve)):
                remainder[t] = self.EFluctuationCurve[t] + self.EConsumptionChosenSchedule[t]
            #save initial global minimum
            if self.OPTcriterion == 'maxmindiff':
                criterion = max(remainder) - min(remainder)
            elif self.OPTcriterion == 'absremainder':
                criterion = 0
                for a in range(len(remainder)):
                    criterion += abs(remainder[a])
            #max_min_diff = max(remainder) - min(remainder)
            self.origins.append(copy.deepcopy(self.CommID))
            self.globalMin.append(copy.deepcopy(criterion))                    #save minimum for origin self
            self.globalMinSchedIdx.append(copy.deepcopy(self.chosenScheduleIndex))
            self.pathLengths.append(1)
            self.min_path.append(copy.deepcopy(self.CommID))
            self.min_path_schedules.append(copy.deepcopy(self.chosenScheduleIndex))

            # send 'remainder' message to all neighbors
            # 'remainder' message has the following structure
            # ['remainder', origin, remainder_curve, path, path_schedules]
            for n in range(len(self.Neighbors)):
                data = ['remainder', copy.deepcopy(self.CommID), copy.deepcopy(remainder), copy.deepcopy([self.CommID]), copy.deepcopy([self.chosenScheduleIndex])]
                self.sendMessage(self.Neighbors[n], 70, data)
        else:
            print 'ID {0}: ERROR! Unable to start Remainder Multicast Optimization, because I am a gas boiler BES!'.format(self.CommID)

        return

    def analyseCoordination(self):
        """
        find best solution among all calculated solutions

        :return:
        """
        #create a list of criteria that correspond to maximal path length
        #max_path_length = max(self.pathLengths)

        #criterion_max_path_length = []
        #origins_max_path_length = []
        #for c in range(len(self.pathLengths)):
        #    if self.pathLengths[c] == max_path_length:
        #        criterion_max_path_length.append(self.globalMin[c])
        #        origins_max_path_length.append(self.origins[c])

        #min_criterion = min(criterion_max_path_length)

        #find index
        #for m in range(len(criterion_max_path_length)):
        #    if criterion_max_path_length[m] == min_criterion:
        #        break

        #for s in range(len(self.origins)):
        #    if self.origins[s] == origins_max_path_length[m]:
        #        break

        min_criterion = self.globalMin[0]
        self.overall_min = min_criterion
        self.overall_max_path_length = len(self.min_path[0])

        if self.chosenScheduleIndex != self.globalMinSchedIdx[0]:
            self.chosenScheduleIndex = self.globalMinSchedIdx[0]
            self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
            self.EConsumptionChosenSchedule = self.EConsumptionScheduleCurves[self.chosenScheduleIndex]
            # update SOC
            self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
            # update modulation level
            self.setStateModlvl(self.chosenSchedule[-1])


        # inform all neighbors about origin that has local minimal criterion
        for n in range(len(self.Neighbors)):
            #structure: ['minimalorigin', ID_minimal_origin, minimal_criterion_value]
            #self.sendMessage(self.Neighbors[n], 70, ['minimalorigin', copy.deepcopy(origins_max_path_length[m]), copy.deepcopy(min_criterion), copy.deepcopy(self.min_path[s]), copy.deepcopy(self.min_path_schedules[s])])
            self.sendMessage(self.Neighbors[n], 70, ['minimalorigin', copy.deepcopy(self.CommID), copy.deepcopy(min_criterion), copy.deepcopy(self.min_path[0]), copy.deepcopy(self.min_path_schedules[0])])

        if self.OPTcriterion == 'maxmindiff':
            fluct_criterion = max(self.EFluctuationCurve) - min(self.EFluctuationCurve)
        elif self.OPTcriterion == 'absremainder':
            fluct_criterion = 0
            for a in range(len(self.EFluctuationCurve)):
                fluct_criterion += abs(self.EFluctuationCurve[a])


        #print 'ID {0}: criterion is: {1} , of origin {4}, path length: {2}, schedules: {5}, with improvement of {3} %'.format(self.CommID, min_criterion, len(self.min_path[s]), 100 - 100*(float((float(min_criterion))/float(fluct_max_min_diff))), origins_max_path_length[m], self.min_path_schedules[s] )
        self.log_message('ID {0}: criterion is: {1} , of origin {4}, path length: {2}, schedules: {5}, with improvement of {3} %'.format(self.CommID, min_criterion, len(self.min_path[0]), 100 - 100*(float((float(min_criterion))/float(fluct_criterion))), self.CommID, self.min_path_schedules[0] ))

    def messageHandler_MulticastBasedCoordination(self, msg):
        """
        message handler for remainder multicast optimization
        :param msg: received message
        :return:
        """

        data = msg.getData()
        sender = msg.getIDSender()
        self.log_message('ID {0} has received msg {1} from ID {2}'.format(self.CommID, data, sender))
        if data[0] == 'remainder':
            origin = data[1]
            remainder = copy.deepcopy(data[2])
            path = copy.deepcopy(data[3])
            path_schedules = copy.deepcopy(data[4])

            if not self.isGasBoiler():

                # is BES's load included in the received remainder?
                if self.CommID in path: #load included

                    # find BES's index in path
                    for p in range(len(path)):
                        if path[p] == self.CommID:
                            break

                    #find origin index in list of origins
                    for o in range(len(self.origins)):
                        if self.origins[o] == origin:
                            break

                    if self.OPTcriterion == 'maxmindiff':
                        criterion_1 = max(remainder) - min(remainder)
                    elif self.OPTcriterion == 'absremainder':
                        criterion_1 = 0
                        for a in range(len(remainder)):
                            criterion_1 += abs(remainder[a])

                    #print 'ID {0}: I am in path at index {1} ({2}) | origin is {3} at index {4} ({5}) | max-min-diff is {6}, global min for this origin is {7}'.format(self.CommID, p, path[p], origin, o, self.origins[o], criterion_1, self.globalMin[o])

                    if len(path) == self.pathLengths[o]: # if remainder has maximal known path length
                        # try to improve it by choosing a new schedule

                        self.chosenScheduleIndex = copy.deepcopy(path_schedules[p])
                        self.EConsumptionChosenSchedule = copy.deepcopy(self.EConsumptionScheduleCurves[self.chosenScheduleIndex])
                        self.selectBestSchedule(copy.deepcopy(remainder))

                        new_remainder = copy.deepcopy(remainder)
                        #update remainder
                        for t in range(len(remainder)):
                            new_remainder[t] -= self.EConsumptionScheduleCurves[path_schedules[p]][t]
                            new_remainder[t] += self.EConsumptionChosenSchedule[t]

                        #new minimum origin??
                        if self.OPTcriterion == 'maxmindiff':
                            criterion_2 = max(new_remainder) - min(new_remainder)
                        elif self.OPTcriterion == 'absremainder':
                            criterion_2 = 0
                            for a in range(len(remainder)):
                                criterion_2 += abs(new_remainder[a])

                        if self.globalMin[o] - criterion_2 > 0.1:
                            #print 'ID {0}: found better max-min-diff for origin {1} | {2} --> {3}'.format(self.CommID, origin, self.globalMin[o], copy.deepcopy(criterion_2))

                            new_path_schedules = copy.deepcopy(path_schedules)

                            new_path_schedules[p] = copy.deepcopy(self.chosenScheduleIndex)

                            self.globalMin[o] = copy.deepcopy(criterion_2)
                            # check the functionality of the nex line, was:
                            # self.globalMinSchedIdx[o] = copy.deepcopy(path_schedules[p])
                            self.globalMinSchedIdx[o] = copy.deepcopy(new_path_schedules[p])
                            self.pathLengths[o] = len(path)
                            self.min_path[o] = copy.deepcopy(path)
                            self.min_path_schedules[o] = copy.deepcopy(new_path_schedules)

                            for n in range(len(self.Neighbors)):
                                self.sendMessage(self.Neighbors[n], 70 , ['remainder', copy.deepcopy(origin), copy.deepcopy(new_remainder), copy.deepcopy(path), copy.deepcopy(new_path_schedules)])
                        # =============================================================================================
                        elif self.globalMin[o] - criterion_1 > 0.1:
                            self.globalMin[o] = copy.deepcopy(criterion_1)
                            self.globalMinSchedIdx[o] = copy.deepcopy(path_schedules[p])
                            self.pathLengths[o] = len(path)
                            self.min_path[o] = copy.deepcopy(path)
                            self.min_path_schedules[o] = copy.deepcopy(path_schedules)

                            #multicast to all neighbors except sender:
                            for n in range(len(self.Neighbors)):
                                if self.Neighbors[n] != sender:
                                    self.sendMessage(self.Neighbors[n], 70, ['remainder', copy.deepcopy(origin), copy.deepcopy(remainder), copy.deepcopy(path), copy.deepcopy(path_schedules)])
                        # =============================================================================================
                        #else:
                            #print 'ID {0}: NO IMPROVEMENT WITH NEW SCHEDULE'.format(self.CommID)

                    elif len(path) > self.pathLengths[o]:
                        #print 'ID {0}: path is longer than known path for origin {1}'.format(self.CommID, origin)
                        self.pathLengths[o] = len(path)

                        self.globalMin[o] = copy.deepcopy(criterion_1)
                        self.globalMinSchedIdx[o] = copy.deepcopy(path_schedules[p])
                        self.min_path[o] = copy.deepcopy(path)
                        self.min_path_schedules[o] = copy.deepcopy(path_schedules)

                        #multicast to all neighbors except sender:
                        for n in range(len(self.Neighbors)):
                            if self.Neighbors[n] != sender:
                                self.sendMessage(self.Neighbors[n], 70, ['remainder', copy.deepcopy(origin), copy.deepcopy(remainder), copy.deepcopy(path), copy.deepcopy(path_schedules)])

                    #elif self.globalMin[o] - criterion_1 > 0.1 and len(path) == self.pathLengths[o]: #new minimum
                    #    #print 'ID {0}: found better max-min-diff for origin {1}'.format(self.CommID, origin)
                    #    self.globalMin[o] = copy.deepcopy(criterion_1)
                    #    self.globalMinSchedIdx[o] = copy.deepcopy(path_schedules[p])
                    #    self.pathLengths[o] = len(path)
                    #    self.min_path[o] = copy.deepcopy(path)
                    #    self.min_path_schedules[o] = copy.deepcopy(path_schedules)

                    #    #multicast to all neighbors except sender:
                    #    for n in range(len(self.Neighbors)):
                    #        if self.Neighbors[n] != sender:
                    #            self.sendMessage(self.Neighbors[n], 70, ['remainder', copy.deepcopy(origin), copy.deepcopy(remainder), copy.deepcopy(path), copy.deepcopy(path_schedules)])
                    else:
                        self.log_message('ID {0}: NOT DOING ANYTHING WITH REMAINDER')

                else: #load NOT included
                    self.log_message('ID {0}: I am not in path and my load is NOT included in the remainder'.format(self.CommID))

                    # assume no schedule to be chosen before and choose best fitting schedule for this remainder
                    self.chosenScheduleIndex = -1
                    self.selectBestSchedule(copy.deepcopy(remainder))

                    new_remainder = copy.deepcopy(remainder)

                    #update remainder with chosen load
                    for t in range(len(remainder)):
                        new_remainder[t] += self.EConsumptionChosenSchedule[t]

                    if self.OPTcriterion == 'maxmindiff':
                        criterion = max(new_remainder) - min(new_remainder)
                    elif self.OPTcriterion == 'absremainder':
                        criterion = 0
                        for a in range(len(remainder)):
                            criterion += abs(new_remainder[a])

                    #max_min_diff = max(new_remainder) - min(new_remainder)

                    new_path = copy.deepcopy(path)
                    new_path_schedules = copy.deepcopy(path_schedules)

                    #update path and path_schedule fields
                    new_path.append(self.CommID)
                    new_path_schedules.append(self.chosenScheduleIndex)

                    if origin in self.origins: # if origin of remainder is known

                        #find origin index in list of origins
                        for o in range(len(self.origins)):
                            if self.origins[o] == origin:
                                break

                        #new minimal criterion?
                        if self.globalMin[o] - criterion > 0.1 and len(new_path) == self.pathLengths[o]: #new minimal criterion
                            self.globalMin[o] = copy.deepcopy(criterion)
                            self.globalMinSchedIdx[o] = copy.deepcopy(self.chosenScheduleIndex)
                            self.pathLengths[o] = len(new_path)
                            self.min_path[o] = copy.deepcopy(new_path)
                            self.min_path_schedules[o] = copy.deepcopy(new_path_schedules)


                            # multicast remainder to all neighbors
                            for n in range(len(self.Neighbors)):
                                new_data = ['remainder', copy.deepcopy(origin), copy.deepcopy(new_remainder), copy.deepcopy(new_path), copy.deepcopy(new_path_schedules)]
                                self.sendMessage(self.Neighbors[n], 70, new_data)


                        elif len(new_path) > self.pathLengths[o]:
                            self.globalMin[o] = copy.deepcopy(criterion)
                            self.globalMinSchedIdx[o] = copy.deepcopy(self.chosenScheduleIndex)
                            self.pathLengths[o] = len(new_path)
                            self.min_path[o] = copy.deepcopy(new_path)
                            self.min_path_schedules[o] = copy.deepcopy(new_path_schedules)


                            # multicast remainder to all neighbors
                            for n in range(len(self.Neighbors)):
                                new_data = ['remainder', copy.deepcopy(origin), copy.deepcopy(new_remainder), copy.deepcopy(new_path), copy.deepcopy(new_path_schedules)]
                                self.sendMessage(self.Neighbors[n], 70, new_data)

                    else: #new origin
                        self.origins.append(copy.deepcopy(origin))
                        self.globalMin.append(copy.deepcopy(criterion))
                        self.globalMinSchedIdx.append(copy.deepcopy(self.chosenScheduleIndex))
                        self.pathLengths.append(len(new_path))
                        self.min_path.append(copy.deepcopy(new_path))
                        self.min_path_schedules.append(copy.deepcopy(new_path_schedules))

                        # multicast remainder to all neighbors
                        for n in range(len(self.Neighbors)):
                            new_data = ['remainder', copy.deepcopy(origin), copy.deepcopy(new_remainder), copy.deepcopy(new_path), copy.deepcopy(new_path_schedules)]
                            self.sendMessage(self.Neighbors[n], 70, new_data)



                min_criterion = min(self.globalMin)

                #find index
                for m in range(len(self.globalMin)):
                    if self.globalMin[m] == min_criterion:
                        break

                if self.chosenScheduleIndex != self.globalMinSchedIdx[m]:
                    self.chosenScheduleIndex = self.globalMinSchedIdx[m]
                    self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
                    self.EConsumptionChosenSchedule = self.EConsumptionScheduleCurves[self.chosenScheduleIndex]
                    # update SOC
                    self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                    # update modulation level
                    self.setStateModlvl(self.chosenSchedule[-1])



        elif data[0] == 'minimalorigin':
            min_origin = copy.deepcopy(data[1])
            min_criterion = copy.deepcopy(data[2])
            #path_length = copy.deepcopy(data[3])
            min_path = copy.deepcopy(data[3])
            min_path_schedules = copy.deepcopy(data[4])


            # if number of participating BES in arrived solution is greater than known maximal path length
            if self.overall_max_path_length < len(min_path) and self.CommID in min_path:
                #print 'ID {0}: received longer path (old: {1}, new {2})'.format(self.CommID, self.overall_max_path_length, len(min_path))
                self.overall_max_path_length = len(min_path)
                self.overall_min = copy.deepcopy(min_criterion)

                #find index
                for u in range(len(min_path)):
                    if min_path[u] == self.CommID:
                        break

                #print 'ID {0}: choosing new schedule with index {1}'.format(self.CommID, min_path_schedules[u])
                #choose schedule corresponding to min origin
                self.chosenScheduleIndex = min_path_schedules[u]
                self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
                self.EConsumptionChosenSchedule = self.EConsumptionScheduleCurves[self.chosenScheduleIndex]
                # update SOC
                self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                # update modulation level
                self.setStateModlvl(self.chosenSchedule[-1])

                #multicast information to all neighbors except sender
                for n in range(len(self.Neighbors)):
                    if self.Neighbors[n] != sender:
                        self.sendMessage(self.Neighbors[n], 70, ['minimalorigin', copy.deepcopy(min_origin), copy.deepcopy(min_criterion), copy.deepcopy(min_path), copy.deepcopy(min_path_schedules)])
            #
            #     else:
            #         print 'ID {0}: unable to choose new schedule because I dont know origin {1}.'.format(self.CommID, min_origin)
            #
            #
            #
            # #if number of participating BES in arrived solution is equal to known maximal path length
            # elif self.overall_max_path_length == len(min_path):

                #print 'ID {0}: received new criterion with maximal known path length of {1}'.format(self.CommID, self.overall_max_path_length)
            elif self.overall_min - min_criterion > 0.1 and self.overall_max_path_length == len(min_path) and self.CommID in min_path: #received better criterion
                #print 'ID {0}: received better criterion (old: {1}, new {2})'.format(self.CommID, self.overall_min, min_criterion)
                self.overall_min = copy.deepcopy(min_criterion)


                #find index
                for u in range(len(min_path)):
                    if min_path[u] == self.CommID:
                        break

                #print 'ID {0}: received better criterion with path length {2}| choosing new schedule with index {1}'.format(self.CommID, min_path_schedules[u], len(min_path))
                #choose schedule corresponding to min origin
                self.chosenScheduleIndex = min_path_schedules[u]
                self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
                self.EConsumptionChosenSchedule = self.EConsumptionScheduleCurves[self.chosenScheduleIndex]
                # update SOC
                self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                # update modulation level
                self.setStateModlvl(self.chosenSchedule[-1])

                #multicast information to all neighbors except sender
                for n in range(len(self.Neighbors)):
                    if self.Neighbors[n] != sender:
                        self.sendMessage(self.Neighbors[n], 70, ['minimalorigin', copy.deepcopy(min_origin), copy.deepcopy(min_criterion), copy.deepcopy(min_path), copy.deepcopy(min_path_schedules)])

            else:
                self.log_message('ID {0}: EITHER PATH IS SMALLER THAN LONGEST KNOWN OR MINIMUM IS WORSE'.format(self.CommID))
            #else:
            #    print 'ID {0}: received smaller path length {1}, ignore!'.format(self.CommID, len(min_path))