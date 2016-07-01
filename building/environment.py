__author__ = 'Christoph Molitor'

import xlrd
import numpy as np
import os
import copy as cp
from toolbox import chngResE as hp


class Environment(object):
    def __init__(self, shareRES, stepSize):
        """
        Constructor of Environment
        :param shareRES: share of electrical load (in percent) which is covered by Renewable Energy Sources
        :param stepSize: duration of time slots in seconds
        """
        # self.RGP_electrical = 0  # Renewable Generation Profile (RGP) standardized to 1000kWh/a
        self.shareRES = float(shareRES)/100  # share of annual energy covered by renewable energy
        self.WindEnergy_TimeSeries = 0.0
        self.WindEnergy_Annual = 0.0
        self.PVEnergy_TimeSeries = 0.0
        self.LclPVEnergy_TimeSeries = 0.0
        self.PVEnergy_Annual = 0.0
        self.RESEnergy_TimeSeries = 0.0
        self.RESEnergy_Annual = 0.0
        self.ratioWindPV = 0.0
        self.ScalingFactorRES = 0.0
        self.ScalingFactorLclPV = 0.0
        self.stepSize = stepSize
        self.internalPVEnergy_Annual = 0

        # Read electrical standard load profiles
        script_dir = os.path.dirname(__file__)
        # Renewable generation curve normed to 1000kWh/a
        # workbook = xlrd.open_workbook(script_dir + '/../data/RES_SLP_2012.xlsx')
        # worksheet = workbook.sheet_by_name('RES_15min')
        # _RGP_electrical = np.array([[x.value for x in worksheet.col(0, 1)], [-x.value for x in worksheet.col(2, 1)]])
        # self.RGP_electrical = hp.changeResolutionEnergy(self, _RGP_electrical, stepSize)
        # =========================================================
        # Reading data of test reference year (TRY)
        # TRY05   Niederrheinisch-westfaelische Bucht und Emsland (Klimaregion  5)
        # Station: Essen                           WMO-Nummer: 10410
        # Lage: 51 Grad 24'N <- B.   6 Grad 58'O <- L.   152 Meter ueber NN
        # Zeitpunkt der Erstellung: November 2010
        #
        # Art des TRY    : mittleres Jahr
        # Bezugszeitraum : 1988-2007
        # Stadteffekt    : gewaehlte Bevoelkerungsanzahl:   116000 Einwohner; Stadttyp: Mittleres Stadtgebiet
        # Hoehenkorrektur : aktuelle Hoehenlage: 55 Meter ueber NN
        #
        # Datenbasis : Beobachtungsdaten Zeitraum 1988-2007
        #
        # Format: (i2,2x,i4,2x,i2,2x,i2,2x,i2,2x,i1,2x,i3,2x,f6.1,2x,f6.1,2x,f7.1,2x,f6.1,2x,i3,2x,i2,2x,i4,2x,i4,1x,i1,2x,i4,2x,i5,2x,i1)
        # Reihenfolge der Parameter:
            # RG TRY-Region                                                           {1..15}
            # IS Standortinformation                                                  {1,2}
            # MM Monat                                                                {1..12}
            # DD Tag                                                                  {1..28,30,31}
            # HH Stunde (MEZ)                                                         {1..24}
            # N  Bedeckungsgrad                                              [Achtel] {0..8;9}
            # WR Windrichtung in 10 m Hoehe ueber Grund                        [Grad]      {0;10..360;999}
            # WG Windgeschwindigkeit in 10 m Hoehe ueber Grund                 [m/s]
            # t  Lufttemperatur in 2m Hoehe ueber Grund                        [Grad C]
            # p  Luftdruck in Stationshoehe                                   [hPa]
            # x  Wasserdampfgehalt, Mischungsverhaeltnis                      [g/kg]
            # RF Relative Feuchte in 2 m Hoehe ueber Grund                     [%]      {1..100}
            # W  Wetterereignis der aktuellen Stunde                                  {0..99}
            # B  Direkte Sonnenbestrahlungsstaerke (horiz. Ebene)             [W/m^2]   abwaerts gerichtet: positiv
            # D  Difuse Sonnenbetrahlungsstaerke (horiz. Ebene)               [W/m^2]   abwaerts gerichtet: positiv
            # IK Information, ob B und oder D Messwert/Rechenwert                     {1;2;3;4;9}
            # A  Bestrahlungsstaerke d. atm. Waermestrahlung (horiz. Ebene)    [W/m^2]   abwaerts gerichtet: positiv
            # E  Bestrahlungsstaerke d. terr. Waermestrahlung                  [W/m^2]   aufwaerts gerichtet: negativ
            # IL Qualitaetsbit fuer die langwelligen Strahlungsgroessen                  (1;2;3;4;5;6;7;8;9)

        _data_TRY = np.loadtxt(script_dir + '/../data/TRY2010_05_Jahr_00116K2_00055m.dat', skiprows=38)
        self.data_TRY = np.zeros((_data_TRY.shape[0], _data_TRY.shape[1]+1))
        self.data_TRY[:, 1:] = _data_TRY
        time = np.array([3600 * i for i in range(0, self.data_TRY.shape[0])])
        self.data_TRY[:, 0] = time.T

        # =========================================================
        # Solar radiation
        self.irradiation_annual = np.ndarray((self.data_TRY[:, 0].shape[0], 2))
        self.irradiation_annual[:, 0] = self.data_TRY[:, 0]
        self.irradiation_annual[:, 1] = self.data_TRY[:, 14] + self.data_TRY[:, 15]

        # =========================================================
        # Ambient temperature
        self.ambientTemperature = np.ndarray((self.data_TRY[:, 0].shape[0], 2))
        self.ambientTemperature[:, 0] = self.data_TRY[:, 0]
        self.ambientTemperature[:, 1] = self.data_TRY[:, 9] + 273.15  # from C to K

        # print("Irradiation: {} kWh/m2".format(self.irradiation_annual/3600000))

        # =========================================================
        # Reading data of wind energy production
        _resolution = 900.0
        _data_WindEnergy = np.genfromtxt(script_dir + '/../data/Amprion_winddaten2_01.01.2012_31.01.2013.csv', skip_header=2, delimiter=";")[:, 1:4]
        time = np.array([_resolution * i for i in range(0, _data_WindEnergy.shape[0])])
        _data_WindEnergy[:, 0] = time.T
        _data_WindEnergy[:, 1:] = _data_WindEnergy[:, 1:] * 1000000 * -900  # conversion to Ws
        self.WindEnergy_TimeSeries = hp.changeResolutionEnergy(self, _data_WindEnergy[:, [0, 2]].T, stepSize).T
        # print(self.WindEnergy_TimeSeries/360000000*4)
        # print(self.WindEnergy_TimeSeries)
        self.WindEnergy_Annual = sum(self.WindEnergy_TimeSeries[:, 1])  # in Ws

        # =========================================================
        # Reading data of interregional PV energy production
        _resolution = 900.0
        # Original data contains prognosis data and real data;
        # thus we select here (_data_PVEnergy[:, [0, 2]]) only the real data
        _data_PVEnergy = np.genfromtxt(script_dir + '/../data/Amprion_Photovoltaik_01.01.2012_31.01.2013.csv', skip_header=2, delimiter=";")[:, 1:4]
        time = np.array([_resolution * i for i in range(0, _data_PVEnergy.shape[0])])
        _data_PVEnergy[:, 0] = time.T
        _data_PVEnergy[:, 1:] = _data_PVEnergy[:, 1:] * 1000000 * -900  # conversion to Ws
        self.PVEnergy_TimeSeries = hp.changeResolutionEnergy(self, _data_PVEnergy[:, [0, 2]].T, stepSize).T

        self.PVEnergy_Annual = sum(self.PVEnergy_TimeSeries[:, 1])  # in Ws

        # =========================================================
        # Reading data of local PV energy production
        _resolution = 900
        workbook = xlrd.open_workbook(script_dir + '/../data/PV_local_TRY.xlsx')
        worksheet = workbook.sheet_by_name('Data')
        _data_lclPVEnergy = np.array([[x.value for x in worksheet.col(0, 1)], [x.value for x in worksheet.col(2, 1)]])
        self.ScalingFactorLclPV = abs(np.sum(_data_lclPVEnergy[1, :])/3600000)
        # print _data_lclPVEnergy.shape
        # print hp.changeResolutionEnergy(self, _data_lclPVEnergy, self.stepSize).shape
        self.LclPVEnergy_TimeSeries = hp.changeResolutionEnergy(self, _data_lclPVEnergy, self.stepSize).T
        # print("self.ScalingFactorLclPV",self.ScalingFactorLclPV)

        # =========================================================
        # Adding up PV and wind energy to determine interregional renewable energy
        self.RESEnergy_TimeSeries = cp.deepcopy(self.WindEnergy_TimeSeries)
        self.RESEnergy_TimeSeries[:, 1:] = self.WindEnergy_TimeSeries[:, 1:] + self.PVEnergy_TimeSeries[:, 1:]

        #  Annual Energy Generation of RES according to input data
        self.RESEnergy_Annual = sum(self.RESEnergy_TimeSeries[:, 1])

        self.sharePV = self.shareRES * self.PVEnergy_Annual/self.RESEnergy_Annual
        self.shareWind = self.shareRES * self.WindEnergy_Annual/self.RESEnergy_Annual
        # print("share PV: ", self.sharePV)
        # print("share wind: ", self.shareWind)

        # normalize RES generation curve to 1 kWh/a = 3600000Ws/a
        self.ScalingFactorRES = abs(self.RESEnergy_Annual/3600000)

    def getRenewableGenerationCurve(self, fromTime, toTime, AnnualEnergyDemand):
        # """
        # :param fromTime: start time in seconds from beginning of year
        # :param toTime: end time in seconds from beginning of year
        # :param AnnualEnergyDemand: annual energy demand in kWh
        # :return: curve of renewable generation for defined time period in Ws
        # """

        # indFrom = min((np.asarray(np.where(self.RESEnergy_TimeSeries[:, 0] >= fromTime)))[0, :])
        # indTo = max((np.asarray(np.where(self.RESEnergy_TimeSeries[:, 0] <= toTime)))[0, :]) + 1
        # RES = np.zeros((indTo-indFrom, 2))
        # RES[:, 0] = self.RESEnergy_TimeSeries[indFrom:indTo, 0]
        # RES[:, 1] = self.RESEnergy_TimeSeries[indFrom:indTo, 1] * self.shareRES * AnnualEnergyDemand / self.ScalingFactor
        # return RES.T

        """
        :param fromTime: start time in seconds from beginning of year
        :param toTime: end time in seconds from beginning of year
        :param AnnualEnergyDemand: annual energy demand in kWh
        :return: curve of renewable generation for defined time period in Ws
        """
        RES = self.getWindEnergyCurve(fromTime, toTime, AnnualEnergyDemand)
        RES[1, :] += self.getPVEnergyCurve(fromTime, toTime, AnnualEnergyDemand)[1, :]

        return RES


    def getWindEnergyCurve(self, fromTime, toTime, AnnualEnergyDemand):
        """
        :param fromTime: start time in seconds from beginning of year
        :param toTime: end time in seconds from beginning of year
        :param AnnualEnergyDemand: annual energy demand in kWh
        :return: curve of wind energy generation for defined time period in Ws
        """
        # The wind energy curve is scaled with the same scaling factor like the overall RES,
        # thus the ratio between PV and wind is kept as it was in the original data

        indFrom = min((np.asarray(np.where(self.WindEnergy_TimeSeries[:, 0] >= fromTime)))[0, :])
        indTo = max((np.asarray(np.where(self.WindEnergy_TimeSeries[:, 0] <= toTime)))[0, :]) + 1
        Wind = np.zeros((indTo-indFrom, 2))
        Wind[:, 0] = self.WindEnergy_TimeSeries[indFrom:indTo, 0]
        Wind[:, 1] = self.WindEnergy_TimeSeries[indFrom:indTo, 1] * self.shareRES * AnnualEnergyDemand / self.ScalingFactorRES
        return Wind.T

    def getPVEnergyCurve(self, fromTime, toTime, AnnualEnergyDemand):
        """
        :param fromTime: start time in seconds from beginning of year
        :param toTime: end time in seconds from beginning of year
        :param AnnualEnergyDemand: annual energy demand in kWh
        :return: curve of PV energy generation for defined time period in Ws
        """
        # The PV energy curve is scaled with the same scaling factor like the overall RES,
        # thus the ratio between PV and wind is kept as it was in the original data

        indFrom = min((np.asarray(np.where(self.PVEnergy_TimeSeries[:, 0] >= fromTime)))[0, :])
        indTo = max((np.asarray(np.where(self.PVEnergy_TimeSeries[:, 0] <= toTime)))[0, :]) + 1
        PV = np.zeros((indTo-indFrom, 2))
        PV[:, 0] = self.PVEnergy_TimeSeries[indFrom:indTo, 0]
        # PV[:, 1] = self.PVEnergy_TimeSeries[indFrom:indTo, 1] * self.shareRES * AnnualEnergyDemand / self.ScalingFactor


        if (AnnualEnergyDemand * self.sharePV) - self.internalPVEnergy_Annual > 0:
            PV[:, 1] = self.PVEnergy_TimeSeries[indFrom:indTo, 1] / self.ScalingFactorRES \
                       * self.shareRES/self.sharePV * (AnnualEnergyDemand * self.sharePV - self.internalPVEnergy_Annual)
        #print("PV: ", np.sum(PV[:,1])/3600000)
        return PV.T

    def getLclPVEnergyCurve(self, fromTime, toTime, AnnualLclPVGeneration):
        """
        method returns a PV generation curve of the local PV system
        :param fromTime: start time in seconds from beginning of year
        :param toTime: end time in seconds from beginning of year
        :param AnnualLclPVGeneration: annual PV energy output in kWh
        :return: curve of PV energy generation for defined time period in Ws (negative values, 2 x timesteps array)
        """
        indFrom = min((np.asarray(np.where(self.LclPVEnergy_TimeSeries[:, 0] >= fromTime)))[0, :])
        indTo = max((np.asarray(np.where(self.LclPVEnergy_TimeSeries[:, 0] <= toTime)))[0, :]) + 1
        LclPV = np.zeros((indTo-indFrom, 2))
        LclPV[:, 0] = self.LclPVEnergy_TimeSeries[indFrom:indTo, 0]
        LclPV[:, 1] = self.LclPVEnergy_TimeSeries[indFrom:indTo, 1] / self.ScalingFactorLclPV * AnnualLclPVGeneration

        return LclPV.T

    def getShareRES(self):
        return self.shareRES * 100  # times 100 to return value in %

    def getTemperatureCurve(self, fromTime, toTime, newStepSize=0):
        """
        :param fromTime: start time of time period
        :param toTime: end time of time period
        :param newStepSize: new step size of the return vector
        :return: returns vector of temperature in desired range and with desired resolution (stepsize)
        """
        if newStepSize == 0:
            newStepSize = self.stepSize

        newTime = np.arange(fromTime, toTime+newStepSize, newStepSize)
        _temp = np.interp(newTime, self.ambientTemperature[:, 0], self.ambientTemperature[:, 1])

        _temp_time = np.vstack((newTime, _temp))
        return _temp_time

    def getSolarRadiationCurve(self, fromTime, toTime, newStepSize=0):
        """
        :param fromTime: start time of time period
        :param toTime: end time of time period
        :param newStepSize: new step size of the return vector
        :return: returns vector of solar radiation in desired range and with desired resolution (stepsize)
        """
        if newStepSize == 0:
            newStepSize = self.stepSize

        newTime = np.arange(fromTime, toTime+newStepSize, newStepSize)
        _temp = np.interp(newTime, self.irradiation_annual[:, 0], self.irradiation_annual[:, 1])

        _temp_time = np.vstack((newTime, _temp))
        return _temp_time

    def addDomesticPVSystem(self, annualPVEnergy):
        """
        updates the annual energy production from domestic PV systems within the environment (in kWh)
        :param annualPVEnergy: energy produced by the pv system being added (in Ws)
        :return: nothing
        """
        self.internalPVEnergy_Annual += annualPVEnergy / 3600000        # convert from Ws to kWh

    def deleteDomesticPVSystem(self, annualPVEnergy):
        """
        updates the annual energy production from domestic PV systems within the environment (in kWh)
        :param annualPVEnergy: energy produced by the pv system being deleted (in Ws)
        :return: nothing
        """
        self.internalPVEnergy_Annual -= annualPVEnergy / 3600000        # convert from Ws to kWh
        if self.internalPVEnergy_Annual < 0:
            self.internalPVEnergy_Annual = 0

