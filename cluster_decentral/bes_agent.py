__author__ = 'Sonja Kolen'

from building.smartbes import SmartBes
from collections import deque
from message import Message
import copy


class BesAgent(SmartBes):
    def __init__(self, message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=None):
        """
        constructor of BesAgent
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
        :param envirmt: the environment for the BesAgent
        """

        super(BesAgent, self).__init__(stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, solPoolAbsGap=absGap, solPoolIntensity=solutionPoolIntensity, env=envirmt)


        #Variables for communication
        self.CommID = ID                                # ID for communication
        self.message_log_file = message_log_file        # file for message logging (absolute path)
        self.Neighbors = []                             # List of known neighbors in the network
        self.ElectricalDistanceToNeighbors = []          # List of electrical distance to all known neighbors (in respective order of self.Neighbors field)
        self.SendMessageBuffer = deque()                # Queue for messages to be send (will be processed by cluster)
        self.ReceiveMessageBuffer = deque()             # Queue for received messaged (filled by cluster, processed by message handler)
        self.MsgSendCount = 0                           # Counter for sent messages over all time (for statistics)
        self.MsgReceiveCount = 0                        # Counter for received messages over all time (for statistics)
        self.MsgSendCount_interval = 0                  # Counter for sent messages per simulated interval, needs to be reset after one simulation interval (for statistics)
        self.MsgReceiveCount_interval = 0               # Counter for received messages per simulated interval, needs to be reset after one simulation interval (for statistics)

        # Variables saving schedule information
        self.prevChosenScheduleIndex = -1                # index of previously chosen schedule
        self.EConsumptionChosenSchedule = []             # array containing the energy consumption curve corresponding to currently chosen schedule
        self.EConsumptionScheduleCurves = []             # array that saves energy consumption curves corresponding to found schedules

        # Variables used independent of optimization algorithm
        self.OPTalg = 'none'                            # which optimization alg shall be performed
        self.fromTime = 0                               # start time
        self.toTime = 0                                 # end time
        self.noOfTimesteps = 0                          # number of time steps
        self.OPTcriterion = 'maxmindiff'                # optimization criterion, defaults to maxmindiff
        self.EFluctuationCurve = []                     # saves energy fluctuation curve of the cluster

    #########################################################
    ############ MESSAGING and NETWORK FUNCTIONS ############
    #########################################################

    def sendMessage(self, receiverID, type, message):
        """
        send a message to a concrete CommBes
        :param receiverID: ID of the receiving ComBes
        :param type: type of message
        :param message: message to be sent
        :return: 0 on success, 1 on error
        """
        #example
        msg = Message(self.CommID, receiverID, type, message)
        #print 'ID {0} sends message {1} to ID {2}'.format(self.CommID, message, receiverID)
        if receiverID in self.Neighbors:
            self.SendMessageBuffer.append(msg)
            self.MsgSendCount += 1                 #increment message counter
            self.MsgSendCount_interval += 1
            return 0
        else:
            print 'Error: ID {0} attempted to send msg to ID {1} who is not a neighbor.'.format(self.CommID, receiverID)
            return 1

    def addNeighbor(self, NewNeighborID, ElectricalDistance):
        """
        add a neighbor to the list of neighbors
        :param NewNeighborID: ID of the new neighbor
        :param ElectricalDistance: electrical distance to the new neighbor in meters
        :return: 0 if success, 1 if error
        """
        if NewNeighborID in self.Neighbors:             #if ID is already a neighbor, then return error
            return 1
        else:
            self.Neighbors.append(NewNeighborID)
            self.ElectricalDistanceToNeighbors.append(ElectricalDistance)
            #self.NeighborMessageRec = [0 for x in range(len(self.Neighbors))]
            #self.NeighborLoads = [0 for x in range(len(self.Neighbors))]
            return 0

    def removeNeighbor(self, WasteNeigborID):
        """
        remove a neighbor from list of neighbors
        :param WasteNeigborID: ID of neighbor that shall be removed
        :return:0 on successful removal, 1 on error
        """
        if WasteNeigborID in self.Neighbors:
            for w in range(len(self.Neighbors)):
                if self.Neighbors[w] == WasteNeigborID:
                    break
            #remove neighbor from lists and update some fields
            self.Neighbors.pop(w)
            self.ElectricalDistanceToNeighbors.pop(w)
            #self.NeighborMessageRec = [0 for x in range(len(self.Neighbors))]
            #self.NeighborLoads = [0 for x in range(len(self.Neighbors))]
            #self.Neighbors.remove(WasteNeigborID)
            return 0
        else:                                       # error: ID is not a neighbor
            return 1

    def appendToReceiveMsgBuffer(self, Message):
        """
        append a messge to the queue of received messages
        :return:
        """
        self.ReceiveMessageBuffer.append(Message)

    def messageHandler(self):
        """
        function of handling of incoming messages
        THIS FUNCTION MUST BE RE-IMPLEMENTED BY EVERY CLASS INHERITING FROM BesAgent CLASS
        :return:
        """

        # all received messages will be processed
        while len(self.ReceiveMessageBuffer) > 0:
            msg = self.ReceiveMessageBuffer.popleft()
            self.MsgReceiveCount += 1
            self.MsgReceiveCount_interval += 1
            type = msg.getType()
            # for communication test (ping pong):
            if type == 0:
                print 'ID {0} has received msg {1} from ID {2}'.format(self.CommID, msg.getData(), msg.getIDSender())
                # send reply
                data = msg.getData()
                if data == 'ping':
                    retval = self.sendMessage(msg.getIDSender(), 0, 'pong')
                    return retval
                elif data == 'pong':
                    retval = self.sendMessage(msg.getIDSender(), 0, 'ping')
                    return retval

        return 0


    #########################################################
    ##################### GETTER FUNCTIONS ##################
    #########################################################

    def getID(self):
        """
        :return: ID of agent
        """
        return self.CommID

    def getType(self):
        """
        :return: main heater device type
        """
        if self.getTER1() == 0:
            return 'GB'
        elif self.getTER1() == 2.3:
            return 'CHP'
        elif self.getTER1() == -1:
            return 'EH'
        elif self.getTER1() == -3:
            return 'HP'
        else:
            return 'unknown'

    def getNeighborsInRadius(self, baseDistance, ElectricalRadius, originID):
        """
        add all neighbors in ElectricalRadius beginning at baseDistance
        :param baseDistance: distance where to begin in meters
        :param ElectricalRadius: electrical radius in meters
        :return:
        """
        neighbors_to_process = self.Neighbors
#        neighbors_to_process.remove(originID)
        neighbors_in_radius = deque()
        distance_to_neighbor = deque()

        if not neighbors_to_process:
            return [[],[]]

        for n in range(len(neighbors_to_process)):
            if baseDistance + self.getElectricalDistance(neighbors_to_process[n]) <= ElectricalRadius and neighbors_to_process[n] != originID:
                neighbors_in_radius.append(neighbors_to_process[n])
                distance_to_neighbor.append(baseDistance + self.getElectricalDistance(neighbors_to_process[n]))

        return [ neighbors_in_radius, distance_to_neighbor ]

    def getSendMessageBuffer(self):
        """
        for cluster; read the buffer of messages to be sent to others
        :return: SendMessageBuffer
        """
        return self.SendMessageBuffer

    def getNumOfMessagesToSend(self):
        """
        return the number of messages that are currently in the send message buffer
        :return: s.a.
        """
        return len(self.SendMessageBuffer)

    def getNumOfMsgSend(self):
        """
        return number of sent messages (for statistical purposes)
        :return: MsgSendCount
        """
        return self.MsgSendCount

    def getNumOfMsgSend_interval(self):
        """
        return number of messages sent in the last simulation interval
        :return: MsgSendCount_interval
        """
        return self.MsgSendCount_interval

    def getNumOfMsgRec(self):
        """
        return number of received messages
        :return: MsgReceiveCount
        """
        return self.MsgReceiveCount

    def getNumOfMsgRec_interval(self):
        """
        return number of received messages in last simulation interval
        :return: MsgReceiveCount_interval
        """
        return self.MsgReceiveCount_interval

    def getNeighbors(self):
        """
        return a list of all known neighbors
        :return:
        """
        return self.Neighbors

    def getElectricalDistance(self, neighborID):
        """
        return electrical distance in meters to neighbor, -1 if neighbor is NOT a neighbor if the current node
        :param neighbor: ID of neighbor
        :return:
        """

        if not neighborID in self.Neighbors: # neighborID is not a neighbor
            return -1

        for n in range(len(self.Neighbors)):
            if self.Neighbors[n] == neighborID:
                break;

        return self.ElectricalDistanceToNeighbors[n]

    def isGasBoiler(self):
        """
        returns 1 if BES is gas boiler and 0 if not
        :return:
        """
        if self.getTER1() == 0 and self.getTER2() == 0:
            return 1 #gas boiler
        else:
            return 0

    def getChosenScheduleSec(self):
        """

        :return:
        """
        return self.schedulesSec[self.chosenScheduleIndex]

    def getChosenLoad(self):
        """
        return chosen load curve (if NOT gas boiler)
        :return:
        """
       # print 'ID {0}: hello'.format(self.CommID)
        if not self.isGasBoiler() and self.chosenSchedule != -1:
            return self.EConsumptionChosenSchedule
        else:
            return -1

    #########################################################
    #################### SETTER FUNCTIONS ###################
    #########################################################

    def setSchedule(self, index):
        """
        set chosen schedule
        :param index: index of schedule
        :return:
        """

        if not self.schedules:
            print 'ID {0}: ERROR - no schedules available!'
            return

        self.chosenScheduleIndex = index
        self.chosenSchedule = copy.deepcopy(self.schedules[index])
        self.EConsumptionChosenSchedule = copy.deepcopy(self.EConsumptionScheduleCurves[index])
        return

    #########################################################
    ############ DEBUGGING AND LOGGING FUNCTIONS ############
    #########################################################

    def log_message(self, text):
        """
        add new line with text to message log file
        :param text: text line to be added
        :return:
        """
        if self.message_log_file != -1:
            #open file in append mode and write line to file
            with open(self.message_log_file, 'a') as log_file:
                log_file.write(text+'\n')
        return

    def printConfig(self):

        print "{0}: Type: {6}, PNom1_el: {1}, PNom2_el: {2}," \
              " PNom1_th: {3}, PNom2_th: {4}, ECap_th: {5}," \
              " SoCmin: {7}, SoCmax: {8}".format(self.CommID,
                                                 self.getNominalElectricalPower1(), self.getNominalElectricalPower2(),
                                                 self.getNominalThermalPower1(), self.getNominalThermalPower2(),
                                                 self.getStorageCapacity(), self.getType() , self.getSOCmin(),
                                                 self.getSOCmax())

    def printNeighbors(self):
        print 'ID {0}: my neighbors are:'.format(self.CommID)
        for k in range(len(self.Neighbors)):
            print 'ID {0}'.format(self.Neighbors[k])

    #########################################################
    ################### SIMULATION FUNCTIONS ################
    #########################################################

    def StartPing(self, receiverID):
        self.sendMessage(receiverID, 0, 'ping')

    def calcScheduleConsumptionCurves(self):
        """
        calculate consumption curves corresponding to calc schedules
        :return:
        """

        if not self.schedules:
            print 'ID {0}: calcScheduleConsumptionCurves Error: no schedules'.format(self.CommID)
            return -1

        print 'ID {0} has calculated {1} schedules'.format(self.CommID, self.noOfSchedules)
        self.EConsumptionScheduleCurves = [[0 for x in range(len(self.schedules[0])-1)] for y in range(self.noOfSchedules)]
        for s in range(self.noOfSchedules):
            for t in range(1, len(self.schedules[0])):
                self.EConsumptionScheduleCurves[s][t-1] = self.schedules[s][t] * self.getNominalElectricalPower1()/self.getModlvls1() * self.stepSize \
                                               + self.schedulesSec[s][t] * self.getNominalElectricalPower2() * self.stepSize

        return 0

    def selectBestSchedule(self, remainder):
        """
        select schedule from pool of schedules (needs to be calculated before)
        :param remainder: energy to compensate in each timeslot
        :return: 1 = new schedule was selected, 0 = no new schedule was selected, -1 = function was called for gas boiler
        """
        # gas boiler? no schedules available!
        if self.getTER1() == 0:
            return -1

        #load_sched = [[0 for x in range(len(self.schedules[0])-1)] for y in range(self.noOfSchedules)]
        abs_sum = [0 for x in range(self.noOfSchedules)]
        max_min_diff = [0 for x in range(self.noOfSchedules)]
        #remainder_average = [0 for x in range(self.noOfSchedules)]
        #NO_worse_slots = [0 for x in range(self.noOfSchedules)]       # saves number of timeslots in which the remainder is worse for each schedule

        min_diff = 0
        idx_min_diff = -1
        child_load = [0 for x in range(len(self.schedules[0])-1)]


        #if self.Children: # if not a leave node: use local knowledge about child loads
        #    for c in range(len(self.Children)):
        #        for t in range(len(child_load)):
        #            child_load[t] += self.EConsumptionChildCurves[c][t]

        for s in range(self.noOfSchedules):

            current_remainder = [0 for x in range(len(remainder))]
            current_remainder_abs = [0 for x in range(len(remainder))]

            for t in range(len(remainder)):
                # add schedule load curve to compensation curve
                current_remainder[t] = remainder[t] + self.EConsumptionScheduleCurves[s][t] #- child_load[t]

                # as currently chosen schedule is included in remainder, subtract it (if not in first round)
                if self.chosenScheduleIndex != -1:
                    current_remainder[t] -= self.EConsumptionChosenSchedule[t]

                current_remainder_abs[t] = abs(current_remainder[t])
                #if current_remainder_abs[t] > remainder[t]:
                #    NO_worse_slots[s] += 1


            # accumulated absolute gradients as measure for similarity of curves
            abs_sum[s] = sum(current_remainder_abs)
            max_min_diff[s] = max(current_remainder)- min(current_remainder)
            #remainder_average[s] = sum(current_remainder_abs)/len(current_remainder_abs)

            #print 'abs_grad_sum: {0}'.format(abs_grad_sum[s])

            # new minimal abs difference?
            if self.OPTcriterion == 'maxmindiff':
                if idx_min_diff == -1 or min_diff - max_min_diff[s] > 0.001 : # min difference is 0.001 Watt to avoid oscillations
                    idx_min_diff = s
                    min_diff = max_min_diff[s]
            elif self.OPTcriterion == 'absremainder':
                if idx_min_diff == -1 or min_diff - abs_sum[s] > 0.001 : # min difference is 0.001 Watt to avoid oscillations
                    idx_min_diff = s
                    min_diff = abs_sum[s]

        if (idx_min_diff != self.chosenScheduleIndex):
            self.chosenSchedule = copy.deepcopy(self.schedules[idx_min_diff])
            if self.chosenScheduleIndex != -1:
                self.prevChosenScheduleIndex = self.chosenScheduleIndex # remember previously chosen schedule
            self.chosenScheduleIndex = idx_min_diff
            self.EConsumptionChosenSchedule = copy.deepcopy(self.EConsumptionScheduleCurves[idx_min_diff])
            #print 'ID {0}: new schedule has index {1}'.format(self.CommID, idx_min_diff)
            return 1
        else:
            if self.chosenScheduleIndex != -1:
                self.prevChosenScheduleIndex = self.chosenScheduleIndex
            #print 'ID {0}: new schedule = old schedule with index {1}'.format(self.CommID, self.chosenScheduleIndex)
            return 0
