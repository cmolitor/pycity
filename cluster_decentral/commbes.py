__author__ = 'Sonja Kolen'

#############################################################################################################################
# THIS FILE AND ITS FUNCTIONS ARE OBSOLETE! THE SIMULATION USES THE FUNCTIONS FROM BesAgent CLASS AND ALL INHERITED CLASSES #
#############################################################################################################################

from building.bes import Bes
from building.smartbes import SmartBes
from message import Message
from collections import deque
import cplex
import copy
import os
import numpy as np
import matplotlib.pyplot as plt
import random

class CommBes(SmartBes): #class CommBes inherits from class SmartBes

    def __init__(self, message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=None):
        """
        constructor of CommBes
        :param stepSize: size of time slot in seconds [s]
        :param TER1: ratio between thermal and electrical power for primary heating system: for EH/HP > 0, COP; for CHP < 0, sigma; for gas boiler = 0;
        :param TER2: ratio between thermal and electrical power for secondary heating system: for EH/HP > 0, COP; for CHP < 0, sigma; for gas boiler = 0
        :param RSC: ratio of storage capacity to  energy output of heater in one hour (3600s); e.g. Pthnom = 10kW and ratioStorageCap = 3 means storage capacity of 30kWh
        :param sizingMethod: share of thermal energy demand which can be covered by main heater; 1: all, < 1: there might be situations that the thermal demand power is higher then the nominal power of the heater
        :param iApartments: number of apartments within the building
        :param sqm: sqm per apartment [m^2]
        :param specDemandTh: specific thermal demand per sqm and year [kWh/(m^2 a)]
        :param ID: ID used for identification of each CommBes in communication network
        :param solutionPoolIntensity: solution pool intensity of cplex solver (1-4)
        :param absGap: absolute gap to optimal solution accepted by the cplex solver
        """

        super(CommBes, self).__init__(stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, solPoolAbsGap=absGap, solPoolIntensity=solutionPoolIntensity, env=envirmt)

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

        #Variables for pseudo tree network structure
        # Pseudo tree is generated due to algorithm presented in
        # Thomas Leaute, Boi Faltings:
        # "Protecting Privacy through Distributed Computation in Multi-agent Decision Making"
        # Online Appendix 2: DFS Tree Generation Algorithm
        # Journal of Artificial Intelligence Research 47 (2013) pp. 649-695
        #
        # Sonja Kolen: This algorithm has been modified to a breadth first search algorithm instead of a depth first
        # search algorithm with the intention to get a much children a possible per node
        self.Children = []                              # in pseudo tree: list of IDs of known children
        self.Parent = []                                # in pseudo tree: ID of parent (root has no parent)
        self.PseudoChildren = []                        # in pseudo tree: list of IDs of known pseudo children (if any)
        self.PseudoParents = []                         # in pseudo tree: list of IDs of known pseudo parents (if any)
        self.OpenNeighbors = []                         # during pseudo tree generation: saves a list of neighbors that still need to be processed
        self.Visited = 0                     # if all open neighbors are processed this flag is set to 1
        self.statusTree = 0                             # saves the current status of the pseudo tree at the current node
        self.noOfChildReplies = 0                       # saves the number of child replies


        # Variables saving schedule information
        #self.solutionPoolIntensity = solutionPoolIntensity
        #self.absGab = absGap
        #self.chosenSchedule = []                        # array containing currently chosen schedule
        #self.chosenScheduleIndex = -1                   # index saving the currently chosen schedule out of schedules array
        self.prevChosenScheduleIndex = -1                # index of previously chosen schedule
        self.EConsumptionChosenSchedule = []             # array containing the energy consumption curve corresponding to currently chosen schedule
        self.EConsumptionScheduleCurves = []             # array that saves energy consumption curves corresponding to found schedules
        #self.schedules = []                             # array containing schedules
        #self.schedulesSec = []                          # array containing schedules for backup/secondary heater
        #self.noOfSchedules = -1                         # current no. of schedules
        #self.SOCEnd = []                                # array containing resulting state of charge of thermal storage at the end of the horizon for all possible schedules

        # Variables used independent of optimization algorithm
        self.OPTalg = 'none'                            # which optimization alg shall be performed
        self.fromTime = 0                               # start time
        self.toTime = 0                                 # end time
        self.noOfTimesteps = 0                          # number of time steps
        self.OPTcriterion = 'maxmindiff'                # optimization criterion, defaults to maxmindiff
        self.EFluctuationCurve = []                     # saves energy fluctuation curve of the cluster

        # Variables used for Load Propagation algorithm
        self.EConsumptionChildCurves = []               # Energy consumption curves of all children
        self.EConsumptionChildCurvesRec = []            # Received energy consumption curves of all children
        self.noOfConsumptionCurvesReceived = 0          # How many energy consumption curves were received?
        self.stateLoadProp = 0                          # current state of load propagation alg
        self.ERemainderLocal = []                       # local view on energy remainder
        self.noNewRounds = 0                            # saves the number of new serach rounds started
        self.scheduleIdxOfPreviousRound = -1            # save schedule of previous round

        # Variables used for Remainder Multicast algorithm
        self.origins = []                               # list of known origin BES for incoming remainder curves
        self.overall_min = 0                            # overall minimum
        self.overall_max_path_length= 0                 # saves overall maximal path length
        self.min_path = []                              # saves path corresponding to current minimum
        self.min_path_schedules = []                    # saves path_schedules corresponding to current minimum
        self.pathLengths = []                           # list of arrived path lengths
        self.globalMin = []                             # saves global minimal value
        self.globalMinSchedIdx = []                     # saves index of schedule that led to global min


    def messageHandler(self):
        """
        message handler for CommBes agent processes incoming message and initiates required task in necessary
        :param senderID: ID of the sender of the message, ID 0 is system message
        :param message: message to be handled
        :return:0 if message was handled successfully, 1 if error occurred
        """

        while len(self.ReceiveMessageBuffer) > 0:       # if message handler is called all received messages will be processed
            #print 'entered message handler of ID {0}'.format(self.CommID)
            msg = self.ReceiveMessageBuffer.popleft()
            self.MsgReceiveCount += 1
            self.MsgReceiveCount_interval += 1
            type = msg.getType()
            # for communication test:
            if type == 0:                          #System message
                print 'ID {0} has received msg {1} from ID {2}'.format(self.CommID, msg.getData(), msg.getIDSender())
                # send reply
                data = msg.getData()
                if data == 'ping':
                    retval = self.sendMessage(msg.getIDSender(), 0, 'pong')
                    return retval
                elif data == 'pong':
                    retval = self.sendMessage(msg.getIDSender(), 0, 'ping')
                    return retval
                # elif data[0] == 'system':
                #     if(data[1] == 'startRONOPT'):
                #         #save fluctuation curve of cluster
                #         self.EFluctuationCurve = data[4]
                #         #begin with local optimization (data[2] = fromTime, data[3]=toTime)
                #         self.stateRONOPT = 0
                #         for n in range(len(self.Neighbors)):
                #             self.NeighborMessageRec[n] = 0
                #         self.RemainderOfNeighborsOpt(data[2],data[3],1)
        #########################################################################################################

            elif type == 20:                                    # pseudo tree generation message
               ret = self.messageHandler_PseudoTree(msg)
               if ret == -1:
                   break

            elif type == 40:                                    # load propagation message
                self.messageHandler_LoadProp(msg)

            elif type == 70:
                self.messageHandler_RemainderMulticast(msg)      #remainder multicast optimization

        return 0

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

    def generatePseudoTree(self, rootID, data):
        """
        generate a pseudo tree structure in the network
        :param rootID: ID of root node of the tree
        :param alg: specifies the algorithm to perfom after the pseudo tree generation
                    'LoadProp' = Load Propagation Optimization
        :return:
        """
        #remark: node == CommBes object in comments

        #reset pseudo tree
        self.Children = []
        self.Parent = []
        self.PseudoChildren = []
        self.PseudoParents = []
        self.Visited = 0
        self.statusTree = 0
        self.noOfChildReplies = 0

        # reset load prop variables
        self.EConsumptionChildCurves = []
        self.EConsumptionChildCurvesRec = []
        self.noOfConsumptionCurvesReceived = 0
        self.stateLoadProp = 0
        self.ERemainderLocal = []
        self.noNewRounds = 0
        self.scheduleIdxOfPreviousRound = -1
        self.EFluctuationCurve = []

        #reset message counters
        self.MsgSendCount_interval = 0
        self.MsgReceiveCount_interval = 0


        # the rest of this function is only performed by the root BES

        if self.CommID == rootID:                           # if current node is root node
            self.Parent = []                                # current node is root of pseudo tree
            if len(self.Neighbors) >= 1:                    # if current node has at least one neighbor

                self.OpenNeighbors = copy.deepcopy(self.Neighbors)       # open all neighbors of the current node
                NewChild = self.OpenNeighbors[0]          # choose an open neighbor
                self.OpenNeighbors.remove(NewChild)         # and remove it from the set of open neighbors
                                                            # for reproducable results the one with the smallest ID is chosen here
                                                            # TODO: chose child randomly
                self.Visited = 1
                self.Children.append(NewChild)              # append chosen node to Children list
                # send 'child' message to chosen node
                self.sendMessage(NewChild, 20, ['child', data[0], data[1], data[2], data[4]])
                self.OPTalg = data[0]                   #remember chosen algorithm
                self.fromTime = data[1]                 #save start time
                self.toTime = data[2]                   #save end time
                self.EFluctuationCurve = copy.deepcopy(data[3])  #root node saves fluctuation curve
                self.ERemainderLocal = copy.deepcopy(data[3])   # save fluctuation curve also as global view on remainder
                self.OPTcriterion = data[4]             #save OPT criterion

        return 0

    def messageHandler_PseudoTree(self, msg):
        """
        Message Handler for pseudo tree generation messages
        :param msg: received message
        :return:
        """
        data = msg.getData()
        sender = msg.getIDSender()
        self.log_message('ID {0} has received message {1} from ID {2}'.format(self.CommID, data, sender))
        if self.Neighbors and self.statusTree == 0:            # if node has neighbors at all and is not finished
            if data[0] == 'child' and self.Visited == 0:   # if first time current node is visited
                self.OpenNeighbors = copy.deepcopy(self.Neighbors)      # open all neighbors of current node...
                self.OpenNeighbors.remove(sender)        # ... except for sender node
                #if not self.OpenNeighbors:
                self.Visited = 1
                self.Parent = sender                   # sender node is parent of current node
                self.log_message('ID {0} has parent with ID {1}'.format(self.CommID, self.Parent))
                self.OPTalg = data[1]           # save alg. type
                self.fromTime = data[2]         # save fromTime
                self.toTime = data[3]           # and toTime
                self.OPTcriterion = data[4]     # and opt. criterion

            elif data == 'pseudo':                       # if message of type PSEUDO
                self.Children.remove(sender)             # remove sender from children
                self.PseudoParents.append(sender)        # and at sender to pseudo parents
                self.noOfChildReplies += 1

            elif data[0] == 'child_ok':
                self.noOfChildReplies += 1

            elif data[0] == 'child' and sender in self.OpenNeighbors:   # if message is of type CHILD and sender is in open neighbors
                self.OpenNeighbors.remove(sender)        # remove sender from open neighbors...
                self.PseudoChildren.append(sender)       # ... and add sender to pseudo children
                self.sendMessage(sender, 20, 'pseudo')   # send pseudo message to sender
                return 0                                           # wait for next message

            elif data[0] == 'ready':       # pseudo three generation finished

                self.EFluctuationCurve = copy.deepcopy(data[1])   # save fluctuation curve
                self.ERemainderLocal = copy.deepcopy(data[2])           # save initial global remainder
                if self.Children != []:                                 # if not a leave node
                    part_fluct = [0 for x in range(len(self.EFluctuationCurve))]
                    for t in range(len(part_fluct)):
                        part_fluct[t] = self.ERemainderLocal[t] / len(self.Children)
                    for i in range(len(self.Children)):
                            self.sendMessage(self.Children[i],20, ['ready', copy.deepcopy(self.EFluctuationCurve), copy.deepcopy(part_fluct)])  # inform all children that pseudo tree generation is ready
                #self.printPseudoTreeInfo()
                self.statusTree = 1                                 # pseudo tree generation for this node is finished
                # start load propagration optimization
                self.startLoadPropagation()
                return 0


            if self.OpenNeighbors:                    # if open neighbor(s) left
                NewChild = self.OpenNeighbors[0]      # choose an open neighbor
                self.OpenNeighbors.remove(NewChild)   # and remove it from the set of open neighbors
                                                      # for reproducable results the one with the smallest ID is chosen here
                                                      # TODO: chose child randomly
                self.Children.append(NewChild)        # append chosen node to Children list
                self.sendMessage(NewChild, 20, ['child', self.OPTalg, self.fromTime, self.toTime, self.OPTcriterion]) # send child message to new child

            else: # no more open neighbors
                if self.Parent and self.noOfChildReplies == len(self.Neighbors)-1:   # if current node is NOT the root  and all neighbors except parent have sent a reply
                    self.sendMessage(self.Parent, 20, ['child_ok'])                  #send a CHILD_OK message to parent node

                elif not self.Parent and self.noOfChildReplies == len(self.Neighbors): # if root node and all neighbors have sent a reply
                    self.statusTree = 1 # pseudo tree generation for this node is finished
                    for i in range(len(self.Children)):
                        part_fluct = [0 for x in range(len(self.EFluctuationCurve))]
                        for t in range(len(part_fluct)):
                            part_fluct[t] = self.EFluctuationCurve[t] / len(self.Children)
                        self.sendMessage(self.Children[i],20, ['ready', copy.deepcopy(self.EFluctuationCurve), copy.deepcopy(part_fluct)])  # inform all children that pseudo tree generation is ready

                    #self.printPseudoTreeInfo()
                    self.startLoadPropagation()

    def printConfig(self):

        print "{0}: Type: {6}, PNom1_el: {1}, PNom2_el: {2}, PNom1_th: {3}, PNom2_th: {4}, ECap_th: {5}, SoCmin: {7}, SoCmax: {8}".format(self.CommID, self.getNominalElectricalPower1(), self.getNominalElectricalPower2(), self.getNominalThermalPower1(), self.getNominalThermalPower2(), self.getStorageCapacity(), self.getType() , self.getSOCmin(), self.getSOCmax())

    def getID(self):
        """
        :return: ID of CommBes
        """
        return self.CommID

    def getType(self):
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

    def getSendMessageBuffer(self):
        """
        for cluster; read the buffer of messages to be sent to others
        :return: SendMessageBuffer
        """
        return self.SendMessageBuffer

    def appendToReceiveMsgBuffer(self, Message):
        """
        append a messge to the queue of received messages
        :return:
        """
        self.ReceiveMessageBuffer.append(Message)

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

    def StartPing(self, receiverID):
        self.sendMessage(receiverID, 0, 'ping')

    def printNeighbors(self):
        print 'ID {0}: my neighbors are:'.format(self.CommID)
        for k in range(len(self.Neighbors)):
            print 'ID {0}'.format(self.Neighbors[k])

    def getNeighbors(self):
        """
        return a list of all known neighbors
        :return:
        """
        return self.Neighbors

    def getChildren(self):
        """
        return children in pseudo tree
        :return:
        """
        if not self.Children:

            #print 'reached leave node {0}'.format(self.CommID)
            #raw_input()
            return [[], []]

        children = deque()
        parent = deque()
        for c in range(len(self.Children)):
            children.append(self.Children[c])
            parent.append(self.CommID)
        retval = (children, parent)

        #print 'retval of ID {0} is {1}'.format(self.CommID, retval)
        #raw_input('wait')

        return retval

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

    def getStatusTree(self):
        """
        return the status of the pseudo tree generation for the current node
        1 indicates creation for current node finished
        0 indicates not finished
        :return:
        """
        return self.statusTree

    def printPseudoTreeInfo(self):
        print 'ID {0}: my pseudo tree connections are:'.format(self.CommID)
        if self.Parent :
            print '     Parent: ID {0}'.format(self.Parent)
        else:
            print 'I am the root!'
        for k in range(len(self.Children)):
            print '     Child: ID {0}'.format(self.Children[k])
        for l in range(len(self.PseudoChildren)):
            print '     PseudoChild: ID {0}'.format(self.PseudoChildren[l])
        for m in range(len(self.PseudoParents)):
            print '     PseudoParent: ID {0}'.format(self.PseudoParents[m])

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

    def plotDebugInfo(self, load_curve):
        """

        :return:
        """
        #calculate absolute local remainder
        abs_overall_remainder = 0
        abs_overall_fluctuation = 0

        max_min_diff_fluct=max(self.EFluctuationCurve) - min(self.EFluctuationCurve)
        max_min_diff_remainder = max(self.ERemainderLocal) - min(self.ERemainderLocal)

        # to be sure: recalculate load curve and remainder (overall remainder)
        for t in range(len(self.ERemainderLocal)):
            #self.ERemainderLocal[t] = self.EFluctuationCurve[t] + load_curve[t]
            abs_overall_remainder = abs_overall_remainder + abs(self.ERemainderLocal[t])
            abs_overall_fluctuation = abs_overall_fluctuation + abs(self.EFluctuationCurve[t])

        print 'ID {0} (root) has received load curves of all children for investigation round {1} and prints current abs. remainder.'.format(self.CommID, self.stateLoadProp)
        print 'current absolute remainder is {0} Watt'.format(abs_overall_remainder)
        print 'absolute fluctuation energy is {0} Watt'.format(abs_overall_fluctuation)
        print 'compensated fluctuations: {0} Watt ({1} %)'.format(abs_overall_fluctuation-abs_overall_remainder, 100-100*(abs_overall_remainder/abs_overall_fluctuation))

        # plot found remainder
        xAxis = [x for x in range(len(self.ERemainderLocal))]
        zeros = [0 for x in range(len(self.ERemainderLocal))]
        index = np.arange(len(self.ERemainderLocal))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, self.EFluctuationCurve, bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, self.ERemainderLocal, bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, load_curve, 'g', label='Load Curve')

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')
        plt.title('Load Optimization result after round {0}'.format(self.stateLoadProp))
        plt.legend()
        plt.tight_layout()
        plt.figtext(0.4,0.2,'Compensation of {0} %'.format(100-100*(abs_overall_remainder/abs_overall_fluctuation)), fontsize=12)
        plt.figtext(0.4,0.175,'Max-Min-Diff Improvement {0} %'.format(100-100*(max_min_diff_remainder/max_min_diff_fluct)), fontsize=12)
        #plot(xAxis, local_remainder, 'bo', xAxis, self.EFluctuationCurve, 'ro', xAxis, zeros, 'black', xAxis, load_curve, 'g')
        plt.show()

    def startLoadPropagation(self):
        """
        This function is called by all BES after pseudo tree generation has finished
        :return:
        """
        self.log_message('ID {0} starts Load Propagation Optimization'.format(self.CommID))
        #self.MsgReceiveCount_interval = 0
        #self.MsgSendCount_interval = 0

        self.noOfTimesteps = (self.toTime - self.fromTime) / self.stepSize + 1

        # calculate pool of schedules (also saved in self.schedules) and schedule load curves
        if self.getTER1() != 0: # if not a gas boiler
            self.calcSchedulePool(self.fromTime, self.toTime)
            self.calcScheduleConsumptionCurves()

        if not self.Parent: #root node
            random.seed()   # initialize pseudo random number generator



        # leave nodes select initial best schedule from schedule pool based on fluctuations curve and propagate their load to parent
        if not self.Children:
            #self.ChildrenProcessed = [0 for x in range(len(self.Children))]
            if self.getTER1() != 0: # not a gas boiler
                self.selectBestSchedule(copy.deepcopy(self.ERemainderLocal))
                self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                self.setStateModlvl(self.chosenSchedule[-1])
                self.sendMessage(self.Parent, 40, ['newload', copy.deepcopy(self.EConsumptionChosenSchedule)])
            else:
                zeros = [0 for x in range(len(self.ERemainderLocal))]
                self.sendMessage(self.Parent, 40, ['newload', copy.deepcopy(zeros)])

        else:  # if not a leave node
            self.EConsumptionChildCurves = [ [0 for x in range(len(self.EFluctuationCurve))] for y in range(len(self.Children))] # initialize array for load curves of children
            self.EConsumptionChildCurvesRec = [ [0 for x in range(len(self.EFluctuationCurve))] for y in range(len(self.Children))] # initialize array for load curves of children
            self.noOfConsumptionCurvesReceived = 0
            #self.ChildLoadCurvesChosen = [0 for x in range(len(self.Children))]
        return

    def messageHandler_LoadProp(self, msg):
        """
        This function is the message handler function for load propagation optimization (message type 40)
        :param msg: received message
        :return:
        """
        data = msg.getData()
        sender = msg.getIDSender()
        self.log_message('ID {0} has received msg {1} from ID {2}'.format(self.CommID, data, sender))
        if data[0] == 'newload':    # new load curve received by child

            for i in range(len(self.Children)): # save received child load curve
                if self.Children[i] == sender:
                    for t in range(len(data[1])):
                        self.EConsumptionChildCurvesRec[i][t] = copy.deepcopy(data[1][t])
                    self.noOfConsumptionCurvesReceived = self.noOfConsumptionCurvesReceived +1
                    break

            # if load curves received by all children
            if self.noOfConsumptionCurvesReceived == len(self.Children):
                self.noOfConsumptionCurvesReceived = 0 # reset counter for received load curves

                #first time all children have sent load curves
                if self.stateLoadProp == 0:
                    self.stateLoadProp += 1
                    consumption_curve = [0 for x in range(len(self.EConsumptionChildCurves[0]))]
                    local_remainder = [0 for x in range(len(self.EConsumptionChildCurves[0]))]

                    #accumulate children's loads
                    for c in range(len(self.Children)):
                        for t in range(len(self.EConsumptionChildCurves[0])):
                            self.EConsumptionChildCurves[c][t] = self.EConsumptionChildCurvesRec[c][t]
                            consumption_curve[t] += self.EConsumptionChildCurves[c][t]

                    # calculate the local remainder (without own load)
                    for t in range(len(consumption_curve)):
                            local_remainder[t] = self.ERemainderLocal[t] + consumption_curve[t]

                    if self.getTER1() != 0: # if NOT a gas boiler
                        #select own best schedule
                        self.selectBestSchedule(local_remainder)
                        self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                        self.setStateModlvl(self.chosenSchedule[-1])

                        #update local remainder with own load curve (global remainder)
                        for t in range(len(consumption_curve)):
                            local_remainder[t] += self.EConsumptionChosenSchedule[t]
                            consumption_curve[t] += self.EConsumptionChosenSchedule[t]

                    # save new global remainder
                    self.ERemainderLocal = local_remainder

                    if self.Parent: # not root
                        for c in range(len(self.Children)):
                            self.sendMessage(self.Children[c], 40, ['localrecap', copy.deepcopy(self.ERemainderLocal)])
                    else: #root
                        # ask all children for a better compensation of the remainder in a new round
                        for c in range(len(self.Children)):
                            self.sendMessage(self.Children[c], 40 , ['newround', copy.deepcopy(self.ERemainderLocal)])

                # any other round than first round
                else:

                    idx_best_compensation = -1
                    min_remainder = -1
                    overall_min = -1
                    overall_min_idx = -1
                    local_remainder = [0 for x in range(len(self.EConsumptionChildCurves[0]))]
                    abs_local_remainder = [0 for x in range(len(self.Children))]
                    abs_global_remainder = 0
                    max_min_diff_local_remainder = [0 for x in range(len(self.Children))]

                    # calc current absolute global remainder
                    for t in range(len(self.ERemainderLocal)):
                        abs_global_remainder += abs(self.ERemainderLocal[t])
                    max_min_diff_global_remainder = max(self.ERemainderLocal) - min(self.ERemainderLocal)

                    for c in range(len(self.Children)):
                        for t in range(len(local_remainder)):
                            local_remainder[t] = self.ERemainderLocal[t] - self.EConsumptionChildCurves[c][t] + self.EConsumptionChildCurvesRec[c][t]
                            abs_local_remainder[c] += abs(local_remainder[t])
                        max_min_diff_local_remainder[c] = max(local_remainder) - min(local_remainder)

                        if self.OPTcriterion == 'absremainder':
                            #remember overall minimum
                            if overall_min_idx == -1 or overall_min - abs_local_remainder[c] > 0.01:
                                overall_min = abs_local_remainder[c]
                                overall_min_idx = c

                            if abs_global_remainder - abs_local_remainder[c] >= 1: # improvement greater or equal 1 Watt
                                if idx_best_compensation == -1 or abs_local_remainder[c] < min_remainder:
                                    idx_best_compensation = c
                                    min_remainder = abs_local_remainder[c]

                        elif self.OPTcriterion == 'maxmindiff':
                            #remember overall minimum
                            if overall_min_idx == -1 or overall_min - max_min_diff_local_remainder[c] > 0.01:
                                overall_min = max_min_diff_local_remainder[c]
                                overall_min_idx = c


                            if max_min_diff_global_remainder - max_min_diff_local_remainder[c] > 0.01: # difference greater than 0.001 Watt
                                if idx_best_compensation == -1 or max_min_diff_local_remainder[c] < min_remainder:
                                    idx_best_compensation = c
                                    min_remainder = max_min_diff_local_remainder[c]

                    # no better compensation at all?
                    if idx_best_compensation == -1:

                        consumption_curve = [0 for x in range(len(self.EConsumptionChildCurves[0]))]
                        self.log_message('ID {0}: did not receive an improvement by any of its children.'.format(self.CommID))

                        for c in range(len(self.Children)):
                            #send fallback to all children
                            if not self.Parent: #root
                                self.sendMessage(self.Children[c], 40, 'fallbackforward')
                            else: #not root
                                self.sendMessage(self.Children[c], 40, 'fallback')
                            # calculate current load curve
                            for t in range(len(self.ERemainderLocal)):
                                consumption_curve[t] += self.EConsumptionChildCurves[c][t]

                        if self.getTER1() != 0: #NOT a gas boiler
                            for t in range(len(consumption_curve)):
                                consumption_curve[t] += self.EConsumptionChosenSchedule[t] #add own load to load curve

                        if self.Parent: #not root --> propagate load curve to parent
                            self.sendMessage(self.Parent, 40, ['newload', copy.deepcopy(consumption_curve)])

                        else: #root
                            # if self.noNewRounds < len(self.Children):
                            #     # tentatively integrate minimal max-min-diff load curve to remainder
                            #     tentative_remainder = [0 for x in range(len(self.ERemainderLocal))]
                            #     random_child = random.randint(0, len(self.Children)-1)
                            #     for t in range(len(tentative_remainder)):
                            #         tentative_remainder[t] = self.ERemainderLocal[t] - self.EConsumptionChildCurves[random_child][t] + self.EConsumptionChildCurvesRec[random_child][t]
                            #
                            #     for c in range(len(self.Children)):
                            #         self.sendMessage(self.Children[c], 40, ['newround', copy.deepcopy(tentative_remainder)])
                            #     self.noNewRounds += 1
                            # else:
                                # finish algorithm
                            self.stateLoadProp = 9999
                                #self.plotDebugInfo(load_curve)

                    else:
                        self.noNewRounds = 0
                        # send fallback message to all children except the one that has the best improving load curve
                        self.log_message('ID {0}: best compensation is from child {1}'.format(self.CommID, self.Children[idx_best_compensation]))
                        #raw_input('press a key')
                        for c in range(len(self.Children)):
                            if c != idx_best_compensation:
                                if not self.Parent: #root
                                    self.sendMessage(self.Children[c], 40, 'fallbackforward')
                                else: #not root
                                    self.sendMessage(self.Children[c], 40, 'fallback')

                        # update remainder and save new child load curve
                        for t in range(len(self.EConsumptionChildCurves[0])):
                            self.ERemainderLocal[t] = self.ERemainderLocal[t] - self.EConsumptionChildCurves[idx_best_compensation][t] + self.EConsumptionChildCurvesRec[idx_best_compensation][t]
                            self.EConsumptionChildCurves[idx_best_compensation][t] = self.EConsumptionChildCurvesRec[idx_best_compensation][t]

                        # update remainder with own new load if not a gas boiler
                        if self.getTER1() != 0:
                            # select own new load

                            remainder_without_own_load = [0 for x in range(len(self.ERemainderLocal))]
                            for t in range(len(remainder_without_own_load)):
                                 remainder_without_own_load[t] = self.ERemainderLocal[t] - self.EConsumptionChosenSchedule[t]

                            self.selectBestSchedule(self.ERemainderLocal)
                            self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                            self.setStateModlvl(self.chosenSchedule[-1])

                            for t in range(len(remainder_without_own_load)):
                                self.ERemainderLocal[t] = remainder_without_own_load[t] + self.EConsumptionChosenSchedule[t]

                        # start new round
                        self.stateLoadProp += 1
                        for c in range(len(self.Children)):
                            if not self.Parent: #root
                                self.sendMessage(self.Children[c], 40, ['newround', copy.deepcopy(self.ERemainderLocal)])
                            else: #not root
                                self.sendMessage(self.Children[c], 40, ['localrecap', copy.deepcopy(self.ERemainderLocal)])


        elif data == 'fallback':
            if self.getTER1() != 0: # NOT a gas boiler
                self.chosenScheduleIndex = self.prevChosenScheduleIndex
                self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
                self.EConsumptionChosenSchedule = copy.deepcopy(self.EConsumptionScheduleCurves[self.chosenScheduleIndex])

                self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                self.setStateModlvl(self.chosenSchedule[-1])

                self.log_message('ID {0} has performed fallback to schedule {1}'.format(self.CommID, self.chosenScheduleIndex))
            else:
                self.log_message('ID {0} is GB (no schedule to fallback to)'.format(self.CommID))


        elif data == 'fallbackforward':
            if self.getTER1() != 0: # NOT a gas boiler
                self.chosenScheduleIndex = self.scheduleIdxOfPreviousRound
                self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
                # save previous load curve
                self.EConsumptionChosenSchedule = copy.deepcopy(self.EConsumptionScheduleCurves[self.chosenScheduleIndex])

                self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                self.setStateModlvl(self.chosenSchedule[-1])

                self.log_message('ID {0} has performed fallback to schedule {1}'.format(self.CommID, self.chosenScheduleIndex))
            else:
                self.log_message('ID {0} is GB (no schedule to fallback to)'.format(self.CommID))

            #inform all children about fallback
            if self.Children:
                for c in range(len(self.Children)):
                    self.sendMessage(self.Children[c], 40, 'fallbackforward')


        elif data[0] == 'newround':
            self.ERemainderLocal = copy.deepcopy(data[1])
            self.stateLoadProp = 0
            if self.getTER1() != 0: #if not a gas boiler
                #remember schedule before starting a new round
                self.scheduleIdxOfPreviousRound = self.chosenScheduleIndex

            if self.Children: # NOT a leave node
                # forward compensation curve to all children
                for c in range(len(self.Children)):
                    self.sendMessage(self.Children[c], 40, ['newround', copy.deepcopy(self.ERemainderLocal)])
            else: #leave node
                if self.getTER1() != 0: # not a gas boiler
                    #remainder_without_own_load = [0 for x in range(len(self.ERemainderLocal))]
                    #for t in range(len(remainder_without_own_load)):
                    #    remainder_without_own_load[t] = self.ERemainderLocal[t] - self.EConsumptionChosenSchedule[t]
                    self.selectBestSchedule(self.ERemainderLocal)
                    self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                    self.setStateModlvl(self.chosenSchedule[-1])
                    self.sendMessage(self.Parent, 40, ['newload', copy.deepcopy(self.EConsumptionChosenSchedule)])
                else:
                    zeros = [0 for x in range(len(self.ERemainderLocal))]
                    self.sendMessage(self.Parent, 40, ['newload', copy.deepcopy(zeros)])

        elif data[0] == 'localrecap':
            self.ERemainderLocal = copy.deepcopy(data[1])
            consumption_curve = [0 for x in range(len(self.ERemainderLocal))]

            if self.getTER1() != 0: #NOT a gas boiler
                #remainder_without_own_load = [0 for x in range(len(self.ERemainderLocal))]
                #for t in range(len(remainder_without_own_load)):
                #    remainder_without_own_load[t] = self.ERemainderLocal[t] - self.EConsumptionChosenSchedule[t]


                self.selectBestSchedule(copy.deepcopy(self.ERemainderLocal))
                self.setSOC(self.SOCEnd[self.chosenScheduleIndex])
                self.setStateModlvl(self.chosenSchedule[-1])

                if self.Children: # NOT a leave node
                    for c in range(len(self.Children)):
                        for t in range(len(consumption_curve)):
                            consumption_curve[t] += self.EConsumptionChildCurves[c][t]

                for t in range(len(consumption_curve)): # add own load
                    consumption_curve[t] += self.EConsumptionChosenSchedule[t]

            else: #gas boiler

                if self.Children: # NOT a leave node
                    for c in range(len(self.Children)):
                        for t in range(len(consumption_curve)):
                            consumption_curve[t] += self.EConsumptionChildCurves[c][t]

            self.sendMessage(self.Parent, 40, ['newload', copy.deepcopy(consumption_curve)])

    def getLoadPropStatus(self):
        return self.stateLoadProp

    def initRemainderMulticastOPT(self, fromTime, toTime, fluct, criterion_type):
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

    def startRemainderMulticastOPT(self):
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

    def analyseRemainderMulticastOPT(self):
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

    def messageHandler_RemainderMulticast(self, msg):
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

    def localBestChoice(self, fromTime, toTime):
        """
        calc schedule pool and select best local solution
        :param fromTime: start time
        :param toTime: end time
        :return:
        """
        #set abs gap to 0
        #self.setSolPoolAbsGap(0)
        #calc schedule pool
        self.calcSchedulePool(fromTime, toTime)
        self.calcScheduleConsumptionCurves()

        if len(self.schedules) > 1: # more than one schedule calculated
            #choose a random schedule out of the pool
            #random.seed()
            idx = random.randint(0, len(self.schedules)-1)
            self.chosenScheduleIndex = idx

        else: # only one schedule calculated
            self.chosenScheduleIndex = 0

        self.chosenSchedule = self.schedules[self.chosenScheduleIndex]
        self.EConsumptionChosenSchedule = self.EConsumptionScheduleCurves[self.chosenScheduleIndex]
        self.setStateModlvl(self.chosenSchedule[-1])
        self.setSOC(self.SOCEnd[self.chosenScheduleIndex])

    def initLocalBestChoice(self):
        """
        initialize Local Best Choice Algorithm
        -> init pseudo random number generator
        :return:
        """
        random.seed()
        return


    def calcScheduleConsumptionCurves(self):
        """
        calculate load curves corresponding to calc schedules
        :return:
        """

        if not self.schedules:
            print 'ID {0}: calcScheduleLoadCurves Error: no schedules'.format(self.CommID)
            return -1

        print 'ID {0} has calculated {1} schedules'.format(self.CommID, self.noOfSchedules)
        self.EConsumptionScheduleCurves = [[0 for x in range(len(self.schedules[0])-1)] for y in range(self.noOfSchedules)]
        for s in range(self.noOfSchedules):
            for t in range(1, len(self.schedules[0])):
                self.EConsumptionScheduleCurves[s][t-1] = self.schedules[s][t] * self.getNominalElectricalPower1()/self.getModlvls1() * self.stepSize \
                                               + self.schedulesSec[s][t] * self.getNominalElectricalPower2() * self.stepSize

        return 0



    # def calcSchedulePool(self, fromTime, toTime, objectiveFcn=1, absGap=2, relGap=0.2, solutionPoolIntensity=3):
    #     """
    #     method creates optimized schedules for given timeframe.
    #     e.g.:   MODLVL		001110010
    #             switchOn	_01000010
    #             switchOff	_00001001
    #             ETHStorage	XXXXXXXXX
    #             PTHStorage	_XXXXXXXX
    #
    #     :param fromTime: beginning time
    #     :param toTime: end time
    #     :param objectiveFcn: not used at the moment
    #     :param absGap: absolute tolerance on objective value for the solutions in the cplex solution pool
    #     :param relGap: relative tolerance on objective value for the solutions in the cplex solution pool
    #     :param solutionPoolIntensity controls the trade off between the number of solutions generated and the time/memory consumed
    #             may be 1 to 4 (low to high time/memory consumption
    #     :return: array [no. solutions x no. timesteps]; resulting schedules (0,1... for each timestep in each sol.)
    #     """
    #
    #      # gas boiler? no calculation.
    #     if self.getTER1() == 0:
    #         self.schedules = []
    #         self.noOfSchedules = 0
    #         return []
    #
    #     # create empty Model
    #     c = cplex.Cplex()
    #     c.set_log_stream(None)
    #     c.set_results_stream(None)
    #     c.objective.set_sense(c.objective.sense.minimize)
    #     c.parameters.mip.pool.absgap.set(absGap)
    #     c.parameters.mip.pool.intensity.set(solutionPoolIntensity)      # parameters may be: 1 - 4 (low to high time/memory consumption)
    #
    #     # py-variables
    #     timeSteps = (toTime-fromTime)/self.stepSize + 1              # no. of steps (e.g. hours)
    #     rangeHorizonFrom1 = range(1, timeSteps+1)         # step array (1,2 ... 24)
    #     rangeHorizonFrom0 = range(0, timeSteps+1)         # dummy    (0,1,2 ... 24)
    #
    #     # decision variables
    #
    #     # modulation level: on=1, off=0
    #     MODLVL = []
    #     for s in rangeHorizonFrom0:
    #         MODLVLName = "MODLVL_"+str(s)
    #         MODLVL.append(MODLVLName)
    #     c.variables.add(obj=[0] * len(MODLVL), names=MODLVL,
    #                     lb=[0] * len(MODLVL), ub=[self.getModlvls1()] * len(MODLVL),
    #                     types=[c.variables.type.integer] * len(MODLVL))
    #
    #     # modulation level of secondary heater
    #     if self.getTER2() == 0:                 # CHP
    #         typeMODLVLSec = c.variables.type.semi_continuous
    #         lbMODLVLSec = 0.2
    #     elif self.getTER2() < 0:     # electric heater, heat pump
    #         typeMODLVLSec = c.variables.type.binary
    #         lbMODLVLSec = 0
    #     else:
    #         raw_input("TER2 of {0} doesn't make sense (TER2>0). Abort.".format(self.CommID))
    #         return -1
    #
    #     MODLVLSec = []
    #     for s in rangeHorizonFrom0:
    #         MODLVLSecName = "MODLVLSec_"+str(s)
    #         MODLVLSec.append(MODLVLSecName)
    #     c.variables.add(obj=[0] * len(MODLVLSec), names=MODLVLSec,
    #                     lb=[lbMODLVLSec] * len(MODLVLSec), ub=[1] * len(MODLVLSec),
    #                     types=[typeMODLVLSec] * len(MODLVLSec))
    #
    #     # stored thermal energy
    #     ETHStorage = []
    #     for s in rangeHorizonFrom0:
    #         ETHStorageName = "ETHStorage_"+str(s)
    #         ETHStorage.append(ETHStorageName)
    #     c.variables.add(obj=[0] * len(ETHStorage), names=ETHStorage,
    #                     lb=[self.getSOCmin()*self.getStorageCapacity()] * len(ETHStorage), ub=[self.getSOCmax()*self.getStorageCapacity()] * len(ETHStorage),
    #                     types=[c.variables.type.continuous] * len(ETHStorage))
    #
    #     # power flow into thermal storage at time=s. (Positive when thermal power flows into device)
    #     PTHStorage = []
    #     thermalDemand = self.getThermalDemandCurve(fromTime, toTime)
    #     maxThermalPowerDemand = max(thermalDemand[1])/self.stepSize
    #     for s in rangeHorizonFrom0:
    #         PTHStorageName = "PTHStorage_"+str(s)
    #         PTHStorage.append(PTHStorageName)
    #     c.variables.add(obj=[0] * len(PTHStorage), names=PTHStorage,
    #                     lb=[-maxThermalPowerDemand] * len(PTHStorage),
    #                     ub=[-self.getNominalThermalPower1()] * len(PTHStorage),
    #                     types=[c.variables.type.continuous] * len(PTHStorage))
    #
    #     # 1 if switched on from time t-1 to t (not def. for t=0)
    #     switchOn = []
    #     for s in rangeHorizonFrom0:
    #         switchOnName = "switchOn_"+str(s)
    #         switchOn.append(switchOnName)
    #     c.variables.add(obj=[0] * len(switchOn), names=switchOn,
    #                     lb=[0] * len(switchOn), ub=[1] * len(switchOn),
    #                     types=[c.variables.type.binary] * len(switchOn))
    #
    #     # 1 if switched off from time t-1 to t (not def. for t=0)
    #     switchOff = []
    #     for s in rangeHorizonFrom0:
    #         switchOffName = "switchOff_"+str(s)
    #         switchOff.append(switchOffName)
    #     c.variables.add(obj=[0] * len(switchOff), names=switchOff,
    #                     lb=[0] * len(switchOff), ub=[1] * len(switchOff),
    #                     types=[c.variables.type.binary] * len(switchOff))
    #
    #     # sum of switching events in switchOn and switchOff. to be minimized.
    #     switchSum = ["switch_Sum"]
    #     c.variables.add(obj=[1], names=switchSum,
    #                     lb=[0], ub=[25],
    #                     types=[c.variables.type.integer])
    #
    #     # constraints
    #
    #     for t in rangeHorizonFrom1:
    #         # sync switchOn/Off and MODLVL
    #         thevars = [MODLVL[t], MODLVL[t-1], switchOn[t], switchOff[t]]
    #         c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1, -1, -1, 1])],
    #                                  senses=["E"], rhs=[0])
    #         thevars = [switchOn[t], switchOff[t]]
    #         c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1, 1])],
    #                                  senses=["L"], rhs=[1])
    #
    #         # Restrict the secondary heater to operate only when the primary heater is already running
    #         thevars = [MODLVLSec[t], MODLVL[t]]
    #         c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [-1, 1])],
    #                                  senses=["G"], rhs=[0])
    #
    #         # SoCmin <= energy in storage <= SoCmax
    #         thevars = [ETHStorage[t]]
    #         c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1])],
    #                                  senses=["G"], rhs=[self.getSOCmin()*self.getStorageCapacity()])
    #         c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1])],
    #                                  senses=["L"], rhs=[self.getSOCmax()*self.getStorageCapacity()])
    #
    #         # energy in storage at time t = energy at time (t-1) + (stepSize * PTHStorage[t])
    #         thevars = [ETHStorage[t], ETHStorage[t-1], PTHStorage[t]]
    #         c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1, -1, -self.stepSize])],
    #                                  senses=["E"], rhs=[0])
    #
    #         # thermal energy produced by main & backup device = thermal demand + thermal energy that is stored in thermal storage
    #         thevars = [MODLVL[t], MODLVLSec[t], PTHStorage[t]]
    #         c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [-self.getNominalThermalPower1() * self.stepSize / self.getModlvls1(), -self.getNominalThermalPower2() * self.stepSize, -self.stepSize])],
    #                                  senses=["E"], rhs=[thermalDemand[1][t-1]])
    #
    #
    #     # MODLVL at time t=0 = MODLVLini TODO: stateModlvl must be updated in algorithm (done for RMOPT)
    #     thevars = [MODLVL[0]]
    #     c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1])], senses=["E"], rhs=[round(self.getStateModlvl())])
    #
    #     # energy in storage at time t=0 = SoCini * storageCapThermal TODO: SOC must be updated in algorithm (done for RMOPT)
    #     if self.getSOC() > self.getSOCmax():
    #         self.setSOC(self.getSOCmax())
    #     elif self.getSOC() < self.getSOCmin():
    #         self.setSOC(self.getSOCmin())
    #     thevars = [ETHStorage[0]]
    #     c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, [1])], senses=["E"], rhs=[self.getSOC() * self.getStorageCapacity()])
    #
    #
    #     # sum of switching events
    #     sumCoeffs = [1]*2*timeSteps
    #     sumCoeffs.append(-1)
    #     thevars = []
    #     for i in rangeHorizonFrom1:
    #         thevars.append(switchOn[i])
    #         thevars.append(switchOff[i])
    #     thevars.append(switchSum[0])
    #     c.linear_constraints.add(lin_expr=[cplex.SparsePair(thevars, sumCoeffs)], senses=["E"], rhs=[0])
    #
    #     # solve problem
    #
    #     pool = c.populate_solution_pool()
    #     noSol = c.solution.pool.get_num()
    #
    #     # for debugging
    #     print "\n ID {0} has calculated {1} solutions".format(self.CommID, noSol)
    #     for n in range(noSol):
    #         #print ""
    #         for j in rangeHorizonFrom0:
    #             lvl = c.solution.pool.get_values(n, MODLVL[j])
    #             #print lvl
    #             #print '%.1f' % lvl,
    #         #print ""
    #         for j in rangeHorizonFrom0:
    #             lvl2 = c.solution.pool.get_values(n, MODLVLSec[j])
    #             #print lvl2
    #             #print '%.1f' % lvl2,
    #         #print c.solution.pool.get_values(n, switchSum)
    #
    #     # create and return optimized schedule-array
    #     self.schedules = [[0 for x in rangeHorizonFrom0] for x in xrange(noSol)]    # create empty multi dim array for schedules
    #     self.schedulesSec = [[0 for x in rangeHorizonFrom0] for x in xrange(noSol)]    # create empty multi dim array for schedules
    #
    #     self.SOCEnd = list()
    #     for n in range(noSol):
    #         self.schedules[n] = c.solution.pool.get_values(n, MODLVL)
    #         self.schedulesSec[n] = c.solution.pool.get_values(n, MODLVLSec)
    #
    #         self.SOCEnd.append(c.solution.pool.get_values(n, float(ETHStorage[-1] / self.getStorageCapacity())))
    #     self.noOfSchedules = noSol
    #
    #     #print 'Saving load curves for ID {0}'.format(self.CommID)
    #     #self.EConsumptionScheduleCurves = [[0 for x in range(len(self.schedules[0])-1)] for y in range(noSol)]
    #     #for s in range(noSol):
    #     #    for t in range(1, len(self.schedules[0])):
    #     #        self.EConsumptionScheduleCurves[s][t-1] = self.schedules[s][t] * self.getNominalElectricalPower1()/self.getModlvls1() * self.stepSize \
    #     #                                       + self.schedulesSec[s][t] * self.getNominalElectricalPower2() * self.stepSize
    #     #print len(self.schedules[0])
    #     return self.schedules

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