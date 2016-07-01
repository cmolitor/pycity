__author__ = 'Sonja Kolen'

import cluster_decentral.networksetup as net
from building.environment import Environment
import time
import os
import datetime
import subprocess


def simulation (stepsize, sim_days, interval, RES_ratio, extend_neighborhood, el_radius, excl_gasboilers, solpoolint, absgap, act_msg_log, bivalent_HS, algtype, criterion_type):

    ######## CONFIGURATION ########

    #stepSize = 3600                             # 1 hour steps (=3600 sec)
    stepSize = stepsize                              # 15 min steps (900 sec)
    simulation_days = sim_days                         # number of days to be simulated
    horizon = 86400*simulation_days             # horizon for scheduling (number of days that shall be scheduled, beginning with 1 Jan)
    interval = interval                            # interval for scheduling (per day)
    renewable_energy_resources_ratio = RES_ratio     # ratio of renewable energy resources
    extend_neighborhood = extend_neighborhood                     # binary, if 1 extendBESNeighborhood will be called
    if extend_neighborhood:
        electric_radius = el_radius                        # needed for neighborhood extension (length in meters)
    exclude_gasboilers = excl_gasboilers                      # binary, if 1 excludeGasboilers will be called
    solutionPoolIntensity = solpoolint                   # set solution pool intensity of the cplex solver
    absGap = absgap                                 # set absolute gab accepted by the cplex solver
    # message logging should only be activated for debugging a few days, as 1 day ~ 40 MB message data
    activate_message_log = act_msg_log                    # binary, if 1 message logging is activated

    bivalent_heating_systems = bivalent_HS                # binary, 1 if bivalent heating systems shall be used, 0 for monovalent

    #set algorithm type | RMOPT = remainder multicast optimization | LPOPT = load propagation optimization
    algorithm_type=algtype
    #algorithm_type = 'LPOPT'
    #algorithm_type = 'RMOPT'
    #algorithm_type = 'LocalBest'

    scenario_file = "../netdata/Scenario.csv"
    network_file = "../netdata/suburban_146.uct"

    if algorithm_type == 'multicast':
        # remainder multicast optimization
        #starting_BES = ['PCC_5_11', 'PCC_9_16', 'PCC_7_07']     # list of BES where remainder multicast optimization is started at once
        #starting_BES = ['LV_Bus', 'PCC_1_07', 'PCC_3_07, PCC_5_07']
        starting_BES = ['LV_Bus', 'PCC_5_11', 'PCC_3_04', 'PCC_2_04']#, 'PCC_8_04', 'PCC_7_04', 'PCC_6_04', 'PCC_5_13']#, 'PCC_9_23', 'PCC_8_06', 'PCC_4_16', 'PCC_3_08', 'PCC_2_08', 'PCC_1_07', 'PCC_1_01', 'PCC_9_17']
    elif algorithm_type == 'tree':
        root_BES = 'LV_Bus'

    # choose global optimization criterion type
    criterion_type = criterion_type
    #criterion_type = 'maxmindiff'
    #criterion_type = 'absremainder


    # log file names and directories

    logfile_results = '/results_log.txt'         # file in which results of each day are saved for further analysis
    date_time_now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if bivalent_heating_systems:
        rel_results_dir = '../results/' + algorithm_type+'_SD'+str(simulation_days)+'_RES'+str(renewable_energy_resources_ratio)+'_bivalent_'+'step'+str(stepSize)+'_T'+date_time_now
    else:
        rel_results_dir = '../results/' + algorithm_type+'_SD'+str(simulation_days)+'_RES'+str(renewable_energy_resources_ratio)+'_mono_'+'step'+str(stepSize)+'_T'+date_time_now
    abs_results_dir = os.path.join(os.path.dirname(__file__), rel_results_dir)
    logfile_results_path = abs_results_dir + logfile_results


    #print logfile_results_path
    #print logfile_msg_path

    # create log directory
    if not os.path.exists(abs_results_dir):
        os.makedirs(abs_results_dir)

    # create results log file and log simulation configuration
    with open(logfile_results_path, 'a') as results_log_file:
        results_log_file.write('############## SIMULATION SETUP CONFIG ###############\n')
        results_log_file.write('HEADER: results log file for simulation with the following configuration\n')
        results_log_file.write('HEADER: time ' + date_time_now + '\n')
        results_log_file.write('HEADER: stepsize ' + str(stepSize)+ '\n')
        results_log_file.write('HEADER: simulationdays ' + str(simulation_days)+ '\n')
        results_log_file.write('HEADER: horizon ' + str(horizon)+ '\n')
        results_log_file.write('HEADER: interval ' + str(interval)+ '\n')
        results_log_file.write('HEADER: RESratiopercent ' + str(renewable_energy_resources_ratio)+ '\n')
        results_log_file.write('HEADER: extendneighborhood ' + str(extend_neighborhood)+ '\n')
        if extend_neighborhood:
            results_log_file.write('HEADER: electricradius ' + str(electric_radius)+ '\n')
        results_log_file.write('HEADER: excludegasboilers ' + str(exclude_gasboilers)+ '\n')
        results_log_file.write('HEADER: solutionPoolIntensity ' + str(solutionPoolIntensity) + '\n')
        results_log_file.write('HEADER: absGap ' + str(absGap) + '\n')
        results_log_file.write('HEADER: algorithm ' + algorithm_type+ '\n')
        if algorithm_type == 'multicast':
            results_log_file.write('HEADER: startingBES ' + str(starting_BES)+ '\n')
        elif algorithm_type == 'tree':
            results_log_file.write('HEADER: rootBES ' + str(root_BES)+ '\n')
        results_log_file.write('HEADER: criterion ' + criterion_type+ '\n')
        #results_log_file.write('HEADER: messagelogfile ' + logfile_msg_path+ '\n')
        results_log_file.write('HEADER: activatemessagelogging ' + str(activate_message_log) + '\n')
        results_log_file.write('HEADER: bivalent heating systems ' + str(bivalent_heating_systems) + '\n')
        results_log_file.write('HEADER: resultslogfile ' + logfile_results_path+ '\n')

        results_log_file.write('#########################################################'+ '\n'+ '\n')

    #generate message log file and log config information
    if activate_message_log:
        logfile_msg = '/message_log.txt'            # file in which messages are saved
        logfile_msg_path = abs_results_dir + logfile_msg
        with open(logfile_msg_path, 'a') as message_log_file:
            message_log_file.write('HEADER: message log file')
    else:
        logfile_msg_path = -1




    #environment setup
    environment1 = Environment(renewable_energy_resources_ratio, stepSize)

    # call bash script for network setup --> this generates a new version of networksetup.py
    #os.system("../scripts/netdata_extractor_v2.sh %s %s %s" % (network_file, scenario_file, algorithm_type))
    # here is a bug somewhere... python does not wait for the bash script to finish
    return_code = subprocess.call(["../scripts/netdata_extractor_v2.sh", network_file, scenario_file, algorithm_type])
    # reload network setup module
    reload(net)

    #cluster setup (via networksetup.py generated by netdata_extractor.sh)
    myMAS = net.setupNetwork(logfile_msg_path, logfile_results_path, environment1, horizon, stepSize, interval, bivalent_heating_systems, solutionPoolIntensity, absGap)

    #generate communication network without gas boilers (comment if communication network shall be electric network)
    if exclude_gasboilers:
        myMAS.excludeGasBoilers()

    #extend neighborhood of each BES by BES in certain electric radius
    if extend_neighborhood:
        if exclude_gasboilers:
            # for gas boiler only network use:
            myMAS.extendBESNeighborhood(electric_radius, myMAS.BESwithoutGasBoilers_ID, myMAS.listLinkswithoutGB)
        else:
            # for whole electric network use:
            myMAS.extendBESNeighborhood(electric_radius, myMAS.listCommBesIDs, myMAS.listLinks)


    # global init
    if algorithm_type == 'uncoord':
        myMAS.initUncoordScheduleSelection()

    #myMAS.printBESinfo()

    # plot graph
    #myMAS.plotClusterGraph(myMAS.BESwithoutGasBoilers_ID, myMAS.listLinkswithoutGB)
    #exit()

    simulation_from_time = 0
    for i in range(simulation_days): #for each day
        #start optimization for day i+1

        # SIMULATION OF REMAINDER MULTICAST ALGORITHM
        if algorithm_type == 'multicast':
            start_time_neg = time.time()
            myMAS.startMulticastBasedCoordination(simulation_from_time, starting_BES, criterion_type)

            print '\nCLUSTER: MULTICAST-BASED COORDINATION FOR DAY {0}\n'.format(i+1)

            counter = 0
            myMAS.noMessages = 0

            while myMAS.getStateNoMessages() == 0:
                myMAS.log_message('################### PLANNING ROUND {0} ON DAY {1} ###################'.format(counter, i+1))        #
                myMAS.ProcessNetworkCommunication()
                counter += 1

            end_time_neg = time.time()
            min_neg = (end_time_neg-start_time_neg)/60
            if min_neg < 1:
                sec_neg = end_time_neg-start_time_neg
                min_neg = 0
            else:
                sec_neg = (end_time_neg-start_time_neg) - int(min_neg)*60
            #print 'CLUSTER: Time for NEGOTIATION PHASE: {0} min {1} sec'.format(min_neg, sec_neg)
            myMAS.log_result('CLUSTER: Time for PLANNING PHASE in day {0}: {1} min {2} sec'.format(i+1, min_neg, sec_neg))

            if len(starting_BES) > 1: # ANALYSIS PHASE is only needed if more than one BES started negotiation phase

                print '\nCLUSTER: ANALYSIS PHASE FOR DAY {0}\n'.format(i+1)
                start_time_analysis = time.time()
                myMAS.analyzeMulticastBasedCoordination(starting_BES)
                myMAS.noMessages = 0

                counter = 0
                while myMAS.getStateNoMessages() == 0:
                    myMAS.log_message('################### ANALYSIS ROUND {0} ON DAY {1} ###################'.format(counter, i+1))
                    myMAS.ProcessNetworkCommunication()
                    counter += 1
                end_time_analysis = time.time()

                min_analysis = (end_time_analysis-start_time_analysis) / 60
                if min_analysis < 1:
                    sec_analysis = end_time_analysis - start_time_analysis
                    min_analysis = 0
                else:
                    sec_analysis = (end_time_analysis - start_time_analysis) - int(min_analysis) * 60
                #print 'CLUSTER: Time for ANALYSIS PHASE: {0} min {1} sec'.format(min_analysis, sec_analysis)
                myMAS.log_result('CLUSTER: Time for ANALYSIS PHASE in day {0}, {1} min {2} sec'.format(i+1, min_analysis, sec_analysis))

                min_all = min_analysis + min_neg
                sec_all = sec_analysis + sec_neg
                if sec_all>=60:
                    min_all += int(sec_all/60)
                    sec_all = sec_all % 60


                myMAS.log_result('CLUSTER: Time for PLANNING + ANALYSIS PHASES: {0} min {1} sec'.format(min_all, sec_all))

        # SIMULATION OF LOAD PROPAGATION ALGORITHM
        elif algorithm_type == 'tree':
            start_time = time.time()
            myMAS.startTreeBasedCoordination(root_BES, simulation_from_time, criterion_type)

            print '\nCLUSTER: TREE-BASED COORDINATION FOR DAY {0}\n'.format(i+1)

            counter = 0
            myMAS.noMessages = 0


            while myMAS.getStateNoMessages() == 0:
                myMAS.log_message('################### MESSAGE PROCESSING ROUND {0} ON DAY {1} ###################'.format(counter, i+1))        #
                #print '\nCLUSTER: NEGOTIATION PHASE FOR DAY {0}\n'.format(i+1)
                myMAS.ProcessNetworkCommunication()
                counter += 1

            end_time = time.time()
            minutes = (end_time-start_time)/60
            if minutes < 1:
                seconds = end_time-start_time
                minutes = 0
            else:
                seconds = (end_time-start_time) - int(minutes)*60
            #print 'CLUSTER: Time for NEGOTIATION PHASE: {0} min {1} sec'.format(min_neg, sec_neg)
            myMAS.log_result('CLUSTER: Time for PLANNING PHASE in day {0}: {1} min {2} sec'.format(i+1, minutes, seconds))

        elif algorithm_type == 'uncoord':
            print '\nCLUSTER: UNCOORDINATED SCHEDULE SELECTION FOR DAY {0}\n'.format(i+1)

            start_time = time.time()
            myMAS.startUncoordScheduleSelection(simulation_from_time)
            end_time = time.time()

            minutes = (end_time-start_time)/60
            if minutes < 1:
                seconds = end_time-start_time
                minutes = 0
            else:
                seconds = (end_time-start_time) - int(minutes)*60
            # the following line is needed in data extraction
            myMAS.log_result('CLUSTER: Time for PLANNING PHASE in day {0}: {1} min {2} sec'.format(i+1, minutes, seconds))


        myMAS.logResultsOfDay(simulation_from_time)
        #myMAS.plotDebugOutput('', simulation_from_time, 'remaindermulticast')

        # simulation of one interval finished
        #update fromTime for next round
        simulation_from_time += interval



