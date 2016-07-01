__author__ = 'Sonja Kolen'

from message import Message
from collections import deque
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import copy


class MultiAgentSystem(object):
    def __init__(self, message_log_file, results_log_file, environment, horizon, stepSize, interval):
        """
        constructor of MultiAgentSystem class
        :param message_log_file: file to save messages in (if enabled)
        :param results_log_file: file to save results in (if enabled)
        :param environment: instance of the environment in which the MAS will be included
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

        self.agents = []                 #list of agents that are part of the MAS
        self.agentIDs = []               #list of agent IDs that are part of the MAS
        self.NumOfLinks = 0              #saves the number of communication links in the network
        self.links = []                  #list of all links in the MAS (format: [agent1, agent2])
        self.environment = environment

        self.noMessages = 0                 # binary variable indicating whether there are messages to be sent in the MAS or not

        self.agentID_wo_GB = []      # saves the network IDs of non-gasboiler agents if function excludeGasBoilers is called
        self.links_wo_GB = []           # saves the communication links in a network without gas boilers if function excludeGabBoilers is called

        #logfile paths
        self.message_log_file = message_log_file     # file for message logging
        self.results_log_file = results_log_file     # file for results logging

    #########################################################
    ###### SETUP AND MAINTENANCE OF MULTI AGENT SYSTEM ######
    #########################################################

    def addMember(self, new_agent):
        """
        Method to add agents to the MAS
        :param new_agent: agent which will be added to the MAS
        """
        self.agents.append(new_agent)
        self.agentIDs.append(new_agent.getID())

    def setLink(self, agent1, agent2, ElectricalDistance):
        """
        create a new bidirectional link between two members of the MAS
        :param agent1: agent to connect with agent2
        :param agent2: agent to connect with agent1
        :param ElectricalDistance: length of cable between agent1 and agent2 in meters = electrical distance in meters
        :return:0 if link was created successfully, 1 if link creation failed
        """
        retval = 1
        if agent1.getID() in self.agentIDs:
            if agent2.getID() in self.agentIDs:                     #only if both IDs exists in the cluster
                for h in range(self.getNumberOfMembers()):
                    currID = self.agents[h].getID()
                    if currID == agent1.getID():                          #create bidirectional link
                        retval = self.agents[h].addNeighbor(agent2.getID(), ElectricalDistance)
                        #if retval == 0:
                            # print 'Connected ID {0} and ID {1}'.format(CommBes1.getID(), CommBes2.getID())
                    elif currID == agent2.getID():
                        retval = self.agents[h].addNeighbor(agent1.getID(), ElectricalDistance)
                        #if retval == 0:
                            # print 'Connected ID {0} and ID {1}'.format(CommBes2.getID(), CommBes1.getID())
                if retval == 0:
                    self.NumOfLinks = self.NumOfLinks + 1
                    link = [agent1.getID(), agent2.getID()]
                    self.links.append(link)
            else:
                 #error ID2 not in cluster
                return retval
        else:
             #error ID1 not in cluster
            return retval
        return retval

    def sendSystemMsg(self, type, data, receiver_agent):
        """
        This function sends a "system message" from MAS administration to any agent member of the MAS
        It can be used to start processes at agents or to stop them in case of error
        :param type: Type of the message that shall be sent
        :param data: Data to be sent in the message
        :param receiver_agent: agent that receives the "system message"
        :return:
        """
        #ceate message object
        msg = Message(0,receiver_agent.getID(),type, data)
        #append message object to receive buffer of CommBES
        receiver_agent.appendToReceiveMsgBuffer(msg)
        return

    def excludeGasBoilers(self):
        """
        This function excludes all gas boiler agents from the MAS
        :return:
        """
        self.log_result('MAS: Gas boiler exclusion...')
        self.agentID_wo_GB = copy.deepcopy(self.agentIDs)
        self.links_wo_GB = copy.deepcopy(self.links)
        #print 'links with GB {0}'.format(self.listLinks)

        for b in range(len(self.agents)):
            if self.agents[b].isGasBoiler():
                neighbors = self.agents[b].getNeighbors()
                for n in range(len(neighbors)):
                    #find neighbor n in agent list
                    for u in range(len(self.agents)):
                        if self.agents[u].getID() == neighbors[n]:
                            break
                    elDist_n = self.agents[b].getElectricalDistance(neighbors[n])

                    for k in range(len(neighbors)):
                        if n != k:
                            elDist_k = self.agents[b].getElectricalDistance(neighbors[k])
                            #add neighbor k to neighbor list of n
                            self.agents[u].addNeighbor(neighbors[k], elDist_n+elDist_k)
                            #if new link not yet in list
                            if not ([neighbors[n], neighbors[k]] in self.links_wo_GB) and not ([neighbors[k], neighbors[n]] in self.links_wo_GB):
                                self.links_wo_GB.append([neighbors[n], neighbors[k]])

                # delete GB agents in neighbor list of neighbors (we have bidirectional links)
                for a in range(len(neighbors)):
                    #find neighbor n in agent list
                    for c in range(len(self.agents)):
                        if self.agents[c].getID() == neighbors[a]:
                            break
                    self.agents[c].removeNeighbor(self.agents[b].getID())

                    #remove links to agent b in list of links without GB
                    if [neighbors[a], self.agents[b].getID()] in self.links_wo_GB:
                        self.links_wo_GB.remove([neighbors[a], self.agents[b].getID()])
                    if [self.agents[b].getID(), neighbors[a]] in self.links_wo_GB:
                        self.links_wo_GB.remove([self.agents[b].getID(), neighbors[a]])


                self.agentID_wo_GB.remove(self.agents[b].getID())
        self.log_result('MAS: Agents without gas boilers: {0}'.format(self.agentID_wo_GB))
        self.log_result('MAS: Links without gas boilers {0}'.format(self.links_wo_GB))
        self.log_result('MAS: Network without gas boilers has {0} agents and {1} links'.format(len(self.agentID_wo_GB), len(self.links_wo_GB)))
        self.log_result('MAS: Gas boiler exclusion finished!')
        return

    def extendAgentNeighborhood(self, ElectricalRadius, list_agents, links):
        """
        This function extends the neighborhood of each agent by all agents that have an electrical distance smaller
        or equal than ElectricalRadius. The direct electrical connections remain in the neighborhood of each node anyway.
        :param ElectricalRadius: Maximal electrical distance for communication neighborhood in meters
        :param list_agents: list of agents to refer to
        :param links: list of links to refer to
        :return:
        """
        self.log_message('MAS: Starting extension of neighborhoods with Electrical Radius of {0}...'.format(ElectricalRadius))

        for u in range(len(list_agents)):
            for b in range(len(self.agents)):
                if self.agents[b].getID() == list_agents[u]:
                    break

            neighbors = self.agents[b].getNeighbors()
            current_ID = self.agents[b].getID()
            for n in range(len(neighbors)):       # for all neighbors of the current agent
                for k in range(len(self.agents)):
                    if self.agentIDs[k] == neighbors[n]:
                        break
                distance = self.agents[k].getElectricalDistance(current_ID)
                new_neighbors = deque()
                distance_to_new_neighbors = deque()
                if distance <= ElectricalRadius: # neighbor in radius
                    [new_neighbors, distance_to_new_neighbors]= self.agents[k].getNeighborsInRadius(distance, ElectricalRadius, current_ID)

                    while new_neighbors:
                        x = new_neighbors.popleft()
                        d = distance_to_new_neighbors.popleft()
                        self.agents[b].addNeighbor(x, d) # add new neighbor
                        if [self.agentIDs[b], x] not in links and [x, self.agentIDs[b]] not in links:
                            links.append([self.agentIDs[b], x])
                            self.NumOfLinks = self.NumOfLinks + 1

                        for s in range(len(self.agentIDs)):
                            if self.agentIDs[s] == x:
                                break

                        [n_temp, d_temp] = self.agents[s].getNeighborsInRadius(d, ElectricalRadius, current_ID)

                        if n_temp:
                            #update list of new neighbors
                            new_neighbors.extend(n_temp)
                            distance_to_new_neighbors.extend(d_temp)
        self.log_message('MAS: Finished Extension of neighborhoods. Now there are {0} links.'.format(self.getNumberOfLinks()))


    #########################################################
    #################### GETTER FUNCTIONS ###################
    #########################################################

    def getNumberOfMembers(self):
        return len(self.agents)

    def getNumberOfLinks(self):
        return self.NumOfLinks

    def getStateNoMessages(self):
        return self.noMessages

    def getElectricalDemandCurve(self, fromTime, toTime):
        """
        Returns the electrical demand curve of the MAS for a given time period
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: multi dimensional array (2x time period); first column: time; second column: values
        """
        _electricalDemandCurve = self.agents[0].getElectricalDemandCurve(fromTime, toTime)
        for x in range(1, len(self.agents)):
            _electricalDemandCurve[1, :] += self.agents[x].getElectricalDemandCurve(fromTime, toTime)[1, :]
        return _electricalDemandCurve

    def getAnnualElectricityConsumption(self):
        """
        adds up annual energy consumption of all agents in the MAS
        :param type:
        :return: annual electrical demand :rtype: int
        """
        _demandelectrical_annual = 0
        for x in range(0, len(self.agents)):
            _demandelectrical_annual += self.agents[x].getAnnualElectricalDemand()
        return _demandelectrical_annual

    def getRenewableGenerationCurve(self, fromTime, toTime):
        """
        :param fromTime: start time in seconds
        :param toTime: end time in seconds
        :return: renewable generation curve for MAS
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

    #########################################################
    ############ DEBUGGING AND LOGGING FUNCTIONS ############
    #########################################################

    def PrintResults(self, fromTime):
        """
        plot the results for the complete scheduling period (fluctuation and load)
        :return:
        """
        toTime = fromTime + (self.hSteps - 1) * self.stepSize

        fluct = self.getFluctuationsCurve(fromTime, toTime)
        load = [0 for i in range(len(fluct))]
        remainder = copy.deepcopy(fluct)
        zeros = [0 for x in range(len(remainder))]
        eldemand = self.getElectricalDemandCurve(fromTime, toTime)


        for b in range(len(self.agents)):
            besload = self.agents[b].getRemainder()
            if besload == -1:
                #error
                print 'Error: Agent with ID {0} has not chosen a schedule'.format(self.agents[b].getID())
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

    def plotDebugOutput(self, root_agent,  fromTime, alg):
        """
        plot the current state of the MAS: fluctuation curve, remainder, load curve
        :param root_agent ID of root
        :param fromTime starting time
        :param alg algorithm (e.g. 'loadprop')
        :return:
        """
        #toTime = fromTime + (self.hSteps - 1) * self.stepSize
        toTime = fromTime + self.interval - self.stepSize
        fluctuation_curve = self.getFluctuationsCurve(fromTime, toTime)
        max_min_diff_fluct=max(fluctuation_curve) - min(fluctuation_curve)
        consumption_curve = [0 for x in range(len(fluctuation_curve))]
        remainder_curve = copy.deepcopy(fluctuation_curve)
        idx_rootagent = -1

        #calculate cluster load curve:
        for b in range(len(self.agents)):
            child_consumption_curve = self.agents[b].getChosenLoad()
            if child_consumption_curve == -1:
                child_consumption_curve = [0 for k in range(len(fluctuation_curve))]
            #print 'ID {0}: child_load_curve is {1}'.format(self.listCommBes[b].getID(), child_load_curve)
            #print 'CLUSTER: BES {0} has load curve {1}'.format(self.listCommBesIDs[b], child_load_curve)
            for t in range(len(consumption_curve)):
                consumption_curve[t] += child_consumption_curve[t]
            if b == root_agent:
                idx_rootagent = b

        #calculate absolute local remainder
        abs_overall_remainder = 0
        abs_overall_fluctuation = 0

        # calc cluster remainder
        for t in range(len(remainder_curve)):
            remainder_curve[t] += consumption_curve[t]

        max_min_diff_remainder = max(remainder_curve) - min(remainder_curve)
        for t in range(len(remainder_curve)):
            abs_overall_remainder += abs(remainder_curve[t])
            abs_overall_fluctuation += abs(fluctuation_curve[t])


        if alg == 'loadprop':
            print 'MAS: ID {0} (root) is in round {1}'.format(root_agent, self.agents[idx_rootagent].getCoordState())
            #self.log_result('CLUSTER: ID {0} (root) is in round {1}'.format(rootBESID, self.listCommBes[idx_rootBES].getLoadPropStatus()))
        elif alg == 'remaindermulticast':
            print 'MAS: remainder multicast algorithm has finished!'
            #self.log_result('CLUSTER: remainder multicast algorithm has finished for day X!')


        print 'MAS: current absolute remainder is {0} Watt'.format(abs_overall_remainder)
        print 'MAS: absolute fluctuation energy is {0} Watt'.format(abs_overall_fluctuation)
        print 'MAS: compensated fluctuations: {0} Watt ({1} %)'.format(abs_overall_fluctuation-abs_overall_remainder, 100-100*(abs_overall_remainder/abs_overall_fluctuation))
        print 'MAS: compensated max-min-diff: {0} Watt ({1} %)'.format(max_min_diff_fluct-max_min_diff_remainder, 100-100*(max_min_diff_remainder/max_min_diff_fluct))

        # plot remainder
        xAxis = [x for x in range(len(remainder_curve))]
        zeros = [0 for x in range(len(remainder_curve))]
        index = np.arange(len(remainder_curve))
        bar_width = 0.5
        opacity = 0.5
        error_config={'ecolor': '0.3'}

        plt.plot(xAxis, zeros, 'black')
        plt.bar(index, fluctuation_curve, bar_width, alpha=opacity, color='r', label='Fluctuation', error_kw=error_config)
        plt.bar(index, remainder_curve, bar_width, alpha=opacity, color='b', label='Remainder', error_kw=error_config)
        plt.plot(index, consumption_curve, 'g', label='Consumption')

        plt.xlabel('Time [h]')
        plt.ylabel('Energy [W]')

        if alg == 'loadprop':
            plt.title('Load Optimization result after round {0}'.format(self.agents[idx_rootagent].getCoordState()))
        elif alg == 'remaindermulticast':
            plt.title('Result of Remainder Multicast Optimization')
        plt.legend(loc='lower left', ncol=3)
        plt.tight_layout()
        plt.figtext(0.3,0.3,'Compensation of {0} %'.format(100-100*(abs_overall_remainder/abs_overall_fluctuation)), fontsize=12)
        plt.figtext(0.3,0.25,'Max-Min-Diff Improvement {0} %'.format(100-100*(max_min_diff_remainder/max_min_diff_fluct)), fontsize=12)
        #plot(xAxis, local_remainder, 'bo', xAxis, self.EFluctuationCurve, 'ro', xAxis, zeros, 'black', xAxis, load_curve, 'g')
        plt.show()

    def plotPseudoTree(self, rootID):
        """
        plot a graph of the pseudo tree
        :param rootID: ID of root agent
        :return:
        """
        print 'Plotting pseudo tree from root ID {0}...'.format(rootID)
        #STEP 1: COLLECT ALL PSEUDO TREE LINKS
        PT_links = []
        agents_to_process = deque()
        parent = deque
        for r in range(len(self.agents)):
            if self.agentIDs[r] == rootID:
                break

        #initialize agents to process with children of root
        [agents_to_process, parent] = self.agents[r].getChildren()
        current_BES = rootID
        while agents_to_process:
            #print 'BES to process: {0}'.format(BES_to_process)

            curr_agent = agents_to_process.popleft()
            #print 'BES is: {0}'.format(BES)
            p = parent.popleft()
            #raw_input('bla')
            if [curr_agent, p] not in PT_links and [p, curr_agent] not in PT_links:
                PT_links.append([p, curr_agent])
            else:
                raw_input('error in pseudo tree: loop detected including the nodes {0} and {1}'.format(curr_agent, p))

            for k in range(len(self.agents)):
                if self.agentIDs[k] == curr_agent:
                    break

            # load children of current node (if any)
            [new_agents, new_p] = self.agents[k].getChildren()
            #print 'new_BES: {0}'.format(new_BES)
            #print 'new_p: {0}'.format(new_p)
            if new_agents:
                agents_to_process += new_agents
                parent += new_p


        # STEP 2: plot the graph
        myGraph = nx.Graph()

        #add nodes
        for a in self.agentIDs:
            myGraph.add_node(a)

        #add edges
        for link in PT_links:
            myGraph.add_edge(link[0],link[1])

        #draw graph
        pos = nx.graphviz_layout(myGraph)
        nx.draw(myGraph, pos)

        # show graph
        plt.show()
        print 'Plotting finished.'

    def checkSolution(self, listStartIDs):
        """
        debugging function for multicast algorithm
        :param listStartIDs: ID list of starting agents
        :return:
        """
        for b in range(len(self.agentID_wo_GB)):
            if self.agentID_wo_GB[b] in listStartIDs:
                for k in range(len(self.agents)):
                    if self.agents[k].getID() == self.agentID_wo_GB[b]:
                        break

                [path, schedules] = self.agents[k].get_min_path()


                for u in range(len(self.agentID_wo_GB)):
                    for v in range(len(self.agents)):
                        if self.agents[v].getID() == self.agentID_wo_GB[u]:
                            break
                    for r in range(len(path)):
                        if path[r] == self.agents[v].getID():
                            break



                self.agents[v].setSchedule(schedules[r])

                self.plotDebugOutput('', 0, 'remaindermulticast')

    def logResultsOfDay(self, fromTime):
        """
        add all relevant results of the day to the results log file
        -- this is the main logging function --
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

        consumption_curve = [0 for x in range(len(fluctuation_curve))]
        remainder_curve = copy.deepcopy(fluctuation_curve)
        number_of_schedules = 0
        list_no_schedules = []
        no_messages_sent = 0
        no_messages_rec = 0

        self.log_result('CLUSTER: Schedules of non-gasboiler BES:')
        self.log_result('CLUSTER: read as ID | index | endSOC | primary schedule | sec schedule')

        #calculate MAS consumption curve:
        for b in range(len(self.agents)):
            if not self.agents[b].isGasBoiler():
                number_of_schedules += self.agents[b].getNoOfSchedules()
                list_no_schedules.append(self.agents[b].getNoOfSchedules())

                no_messages_sent += self.agents[b].getNumOfMsgSend_interval()
                no_messages_rec += self.agents[b].getNumOfMsgSend_interval()

                agent_consumption_curve = self.agents[b].getChosenLoad()
                bes_schedule = self.agents[b].getChosenSchedule()
                bes_schedule_sec = self.agents[b].getChosenScheduleSec()
                bes_schedule_index = self.agents[b].getChosenScheduleIndex()
                bes_end_thsoc = self.agents[b].getSOC()
                self.log_result('CLUSTER: ID {0} | {1} | {2} | {3} | {4}'.format(self.agents[b].getID(), bes_schedule_index, bes_end_thsoc, bes_schedule, bes_schedule_sec))

                if agent_consumption_curve == -1:
                    agent_consumption_curve = [0 for k in range(len(fluctuation_curve))]
                #print 'ID {0}: child_load_curve is {1}'.format(self.listCommBes[b].getID(), child_load_curve)
                #print 'CLUSTER: BES {0} has load curve {1}'.format(self.listCommBesIDs[b], child_load_curve)
                for t in range(len(consumption_curve)):
                    consumption_curve[t] += agent_consumption_curve[t]


        #average number of schedules (only take non-gasboiler BES into account)
        avg_no_schedules = number_of_schedules / len(self.agentID_wo_GB)
        self.log_result('CLUSTER: average schedules | {0}'.format(avg_no_schedules))
        self.log_result('CLUSTER: min schedules | {0}'.format(min(list_no_schedules)))
        self.log_result('CLUSTER: max schedules | {0}'.format(max(list_no_schedules)))

        # log number of messages
        self.log_result('CLUSTER: sent messages | {0}'. format(no_messages_sent))
        self.log_result('CLUSTER: received messages | {0}'.format(no_messages_rec))


        # calc cluster remainder
        for t in range(len(remainder_curve)):
            remainder_curve[t] += consumption_curve[t]

        self.log_result('CLUSTER: fluctuation | {0}'.format(fluctuation_curve))
        self.log_result('CLUSTER: loadcurve | {0}'.format(consumption_curve))
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

    def printAgentInfo(self):
        """

        :return:
        """
        for b in range(len(self.agentIDs)):

            self.agents[b].printConfig()

    #########################################################
    ################# SIMULATION FUNCTIONS ##################
    #########################################################


    def ProcessNetworkCommunication(self):
        """
        process all send and receive buffers (in this order) of all cluster members
        -- this is the main function of the MultiAgentSystem class --
        :return:
        """
        # fist step: send all messages in all send buffers to their respective receivers
        no_empty_sendbuffer = 0
        for h in range(len(self.agents)):
            sendbuffer = self.agents[h].getSendMessageBuffer()
            if not sendbuffer:
                no_empty_sendbuffer += 1
            else:
                while len(sendbuffer) > 0:
                    #print 'PNC: buffer of ID {0} contains {1} elements'.format(self.listCommBes[h].getID(), len(sendbuffer))
                    msg = sendbuffer.popleft()
                    for k in range(len(self.agents)):
                        if msg.getIDReceiver() == self.agents[k].getID():
                            self.agents[k].appendToReceiveMsgBuffer(msg)
                            break
        if no_empty_sendbuffer == len(self.agents):
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

        for b in range(len(self.agents)):
           self.agents[b].messageHandler()

    def PingPong(self, ID):
        print 'Starting Ping Pong...'
        self.agents[0].StartPing(ID)

    #def setupPseudoTree(self, root):
    #    if root.getID() in self.agentIDs:                       #  if a not with the rootID exists in the cluster
    #        for i in range(len(self.agents)):              # find this node in list of CommBes
    #            if self.agents[i].getID() == root.getID():
    #                self.agents[i].generatePseudoTree(0, ['none'])   #start pseudo tree generation (parameter 0 indicates root)
    #                break

    def startTreeBasedCoordination(self, rootBesID, fromTime, criterion_type):
        """
        This function starts tree-based coordination algorithm
        :return:
        """
        #toTime = fromTime + (self.hSteps - 1) * self.stepSize
        toTime = fromTime + self.interval - self.stepSize

        if self.agentID_wo_GB == []:
            print 'Error: gas boilers not excluded!'
            return

        fluctcurve_tmp = self.getFluctuationsCurve(fromTime, toTime)
        fluctcurve = []
        for t in range(len(fluctcurve_tmp)):
            fluctcurve.append(float(fluctcurve_tmp[t]))

        for b in range(len(self.agents)):
            if self.agentIDs[b] in self.agentID_wo_GB:
                # tell all non-gasboiler BES to start Pseudo tree generation for load prop optimization
                # only root node starts to send messages, the rest performs only reset of variables
                self.agents[b].generatePseudoTree(rootBesID, ['LoadProp', fromTime, toTime, fluctcurve, criterion_type])
        return

    def startMulticastBasedCoordination(self, fromTime, list_start_IDs, criterion_type):
        """
        start remainder multicast optimization in cluster
        :param fromTime: start time
        :param startID: id of starting node
        :param criterion_type: type of optimization criterion, either 'maxmindiff' or 'absremainder'
        :return:
        """
        if not self.agentID_wo_GB:
            print 'ERROR: function excludeGasBoilers was not called!'
            return

        #toTime = fromTime + (self.hSteps - 1) * self.stepSize
        toTime = fromTime + self.interval - self.stepSize
        fluct_temp = self.getFluctuationsCurve(fromTime, toTime)
        fluct = []
        #fluct = [0 for k in range(len(fluct_temp))]
        for t in range(len(fluct_temp)):
            fluct.append(float(fluct_temp[t]))

        for b in range(len(self.agentID_wo_GB)):
            for k in range(len(self.agents)):
                if self.agents[k].getID() == self.agentID_wo_GB[b]:
                    break
            self.agents[k].initCoordination(fromTime, toTime, fluct, criterion_type)

            if self.agents[k].getID() in list_start_IDs:
                print "CLUSTER: Starting RMOPT for Agent {0}".format(self.agents[k].getID())
                self.agents[k].startCoordination()

    def analyzeMulticastBasedCoordination(self, list_start_IDs):
        """
        among all calculated results, choose the best one
        :return:
        """
        for b in range(len(self.agentID_wo_GB)):
            if self.agentID_wo_GB[b] in list_start_IDs:
                for k in range(len(self.agents)):
                    if self.agents[k].getID() == self.agentID_wo_GB[b]:
                        break

                self.agents[k].analyseCoordination()

    def initUncoordScheduleSelection(self):
        """
        init uncoordinated schedule selection
        must be called once at the beginning of the simulation to start the pseudo random number generator at each BES
        :return:
        """
        if not self.agentID_wo_GB:
            print 'ERROR: function excludeGasBoilers was not called!'
            return

        for b in range(len(self.agentID_wo_GB)):
            for k in range(len(self.agents)):
                if self.agentIDs[k] == self.agentID_wo_GB[b]:
                    break;
            # let each BES choose a schedule that is only locally optimal (no coordination with other agents)

            self.agents[k].initUncoordScheduleSelection()

        return

    def startUncoordScheduleSelection(self, fromTime):
        """
        Tell each BES to calc a solution Pool with absGap= 0 (local best choice)
        if there is more than one schedule in the pool, select one randomly
        :param fromTime: start time
        :return:
        """
        if not self.agentID_wo_GB:
            print 'ERROR: function excludeGasBoilers was not called!'
            return


        toTime = fromTime + self.interval - self.stepSize

        for b in range(len(self.agentID_wo_GB)):
            for k in range(len(self.agents)):
                if self.agentIDs[k] == self.agentID_wo_GB[b]:
                    break;
            # let each BES choose a schedule that is only locally optimal (no coordination with other agents)

            self.agents[k].startUncoordScheduleSelection(fromTime, toTime)

        return


