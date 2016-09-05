#! /usr/bin/env python

import os,sys,csv
from fuzzywuzzy import fuzz

#Directories
sourcedir=   ##################
indir=       ##################
outdir=      ##################

#Filenames
cow_source='COW Country Codes.csv'
infile=     #######################
outfile=    #######################

#Which column in your infile is your country LABEL in (integer)? 
labelcol=   #

#Which column in your infile will your ccode be written into (integer)?
cowcol=     #

########
#Error file name. Deletable after script is complete. Program will constantly write/rewrite this file.
#     Default is "check_cow_errors.csv". 
########
errfile="check_cow_errors.csv"

#Does your file have a header/first row to skip (I'll write it into the new file still). Default = True.
file_header=True


#############################
#NO MORE USER INPUTS BEYOND THIS POINT
#############################

#double check the user's deleted his/her error file
os.chdir(outdir)
try:
    os.remove(errfile)
except OSError:
    pass

###################
###########
#    CODE
###########
###################

#Build dictionary from sourcefile
os.chdir(sourcedir)
cowdict={}
with open(cow_source,'rb') as c:
    reader=csv.reader(c)
    reader.next()
    for row in reader:
        ccode=int(row[1])
        statename=row[2]
        cowdict.update({statename:ccode})

#Define functions for cow coding
def writerow(currow,ofile,odir,aw):
    curdir=os.getcwd()
    os.chdir(odir)
    with open(ofile,aw) as output:
        writer=csv.writer(output)
        writer.writerow(currow)
    os.chdir(curdir)

def label_value(label,cowdict):
    cowcodelist=[]
    if label in cowdict:
        value=cowdict[label]
        cowcodelist.append(value)
    return cowcodelist

def label_list(label,cowdict):
    ccodelist=[]
    perflist=[]
    if label in cowdict:
        ccodelist.append(cowdict[label])
    else:
        for k,v in cowdict.iteritems():
            key=str(k)
            value=int(v)
            break
            cowvalue=fuzz.token_set_ratio(label,key)
            if cowvalue>75:
                ccodelist.append(value)
            if cowvalue==100:
                perflist.append(value)
        if len(perflist)==1:
            ccodelist=perflist
    return ccodelist

#Cow Coding: First read of your input     
errs={}
os.chdir(indir)
counter=0
with open(infile,'rb') as f:
    reader=csv.reader(f)
    for row in reader:
        
        #catch header
        if counter==0:
            if file_header==True:
                header=row
                writerow(header,outfile,outdir,'w')
                counter+=1
                continue
            else:
                pass
        
        #iterate over rows
        country_label=row[labelcol]
        country_label=country_label.strip()
        clist=label_list(country_label,cowdict)
        try:
            row[cowcol]=clist[0]
        except IndexError:
            row[cowcol]=clist
        
        #write out row to output file
        writerow(row,outfile,outdir,'a')
        
        #Output your errors
        if len(clist)!=1:
            if country_label not in errs:
                errs[country_label]=clist
                err_row=[country_label,clist]
                writerow(err_row,errfile,outdir,'a')
            else:
                pass
        else:
            cowdict[country_label]=int(clist[0])
            pass
        
        print counter
        counter+=1

print ""
print ""
print ""       
##############
#Edit the errors file
##############

def update_errdict(errfile,errdir,cowdict):
    curdir=os.getcwd()
    os.chdir(errdir)
    with open(errfile,'rb') as e:
        reader=csv.reader(e)
        for row in reader:
            country=row[0]
            ccode=row[2]
            if ccode:
                cowdict[country]=int(ccode)
    os.chdir(curdir)
    return cowdict

while len(errs)>0:
    errs_edited=input("Edit error file. Remember to use column 3, the first BLANK column. Type 'yes' (WITH QUOTES) when done. Type 'done' (WITH QUOTES) when your file is done (e.g. errors are not countries)___")
    
    if errs_edited=="yes":
        
        os.chdir(outdir)
        #rewrite that output file
        if file_header==True:
            writerow(header,outfile,outdir,'w')
        else:
            os.remove(outfile)
        
        #add in your edited values to our CowCode dictionary
        cowdict=update_errdict(errfile,outdir,cowdict)
                
        #remove that previous error file
        os.remove(errfile)
        
        #now RE-RUN that COW CODING from before, including your new edits
        errs={}
        os.chdir(indir)
        with open(infile,'rb') as f:
            reader=csv.reader(f)
            if file_header==True:
                reader.next()
            else:
                pass
            for row in reader:
                #iterate over rows
                country_label=row[labelcol]
                country_label=country_label.strip()
                clist=label_value(country_label,cowdict)
                try:
                    row[cowcol]=clist[0]
                except IndexError:
                    row[cowcol]=clist
                
                #write out row to output file
                writerow(row,outfile,outdir,'a')
                
                #Output your errors
                if len(clist)!=1:
                    if country_label not in errs:
                        errs[country_label]=clist
                        err_row=[country_label,clist]
                        writerow(err_row,errfile,outdir,'a')
                    else:
                        pass
                else:
                    cowdict[country_label]=int(clist[0])
                    pass
                    
    elif errs_edited=="done":
        print ""
        print ""
        sys.exit("You have exited! Delete the generated files prior to restarting")
        
    else:
        continue
        
print "fin!"        
        
                
                
                
            