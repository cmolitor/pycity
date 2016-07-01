__author__ = 'Sonja Kolen'

from bes_agent import BesAgent
import copy
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
import random

class TreeAgent(BesAgent):
    def __init__(self, message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=None):
        """
        class TreeAgent inherits from class BesAgent (and SmartBes)
        constructor of TreeAgent
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
        :param envirmt: the environment for the TreeAgent
        :return:
        """
        super(TreeAgent, self).__init__(message_log_file, stepSize, TER1, TER2, RSC, sizingMethod, iApartments, sqm, specDemandTh, ID, solutionPoolIntensity, absGap, envirmt=envirmt)

        #Variables for pseudo tree network structure
        # Pseudo tree is generated according to algorithm presented in
        # Thomas Leaute, Boi Faltings:
        # "Protecting Privacy through Distributed Computation in Multi-agent Decision Making"
        # Online Appendix 2: DFS Tree Generation Algorithm
        # Journal of Artificial Intelligence Research 47 (2013) pp. 649-695
        #
        # with slight modifications by Sonja Kolen
        self.Children = []                   # in pseudo tree: list of IDs of known children
        self.Parent = []                     # in pseudo tree: ID of parent (root has no parent)
        self.PseudoChildren = []             # in pseudo tree: list of IDs of known pseudo children (if any)
        self.PseudoParents = []              # in pseudo tree: list of IDs of known pseudo parents (if any)
        self.OpenNeighbors = []              # during pseudo tree generation: saves a list of neighbors that still need to be processed
        self.Visited = 0                     # if all open neighbors are processed this flag is set to 1
        self.statusTree = 0                  # saves the current status of the pseudo tree at the current node
        self.noOfChildReplies = 0            # saves the number of child replies

        # Variables used for tree-based coordination algorithm
        self.EConsumptionChildCurves = []               # Energy consumption curves of all children
        self.EConsumptionChildCurvesRec = []            # Received energy consumption curves of all children
        self.noOfConsumptionCurvesReceived = 0          # How many energy consumption curves were received?
        self.state_coordination = 0                     # current state of coordination alg
        self.ERemainderLocal = []                       # local view on energy remainder
        self.noNewRounds = 0                            # saves the number of new coordination rounds started
        self.scheduleIdxOfPreviousRound = -1            # save schedule of previous round


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

            if type == 20:   # pseudo tree generation message
               ret = self.messageHandler_PseudoTree(msg)
               if ret == -1:
                   break

            elif type == 40: # tree-based coordination message
                self.messageHandler_TreeBasedCoord(msg)

        return 0

    #########################################################
    #################### GETTER FUNCTIONS ###################
    #########################################################

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

    def getStatusTree(self):
        """
        return the status of the pseudo tree generation for the current node
        1 indicates creation for current node finished
        0 indicates not finished
        :return:
        """
        return self.statusTree

    def getCoordState(self):
        return self.state_coordination

    #########################################################
    ########## DEBUGGING AND LOGGING FUNCTIONS ##############
    #########################################################

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

        print 'ID {0} (root) has received load curves of all children for investigation round {1} and prints current abs. remainder.'.format(self.CommID, self.state_coordination)
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
        plt.title('Load Optimization result after round {0}'.format(self.state_coordination))
        plt.legend()
        plt.tight_layout()
        plt.figtext(0.4,0.2,'Compensation of {0} %'.format(100-100*(abs_overall_remainder/abs_overall_fluctuation)), fontsize=12)
        plt.figtext(0.4,0.175,'Max-Min-Diff Improvement {0} %'.format(100-100*(max_min_diff_remainder/max_min_diff_fluct)), fontsize=12)
        #plot(xAxis, local_remainder, 'bo', xAxis, self.EFluctuationCurve, 'ro', xAxis, zeros, 'black', xAxis, load_curve, 'g')
        plt.show()

    #########################################################
    ############# PSEUDO TREE SETUP FUNCTIONS ###############
    #########################################################

    def generatePseudoTree(self, rootID, data):
        """
        generate a pseudo tree structure in the network
        :param rootID: ID of root node of the tree
        :param data: initial system data set
        :return:
        """

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
        self.state_coordination = 0
        self.ERemainderLocal = []
        self.noNewRounds = 0
        self.scheduleIdxOfPreviousRound = -1
        self.EFluctuationCurve = []

        #reset message counters
        self.MsgSendCount_interval = 0
        self.MsgReceiveCount_interval = 0


        # the rest of this function is only performed by the root agent

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
                self.startTreeBasedCoord()
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
                    self.startTreeBasedCoord()

    #########################################################
    ########## TREE-BASED COORDINATION FUNCTIONS ############
    #########################################################

    def startTreeBasedCoord(self):
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

    def messageHandler_TreeBasedCoord(self, msg):
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
                if self.state_coordination == 0:
                    self.state_coordination += 1
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
                            self.state_coordination = 9999
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
                        self.state_coordination += 1
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
            self.state_coordination = 0
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