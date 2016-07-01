__author__ = 'Sonja Kolen'

from cluster_decentral.networksetup import setupNetwork
from building.environment import Environment
import matplotlib.pyplot as plt
from cluster_decentral.commbes import CommBes
from cluster_decentral.commcluster import CommCluster
import time

stepSize = 3600
horizon = 86400*1  # horizon for scheduling
interval = 86400  # interval for scheduling

environment1 = Environment(50, stepSize)

# parameter 'dir' does nothing at the moment
myCluster = setupNetwork('dir', environment1, horizon, stepSize, interval)
#myCluster.plotClusterGraph(myCluster.listCommBesIDs, myCluster.listLinks)

myCluster.excludeGasBoilers()
#myCluster.extendBESNeighborhood(20, myCluster.BESwithoutGasBoilers_ID, myCluster.listLinkswithoutGB)
#myCluster.plotClusterGraph(myCluster.BESwithoutGasBoilers_ID, myCluster.listLinkswithoutGB)



#starting_BES = ['PCC_1_01', 'PCC_4_04', 'PCC_2_11']
starting_BES = ['PCC_5_11', 'PCC_9_16', 'PCC_7_07']
#starting_BES = myCluster.BESwithoutGasBoilers_ID
criterion_type = 'maxmindiff'
#criterion_type = 'absremainder'

####################PHASE 1####################################
myCluster.startRemainderMulticastOPT(0, starting_BES, criterion_type)
counter = 0
# while there are still messages sent:
start_time_neg = time.time()
while myCluster.getStateNoMessages() == 0:
#while counter < 5:
    print '######################################## NEGOTIATION ROUND {0} ########################################'.format(counter)
    #raw_input('new round, press any key...')
    myCluster.ProcessNetworkCommunication()
    counter += 1

end_time_neg = time.time()
min_neg = (end_time_neg-start_time_neg)/60
if min_neg < 1:
    sec_neg = end_time_neg-start_time_neg
    min_neg = 0
else:
    sec_neg = (end_time_neg-start_time_neg) - int(min_neg)*60
print 'CLUSTER: Time for NEGOTIATION PHASE: {0} min {1} sec'.format(min_neg, sec_neg)

myCluster.plotDebugOutput('dummy', 0, 'remaindermulticast')
#myCluster.checkSolution('PCC_5_11')

if len(starting_BES) > 1: # ANALYSIS PHASE is only needed if more than one BES started negotiation phase

    ################### PHASE 2 ###################################
    myCluster.anaylseRemainderMulticastOPT(starting_BES)
    myCluster.noMessages = 0
    #raw_input('press any key....')
    counter = 0
    start_time_analysis = time.time()
    while myCluster.getStateNoMessages() == 0:
        print '############################ ANALYSIS ROUND {0} ##########################'.format(counter)
        myCluster.ProcessNetworkCommunication()
        counter += 1
    end_time_analysis = time.time()

    min_analysis = (end_time_analysis-start_time_analysis) / 60
    if min_analysis < 1:
        sec_analysis = end_time_analysis - start_time_analysis
        min_analysis = 0
    else:
        sec_analysis = (end_time_analysis - start_time_analysis) - int(min_analysis) * 60
    #################### END ##################################
    print 'CLUSTER: Time for ANALYSIS PHASE: {0} min {1} sec'.format(min_analysis, sec_analysis)

    min_all = min_analysis + min_neg
    sec_all = sec_analysis + sec_neg
    if sec_all>=60:
        min_all += int(sec_all/60)
        sec_all = sec_all % 60


    print 'CLUSTER: Time for NEGOTIATION + ANALYSIS PHASES: {0} min {1} sec'.format(min_all, sec_all)

    myCluster.plotDebugOutput('dummy', 0, 'remaindermulticast')

#calculate and print statistics

TotalMsgSend = 0
TotalMsgReic = 0

for i in range(len(myCluster.listCommBes)):
    TotalMsgSend = TotalMsgSend + myCluster.listCommBes[i].getNumOfMsgSend()
    TotalMsgReic = TotalMsgReic + myCluster.listCommBes[i].getNumOfMsgRec()
    #myCluster.listCommBes[i].printPseudoTreeInfo()

print 'CLUSTER: Messages sent: {0}'.format(TotalMsgSend)
print 'CLUSTER: Messages received: {0}'.format(TotalMsgReic)
#myCluster.PrintResults(0)
#myCluster.plotClusterGraph()
print 'Finished!'