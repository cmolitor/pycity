__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
from mpl_toolkits.axes_grid1 import host_subplot


interval = 86400
stepsize = 900

slides = 1

resultfile_multicast = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'
#resultfile_multicast = '../results/RMOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_20-05-49/results_log.txt'

multicast_extractor = ResultExtractor(resultfile_multicast, interval, stepsize, 1, 365)
multicast_extractor.extractResults()
multicast_msg_avg = multicast_extractor.getAvgMessages()
multicast_RPTV_avg = multicast_extractor.getAvgRelPTV()
multicast_mvgavg_msg = multicast_extractor.getMessage_MovingAvg(21)
multicast_mvgavg_RPTV = multicast_extractor.getRPTV_MovingAvg(21)


dayAxis = [x for x in range(1,366)]
multicast_msg_avg_curve = [multicast_msg_avg for i in range(0,365)]
multicast_RPTV_avg_curve = [multicast_RPTV_avg for i in range(0,365)]


#latex settings for plot
plt.rc('text', usetex=True)

if slides:
    plt.rc('font', family='sans-serif')
else:
    plt.rc('font', family='serif')


fig = plt.figure()
ax1 = host_subplot(111, axes_class=AA.Axes)

#ax1.plot(dayAxis, multicast_mvgavg_msg, 'ro', label=r'\small{number of messages}')
ax1.plot(dayAxis, multicast_mvgavg_msg, 'r')
ax1.plot(dayAxis, multicast_msg_avg_curve, 'r--')
ax1.set_xlabel(r'\small{days}')
ax1.set_ylabel(r'\small{number of messages}', color='r')
for tl in ax1.get_yticklabels():
     tl.set_color('r')

ax11 = ax1.twinx()
#ax11.plot(dayAxis, multicast_mvgavg_RPTV, 'bo', label=r'\small{RPTV tree}')
ax11.plot(dayAxis, multicast_mvgavg_RPTV, 'b')
#ax11.plot(dayAxis, multicast_RPTV_avg_curve, 'b--')
ax11.set_ylabel(r'\small{RPTV}', color='b')
for tl in ax11.get_yticklabels():
    tl.set_color('b')

# turn on grid
ax1.grid(True)
ax11.grid(True)
plt.text(5, 19000, 'average number of messages: {0:.0f}'.format(multicast_msg_avg, fontsize=10))
plt.xlim([1,365])

#ax2.grid(True)
plt.subplots_adjust(hspace=0.5, left=0.11, right=0.91, bottom=0.12, top=0.95)

fig.set_size_inches(6.2, 3.5)

#plt.legend(loc='lower right', ncol=1)
if slides:
    plt.savefig("fig_multicast_msg_RPTV_year_slides", dpi=300)
else:
    plt.savefig("fig_multicast_msg_RPTV_year", dpi=300)
#plt.show()