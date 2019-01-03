#! /usr/bin/env python

#############
#Written for python 2.7
#############

import re, sys, os, getopt, pandas, time
from collections import Counter
import numpy as np
from datetime import datetime
from collections import Counter

#########################
#Input and output directories
#########################

inpath = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/3_dtmprep/1_multgen/"
outpath = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/3_dtmprep/1_multgen/"

assert "full-reflist.txt" in os.listdir(inpath)

########################
#Option
########################
write_full_meta=True

######################
#########
#Code
#########
######################

##############
#Function
##############

# Import multiple csv files into a single pandas dataframe and sort
#   them by day/month/year timing. 
def import_csvs(csvfile_list,indir):
    os.chdir(indir)
    list_=[]
    for file_ in csvfile_list:
        my_temp_df=pandas.read_csv(file_,index_col=None)
        ed_df=my_temp_df[['id','year','month','day','speaker','speech']]
        list_.append(ed_df)
    frame=pandas.concat(list_)
    final_frame=frame.sort(['year','month','day'],ascending=[1,1,1])
    return final_frame

###############
#We need to be certain about the order of our mult file
#As a result, this might be inefficient, but it will ensure
#absolutely that we read in and concatenate our files
#in consecutive order. 
###############
yrs=list(set(re.findall("\d{4}",str(os.listdir(inpath)))))
yrs=np.sort(np.array(yrs,dtype=int))

yr_str=np.array(yrs,dtype=str)
file_iter=(s+"_full-mult.dat" for s in yr_str)

os.chdir(inpath)
fintxt=""
for f in file_iter:
	with open(f,"r") as infile:
		intxt=infile.read()
		intxt=intxt.strip()
		fintxt=fintxt+"\n"+intxt
fintxt=fintxt.strip()

os.chdir(outpath)
with open("full-mult.dat","w") as outfile:
	outfile.write(fintxt)

#Write out full meta file
if write_full_meta==True:
	
	###############
	#We need to be certain about the order of our meta files
	#As a result, this might be inefficient, but it will ensure
	#absolutely that we read in and concatenate our files
	#in consecutive order. 
	###############
	yrs=list(set(re.findall("\d{4}",str(os.listdir(inpath)))))
	yrs=np.sort(np.array(yrs,dtype=int))

	yr_str=np.array(yrs,dtype=str)
	file_list=[s+"_"+metafilebase for s in yr_str]

	os.chdir(inpath)
	assert file_list[0] in os.listdir(inpath),"your metafile doesn't exist"

	df_meta=import_csvs(file_list,inpath)

	os.chdir(outpath)
	df_meta.to_csv(metafilebase,index=False)

	print "Meta file written"
print("Mult files consolidated")