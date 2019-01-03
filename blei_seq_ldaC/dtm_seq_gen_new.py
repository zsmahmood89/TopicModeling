#! /usr/bin/env python

import os,sys,csv,re
from collections import defaultdict
from time import strptime
import pandas as pd
import numpy as np

##########
#Written for Python 2.7
##########

#This file generaets a SEQ file based on the output from "dtm_input_gen.py"
#   Note: The file will originally be written out as a csv file, then
#           converted to a .DAT file. The CSV module is useful and reliable
#           for writing out rows in sequence, and switching that to a .DAT
#           extension is very straightforward using the OS module.

##############
#Input = "final_meta.csv" from DTM gen
#
#    Required header (exact): [index1,id,Full String,day,month,year,speaker]
#        If you're coming directly from dtm_input_gen.py, 
#        it should already be like this.
#
#    If you're coming directly from dtm_input_gen.py,
#    the rows should also already be sorted ascending in time.
#
#
#Output = 
#    "final-seq.dat" (for the DTM)
#    "seq_meta.csv" (so you can cross reference the seq file)
#
##############

##############
#Directories
##############

wkdir = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/"
inpath = wkdir+"OUTPUT/0_topicmodel/3_dtmprep/1_multgen/"
outpath = wkdir+"OUTPUT/0_topicmodel/3_dtmprep/2_seqgen/"

##############
#User options
##############

#Tell me how you want to divide time slices.
#   Options = "daily"; "monthly"; "quarterly"; "biannual"; "annual"
timeslice='biannual'

#Do you want to write out a metafile with seqIDs per row? (recommend True)
#   It'll take longer to run the script, but you'll have a trail
#   to return to if you think there's a problem with the sequencing.
#   For very big datasets, this will add some time.
seq_meta=True

#Are your months numeric, or are they strings? 
#   Options = "numeric"; "string"
month_type="numeric"

#If they are strings, do you want to update them interactively if my canned method won't work?
#   I can try to only use a canned method, but no gurantees (e.g. misspellings).
#   Canned method recognizes 3-character abbreviations and correctly spelled name
#   Choosing "False" will break the code if my canned method doesn't work.
str2num_interactive=False

#If you changed the name of your "final_meta.csv" output, give it here.
#   Otherwise, leave it as "final_meta.csv"
infilebase='final_meta.csv'

###############
########
# NO MORE USER INPUTS PAST THIS POINT
########
###############

outseqbase='full-seq'
outmeta='seq_meta.csv'

############
#Functions
############

# Import multiple csv files into a single pandas dataframe and sort
#   them by day/month/year timing. 
def import_csvs(csvfile_list,indir):
    os.chdir(indir)
    list_=[]
    for file_ in csvfile_list:
        my_temp_df=pd.read_csv(file_,index_col=None)
        #ed_df=my_temp_df[['id','year','month','day','speaker','speech']]
        list_.append(my_temp_df)
    frame=pd.concat(list_)
    final_frame=frame.sort(['year','month','day'],ascending=[1,1,1])
    return final_frame

def cannedmonthnum(month_str):
    try:
        month_no=strptime(month_str,'%b').tm_mon
    except ValueError:
        try:
            month_no=strptime(month_str,'%B').tm_mon
        except ValueError:
            month_no=0
    return month_no

def dictmonthnum(month_str,month_dict):
    try:
        month_no=month_dict[month_str]
    except KeyError:
        sys.exit("Your month dict is incomplete. Why?")
    return month_no
    
def gettstuple(dmyRow):
    d=dmyRow["day"]
    m=dmyRow["month"]
    y=dmyRow["year"]
    if timeslice=="daily":
        tstuple=(int(y),int(m),int(d))
    elif timeslice=="monthly":
        tstuple=(int(y),int(m))
    elif timeslice=="quarterly":
        if int(m)<=3:
            tsliceid=1
        elif 3<int(m)<=6:
            tsliceid=2
        elif 6<int(m)<=9:
            tsliceid=3
        elif 9<int(m)<=12:
            tsliceid=4
        tstuple=(int(y),tsliceid)
    elif timeslice=="biannual":
        if int(m)<=6:
            tsliceid=1
        elif int(m)>6:
            tsliceid=2
        tstuple=(int(y),tsliceid)
    elif timeslice=="annual":
        tstuple=(int(y),1)
    else:
        sys.exit("Did you define your timeslice option correctly?")
    return tstuple

##########
#Code
##########

#########
#Import all the final_meta datasets
#########
os.chdir(inpath)

yrs=list(set(re.findall("\d{4}",str(os.listdir(inpath)))))
yrs=np.sort(np.array(yrs,dtype=int))
yr_str=np.array(yrs,dtype=str)
metafile_list=[s+"_"+infilebase for s in yr_str]

df_meta_raw=import_csvs(metafile_list,inpath)

#########
#Take care of months
#########
if month_type=="string":
    mn_raw=df_meta_raw.month
    if mn_raw.dtype!=int:
        molistmoprob=mn_raw.tolist()
        molist=list(set(molistmoprob))
        monthdict={}
        for mo in molist:
            mo_no=cannedmonthnum(str(mo))
            if mo_no==0:
                #Interactive
                if str2num_interactive==True:
                    mo_no=input("input an integer for the following month after the equal sign: "+str(mo)+"= ")
                
                #Non-interactive
                elif str2num_interactive==False:
                    sys.exit("Sorry, canned methods [can]'t recognize this month: '"+str(mo)+"'. There may be more errors, but this is one of them. Use interactive method or manually do it yourself.")
            monthdict[str(mo)]=int(mo_no)
        print monthdict
    
########
#Iterate over rows
########

finlist=[]
seqiddict=defaultdict(lambda:0)
counter=0
df_meta_out=df_meta_raw
df_meta_out["seqid"]=df_meta_out.apply(gettstuple,axis=1)
out_seq=df_meta_out.set_index(["seqid","id"]).count(level="seqid")
out_seq_cons=out_seq[["year","speaker"]]
out_seq_add=pd.DataFrame(np.array([[out_seq_cons.shape[0],out_seq_cons.shape[0]]]), columns=["year","speaker"]).append(out_seq_cons, ignore_index=True)
out_seq_fin=out_seq_add["speaker"]

#Write out your files
os.chdir(outpath)
out_seq_fin.to_csv(outseqbase+'.dat',header=False,index=False,sep="\n")
df_meta_out.to_csv(outmeta,header=True,index=False)

print 'FIN'