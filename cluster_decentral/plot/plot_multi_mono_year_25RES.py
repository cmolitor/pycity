__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt
import numpy as np


interval = 86400
stepsize = 900

slides = 1 # set to 0 if figures are for thesis, set to 1 if figures are for slides (changes font type and file name)

resultfile = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'
extractor = ResultExtractor(resultfile, interval, stepsize, 1, 365)
extractor.extractResults()

RPTV = extractor.getRPTV()
avg_RPTV = extractor.getAvgRelPTV()
mvgavg_RPTV = extractor.getRPTV_MovingAvg(21)
stddev = np.std(RPTV)

stddev_upper = [avg_RPTV+stddev for i in range(0,365)]
stddev_lower = [avg_RPTV-stddev for i in range(0,365)]

avg_PRTV_curve = [avg_RPTV for i in range(0, 365)]

#plot
#latex settings for plot
plt.rc('text', usetex=True)
if slides:
    plt.rc('font', family='sans-serif')
else:
    plt.rc('font', family='serif')

dayAxis = [x for x in range(1,366)]

fig = plt.figure()

plt.plot(dayAxis, avg_PRTV_curve, 'k--')
plt.plot(dayAxis, stddev_upper, 'r--')
plt.plot(dayAxis, stddev_lower, 'r--')
plt.plot(dayAxis, RPTV, 'b.')
plt.plot(dayAxis, mvgavg_RPTV, 'b')
plt.xlabel(r'\small{days}')
plt.ylabel(r'\small{RPTV}')
plt.xlim([1,365])

plt.grid(True)
plt.subplots_adjust(hspace=0.5, wspace=0.5, left=0.1, right=0.99, bottom=0.15, top=0.99)
plt.text(90, 0.25, 'average RPTV: {0:.4f}'.format(avg_RPTV), fontsize=10)
plt.text(240, 0.25, 'standard deviation: {0:.4f}'.format(stddev), fontsize=10, color='r')
fig.set_size_inches(6.2, 3.0)

if slides:
    plt.savefig("fig_multi_mono_year_25RES_slides", dpi=300)
else:
    plt.savefig("fig_multi_mono_year_25RES", dpi=300)