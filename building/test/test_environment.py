__author__ = 'Christoph Molitor'

from building.environment import Environment
import xlwt
import numpy as np

stepSize = 900
bWriteToExcel = 0

wb = xlwt.Workbook()
ws = wb.add_sheet("test", cell_overwrite_ok=True)

testEnvironment = Environment(50, stepSize)

print("Wind: ", testEnvironment.WindEnergy_Annual)
print("PV: ", testEnvironment.PVEnergy_Annual)
print("Res: ", testEnvironment.RESEnergy_Annual)
#_test = testEnvironment.getLclPVEnergyCurve(0, 86400, 900)
#print (_test)
#print (np.sum(_test[1, :]))

#print("Renewable generation curve: {} Ws".format(testEnvironment.getRenewableGenerationCurve(0, 365*24*3600, 1000)))
print("Wind generation curve: {} Ws".format(testEnvironment.getWindEnergyCurve(0, 365*24*3600, 1000)))
print("Solar generation curve: {} Ws".format(testEnvironment.getPVEnergyCurve(0, 365*24*3600, 1000)))

print(sum(testEnvironment.getPVEnergyCurve(0, 365*24*3600, 1000)[1,:])/3600000)
testEnvironment.addDomesticPVSystem(100*3600000)
print(sum(testEnvironment.getPVEnergyCurve(0, 365*24*3600, 1000)[1,:])/3600000)
testEnvironment.addDomesticPVSystem(100*3600000)
print(sum(testEnvironment.getPVEnergyCurve(0, 365*24*3600, 1000)[1,:])/3600000)
testEnvironment.addDomesticPVSystem(100*3600000)
print(sum(testEnvironment.getPVEnergyCurve(0, 365*24*3600, 1000)[1,:])/3600000)

if bWriteToExcel > 0:
    _res = testEnvironment.getRenewableGenerationCurve(0, 365*24*3600, 1000)
    _res = np.transpose(_res)

    nrows = _res.shape[0]
    ncols = _res.shape[1]

    for iR in range(0, nrows):
        for iC in range(0, ncols):
            ws.write(iR, iC, _res[iR, iC])

    # Different stepsize
    stepSize = 900
    testEnvironment = Environment(50, stepSize)
    _res = testEnvironment.getRenewableGenerationCurve(0, 365*24*3600, 1000)

    # print("Renewable generation curve: {} Wh".format(testEnvironment.getRenewableGeneration(0, 365*24*3600, 1000)))

    _res = np.transpose(_res)

    nrows = _res.shape[0]
    ncols = _res.shape[1]

    for iR in range(0, nrows):
        for iC in range(0, ncols):
            ws.write(iR, iC + 3, _res[iR, iC])

    # Different stepsize
    stepSize = 1000
    testEnvironment = Environment(50, stepSize)
    _res = testEnvironment.getRenewableGenerationCurve(0, 365*24*3600, 1000)

    # print("Renewable generation curve: {} Wh".format(testEnvironment.getRenewableGeneration(0, 365*24*3600, 1000)))

    _res = np.transpose(_res)

    nrows = _res.shape[0]
    ncols = _res.shape[1]

    for iR in range(0, nrows):
        for iC in range(0, ncols):
            ws.write(iR, iC + 6, _res[iR, iC])

    wb.save('test_environment.xls')