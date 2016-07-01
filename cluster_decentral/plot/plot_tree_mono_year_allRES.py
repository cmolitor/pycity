__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt


interval = 86400
stepsize = 900

resultfile_0 = '../results/LPOPT_SD365_RES0_mono_step900_dynCOP_T2015-03-07_22-07-21/results_log.txt'
resultfile_25 = '../results/LPOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-10_10-36-33/results_log.txt'
resultfile_50 = '../results/LPOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_02-54-05/results_log.txt'
resultfile_75 = '../results/LPOPT_SD365_RES75_mono_step900_dynCOP_T2015-03-10_15-24-32/results_log.txt'
resultfile_100 = '../results/LPOPT_SD365_RES100_mono_step900_dynCOP_T2015-03-08_07-37-20/results_log.txt'
extractor_0 = ResultExtractor(resultfile_0, interval, stepsize, 1, 365)
extractor_25 = ResultExtractor(resultfile_25, interval, stepsize, 1, 365)
extractor_50 = ResultExtractor(resultfile_50, interval, stepsize, 1, 365)
extractor_75 = ResultExtractor(resultfile_75, interval, stepsize, 1, 365)
extractor_100 = ResultExtractor(resultfile_100, interval, stepsize, 1, 365)
extractor_0.extractResults()
extractor_25.extractResults()
extractor_50.extractResults()
extractor_75.extractResults()
extractor_100.extractResults()

RPTV_0 = extractor_0.getRPTV()
RPTV_25 = extractor_25.getRPTV()
RPTV_50 = extractor_50.getRPTV()
RPTV_75 = extractor_75.getRPTV()
RPTV_100 = extractor_100.getRPTV()
avg_RPTV_0 = extractor_0.getAvgRelPTV()
avg_RPTV_25 = extractor_25.getAvgRelPTV()
avg_RPTV_50 = extractor_50.getAvgRelPTV()
avg_RPTV_75 = extractor_75.getAvgRelPTV()
avg_RPTV_100 = extractor_100.getAvgRelPTV()

avg_RPTV_curve_0 = [avg_RPTV_0 for i in range(0, 365)]
avg_RPTV_curve_25 = [avg_RPTV_25 for i in range(0, 365)]
avg_RPTV_curve_50 = [avg_RPTV_50 for i in range(0, 365)]
avg_RPTV_curve_75 = [avg_RPTV_75 for i in range(0, 365)]
avg_RPTV_curve_100 = [avg_RPTV_100 for i in range(0, 365)]

#plot
#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

dayAxis = [x for x in range(1,366)]

fig = plt.figure()
plt.plot(dayAxis, RPTV_0, 'y.', alpha=0.7, label=r'\tiny{0 \% RES}')
#plt.plot(dayAxis, avg_RPTV_curve_0, 'y')
plt.plot(dayAxis, RPTV_25, 'r.', alpha=0.7, label=r'\tiny{25 \% RES}')
#plt.plot(dayAxis, avg_RPTV_curve_25, 'r')
plt.plot(dayAxis, RPTV_50, 'b.', alpha=0.7, label=r'\tiny{50 \% RES}')
#plt.plot(dayAxis, avg_RPTV_curve_50, 'b')
plt.plot(dayAxis, RPTV_75, 'c.', alpha=0.7, label=r'\tiny{75 \% RES}')
#plt.plot(dayAxis, avg_RPTV_curve_75, 'c')
plt.plot(dayAxis, RPTV_100, 'g.', alpha=0.7, label=r'\tiny{100 \% RES}')
#plt.plot(dayAxis, avg_RPTV_curve_100, 'g')
plt.xlabel(r'\small{days}')
plt.ylabel(r'\small{RPTV}')
plt.xlim([1,365])

plt.grid(True)
plt.subplots_adjust(hspace=0.5, wspace=0.5, left=0.1, right=0.95, bottom=0.15, top=0.9)
plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=5, mode='expand',borderaxespad=0.)

fig.set_size_inches(6.2, 3.5)
plt.savefig("fig_tree_mono_year_allRES", dpi=300)