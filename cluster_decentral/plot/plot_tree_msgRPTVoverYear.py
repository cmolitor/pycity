__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
from mpl_toolkits.axes_grid1 import host_subplot


interval = 86400
stepsize = 900

slides = 1

resultfile_tree = '../results/LPOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-10_10-36-33/results_log.txt'
#resultfile_tree = '../results/LPOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_02-54-05/results_log.txt'

tree_extractor = ResultExtractor(resultfile_tree, interval, stepsize, 1, 365)
tree_extractor.extractResults()
tree_msg = tree_extractor.getMessages()
tree_msg_avg = tree_extractor.getAvgMessages()
tree_RPTV_avg = tree_extractor.getAvgRelPTV()
tree_mvgavg_msg = tree_extractor.getMessage_MovingAvg(21)
tree_mvgavg_RPTV = tree_extractor.getRPTV_MovingAvg(21)


dayAxis = [x for x in range(1,366)]
tree_msg_avg_curve = [tree_msg_avg for i in range(0,365)]
tree_RPTV_avg_curve = [tree_RPTV_avg for i in range(0,365)]


#latex settings for plot
plt.rc('text', usetex=True)
if slides:
    plt.rc('font', family='sans-serif')
else:
    plt.rc('font', family='serif')

fig = plt.figure()
ax1 = host_subplot(111, axes_class=AA.Axes)
#fig.suptitle("Evaluation of absolute gap to optimal local solution for multicast-based coordination")

#plot schedules
#ax1 = AA.Subplot(fig, 1,1,1 )
#fig.add_subplot(ax1, title=r'\normalsize{Average schedules vs. average relPTV}')
#plt.title('Average Number of schedules for 14 day simulation with different absolute gaps')
#ax1.plot(dayAxis, tree_mvgavg_msg, 'ro', label=r'\small{number of messages tree}')
#ax1.plot(dayAxis, tree_msg, 'r.')
ax1.plot(dayAxis, tree_mvgavg_msg, 'r')
ax1.plot(dayAxis, tree_msg_avg_curve, 'r--')
ax1.set_xlabel(r'\small{days}')
ax1.set_ylabel(r'\small{number of messages}', color='r')
for tl in ax1.get_yticklabels():
     tl.set_color('r')

# plot relPTV
ax11 = ax1.twinx()
#ax11.plot(dayAxis, tree_mvgavg_RPTV, 'bo', label=r'\small{RPTV tree}')
ax11.plot(dayAxis, tree_mvgavg_RPTV, 'b')
#ax11.plot(dayAxis, tree_RPTV_avg_curve, 'b--')
ax11.set_ylabel(r'\small{RPTV}', color='b')
for tl in ax11.get_yticklabels():
    tl.set_color('b')


# turn on grid
ax1.grid(True)
ax11.grid(True)
plt.xlim([1,365])



#ax2.grid(True)
plt.subplots_adjust(hspace=0.5, left=0.1, right=0.9, bottom=0.12, top=0.95)
plt.text(100, 1850, 'average number of messages: {0:.0f}'.format(tree_msg_avg, fontsize=10))
fig.set_size_inches(6.2, 3.5)
#plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
#           ncol=4, mode='expand',borderaxespad=0.)
#plt.legend(loc='lower right', ncol=1)

if slides:
    plt.savefig("fig_tree_msg_RPTV_year_slides", dpi=300)
else:
    plt.savefig("fig_tree_msg_RPTV_year", dpi=300)
#plt.show()