__author__ = 'Anni'

import random

from buildingControl.smartbes import SmartBes
from building.pvsystem import PVSystem
import numpy as np



class DataBase(object):
    """
    holds information and methods for creating random BES's
    """

    @staticmethod
    def createRandomBESs(number, sharesOfBESTypes, environment, stepSize, RSC, solPoolAbsGap=2, solPoolRelGap=0.2, solPoolIntensity=4, pseudorandom = True, randomSeed = 1, sqm=0, specDemandTh=0, iApartments=0, lclPV=True):
        """
        method adds given number of random members. based on statistics of german households.
        sources:    Number of apartments per building   | Zensus 2011
                    Sqm per apartment                   | Zensus 2011
                    Thermal demand (1 aptm. buildings)  | Zusatzauswertung zur Studie "Wohnungsbau in Deutschland - 2011, Modernisierung oder Bestandsersatz" (inkl. Warmwasser, bezogen auf Wohnflaeche)
                    Thermal demand (>1 aptm. buildings) | Energiekennwerte 2013, Techem
                    Specific PV Generation              | http://www.umwelt-campus.de/ucb/fileadmin/users/176_h.teheesen/dokumente/Publikationen/Ertragsstudie_2012.pdf
                    TER 1 for HPs                       | Dimplex LA 12TU (http://www.dimplex.de/pdf/de/produktattribute/produkt_1725609_extern_egd.pdf)
        :param number: number of new BES to be added to the cluster
        :param sharesOfBESTypes:    array of shares of both types of BESs
                                    1. HPs | 2. CHPs (in %)
                                    if sum != 100% -> remaining share will be GBs
        :param pseudorandom: set to True if created BES's are supposed to be the exact same each time method is run
        :return:
        """

        # if pseudorandom is true, create reproducible BES with equal properties every time this method is called
        if pseudorandom:
            random.seed(randomSeed)

        # ==============================================================================================================
        # create data arrays of statistics for different BES parameters
        # ==============================================================================================================

        # no. of apartments per BES
        noApartmentsList = [1] * 651 \
                         + [2] * 172 \
                         + [3] * 29 + [4] * 29 + [5] * 29 + [6] * 29 \
                         + [7] * 8 + [8] * 8 + [9] * 8 + [10] * 8 + [11] * 8 + [12] * 7 \
                         + [13] + [14] + [15] + [16] + [17] + [18] + [19] + [20] + [21] + [22] + [23] + [24]

        # thermal demand per sqm and year, distribution depending on number of apartments in building
        demandList1 = [random.randint(30,60) for _ in range(4)] + [random.randint(60,80) for _ in range(17)] + [random.randint(80,100) for _ in range(38)] \
                   + [random.randint(100,120) for _ in range(59)] + [random.randint(120,140) for _ in range(85)] + [random.randint(140,160) for _ in range(106)] \
                   + [random.randint(160,180) for _ in range(120)] + [random.randint(180,200) for _ in range(123)] + [random.randint(200,220) for _ in range(119)] \
                   + [random.randint(220,240) for _ in range(100)] + [random.randint(240,260) for _ in range(55)] + [random.randint(260,280) for _ in range(38)] \
                   + [random.randint(280,300) for _ in range(29)] + [random.randint(300,320) for _ in range(24)] + [random.randint(320,340) for _ in range(20)] \
                   + [random.randint(340,360) for _ in range(18)] + [random.randint(360,380) for _ in range(13)] + [random.randint(380,400) for _ in range(13)] \
                   + [random.randint(400,500) for _ in range(19)]
        demandList2 = [random.randint(40,80) for _ in range(65)] + [random.randint(80,120) for _ in range(205)] + [random.randint(120,160) for _ in range(286)] \
                   + [random.randint(160,200) for _ in range(222)] + [random.randint(200,240) for _ in range(122)] + [random.randint(240,280) for _ in range(58)] \
                   + [random.randint(280,320) for _ in range(27)] + [random.randint(320,560) for _ in range(17)]
        demandList3 = [random.randint(40,80) for _ in range(81)] + [random.randint(80,120) for _ in range(289)] + [random.randint(120,160) for _ in range(330)] \
                   + [random.randint(160,200) for _ in range(186)] + [random.randint(200,240) for _ in range(75)] + [random.randint(240,280) for _ in range(25)] \
                   + [random.randint(280,320) for _ in range(8)] + [random.randint(320,560) for _ in range(5)]
        demandList7 = [random.randint(40,80) for _ in range(95)] + [random.randint(80,120) for _ in range(368)] + [random.randint(120,160) for _ in range(350)] \
                   + [random.randint(160,200) for _ in range(137)] + [random.randint(200,240) for _ in range(35)] + [random.randint(240,280) for _ in range(10)] \
                   + [random.randint(280,320) for _ in range(3)] + [random.randint(320,560) for _ in range(3)]
        demandList13 = [random.randint(40,80) for _ in range(98)] + [random.randint(80,120) for _ in range(404)] + [random.randint(120,160) for _ in range(339)] \
                   + [random.randint(160,200) for _ in range(121)] + [random.randint(200,240) for _ in range(28)] + [random.randint(240,280) for _ in range(6)] \
                   + [random.randint(280,320) for _ in range(1)] + [random.randint(320,560) for _ in range(2)]

        # pv system sizes in kWp
        pvSystemkWpList = [1.5 for _ in range(11)] + [2.5 for _ in range(38)] + [3.5 for _ in range(83)] + [4.5 for _ in range(137)] + [5.5 for _ in range(172)] \
                       + [6.5 for _ in range(122)] + [7.5 for _ in range(145)] + [8.5 for _ in range(129)] + [9.5 for _ in range(163)]

        # ==============================================================================================================
        # setup variables etc.
        # ==============================================================================================================

        # calculate numbers of HPs, CHPs and GBs each
        noHPs  = int(round(sharesOfBESTypes[0] * number / 100))
        noCHPs = int(round(sharesOfBESTypes[1] * number / 100))
        noGBs = number - noHPs - noCHPs

        # specific PV generation per year (2012) in kWh per kWp for PV systems in Bottrop (PLZ 46*) (source in comments above)
        specificGeneration = 918

        # create parameter arrays depending on number of each HS type
        TER1_arr = [-2.32] * noHPs + [+2.3] * noCHPs + [0] * noGBs      # TER 1
        TER2_arr = [-1]    * noHPs + [0]    * noCHPs + [0] * noGBs      # TER 2
        SM_arr   = [-2]    * noHPs + [-1]   * noCHPs + [1] * noGBs      # sizing method

        noApartments_arr = np.zeros(number)
        sqmPerApartment_arr = np.zeros(number)
        demand_arr = np.zeros(number)

        for i in range(number):

            noApartments_arr[i] = int(random.choice(noApartmentsList))  # no of apartments

            # get sqm and thermal demand depending on number of apartments in BES
            if noApartments_arr[i] == 1:
                sqmPerApartment_arr[i] = 128.5     # average sqm for 1 apartment buildings: 128,5
                demand_arr[i] = random.choice(demandList1)
            elif noApartments_arr[i] == 2:
                sqmPerApartment_arr[i] = 101.1     # average sqm for 2 apartment buildings: 101,1
                demand_arr[i] = random.choice(demandList2)
            else:
                sqmPerApartment_arr[i] = 68        # average sqm for >3 apartment buildings: 68

                if 2 < noApartments_arr[i] < 7:
                    demand_arr[i] = random.choice(demandList3)
                elif 6 < noApartments_arr[i] < 13:
                    demand_arr[i] = random.choice(demandList7)
                else:
                    demand_arr[i] = random.choice(demandList13)

        # ==============================================================================================================
        # create list of random BESs
        # ==============================================================================================================

        listBes = list()

        if sqm == 0:
            for i in range(number):
                listBes.append(SmartBes(stepSize=stepSize, TER1=TER1_arr[i], TER2=TER2_arr[i], RSC=RSC, sizingMethod=SM_arr[i], iApartments=int(noApartments_arr[i]),
                                        sqm=sqmPerApartment_arr[i], specDemandTh=demand_arr[i], env=environment, solPoolAbsGap=solPoolAbsGap,
                                        solPoolRelGap=solPoolRelGap, solPoolIntensity=solPoolIntensity))
        elif sqm > 0:
            for i in range(number):
                listBes.append(SmartBes(stepSize=stepSize, TER1=TER1_arr[i], TER2=TER2_arr[i], RSC=RSC, sizingMethod=SM_arr[i], iApartments=iApartments,
                                        sqm=sqm, specDemandTh=specDemandTh, env=environment, solPoolAbsGap=solPoolAbsGap,
                                        solPoolRelGap=solPoolRelGap, solPoolIntensity=solPoolIntensity))

        # ==============================================================================================================
        # equip BESs with available PV systems
        # ==============================================================================================================

        if lclPV==True:
            annualElecDemand = np.sum([bes.getAnnualElectricalDemand() for bes in listBes])     # in kWh
            desiredAnnualLclPVGeneration = np.abs(np.sum(environment.getPVEnergyCurve(0, 86400*365, annualElecDemand)[1,:]) / 3600000)  # in kWh

            listPVSystems = list()
            _pvSystemsGen = 0

            # create pv systems
            while len(listPVSystems) < number:
                # pick a random value for annual generation
                _annGen = random.choice(pvSystemkWpList) * specificGeneration

                # if this value causes the overall local pv generation to exceed the desired value...
                if _pvSystemsGen + _annGen > desiredAnnualLclPVGeneration:
                    # ...calculate difference between desired and current overall local pv generation...
                    _diff_kWp = (desiredAnnualLclPVGeneration - _pvSystemsGen) / specificGeneration
                    # ...and break if difference is smaller than the smallest pv system possible...
                    if _diff_kWp < 1.5:         # 1.5 kWp = smallest possible system size
                        break
                    # ...or add another last pv system before breaking if difference can be decreased any further
                    else:
                        _last_kWp = round(_diff_kWp) - 0.5                      # will be a value from the kWp system size array (x.5)
                        _annGen = _last_kWp * specificGeneration                # use this value to calculate annual generation of last pv system
                        listPVSystems.append(PVSystem(environment, _annGen))    # add system to list...
                        break                                                   # ...and break from while loop

                # add system to list & update pv systems' generation variable
                listPVSystems.append(PVSystem(environment, _annGen))
                _pvSystemsGen += _annGen


            # generate random list of BESs that receive a PV system
            noPVSystems = len(listPVSystems)
            listPVequippedBESs = random.sample(listBes[:], noPVSystems)

            # add pv systems to BESs
            for p in range(noPVSystems):
                listPVequippedBESs[p].addPVSystem(listPVSystems[p])


        # ==============================================================================================================
        # return list of BESs
        # ==============================================================================================================
        random.shuffle(listBes)
        return listBes