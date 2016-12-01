#! /usr/bin/env python

import os,sys,csv
from collections import defaultdict
from time import strptime
import pandas as pd

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

inpath = ""
outpath = ""

##############
#User options
##############

#Tell me how you want to divide time slices.
#   Options = "daily"; "monthly"; "quarterly"; "biannual"; "annual"
timeslice='quarterly'

#Do you want to write out a metafile with seqIDs per row? (recommend True)
#   It'll take longer to run the script, but you'll have a trail
#   to return to if you think there's a problem with the sequencing.
#   For very big datasets, this will add some time.
seq_meta=True

#Are your months numeric, or are they strings? 
#   Options = "numeric"; "string"
month_type="string"

#If they are strings, do you want to update them interactively if my canned method won't work?
#   I can try to only use a canned method, but no gurantees (e.g. misspellings).
#   Canned method recognizes 3-character abbreviations and correctly spelled name
#   Choosing "False" will break the code if my canned method doesn't work.
str2num_interactive=True

#If you changed the name of your "final_meta.csv" output, give it here.
#   Otherwise, leave it as "final_meta.csv"
infile='final_meta.csv'

###############
########
# NO MORE USER INPUTS PAST THIS POINT
########
###############

outseqbase='full-seq'
outmeta='seq_meta.csv'

#Functions
def writerow(row,ofile,odir,aw):
    curdir=os.getcwd()
    os.chdir(odir)
    with open(ofile,aw) as output:
        writer=csv.writer(output)
        writer.writerow(row)
    os.chdir(curdir)

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
    
def gettstuple(d,m,y,timeslice):
    if timeslice=="daily":
        tstuple=(int(d),int(m),int(y))
    elif timeslice=="monthly":
        tstuple=(int(m),int(y))
    elif timeslice=="quarterly":
        if int(m)<=3:
            tsliceid=1
        elif 3<int(m)<=6:
            tsliceid=2
        elif 6<int(m)<=9:
            tsliceid=3
        elif 9<int(m)<=12:
            tsliceid=4
        tstuple=(tsliceid,int(y))
    elif timeslice=="biannual":
        if int(m)<=6:
            tsliceid=1
        elif int(m)>6:
            tsliceid=2
        tstuple=(tsliceid,int(y))
    elif timeslice=="annual":
        tstuple=(1,int(y))
    else:
        sys.exit("Did you define your timeslice option correctly?")
    return tstuple
    
##########
#Code
##########

#########
#Take care of months
#########
if month_type=="string":
    os.chdir(inpath)
    tempdf=pd.read_csv(infile)
    molistmoprob=tempdf["month"].tolist()
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

os.chdir(inpath)
finlist=[]
seqiddict=defaultdict(lambda:0)
counter=0
with open(infile,'rb') as f:
    reader=csv.reader(f)
    for row in reader:
        print counter
        if counter==0:
            if seq_meta==True:
                addrow=['seqid']
                header=[row[1],row[3],row[4],row[5],row[6]]
                finrow=header+addrow
                writerow(finrow,outmeta,outpath,'w')
            counter+=1
            continue
        
        day=int(row[3])
        mon_raw=row[4]
        
        if month_type=='string':
            mon=dictmonthnum(mon_raw,monthdict)
        else:
            mon=int(mon_raw)
            
        yr=int(row[5])
        
        #initialize the sequencing
        if counter==1:
            prevtuple=gettstuple(day,mon,yr,timeslice)
        
        #If you're on a new tuple, store the old one
        curtuple=gettstuple(day,mon,yr,timeslice)
        if seqiddict[curtuple]==0:
            finlist.append(seqiddict[prevtuple])
        
        #If you're writing out metafiles, write it out here
        if seq_meta==True:
            addrow=[curtuple]
            currow=[row[1],row[3],row[4],row[5],row[6]]
            finrow=currow+addrow
            writerow(finrow,outmeta,outpath,'a')
        
        #Go to the next row and store your current tuple as new "previous" one
        seqiddict[curtuple]+=1
        counter+=1
        prevtuple=curtuple
        
#Don't forget to tack on that last one!
finlist.append(seqiddict[prevtuple])


############
#Finish off the seq file
############
finlist[0]=len(finlist)-1
if sum(finlist)-(len(finlist)-1)!=counter-1:
    print sum(finlist)-(len(finlist)-1)
    print ""
    print "Should be equal to"
    print ""
    print counter-1
    sys.exit()
outseq_csv=outseqbase+'.csv'
for item in finlist:
    writerow([item],outseq_csv,outpath,'a')

os.chdir(outpath)
base = os.path.splitext(outseq_csv)[0]
os.rename(outseq_csv, base + ".dat")

print ''
print ''
print ''
print 'FIN'