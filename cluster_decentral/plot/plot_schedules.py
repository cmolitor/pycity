__author__ = 'Sonja Kolen'

from cluster_decentral.simulation.resultextractor import ResultExtractor
import matplotlib.pyplot as plt

interval = 86400
stepsize = 900

#multicast, RSC3, monovalent, 25% RES
result_file_path = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'

extractor = ResultExtractor(result_file_path, interval, stepsize, 1, 365)
extractor.extractResults()

curves = extractor.getSchedules(21)

print max(curves[4])

# plot
dayAxis = [x for x in range(1, 366)]

#latex settings for plot
plt.rc('text', usetex=True)
plt.rc('font', family='serif')

fig = plt.figure()

plt.plot(dayAxis, curves[0], 'b.', label=r'\small{min}')
#plt.plot(dayAxis, curves[1], 'b')

plt.plot(dayAxis, curves[2], 'g.', label=r'\small{average}')
#plt.plot(dayAxis, curves[3], 'g')

plt.plot(dayAxis, curves[4], 'r.', label=r'\small{max}')
#plt.plot(dayAxis, curves[5], 'r')
plt.xlabel(r'\small{days}')
plt.ylabel(r'\small{number of schedules}')
#plt.title('{0}: \n Number of Schedules'.format(self.resultfile_tree))

plt.grid(True)
plt.subplots_adjust(left=0.08, right=0.99, bottom=0.15, top=0.85)
plt.xlim([1, 365])
plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=3, mode='expand',borderaxespad=0.)


fig.set_size_inches(6.2, 3.0)
#plt.legend(loc='lower right', ncol=1)
plt.savefig("fig_schedules", dpi=300)
#plt.show()