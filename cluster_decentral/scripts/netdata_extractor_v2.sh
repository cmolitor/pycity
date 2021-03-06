#!/bin/bash

# This script extracts the nodes and network connections of a Nepal exported (uct file) electricity network.
# Nodes (agents) obtain the same name as in uct file. The communication ID is euqal to the name.
# Medium voltage network is currrently ignored.
# Functions from python class "MultiAgentSysten" are used to generate network for python testing and simulation.
# Current content of networksetup.py file will be overwritten!

# no argument error
if [[ $# -lt 3 ]]; then
	echo "usage: $0 <uct-file[uct]> <scenario-file[csv]> <algorithm type>"
	exit
fi

UCT_FILE=$1
SCENARIO_FILE=$2
ALG_TYPE=$3
PY_FILE="../networksetup.py"
CLUSTER_NAME="testMAS"
DATE=$(date)
STATE=0
NO_BES=0
NO_LINKS=0
BES=()
NUMBER_CB=83            # building type 151 in Scenario.csv
NUMBER_CHP=31           # building type 152 in Scenario.csv
NUMBER_EH=4             # building type 153 in Scenario.csv
NUMBER_HPair=28         # building type 154 in Scenario.csv

ElectricalDistance=10 # assume there is a cable of 20 meters length between all BES
ElectricalDistanceTrafo=50 #electrical distance to trafo is 30 meters
TrafoID='LV_Bus'

#echo "$UCT_FILE"


if [[ -r $UCT_FILE ]]; then 	# test if argument is a readable file
    echo "Creating file $PY_FILE     ..."
	# create "network.py" file in directory "cluster_decentral"
	# if a "netwotk.py" file exsits this will be overwritten!
	echo "__author__ = 'netdata_extractor script'" > $PY_FILE
	echo "# THIS FILE WAS AUTO-GENERATED BY netdata_extractor.sh SCRIPT from UCT file $UCT_FILE, scenario file $SCENARIO_FILE for algorithm type $ALG_TYPE" >> $PY_FILE
#	echo "# $DATE" >> $PY_FILE
	echo "" >> $PY_FILE
	echo "from multi_agent_system import MultiAgentSystem" >> $PY_FILE
	if [ "$ALG_TYPE" == "tree" ]; then
	    echo "from tree_agent import TreeAgent" >> $PY_FILE
	elif [ "$ALG_TYPE" == "multicast" ]; then
		echo "from multicast_agent import MulticastAgent" >> $PY_FILE
	elif [ "$ALG_TYPE" == "uncoord" ]; then
		echo "from uncoord_agent import UncoordAgent" >> $PY_FILE
	fi
	#echo "from multiprocessing import Process" >> $PY_FILE
	echo "" >> $PY_FILE
	echo "def setupNetwork(message_log, results_log, env, horizon, stepSize, interval, bivalent, solPoolInt, absSolGap):" >> $PY_FILE
	echo " " >> $PY_FILE
	echo "    RSC = 3" >> $PY_FILE
	echo "    iApartments = 1" >> $PY_FILE
	echo "    sqmAppartmentSize = 100" >> $PY_FILE
	echo "    specDemandTh = 160" >>$PY_FILE
	echo "    TER1_HP = -3" >> $PY_FILE
	echo "    TER1_EH = -1" >> $PY_FILE
	echo "    TER1_CHP = 2.3" >> $PY_FILE
	echo "    TER1_NETH = 0" >> $PY_FILE
	echo "    TER2_NETH = 0" >> $PY_FILE
	echo "    sizingMethod_NETH = 1" >> $PY_FILE
	echo "    if bivalent == 1:" >> $PY_FILE
	echo "        TER2_HP = -1" >> $PY_FILE
	echo "        TER2_EH = -1" >> $PY_FILE
	echo "        TER2_CHP = 0" >> $PY_FILE
	#echo "        sizingMethod_HP = 0.98" >> $PY_FILE
	echo "        sizingMethod_HP = -2" >> $PY_FILE
	echo "        sizingMethod_EH = 1" >> $PY_FILE
	echo "        sizingMethod_CHP = -1" >> $PY_FILE
	echo "    else:" >> $PY_FILE
	echo "        TER2_HP = 0" >> $PY_FILE
	echo "        TER2_EH = 0" >> $PY_FILE
	echo "        TER2_CHP = 0" >> $PY_FILE
	#echo "        sizingMethod_HP = 1" >> $PY_FILE
	echo "        sizingMethod_HP = -2" >> $PY_FILE
	echo "        sizingMethod_EH = 1" >> $PY_FILE
	echo "        sizingMethod_CHP = 1" >> $PY_FILE

	echo "    print 'NETWORKSETUP: Starting network setup...'" >> $PY_FILE
	echo -e "\n    # Generate Cluster" >> $PY_FILE
	echo "    print 'NETWORKSETUP: Generating MultiAgentSystem Object...'" >> $PY_FILE
	echo "    $CLUSTER_NAME = MultiAgentSystem(message_log, results_log, env, horizon, stepSize, interval)" >> $PY_FILE
	echo -e "\n    # Generate agents" >> $PY_FILE

	echo "    print 'NETWORKSETUP: Generating agent objects'" >> $PY_FILE
	if [ "$UCT_FILE" == "../netdata/suburban_146.uct" ]; then
		echo "Processing files $UCT_FILE and $SCENARIO_FILE"
		while read line		# read file line by line
		do
			#echo $line
			if [[ $line == *"##ZZone 1"* ]]; then		# section of nodes /agents
				STATE=1				# remember that we entered this section
				#echo "State = $STATE"
			elif [[ $line == *"##L"* ]]; then			# section of network connections
				STATE=2				# remember that we entered this section
				#echo "State = $STATE"
				# add BES objects to cluster
				echo "    print 'NETWORKSETUP: Adding all agent objects to the MAS...'" >> $PY_FILE
				for b in "${BES[@]}"
				do
				    echo "    $CLUSTER_NAME.addMember($b)" >> $PY_FILE
			    done
				echo "    print 'NETWORKSETUP: Generating links in the network...'" >> $PY_FILE
			elif [[ $line == *"##T"* ]]; then
				STATE=3
				#echo "State = $STATE"
			elif [[ $line == *"##R"* ]]; then
				STATE=4
				#echo "State = $STATE"
			elif [[ $line != *"HCP"* && $STATE == "1" && $line != *"N122"* ]]; then

				BES_name=$(echo $line | cut -d" " -f1)
				#echo "Found PCC agent $BES_name"
                if [[ $BES_name == "LV_Bus" ]]; then # special case LV_Bus Trafo
                        if [ "$ALG_TYPE" == "tree" ]; then
                            echo "    $BES_name = TreeAgent(message_log, stepSize, TER1_CHP, TER2_CHP, RSC, sizingMethod_CHP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                        elif [ "$ALG_TYPE" == "multicast" ]; then
                            echo "    $BES_name = MulticastAgent(message_log, stepSize, TER1_CHP, TER2_CHP, RSC, sizingMethod_CHP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                        elif [ "$ALG_TYPE" == "uncoord" ]; then
                            echo "    $BES_name = UncoordAgent(message_log, stepSize, TER1_CHP, TER2_CHP, RSC, sizingMethod_CHP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                        fi
                        #echo "    $BES_name = CommBes(message_log, stepSize, TER1_NETH, TER2_NETH, RSC, sizingMethod_NETH, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name')" >> $PY_FILE
                    BES+=($BES_name)
				    NO_BES=$(($NO_BES+1))
                    continue
                else
                    BES_id=${BES_name:4:${#BES_name}}
                    #echo $BES_id
                    BES_type=`cat $SCENARIO_FILE | grep $BES_id | cut -d";" -f3`
                    #echo $BES_type
                fi
				# replace "-" by "_"
				BES_name=$(echo $BES_name | sed 's/-/_/')
				# create BES object
				if [[ $BES_type == 151 ]]; then # condensoning boiler (CB)
				    if [ "$ALG_TYPE" == "tree" ]; then
                        echo "    $BES_name = TreeAgent(message_log, stepSize, TER1_NETH, TER2_NETH, RSC, sizingMethod_NETH, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "multicast" ]; then
                        echo "    $BES_name = MulticastAgent(message_log, stepSize, TER1_NETH, TER2_NETH, RSC, sizingMethod_NETH, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "uncoord" ]; then
                        echo "    $BES_name = UncoordAgent(message_log, stepSize, TER1_NETH, TER2_NETH, RSC, sizingMethod_NETH, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    fi

                elif [[ $BES_type == 152 ]]; then # Combined Heat and Power (CHP)
                    if [ "$ALG_TYPE" == "tree" ]; then
                        echo "    $BES_name = TreeAgent(message_log, stepSize, TER1_CHP, TER2_CHP, RSC, sizingMethod_CHP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "multicast" ]; then
                        echo "    $BES_name = MulticastAgent(message_log, stepSize, TER1_CHP, TER2_CHP, RSC, sizingMethod_CHP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "uncoord" ]; then
                        echo "    $BES_name = UncoordAgent(message_log, stepSize, TER1_CHP, TER2_CHP, RSC, sizingMethod_CHP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    fi

                elif [[ $BES_type == 153 ]]; then # Electrically Heated Boiler (EH)
                    if [ "$ALG_TYPE" == "tree" ]; then
                        echo "    $BES_name = TreeAgent(message_log, stepSize, TER1_EH, TER2_EH, RSC, sizingMethod_EH, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "multicast" ]; then
                        echo "    $BES_name = MulticastAgent(message_log, stepSize, TER1_EH, TER2_EH, RSC, sizingMethod_EH, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "uncoord" ]; then
                        echo "    $BES_name = UncoordAgent(message_log, stepSize, TER1_EH, TER2_EH, RSC, sizingMethod_EH, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    fi

                elif [[ $BES_type == 154 ]]; then # Heat Pump with air source (HPair)
                    if [ "$ALG_TYPE" == "tree" ]; then
                        echo "    $BES_name = TreeAgent(message_log, stepSize, TER1_HP, TER2_HP, RSC, sizingMethod_HP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "multicast" ]; then
                        echo "    $BES_name = MulticastAgent(message_log, stepSize, TER1_HP, TER2_HP, RSC, sizingMethod_HP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    elif [ "$ALG_TYPE" == "uncoord" ]; then
                        echo "    $BES_name = UncoordAgent(message_log, stepSize, TER1_HP, TER2_HP, RSC, sizingMethod_HP, iApartments, sqmAppartmentSize, specDemandTh, ID='$BES_name', solutionPoolIntensity=solPoolInt, absGap=absSolGap, envirmt=env)" >> $PY_FILE
                    fi
                fi

				#echo "    $BES_name = CommBes(stepSize=3600, TER1=2, TER2=0, RSC=3, sizingMethod=1, iApartments=1, sqm=100, specDemandTh=160, ID='$BES_name')" >> $PY_FILE
				#remember BES object (for generation + adding it to cluster later)
				BES+=($BES_name)
				NO_BES=$(($NO_BES+1))
			elif [[ $STATE == "2" && $line != *"HCP"* ]]; then
				BES_1=$(echo $line | cut -d" " -f1)
				BES_1=$(echo $BES_1 | sed 's/-/_/')
				BES_2=$(echo $line | cut -d" " -f2)
				BES_2=$(echo $BES_2 | sed 's/-/_/')
				if [[ $BES_1 == $TrafoID || $BES_2 == $TrafoID ]]; then
				    echo "    $CLUSTER_NAME.setLink($BES_1, $BES_2, $ElectricalDistanceTrafo)" >> $PY_FILE
				else
				    echo "    $CLUSTER_NAME.setLink($BES_1, $BES_2, $ElectricalDistance)" >> $PY_FILE
				fi
				NO_LINKS=$(($NO_LINKS+1))

			fi
		done < $UCT_FILE
		echo "    print 'NETWORKSETUP: Generated MAS with $NO_BES agent objects and $NO_LINKS links!'" >> $PY_FILE
		echo "    print 'NETWORKSETUP: Network setup finished!'" >> $PY_FILE
		echo "    return $CLUSTER_NAME" >> $PY_FILE
	else
		echo "The file $UCT_FILE is unknown to the netdata_extractor script. Please extend the script to use this file."
	fi
	echo "Done."

else
	echo "error: file $UCT_FILE is not found!"
fi
