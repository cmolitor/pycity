# coding=utf-8
__author__ = 'Annika Wierichs'

from clustering.smartbes import SmartBes
import random
import numpy as np

# create smartbes object
testSmartBes1 = SmartBes(stepSize=3600, TER1=2.3, TER2=0, RSC=3, sizingMethod=-1, iApartments=1, sqm=100, specDemandTh=160)    # CHP
testSmartBes2 = SmartBes(stepSize=3600, TER1=-3, TER2=-1, RSC=3, sizingMethod=0.98, iApartments=1, sqm=100, specDemandTh=160)    # HP

# # test:
# test_schedulePool = testSmartBes.calcSchedulePool(fromTime=0, toTime=23*3600, objectiveFcn=1, absGap=1, relGap=0.3, solutionPoolIntensity=1)
# test_flexibility = testSmartBes.calcFlexibility()
# test_noOfSchedules = testSmartBes.getNoOfSchedules()
#
# print "Solution Pool (Number: %d)" % test_noOfSchedules
# for n in range(test_noOfSchedules):
#     print ""
#     for j in range(len(test_schedulePool[0])):
#         print '%.0f' % test_schedulePool[n][j],


# test flexibility
print "\n CHP:\n"
testSmartBes1.calcSchedulePool(fromTime=0, toTimeH=23*3600, objectiveFcn=1, absGap=2, relGap=0.3, solutionPoolIntensity=4)
testSmartBes1.calcImpactArray()
print "\n HP:\n"
testSmartBes2.calcSchedulePool(fromTime=0, toTimeH=23*3600, objectiveFcn=1, absGap=1, relGap=0.3, solutionPoolIntensity=3)
testSmartBes2.calcImpactArray()
