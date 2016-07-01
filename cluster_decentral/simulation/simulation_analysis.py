__author__ = 'Sonja Kolen'

from resultextractor import ResultExtractor

#Simulation results with stepsize 3600 sec = 1 hour

#result_file_path = '../results/LPOPT_SD365_RES0_mono_step3600_T2015-01-22_10-16-40/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES0_bivalent_step3600_T2015-01-22_10-59-06/results_log.txt'

#result_file_path = '../results/LPOPT_SD365_RES50_mono_step3600_T2015-01-21_15-45-09/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES50_bivalent_step3600_T2015-01-21_16-28-50/results_log.txt'

#result_file_path = '../results/LPOPT_SD365_RES100_mono_step3600_T2015-01-21_17-16-52/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES100_bivalent_step3600_T2015-01-21_17-59-23/results_log.txt'

#result_file_path = '../results/RMOPT_SD365_RES0_mono_step3600_T2015-01-21_18-44-29/results_log.txt'
#result_file_path = '../results/RMOPT_SD365_RES0_bivalent_step3600_T2015-01-21_20-15-56/results_log.txt'

#result_file_path = '../results/RMOPT_SD365_RES50_mono_step3600_T2015-01-21_21-50-41/results_log.txt'
#result_file_path = '../results/RMOPT_SD365_RES50_bivalent_step3600_T2015-01-21_23-22-21/results_log.txt'

#result_file_path = '../results/RMOPT_SD365_RES50_bivalent_step3600_T2015-01-21_23-22-21/results_log.txt'
#result_file_path = '../results/RMOPT_SD365_RES100_bivalent_step3600_T2015-01-22_02-27-08/results_log.txt'

#result_file_path = '../results/LocalBest_SD365_RES0_mono_step3600_T2015-01-22_03-59-02/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES0_bivalent_step3600_T2015-01-22_04-15-18/results_log.txt'

#result_file_path = '../results/LocalBest_SD365_RES50_mono_step3600_T2015-01-22_04-33-03/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES50_bivalent_step3600_T2015-01-22_04-49-19/results_log.txt'

#result_file_path = '../results/LocalBest_SD365_RES100_mono_step3600_T2015-01-22_05-07-02/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES100_bivalent_step3600_T2015-01-22_05-23-20/results_log.txt'


##################################################################################################################

# simulation results with stepsize = 900 sec = 15 min

#result_file_path = '../results/LPOPT_SD365_RES0_mono_step900_T2015-01-19_12-07-30/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES0_bivalent_step900_T2015-01-19_14-54-08/results_log.txt'

#result_file_path = '../results/LPOPT_SD365_RES50_mono_step900_T2015-01-19_16-23-45/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES50_bivalent_step900_T2015-01-19_19-14-18/results_log.txt'

#result_file_path = '../results/LPOPT_SD365_RES100_mono_step900_T2015-01-19_21-51-28/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES100_bivalent_step900_T2015-01-20_00-18-10/results_log.txt'

#result_file_path = '../results/RMOPT_SD365_RES0_mono_step900_T2015-01-20_02-48-57/results_log.txt'         # old
#result_file_path = '../results/RMOPT_SD365_RES0_mono_step900_T2015-03-01_15-14-44/results_log.txt'         # 1st bugfix (index)
result_file_path = '../results/RMOPT_SD365_RES0_mono_step900_T2015-03-02_14-19-44/results_log.txt'         # 2nd bugfix (if-statement)

#result_file_path = '../results/RMOPT_SD365_RES0_bivalent_step900_T2015-01-20_07-21-58/results_log.txt'      # old
#result_file_path = '../results/RMOPT_SD365_RES0_bivalent_step900_T2015-01-20_07-21-58/results_log.txt'     # 2nd bugfix (if-statement)

#result_file_path = '../results/RMOPT_SD365_RES50_mono_step900_T2015-01-20_12-15-37/results_log.txt'        # old
#result_file_path = '../results/RMOPT_SD365_RES50_mono_step900_T2015-03-01_22-44-02/results_log.txt'        # 1st bugfix (index)
#result_file_path = '../results/RMOPT_SD365_RES50_mono_step900_T2015-03-03_11-00-32/results_log.txt'        # 12nd bugfix (if-statement)

#result_file_path = '../results/RMOPT_SD365_RES50_bivalent_step900_T2015-01-20_17-06-42/results_log.txt'    # old

#result_file_path = '../results/RMOPT_SD365_RES100_mono_step900_T2015-01-20_22-14-44/results_log.txt'       # old
#result_file_path = '../results/RMOPT_SD365_RES100_mono_step900_T2015-03-02_05-53-13/results_log.txt'       #1st bugfix (index)

#result_file_path = '../results/RMOPT_SD365_RES100_bivalent_step900_T2015-01-21_02-56-34/results_log.txt'   # old

#result_file_path = '../results/LocalBest_SD365_RES0_mono_step900_T2015-01-21_07-53-29/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES0_bivalent_step900_T2015-01-21_09-25-57/results_log.txt'

#result_file_path = '../results/LocalBest_SD365_RES50_mono_step900_T2015-01-21_10-56-10/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES50_bivalent_step900_T2015-01-21_12-03-59/results_log.txt'

#result_file_path = '../results/LocalBest_SD365_RES100_mono_step900_T2015-01-21_13-18-42/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES100_bivalent_step900_T2015-01-21_14-25-39/results_log.txt'


#################### Dynamic COP for HPs ++++++++++++++++++++++++++++
# tree-based coordination, monovalent
#result_file_path = '../results/LPOPT_SD365_RES0_mono_step900_dynCOP_T2015-03-07_22-07-21/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-10_10-36-33/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_02-54-05/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES75_mono_step900_dynCOP_T2015-03-10_15-24-32/results_log.txt'
#result_file_path = '../results/LPOPT_SD365_RES100_mono_step900_dynCOP_T2015-03-08_07-37-20/results_log.txt'

# tree-based coordination, bivalent
result_file_path = '../results/LPOPT_SD365_RES25_bivalent_step900_dynCOP_T2015-03-10_20-05-37/results_log.txt'

# multicast-based coordination, monovalent
#result_file_path = '../results/RMOPT_SD365_RES0_mono_step900_dynCOP_T2015-03-08_12-20-19/results_log.txt'
#result_file_path = '../results/RMOPT_SD365_RES25_mono_step900_dynCOP_T2015-03-11_00-53-46/results_log.txt'
#result_file_path = '../results/RMOPT_SD365_RES50_mono_step900_dynCOP_T2015-03-08_20-05-49/results_log.txt'
#result_file_path = '../results/RMOPT_SD365_RES75_mono_step900_dynCOP_T2015-03-11_08-36-33/results_log.txt'
#result_file_path = '../results/RMOPT_SD365_RES100_mono_step900_dynCOP_T2015-03-09_03-31-42/results_log.txt'

# multicast-based coordination, bivalent
#result_file_path = '../results/RMOPT_SD365_RES100_bivalent_step900_T2015-01-21_02-56-34/results_log.txt' # not yet run


#result_file_path = '../results/LocalBest_SD365_RES0_mono_step900_dynCOP_T2015-03-09_10-49-12/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES0_bivalent_step900_T2015-01-21_09-25-57/results_log.txt' # not yet run

#result_file_path = '../results/LocalBest_SD365_RES50_mono_step900_dynCOP_T2015-03-09_15-17-55/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES50_bivalent_step900_T2015-01-21_12-03-59/results_log.txt' # not yet run

#result_file_path = '../results/LocalBest_SD365_RES100_mono_step900_dynCOP_T2015-03-09_19-40-34/results_log.txt'
#result_file_path = '../results/LocalBest_SD365_RES100_bivalent_step900_T2015-01-21_14-25-39/results_log.txt' # not yet run

#########################################################################

#result_file_path = '../results/RMOPT_SD14_RES25_mono_step900_16Starters_T2015-03-13_13-17-36/results_log.txt'

# solution pool intensity 2:

#result_file_path = '../results/LPOPT_SD365_RES100_mono_SPI2_T2014-11-25_10-46-59/results_log.txt' # solution pool intensity 2 (instead of 3)
#result_file_path = '../results/LPOPT_SD365_RES100_bivalent_SPI2_T2014-11-25_10-34-51/results_log.txt' # solution pool intensity 2 (instead of 3)


#result_file_path = '../results/RMOPT_SD5_RES0_mono_step900_T2015-03-07_20-05-47/results_log.txt'

interval = 86400
stepsize = 900

startMonths = [1, 32, 61, 92, 122, 153, 183, 214, 245, 275, 306, 336]       # start days of all months
endMonths = [31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 365]       # end days of all months
middleMonths = [14, 44, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]    # 14th of each month (first 14 days of a month)

#myExtractor = ResultExtractor(result_file_path, interval, stepsize, 61, 74)
myExtractor = ResultExtractor(result_file_path, interval,stepsize, 326, 365)
myExtractor.extractResults()


#myExtractor.plot_all_results()

#myExtractor.plot_criteria()
#myExtractor.plot_relativePowerAverage()
#myExtractor.plot_relativePeakToAveragePower()
myExtractor.plot_PTVimprovement()
#myExtractor.plot_relativePowerToAverage()

#myExtractor.plot_min_maxmindiff()
#myExtractor.plot_max_maxmindiff()

#myExtractor.plot_max_maxmindiff_new()

#myExtractor.plot_min_absremainder()
#myExtractor.plot_max_absremainder()

#myExtractor.plot_max_remainderfluct()
#myExtractor.plot_min_remainderfluct()

#myExtractor.plot_scheduledata()

#myExtractor.plot_messages_sent_runtime()
#myExtractor.plot_messages()

