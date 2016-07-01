__author__ = 'Sonja Kolen'

from cluster_decentral.networksetup import setupNetwork
from building.environment import Environment
import time

stepSize = 3600
horizon = 86400*1  # horizon for scheduling
interval = 86400  # interval for scheduling

environment1 = Environment(100, stepSize)

# parameter 'dir' does nothing at the moment
myCluster = setupNetwork('dir_a', 'dir_b',  environment1, horizon, stepSize, interval, 0)
#myCluster.plotClusterGraph()
myCluster.excludeGasBoilers()
#myCluster.extendBESNeighborhood(20, myCluster.listCommBesIDs, myCluster.listLinks)
#myCluster.plotClusterGraph(myCluster.BESwithoutGasBoilers_ID, myCluster.listLinkswithoutGB)


root_ID = 'LV_Bus'
criterion_type = 'maxmindiff'
#criterion_type = 'absremainder'

#for i in range(len(myCluster.listCommBes)):
#    myCluster.listCommBes[i].printNeighbors()

for b in range(len(myCluster.listCommBes)):
    if myCluster.listCommBes[b].getID() == root_ID:
        break

#myCluster.listCommBes[b].generatePseudoTree(0, ['none'])
myCluster.StartLoadPropagationOPT(root_ID, 0, criterion_type)

state = myCluster.listCommBes[b].getLoadPropStatus()
#
#run cluster simulation
count = 0
start_time_neg = time.time()
#while myCluster.listCommBes[b].getLoadPropStatus() != 9999:
while myCluster.getStateNoMessages() == 0:
    print '################### NEGOTIATION ROUND {0} ################### '.format(count)
    myCluster.ProcessNetworkCommunication()
    count += 1

#count_2 = 0
#myCluster.noMessages = 0
#while myCluster.getStateNoMessages() == 0:
#    print '################### NEGOTIATION ROUND {0} ################### '.format(count + count_2)
#    myCluster.ProcessNetworkCommunication()
#    count_2 +=1
end_time_neg = time.time()

#calculate and print runtime
min_neg = (end_time_neg-start_time_neg)/60
if min_neg < 1:
    sec_neg = end_time_neg-start_time_neg
    min_neg = 0
else:
    sec_neg = (end_time_neg-start_time_neg) - int(min_neg)*60
print 'CLUSTER: Time for NEGOTIATION PHASE: {0} min {1} sec'.format(min_neg, sec_neg)

myCluster.plotDebugOutput(root_ID, 0, 'loadprop')

#myCluster.plotPseudoTree(root_ID)

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