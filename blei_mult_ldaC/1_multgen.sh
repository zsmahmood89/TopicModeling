#!/bin/bash
shopt -s expand_aliases
source ~/.bash_profile

########
#This script will generate the reflist, if applicable.
#After that, we will run all years in parallel.
#Maximum of 3 parallel processes, one year at a time.
#########

#Initialize directories
wkdir=`pwd`
scripts="${wkdir}/SCRIPTS"

#Script names
prepscript="0_UNGA_dtm_prep.py"
multscript="1_UNGA_dtm_mult.py"
consscript="2_UNGA_dtm_cons.py"

#Arguments
ARG1=${1:-1982}
ARG2=${2:-2014} #INCLUSIVE!!!

#Reflist file name
refname="full-reflist.txt"

########
#Run
########

####################
#Prepare vocabulary if reflist doesn't exist
####################
cd "$wkdir"
if [ -e "$refname" ]
	then
	echo "$refname detected. Continuing to mult gen step"
	echo "You have 7 seconds to ctl-c out of this if you want to delete $refname and regenerate"
	sleep 10s
else
	echo "PREPARING vocabulary reflist"
	cd "$scripts"
	canopy $prepscript $ARG1 $ARG2
fi

##############################
#Generate MULT scripts
###############################
cd "$scripts"
curyear=$((ARG1))

while [ $((curyear)) -le $((ARG2)) ]
	do
		#if we can do three parallel scripts
		if [ $((curyear+2)) -le $((ARG2)) ]
			then
			echo "Generating years $curyear through $((curyear+2))"
			canopy $multscript "$curyear" & 
			canopy $multscript "$((curyear+1))" &
			canopy $multscript "$((curyear+2))" &
			wait &&
			curyear=$((curyear+3))
		else
			#if we can do two parallel scripts
			if [ $((curyear+1)) -le $((ARG2)) ]
				then
				echo "Generating years $curyear through $((curyear+1))"
				canopy $multscript "$curyear" & 
				canopy $multscript "$((curyear+1))" &
				wait &&
				curyear=$((curyear+2))
			else
				#Guess we can only do one
				echo "Generating year $curyear"
				canopy $multscript "$curyear"
				wait &&
				curyear=$((curyear+1))
			fi
		fi
	done

############################
#Concatenate the final outputs into a single mult file
############################
cd "$scripts"
echo "Generating full-mult.dat file"
canopy $consscript

echo "All your MULT are belong to us"