__author__ = 'Sonja Kolen'

###########################################################################################################
# THIS FILE AND ITS FUNCTIONS ARE OBSOLETE! THE SIMULATION USES THE FUNCTIONS FROM MultiAgentSystem CLASS #
###########################################################################################################


from commbes import CommBes
from _collections import deque
from multiprocessing import Process
from message import Message
from collections import deque
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import copy

class CommCluster(object):

    def __init__(self, message_log_file, results_log_file, environment, horizon, stepSize, interval):
        """
        constructor of CommCluster class
        :param dirAbsResults: directory to save results in ?
        :param environment: instance of the environment in which the cluster will be included
        :param horizon: time period (s) for which the schedules are calculated (e.g. 1 day ahead = 86400s)
        :param stepSize: time period (s) of the individual time step
        :param interval: time period (s) after which new schedules are calculated (interval <= horizon)
        :return:
        """

        self.horizon = horizon  # in seconds
        self.stepSize = stepSize  # in seconds
        self.interval = interval  # in seconds
        self.hSteps = horizon / stepSize
        self.iSteps = interval / stepSize

        self.listCommBes = []               #list of CommBes that are part of the cluster
        self.listCommBesIDs = []            #list of CommBes IDs that are part of the cluster
        self.NumOfLinks = 0                 #saves the number of links in the network
        self.listLinks = []               #list of all links in the cluster (format: [BES1, BES2])
        self.environment = environment

        self.noMessages = 0                 # binary variable indicating weather there were messages to be sent in the cluster or not

        self.BESwithoutGasBoilers_ID = []      # saves the network IDs of non-gasboiler BES if function excludeGasBoilers is called
        self.listLinkswithoutGB = []           # saves the links in a network without gas boilers if function excludeGabBoilers is called

        #logfile paths
        self.message_log_file = message_log_file     # file for message logging
        self.results_log_file = results_log_file     # file for results logging


    def addMember(self, CommBes):
        """
        Method to add CommBes to the cluster
        :param CommBes: CommBes which will be added to the cluster
        """
        self.listCommBes.append(CommBes)
        self.listCommBesIDs.append(CommBes.getID())

    def getNumberOfMembers(self):
        return len(self.listCommBes)

    def getNumberOfLinks(self):
        return self.NumOfLinks

    def setLink(self, CommBes1, CommBes2, ElectricalDistance):
        """
        create a new link between two members of the cluster, links are assumed to be bidirectional
        :param ID1: ID of CommBes to connect with ID2
        :param ID2: ID of CommBes to connect with ID1
        :param ElectricalDistance: length of cable between CommBes1 and CommBes2 in meters = electrical distance in meters
        :return:0 if link was created successfully, 1 if link creation failed
        """
        retval = 1
        if CommBes1.getID() in self.listCommBesIDs:
            if CommBes2.getID() in self.listCommBesIDs:                     #only if both IDs exists in the cluster
                for h in range(self.getNumberOfMembers()):
                    currID = self.listCommBes[h].getID()
                    if currID == CommBes1.getID():                          #create bidirectional link
                        retval = self.listCommBes[h].addNeighbor(CommBes2.getID(), ElectricalDistance)
                        #if retval == 0:
                            # print 'Connected ID {0} and ID {1}'.format(CommBes1.getID(), CommBes2.getID())
                    elif currID == CommBes2.getID():
                        retval = self.listCommBes[h].addNeighbor(CommBes1.getID(), ElectricalDistance)
                        #if retval == 0:
                            # print 'Connected ID {0} and ID {1}'.format(CommBes2.getID(), CommBes1.getID())
                if retval == 0:
                    self.NumOfLinks = self.NumOfLinks + 1
                    link = [CommBes1.getID(), CommBes2.getID()]
                    self.listLinks.append(link)
            else:
                 #error ID2 not in cluster
                return retval
        else:
             #error ID1 not in cluster
            return retval
        return retval

    def sendMessageToCommBes(self, type, data, receiverBES):
        """
        This function sends a "system message" from commcluster administration to any CommBes member of the cluster
        It can be used to start processes at agents or to stop them in case of error
        :param type: Type of the message that shall be sent
        :param data: Data to be sent in the message
        :param receiverBES: CommBes that receives the "system message"
        :return:
        """
        #ceate message object
        msg = Message(0,receiverBES.getID(),type, data)
        #append message object to receive buffer of CommBES
        receiverBES.appendToReceiveMsgBuffer(msg)
        return

    def ProcessNetworkCommunication(self):
        """
        process all send and receive buffers (in this order) of all cluster members
        :return:
        """
        # fist step: send all messages in all send buffers to their respective receivers
        no_empty_sendbuffer = 0
        for h in range(len(self.listCommBes)):
            sendbuffer = self.listCommBes[h].getSendMessageBuffer()
            if not sendbuffer:
                no_empty_sendbuffer += 1
            else:
                while len(sendbuffer) > 0:
                    #print 'PNC: buffer of ID {0} contains {1} elements'.format(self.listCommBes[h].getID(), len(sendbuffer))
                    msg = sendbuffer.popleft()
                    for k in range(len(self.listCommBes)):
                        if msg.getIDReceiver() == self.listCommBes[k].getID():
                            self.listCommBes[k].appendToReceiveMsgBuffer(msg)
                            break
        if no_empty_sendbuffer == len(self.listCommBes):
            self.noMessages = 1

        #second step: proccess all received messages at each CommBes
        # this step can be parallelized
        #CommBesProcs = []
        #for m in range(len(self.listCommBes)):
        #     proc = Process(target=self.listCommBes[m].messageHandler())
        #     proc.start() #start execution of CommBes agents in parallel
        #     CommBesProcs.append(proc)
        #for k in range(len(CommBesProcs)):
        #    CommBesProcs[k].join() # wait until all CommBes agents have finished

        for b in range(len(self.listCommBes)):
           self.listCommBes[b].messageHandler()

    def getStateNoMessages(self):
        return self.noMessages

    def PingPong(self, ID):
        print 'Starting Ping Pong...'
        self.listCommBes[0].StartPing(ID)

    def SendHello(self):
        print 'Starting hello messages...'
        self.listCommBes[2].StartHello()

    def setupPseudoTree(self, root):
        if root.getID() in self.listCommBesIDs:                       #  if a not with the rootID exists in the cluster
            for i in range(len(self.listCommBes)):              # find this node in list of CommBes
                if self.listCommBes[i].getID() == root.getID():
                    self.listCommBes[i].generatePseudoTree(0, ['none'])   #start pseudo tree generation (parameter 0 indicates root)
                    break

    def getElectricalDemandCurve(self, fromTime, toTime):
        """
        Returns the electrical demand curve of the cluster for a given time period
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: multi dimensional array (2x time period); first column: time; second column: values
        """
        _electricalDemandCurve = self.listCommBes[0].getElectricalDemandCurve(fromTime, toTime)
        for x in range(1, len(self.listCommBes)):
            _electricalDemandCurve[1, :] += self.listCommBes[x].getElectricalDemandCurve(fromTime, toTime)[1, :]
        return _electricalDemandCurve

    def getAnnualElectricityConsumption(self):
        """
        adds up annual energy consumption of all BES in cluster
        :param type:
        :return: annual electrical demand :rtype: int
        """
        _demandelectrical_annual = 0
        for x in range(0, len(self.listCommBes)):
            _demandelectrical_annual += self.listCommBes[x].getAnnualElectricalDemand()
        return _demandelectrical_annual

    def getRenewableGenerationCurve(self, fromTime, toTime):
        """
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: renewable generation curve for cluster
        """
        _AnnualEnergyDemand = self.getAnnualElectricityConsumption()
        return self.environment.getRenewableGenerationCurve(fromTime, toTime, _AnnualEnergyDemand)

    def getFluctuationsCurve(self, fromTime, toTime):
        """
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: resulting curve (electrical demand minus energy covered by RG) that will be flattened (1 x time period)
        """
        _RES = self.getRenewableGenerationCurve(fromTime, toTime)
        _Load = self.getElectricalDemandCurve(fromTime, toTime)
        return _RES[1, :] + _Load[1, :]

    def PrintResults(self, fromTime):
        """

        :return:
        """
        toTime = fromTime + (self.hSteps - 1) * self.stepSize

        fluct = self.getFluctuationsCurve(fromTime, toTime)
        load = [0 for i in range(len(fluct))]
        remainder = copy.deepcopy(fluct)
        zeros = [0 for x in range(len(remainder))]
        eldemand = self.getElectricalDemandCurve(fromTime, toTime)


        for b in range(len(self.listCommBes)):
            besload = self.listCommBes[b].getRemainder()
            if besload == -1:
                #error
                print 'Error: BES with ID {0} has not chosen a schedule'.format(self.listCommBes[b].getID())
                return
            for t in range((toTime-fromTime)/self.stepSize):
                load[t] = load[t] + besload[t]




        # plot for debugging
        xAxis = [x for x in range(1,self.hSteps+1)]
        xAxis2 = [x for x in range(1, self.hSteps+1)]
        #print 'dim of el demand curve is {0}'. format(len(eldemand[0]))

        #index = np.arrange

        plt.plot(xAxis, zeros, 'black', xAxis, fluct, 'r', xAxis, load, 'b')
        plt.plot(xAxis2, eldemand[1], 'y')
        plt.show()

    def plotClusterGraph(self, list_node_IDs, list_edges):
        """
        This function is meant to be a plot function for the cluster structure with all nodes and links
        :return:
        """
        myGraph = nx.Graph()

        #add nodes
        for bes in list_node_IDs:
            myGraph.add_node(bes)

        #add edges
        for link in list_edges:
            myGraph.add_edge(link[0],link[1])

        #draw graph
        pos = nx.graphviz_layout(myGraph)
        nx.draw(myGraph, pos)

        # show graph
        plt.show()

    def StartLoadPropagationOPT(self, rootBesID, fromTime, criterion_type):
        """
        This function starts a load propagation optimization
        - The cluster structures itself as a pseudo tree (from a given root node, root node determination to be distributed)

        - When a node has finished pseudo tree generation, it calculates its schedule pool
        - Each node chooses the "best" schedule out of the schedule pool (criterion for "best" TBD)
        - If a node is a child node it transmits the load curve corresponding to its chosen schedule to its parent
        - If a node has received load curves from all children, it sums them up, adds its on load curve and transmits
          this curve to its parent
        - If the root has obtained load curves of all its children, it calculates the overall load curve and the
          resulting remainder
        - The root node evaluates in which time slots which amount of energy is remaining and asks its children to
          find a way to compensate a certain amount of the remainder of each time slot (root decides when compensation
          is good enough, i.e. when it does not try to find a better remainder, criterion TBD)
        - If a node receives a load curve by its parent, defining in which time slot which amount of energy needs to be
          stored/ used more than before, it tries to find a schedule in its pool that "fits better" and hands the rest of
          the uncompensated energy over to all of its children (each a certain amount TBD)
        - If a leave node has received a compensation curve from its parent, and chosen a better schedule, its transmits
          its load curve to its parent (only if it has changed)
        - Parent nodes, again, collect the load curves of all children and propagate the accumulated load to the root,
          which then must decide if its starts a new round of investigation or not

        - constraints could be:
                    * a node must never use a schedule twice
                    * the amount of energy that was additionally compensated in the last investigation in relation to
                      the amount that was asked for could be an indicator for the root, if a new investigation is useful
                    * best schedule could be initially determined by smallest number of switching events (enough ?)
                    * take (normalized) gradient of curves into account for determining if a schedule "fits better"

        :return:
        """
        #toTime = fromTime + (self.hSteps - 1) * self.stepSize
        toTime = fromTime + self.interval - self.stepSize

        if self.BESwithoutGasBoilers_ID == []:
            print 'Error: gas boilers not excluded!'
            return

        fluctcurve_tmp = self.getFluctuationsCurve(fromTime, toTime)
        fluctcurve = []
        for t in range(len(fluctcurve_tmp)):
            fluctcurve.append(float(fluctcurve_tmp[t]))

        for b in range(len(self.listCommBes)):
            if self.listCommBesIDs[b] in self.BESwithoutGasBoilers_ID:
                # tell all non-gasboiler BES to start Pseudo tree generation for load prop optimization
                # only root node starts to send messages, the rest performs only reset of variables
                self.listCommBes[b].generatePseudoTree(rootBesID, ['LoadProp', fromTime, toTime, fluctcurve, criterion_type])
        return

    def plotDebugOutput(self, rootBESID,  fromTime, alg):
        """
        plot the current state of the cluster = fluctuation curve, remainder, load curve
        :param rootBESID ID of root
        :param fromTime starting time
        :param alg algorithm ('loadprop')
        :return:
        """
        #toTime = fromTime + (self.hSteps - 1) * self.stepSize
        toTime = fromTime + self.interval - self.stepSize
        fluctuation_curve = self.getFluctuationsCurve(fromTime, toTime)
        max_min_diff_fluct=max(fluctuation_curve) - min(fluctuation_curve)
        load_curve = [0 for x in range(len(fluctuation_curve))]
        remainder_curve = copy.deepcopy(fluctuation_curve)
        idx_rootBES = -1

        #calculate cluster load curve:
        for b in range(len(self.listCommBes)):
            child_load_curve = self.listCommBes[b].getChosenLoad()
            if child_load_curve == -1:
                child_load_curve = [0 for k in range(len(fluctuation_curve))]
            #print 'ID {0}: child_load_curve is {1}'.format(self.listCommBes[b].getID(), child_load_curve)
            #print 'CLUSTER: BES {0} has load curve {1}'.format(self.listCommBesIDs[b], child_load_curve)
            for t in range(len(load_curve)):
                load_curve[t] += child_load_curve[t]
            if b == rootBESID:
                idx_rootBES = b

        #calculate absolute local remainder
        abs_overall_remainder = 0
        abs_overall_fluctuation = 0

        # calc cluster remainder
        for t in range(len(remainder_curve)):
            remainder_curve[t] += load_curve[t]

        max_min_diff_remainder = max(remainder_curve) - min(remainder_curve)
        for t in range(len(remainder_curve)):
            abs_overall_remainder += abs(remainder_curve[t])
            abs_overall_fluctuation += abs(fluctuation_curve[t])


        if alg == 'loadprop':
            print 'CLUSTER: ID {0} (root) is in round {1}'.format(rootBESID, self.listCommBes[idx_rootBES].getLoadPropStatus())
            #self.log_result('CLUSTER: ID {0} (root) is in round {1}'.format(rootBESID, self.listCommBes[idx_rootBES].getLoadPropStatus()))
        elif alg == 'remaindermulticast':
            print 'CLUSTER: remainder multicast algorithm has finished!'
            #self.log_result('CLUSTER: remainder multicast algorithm has finished for day X!')


        print 'CLUSTER: current absolute remainder is {0} Watt'.format(abs_overall_remainder)
        print 'CLUSTER: absolute fluctuation energy is {0} Watt'.format(abs_overall_fluctuation)
        print 'CLUSTER: compensated fluctuations: {0} Watt ({1} %)'.format(abs_overall_fluctuation-abs_overall_remainder, 100-100*(abs_overall_remainder/abs_overall_fluctuation))
        print 'CLUSTER: compensated max-min-diff: {0} Watt ({1} %)'.format(max_min_diff_fluct-max_min_diff_remainder, 100-100*(max_min_diff_remainder/max_min_diff_fluct))

        # plot found remainder
        xAxis = [x for x in range(len(remainder_curve))]
        zeros = [0 for x in range(len(remainder_curve))]
        index = np.arange(len(remainder_curve))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, fluctuation_curve, bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, remainder_curve, bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, load_curve, 'g', label='Load Curve')

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')

        if alg == 'loadprop':
            plt.title('Load Optimization result after round {0}'.format(self.listCommBes[idx_rootBES].getLoadPropStatus()))
        elif alg == 'remaindermulticast':
            plt.title('Result of Remainder Multicast Optimization')
        plt.legend(loc='lower left', ncol=3)
        plt.tight_layout()
        plt.figtext(0.3,0.3,'Compensation of {0} %'.format(100-100*(abs_overall_remainder/abs_overall_fluctuation)), fontsize=12)
        plt.figtext(0.3,0.25,'Max-Min-Diff Improvement {0} %'.format(100-100*(max_min_diff_remainder/max_min_diff_fluct)), fontsize=12)
        #plot(xAxis, local_remainder, 'bo', xAxis, self.EFluctuationCurve, 'ro', xAxis, zeros, 'black', xAxis, load_curve, 'g')
        plt.show()

    def extendBESNeighborhood(self, ElectricalRadius, list_BES, links):
        """
        This functions extends the neighborhood of each CommBES by all nodes that have an electrical distance smaller
        or equal than ElectricalRadius. The direct electrical connections remain in the neighborhood of each node anyway.
        :param ElectricalRadius: Maximal electrical distance for communication neighborhood in meters
        :return:
        """
        self.log_message('CLUSTER: Starting extension of neighborhoods with Electrical Radius of {0}...'.format(ElectricalRadius))

        for u in range(len(list_BES)):
            for b in range(len(self.listCommBes)):
                if self.listCommBes[b].getID() == list_BES[u]:
                    break

            neighbors = self.listCommBes[b].getNeighbors()
            current_ID = self.listCommBes[b].getID()
            for n in range(len(neighbors)):       # for all neighbors of the current CommBES object
                for k in range(len(self.listCommBes)):
                    if self.listCommBesIDs[k] == neighbors[n]:
                        break
                distance = self.listCommBes[k].getElectricalDistance(current_ID)
                new_neighbors = deque()
                distance_to_new_neighbors = deque()
                if distance <= ElectricalRadius: # neighbor in radius
                    [new_neighbors, distance_to_new_neighbors]= self.listCommBes[k].getNeighborsInRadius(distance, ElectricalRadius, current_ID)

                    while new_neighbors:
                        x = new_neighbors.popleft()
                        d = distance_to_new_neighbors.popleft()
                        self.listCommBes[b].addNeighbor(x, d) # add new neighbor
                        if [self.listCommBesIDs[b], x] not in links and [x, self.listCommBesIDs[b]] not in links:
                            links.append([self.listCommBesIDs[b], x])
                            self.NumOfLinks = self.NumOfLinks + 1

                        for s in range(len(self.listCommBesIDs)):
                            if self.listCommBesIDs[s] == x:
                                break

                        [n_temp, d_temp] = self.listCommBes[s].getNeighborsInRadius(d, ElectricalRadius, current_ID)

                        if n_temp:
                            #update list of new neighbors
                            new_neighbors.extend(n_temp)
                            distance_to_new_neighbors.extend(d_temp)
        self.log_message('CLUSTER: Finished Extension of neighborhoods. Now there are {0} links.'.format(self.getNumberOfLinks()))

    def plotPseudoTree(self, rootID):
        """
        plot a graph of the pseudo tree
        :param rootID:
        :return:
        """
        print 'Plotting pseudo tree from root ID {0}...'.format(rootID)
        #STEP 1: COLLECT ALL PSEUDO TREE LINKS
        PT_links = []
        BES_to_process = deque()
        parent = deque
        for r in range(len(self.listCommBes)):
            if self.listCommBesIDs[r] == rootID:
                break

        #initialize BES to process with children of root
        [BES_to_process, parent] = self.listCommBes[r].getChildren()
        current_BES = rootID
        while BES_to_process:
            #print 'BES to process: {0}'.format(BES_to_process)

            BES = BES_to_process.popleft()
            #print 'BES is: {0}'.format(BES)
            p = parent.popleft()
            #raw_input('bla')
            if [BES, p] not in PT_links and [p, BES] not in PT_links:
                PT_links.append([p, BES])
            else:
                raw_input('error in pseudo tree: loop detected including the nodes {0} and {1}'.format(BES, p))

            for k in range(len(self.listCommBes)):
                if self.listCommBesIDs[k] == BES:
                    break

            # load children of current node (if any)
            [new_BES, new_p] = self.listCommBes[k].getChildren()
            #print 'new_BES: {0}'.format(new_BES)
            #print 'new_p: {0}'.format(new_p)
            if new_BES:
                BES_to_process += new_BES
                parent += new_p


        # STEP 2: plot the graph
        myGraph = nx.Graph()

        #add nodes
        for bes in self.listCommBesIDs:
            myGraph.add_node(bes)

        #add edges
        for link in PT_links:
            myGraph.add_edge(link[0],link[1])

        #draw graph
        pos = nx.graphviz_layout(myGraph)
        nx.draw(myGraph, pos)

        # show graph
        plt.show()
        print 'Plotting finished.'

    def excludeGasBoilers(self):
        """
        This function excludes all gas boiler BES from the communication network
        :return:
        """
        self.log_result('CLUSTER: Gas boiler exclusion...')
        self.BESwithoutGasBoilers_ID = copy.deepcopy(self.listCommBesIDs)
        self.listLinkswithoutGB = copy.deepcopy(self.listLinks)
        #print 'links with GB {0}'.format(self.listLinks)

        for b in range(len(self.listCommBes)):
            if self.listCommBes[b].isGasBoiler():
                neighbors = self.listCommBes[b].getNeighbors()
                for n in range(len(neighbors)):
                    #find neighbor n in BES list
                    for u in range(len(self.listCommBes)):
                        if self.listCommBes[u].getID() == neighbors[n]:
                            break
                    elDist_n = self.listCommBes[b].getElectricalDistance(neighbors[n])

                    for k in range(len(neighbors)):
                        if n != k:
                            elDist_k = self.listCommBes[b].getElectricalDistance(neighbors[k])
                            #add neighbor k to neighbor list of n
                            self.listCommBes[u].addNeighbor(neighbors[k], elDist_n+elDist_k)
                            #if new link not yet in list
                            if not ([neighbors[n], neighbors[k]] in self.listLinkswithoutGB) and not ([neighbors[k], neighbors[n]] in self.listLinkswithoutGB):
                                self.listLinkswithoutGB.append([neighbors[n], neighbors[k]])

                # delete GB BES in neighbor list of neighbors (we have bidirectional links)
                for a in range(len(neighbors)):
                    #find neighbor n in BES list
                    for c in range(len(self.listCommBes)):
                        if self.listCommBes[c].getID() == neighbors[a]:
                            break
                    self.listCommBes[c].removeNeighbor(self.listCommBes[b].getID())

                    #remove links to BES b in list of links without GB
                    if [neighbors[a], self.listCommBes[b].getID()] in self.listLinkswithoutGB:
                        #print 'hello1'
                        self.listLinkswithoutGB.remove([neighbors[a], self.listCommBes[b].getID()])
                    if [self.listCommBes[b].getID(), neighbors[a]] in self.listLinkswithoutGB:
                        #print 'hello2'
                        self.listLinkswithoutGB.remove([self.listCommBes[b].getID(), neighbors[a]])


                self.BESwithoutGasBoilers_ID.remove(self.listCommBes[b].getID())
        self.log_result('CLUSTER: BES without gas boilers: {0}'.format(self.BESwithoutGasBoilers_ID))
        self.log_result('CLUSTER: Links without gas boilers {0}'.format(self.listLinkswithoutGB))
        self.log_result('CLUSTER: Network without gas boilers has {0} BES and {1} links'.format(len(self.BESwithoutGasBoilers_ID), len(self.listLinkswithoutGB)))
        self.log_result('CLUSTER: Gas boiler exclusion finished!')
        return

    def startRemainderMulticastOPT(self, fromTime, list_start_IDs, criterion_type):
        """
        start remainder multicast optimization in cluster
        :param fromTime: start time
        :param startID: id of starting node
        :param criterion_type: type of optimization criterion, either 'maxmindiff' or 'absremainder'
        :return:
        """
        if not self.BESwithoutGasBoilers_ID:
            print 'ERROR: function excludeGasBoilers was not called!'
            return

        #toTime = fromTime + (self.hSteps - 1) * self.stepSize
        toTime = fromTime + self.interval - self.stepSize
        fluct_temp = self.getFluctuationsCurve(fromTime, toTime)
        fluct = []
        #fluct = [0 for k in range(len(fluct_temp))]
        for t in range(len(fluct_temp)):
            fluct.append(float(fluct_temp[t]))

        for b in range(len(self.BESwithoutGasBoilers_ID)):
            for k in range(len(self.listCommBes)):
                if self.listCommBes[k].getID() == self.BESwithoutGasBoilers_ID[b]:
                    break
            self.listCommBes[k].initRemainderMulticastOPT(fromTime, toTime, fluct, criterion_type)

            if self.listCommBes[k].getID() in list_start_IDs:
                print "CLUSTER: Starting RMOPT for Agent {0}".format(self.listCommBes[k].getID())
                self.listCommBes[k].startRemainderMulticastOPT()

    def anaylseRemainderMulticastOPT(self, list_start_IDs):
        """
        among all calculated results, choose the best one
        :return:
        """
        for b in range(len(self.BESwithoutGasBoilers_ID)):
            if self.BESwithoutGasBoilers_ID[b] in list_start_IDs:
                for k in range(len(self.listCommBes)):
                    if self.listCommBes[k].getID() == self.BESwithoutGasBoilers_ID[b]:
                        break

                self.listCommBes[k].analyseRemainderMulticastOPT()

    def checkSolution(self, listStartIDs):
        for b in range(len(self.BESwithoutGasBoilers_ID)):
            if self.BESwithoutGasBoilers_ID[b] in listStartIDs:
                for k in range(len(self.listCommBes)):
                    if self.listCommBes[k].getID() == self.BESwithoutGasBoilers_ID[b]:
                        break

                [path, schedules] = self.listCommBes[k].get_min_path()


                for u in range(len(self.BESwithoutGasBoilers_ID)):
                    for v in range(len(self.listCommBes)):
                        if self.listCommBes[v].getID() == self.BESwithoutGasBoilers_ID[u]:
                            break
                    for r in range(len(path)):
                        if path[r] == self.listCommBes[v].getID():
                            break



                self.listCommBes[v].setSchedule(schedules[r])

                self.plotDebugOutput('', 0, 'remaindermulticast')

    def initLocalBestChoice(self):
        """
        init local best choice alg
        must be called once at the beginning of the simulation to start the pseudo random number generator at each BES
        :return:
        """
        if not self.BESwithoutGasBoilers_ID:
            print 'ERROR: function excludeGasBoilers was not called!'
            return

        for b in range(len(self.BESwithoutGasBoilers_ID)):
            for k in range(len(self.listCommBes)):
                if self.listCommBesIDs[k] == self.BESwithoutGasBoilers_ID[b]:
                    break;
            # let each BES choose a schedule that is only locally optimal (no coordination with other agents)

            self.listCommBes[k].initLocalBestChoice()

        return



    def startLocalBestChoice(self, fromTime):
        """
        Tell each BES to calc a solution Pool with absGap= 0 (local best choice)
        if there is more than one schedule in the pool, select one randomly
        :param fromTime: start time
        :return:
        """
        if not self.BESwithoutGasBoilers_ID:
            print 'ERROR: function excludeGasBoilers was not called!'
            return


        toTime = fromTime + self.interval - self.stepSize

        for b in range(len(self.BESwithoutGasBoilers_ID)):
            for k in range(len(self.listCommBes)):
                if self.listCommBesIDs[k] == self.BESwithoutGasBoilers_ID[b]:
                    break;
            # let each BES choose a schedule that is only locally optimal (no coordination with other agents)

            self.listCommBes[k].localBestChoice(fromTime, toTime)

        return


    def logResultsOfDay(self, fromTime):
        """
        add all relevant results of the day to the results log file
        :return:
        """

        #toTime = fromTime + (self.hSteps - 1) * self.stepSize
        toTime = fromTime + self.interval-self.stepSize
        toTimeReal = fromTime + self.interval
        #self.log_result('\nCLUSTER: Result for day {0} ({1} sec - {2} sec)'.format(round(float(toTime/(toTime-fromTime))), fromTime, toTime, ))
        self.log_result('\nCLUSTER: Result for time interval {0} sec - {1} sec'.format(fromTime, toTimeReal))

        fluctuation_curve_temp = self.getFluctuationsCurve(fromTime, toTime)
        fluctuation_curve = []
        for t in range(len(fluctuation_curve_temp)):
            fluctuation_curve.append(fluctuation_curve_temp[t])

        load_curve = [0 for x in range(len(fluctuation_curve))]
        remainder_curve = copy.deepcopy(fluctuation_curve)
        number_of_schedules = 0
        list_no_schedules = []
        no_messages_sent = 0
        no_messages_rec = 0

        self.log_result('CLUSTER: Schedules of non-gasboiler BES:')
        self.log_result('CLUSTER: read as ID | index | endSOC | primary schedule | sec schedule')

        #calculate cluster load curve:
        for b in range(len(self.listCommBes)):
            if not self.listCommBes[b].isGasBoiler():
                number_of_schedules += self.listCommBes[b].getNoOfSchedules()
                list_no_schedules.append(self.listCommBes[b].getNoOfSchedules())

                no_messages_sent += self.listCommBes[b].getNumOfMsgSend_interval()
                no_messages_rec += self.listCommBes[b].getNumOfMsgSend_interval()

                bes_load_curve = self.listCommBes[b].getChosenLoad()
                bes_schedule = self.listCommBes[b].getChosenSchedule()
                bes_schedule_sec = self.listCommBes[b].getChosenScheduleSec()
                bes_schedule_index = self.listCommBes[b].getChosenScheduleIndex()
                bes_end_thsoc = self.listCommBes[b].getSOC()
                self.log_result('CLUSTER: ID {0} | {1} | {2} | {3} | {4}'.format(self.listCommBes[b].getID(), bes_schedule_index, bes_end_thsoc, bes_schedule, bes_schedule_sec))

                if bes_load_curve == -1:
                    bes_load_curve = [0 for k in range(len(fluctuation_curve))]
                #print 'ID {0}: child_load_curve is {1}'.format(self.listCommBes[b].getID(), child_load_curve)
                #print 'CLUSTER: BES {0} has load curve {1}'.format(self.listCommBesIDs[b], child_load_curve)
                for t in range(len(load_curve)):
                    load_curve[t] += bes_load_curve[t]


        #average number of schedules (only take non-gasboiler BES into account)
        avg_no_schedules = number_of_schedules / len(self.BESwithoutGasBoilers_ID)
        self.log_result('CLUSTER: average schedules | {0}'.format(avg_no_schedules))
        self.log_result('CLUSTER: min schedules | {0}'.format(min(list_no_schedules)))
        self.log_result('CLUSTER: max schedules | {0}'.format(max(list_no_schedules)))

        # log number of messages
        self.log_result('CLUSTER: sent messages | {0}'. format(no_messages_sent))
        self.log_result('CLUSTER: received messages | {0}'.format(no_messages_rec))


        # calc cluster remainder
        for t in range(len(remainder_curve)):
            remainder_curve[t] += load_curve[t]

        self.log_result('CLUSTER: fluctuation | {0}'.format(fluctuation_curve))
        self.log_result('CLUSTER: loadcurve | {0}'.format(load_curve))
        self.log_result('CLUSTER: remainder | {0}'.format(remainder_curve))

        # calc max min diff criterion
        max_min_diff_fluct=max(fluctuation_curve) - min(fluctuation_curve)
        max_min_diff_remainder = max(remainder_curve) - min(remainder_curve)
        self.log_result('CLUSTER: max-min-diff fluctuation curve {0} Watt'.format(max_min_diff_fluct))
        self.log_result('CLUSTER: max-min-diff remainder curve {0} Watt'.format(max_min_diff_remainder))
        self.log_result('CLUSTER: max-min-diff improvement {0} %'.format(100-100*float(max_min_diff_remainder/max_min_diff_fluct)))

        #calculate absolute remainder
        abs_overall_remainder = 0
        abs_overall_fluctuation = 0
        for t in range(len(remainder_curve)):
            abs_overall_remainder += abs(remainder_curve[t])
            abs_overall_fluctuation += abs(fluctuation_curve[t])
        self.log_result('CLUSTER: abs fluctuation {0} Watt'.format(abs_overall_fluctuation))
        self.log_result('CLUSTER: abs remainder {0} Watt'.format(abs_overall_remainder))
        self.log_result('CLUSTER: abs improvement {0} %'.format(100-100*float(abs_overall_remainder/abs_overall_fluctuation)))
        self.log_result('\n\n')

        return

    def log_result(self, text):
        """
        add new line with text to results log file
        :param text: text line to be logged
        :return:
        """

        with open(self.results_log_file, 'a') as log_file:
            log_file.write(text+'\n')
        return

    def log_message(self, text):
        """
        add new line with text to message log file
        :param text: text line to be added
        :return:
        """
        if self.message_log_file != -1:
            with open(self.message_log_file, 'a') as log_file:
                log_file.write(text+'\n')
        return

    def printBESinfo(self):
        """

        :return:
        """
        for b in range(len(self.listCommBesIDs)):

            self.listCommBes[b].printConfig()




