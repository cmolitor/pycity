__author__ = 'cmo'

import numpy as np

import toolbox.chngResE as hp


# Read thermal demand profiles
data = np.genfromtxt("Aggregated_profiles_sum.csv", delimiter=';')

data1BES = np.array([data[1:,0], data[1:,1]])
data1BES_new = hp.changeResolutionEnergy(hp, data1BES, 3600).T

# print(data1BES_new.shape[1])
dataAllBES = np.zeros((data1BES_new.shape[0], data.shape[1]))
dataAllBES[:,0] = data1BES_new[:,0]

for i in range(1, data.shape[1]):
    # times 60 to calculate energy (here: power times 60s)
    data1BES = np.array([data[1:,0], np.multiply(data[1:,i],60)])
    dataAllBES[:,i] = hp.changeResolutionEnergy(hp, data1BES, 3600).T[:,1]

np.savetxt('Aggregated_profiles_sum_newREs.csv', dataAllBES, fmt='%f', delimiter=';')


# SLP_thermal_org = np.array([[x.value for x in worksheet.col(1, 1)], [x.value for x in worksheet.col(3, 1)]])
# Apartment.SLP_thermal_SFH = hp.changeTimescale(self, SLP_thermal_SFH_org, stepSize)
