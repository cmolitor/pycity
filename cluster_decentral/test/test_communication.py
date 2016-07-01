__author__ = 'Sonja Kolen'

from cluster_decentral.commbes import CommBes
from cluster_decentral.commcluster import CommCluster
from building.environment import Environment
from cluster_decentral.networksetup import setupNetwork
from multiprocessing import Process
import matplotlib.pyplot as plt

stepSize = 3600  # todo: not tested with other stepsize
horizon = 86400*1  # horizon for scheduling
interval = 86400  # interval for scheduling

environment1 = Environment(100, stepSize)


#myCluster = setupNetwork('dir', environment1, horizon, stepSize, interval)

testCommCluster1 = CommCluster('directory', environment1, horizon, stepSize, interval)

# create smartbes object
testCommBes1 = CommBes(stepSize=3600, TER1=2, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=100, specDemandTh=160, ID=100)
testCommBes2 = CommBes(stepSize=3600, TER1=2, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=100, specDemandTh=160, ID=101)
testCommBes3 = CommBes(stepSize=3600, TER1=2, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=100, specDemandTh=160, ID=102)
testCommBes4 = CommBes(stepSize=3600, TER1=2, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=100, specDemandTh=160, ID=103)
testCommBes5 = CommBes(stepSize=3600, TER1=2, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=100, specDemandTh=160, ID=104)
#testSmartBes3 = SmartBes(stepSize=3600, TER1=0, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=100, specDemandTh=160)

# add CommBes members to the cluster
testCommCluster1.addMember(testCommBes1)
testCommCluster1.addMember(testCommBes2)
testCommCluster1.addMember(testCommBes3)
testCommCluster1.addMember(testCommBes4)
testCommCluster1.addMember(testCommBes5)


# establish connections
testCommCluster1.setLink(testCommBes1, testCommBes2)
testCommCluster1.setLink(testCommBes1, testCommBes3)
testCommCluster1.setLink(testCommBes1, testCommBes5)
testCommCluster1.setLink(testCommBes2, testCommBes4)
testCommCluster1.setLink(testCommBes2, testCommBes5)
testCommCluster1.setLink(testCommBes3, testCommBes4)
testCommCluster1.setLink(testCommBes5, testCommBes4)

# print connectedness
# for k in range(len(testCommCluster1.listCommBes)):
#     testCommCluster1.listCommBes[k].printNeighbors()
#
# # perform initial action
# #testCommCluster1.PingPong(101)
# #testCommCluster1.SendHello()
# testCommCluster1.setupPseudoTree(testCommBes5)
#
# #fluct = testCommCluster1.getFluctuationsCurve(0, 82800)
# #xAxis = [x for x in range(1,24+1)]
#
# #plt.plot(xAxis, fluct, 'r')
# #plt.show()
testCommCluster1.PingPong(101)
#
#run cluster simulation
while 1: #endless loop
    testCommCluster1.ProcessNetworkCommunication()

#calculate and print statistics

TotalMsgSend = 0
TotalMsgReic = 0

for i in range(len(testCommCluster1.listCommBes)):
    TotalMsgSend = TotalMsgSend + testCommCluster1.listCommBes[i].getNumOfMsgSend()
    TotalMsgReic = TotalMsgReic + testCommCluster1.listCommBes[i].getNumOfMsgRec()
    #testCommCluster1.listCommBes[i].printPseudoTreeInfo()

print 'Messages sent: {0}'.format(TotalMsgSend)
print 'Messages received: {0}'.format(TotalMsgReic)
#testCommCluster1.PrintResults(0)
#testCommCluster1.plotClusterGraph()
print 'Finished!'