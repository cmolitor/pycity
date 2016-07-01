__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
from mpl_toolkits.axes_grid1 import host_subplot


interval = 86400
stepsize = 900

# result files_multicast, 14 days, abs gap 0-7
multicast_file_absGap0 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap0_T2015-03-11_12-00-39/results_log.txt'
multicast_file_absGap1 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap1_T2015-03-11_14-13-13/results_log.txt'
multicast_file_absGap2 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap2_T2015-03-11_14-50-22/results_log.txt'
multicast_file_absGap3 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap3_T2015-03-11_15-27-19/results_log.txt'
multicast_file_absGap4 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap4_T2015-03-11_16-03-20/results_log.txt'
multicast_file_absGap5 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap5_T2015-03-11_16-37-12/results_log.txt'
multicast_file_absGap6 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap6_T2015-03-11_17-13-01/results_log.txt'
multicast_file_absGap7 = '../results/RMOPT_SD14_RES25_mono_step900_AbsGap7_T2015-03-11_17-49-41/results_log.txt'

mulicast_extractor_absgap0 = ResultExtractor(multicast_file_absGap0, interval, stepsize, 1, 14)
mulicast_extractor_absgap1 = ResultExtractor(multicast_file_absGap1, interval, stepsize, 1, 14)
mulicast_extractor_absgap2 = ResultExtractor(multicast_file_absGap2, interval, stepsize, 1, 14)
mulicast_extractor_absgap3 = ResultExtractor(multicast_file_absGap3, interval, stepsize, 1, 14)
mulicast_extractor_absgap4 = ResultExtractor(multicast_file_absGap4, interval, stepsize, 1, 14)
mulicast_extractor_absgap5 = ResultExtractor(multicast_file_absGap5, interval, stepsize, 1, 14)
mulicast_extractor_absgap6 = ResultExtractor(multicast_file_absGap6, interval, stepsize, 1, 14)
mulicast_extractor_absgap7 = ResultExtractor(multicast_file_absGap7, interval, stepsize, 1, 14)

mulicast_extractor_absgap0.extractResults()
mulicast_extractor_absgap1.extractResults()
mulicast_extractor_absgap2.extractResults()
mulicast_extractor_absgap3.extractResults()
mulicast_extractor_absgap4.extractResults()
mulicast_extractor_absgap5.extractResults()
mulicast_extractor_absgap6.extractResults()
mulicast_extractor_absgap7.extractResults()


#plot avg schedules
avg_no_schedules = []
avg_no_schedules.append(mulicast_extractor_absgap0.getAvgNumberOfSchedules())
avg_no_schedules.append(mulicast_extractor_absgap1.getAvgNumberOfSchedules())
avg_no_schedules.append(mulicast_extractor_absgap2.getAvgNumberOfSchedules())
avg_no_schedules.append(mulicast_extractor_absgap3.getAvgNumberOfSchedules())
avg_no_schedules.append(mulicast_extractor_absgap4.getAvgNumberOfSchedules())
avg_no_schedules.append(mulicast_extractor_absgap5.getAvgNumberOfSchedules())
avg_no_schedules.append(mulicast_extractor_absgap6.getAvgNumberOfSchedules())
avg_no_schedules.append(mulicast_extractor_absgap7.getAvgNumberOfSchedules())

avg_relPTV = []
avg_relPTV.append(mulicast_extractor_absgap0.getAvgRelPTV())
avg_relPTV.append(mulicast_extractor_absgap1.getAvgRelPTV())
avg_relPTV.append(mulicast_extractor_absgap2.getAvgRelPTV())
avg_relPTV.append(mulicast_extractor_absgap3.getAvgRelPTV())
avg_relPTV.append(mulicast_extractor_absgap4.getAvgRelPTV())
avg_relPTV.append(mulicast_extractor_absgap5.getAvgRelPTV())
avg_relPTV.append(mulicast_extractor_absgap6.getAvgRelPTV())
avg_relPTV.append(mulicast_extractor_absgap7.getAvgRelPTV())

avg_runtime = []
avg_runtime.append(mulicast_extractor_absgap0.getAvgRuntime())
avg_runtime.append(mulicast_extractor_absgap1.getAvgRuntime())
avg_runtime.append(mulicast_extractor_absgap2.getAvgRuntime())
avg_runtime.append(mulicast_extractor_absgap3.getAvgRuntime())
avg_runtime.append(mulicast_extractor_absgap4.getAvgRuntime())
avg_runtime.append(mulicast_extractor_absgap5.getAvgRuntime())
avg_runtime.append(mulicast_extractor_absgap6.getAvgRuntime())
avg_runtime.append(mulicast_extractor_absgap7.getAvgRuntime())

print avg_no_schedules
print avg_relPTV
print avg_runtime

absGapAxis = [x for x in range(0,8)]


#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig = plt.figure()
ax1 = host_subplot(111, axes_class=AA.Axes)
#fig.suptitle("Evaluation of absolute gap to optimal local solution for multicast-based coordination")

#plot schedules
#ax1 = AA.Subplot(fig, 1,1,1 )
#fig.add_subplot(ax1, title=r'\normalsize{Average schedules vs. average relPTV}')
#plt.title('Average Number of schedules for 14 day simulation with different absolute gaps')
ax1.plot(absGapAxis, avg_no_schedules, 'r', label=r'average number of schedules')
ax1.plot(absGapAxis, avg_no_schedules, 'ro')
ax1.set_xlabel(r'\small{allowed absolute gap to optimal solution}')
ax1.set_ylabel(r'\small{average number of schedules}', color='r')
for tl in ax1.get_yticklabels():
    tl.set_color('r')

# plot relPTV
ax11 = ax1.twinx()
ax11.plot(absGapAxis, avg_relPTV, 'b', label=r'average RPTV')
ax11.plot(absGapAxis, avg_relPTV, 'bo')
ax11.set_ylabel(r'\small{average RPTV}', color='b')
for tl in ax11.get_yticklabels():
    tl.set_color('b')

# plot runtime
ax12 = ax1.twinx()
ax12.plot(absGapAxis, avg_runtime, 'g', label=r'average runtime')
ax12.plot(absGapAxis, avg_runtime, 'go')
ax12.set_ylabel(r'\small{average runtime [s]}', color='g')
for tl in ax12.get_yticklabels():
    tl.set_color('g')
new_fixed_axes = ax12.get_grid_helper().new_fixed_axis
ax12.axis["right"] = new_fixed_axes(loc="right", axes=ax12, offset=(60, 0))

# turn on grid
ax1.grid(True)
ax11.grid(True)
ax12.grid(True)


#second plot
#ax2 = fig.add_subplot(212, title=r'\normalsize{Average schedules vs. average runtime}')
#ax2.plot(absGapAxis, avg_no_schedules, 'r', label=r'average number of schedules')
#ax2.plot(absGapAxis, avg_no_schedules, 'ro')
#ax2.set_xlabel(r'\small{allowed absolute gap to optimal solution}')
#ax2.set_ylabel(r'\small{average schedules}', color='r')
#for tl in ax2.get_yticklabels():
#    tl.set_color('r')

#ax22 = ax2.twinx()
#ax22.plot(absGapAxis, avg_runtime, 'g', label=r'average runtime')
#ax22.plot(absGapAxis, avg_runtime, 'go')
#ax22.set_ylabel(r'\small{average runtime [s]}', color='g')
#for tl in ax22.get_yticklabels():
#    tl.set_color('g')

#ax2.grid(True)
plt.subplots_adjust(hspace=0.5, left=0.1, right=0.75, bottom=0.15, top=0.9)

fig.set_size_inches(6.2, 3.5)
#plt.legend(loc='lower right', ncol=1)
plt.savefig("fig_absgap", dpi=300)
#plt.show()

