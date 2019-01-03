#! /usr/bin/env python

#############
#Written for python 2.7
#############

import nltk, re, sys, os, getopt, pandas, time
from collections import Counter
import numpy as np
from datetime import datetime
from nltk import word_tokenize as token_d
from nltk.tokenize import RegexpTokenizer as token_re
from collections import Counter
from nltk.corpus import stopwords

#Adapted from data_transformation_pt2_1914 (Will Issac and James Murray)
#    clarified outputs, 
#    an option for custom stopwords and custom regex for additional cleaning; 
#    an option for custom tokens as regex (e.g. s\/res\/\d{4} for security council);
#    an generalized workflow, given the header as stated below.
#    ability to topic model multiple csv files. MUST HAVE SAME HEADERS!!!

nltk.download('stopwords')

###########################
#NOTES
###########################

#REQUIREMENT FOR INPUT CSV FILE:
#   Header includes = ['id','day','month','year','speaker', 'speech']
#       (for example, "id" could be a session of the UNSC during which a speaker spoke)
#       (if you're not working with speeches, the text to be topic modeled goes under "speech")

#REQUIRES AS INPUT
#   CSV (one or more) with the above header

#OPTIONAL INPUT
#   text file with list of custom stopwords (one stopword per line)
#       (for example, in the UNSC project I removed references to countries)

#OUTPUT FILES:
#   meta_output.csv = metadata without DAT info
#   full_reflist.txt = reference wordlist
#   full_mult.dat = DAT info
#   final_meta.csv = metadata with DAT info
#   [user defined name].csv = full dataframe, including speeches, metadata, and DAT info

###################
# User Options 
###################

# If True, words in document will be stemmed using NLTK Snowball stemmer.
stem_mc = False			# Default: True

# If True, stopwords will be excluded.
exclude_stopwords = True	# Default: True

#Should I write out the FULL dataframe, including all speeches, as a single csv?
write_teh_big_one = True           #Default: True

# Give me any regex for custom tokens (order matters). Separate by "|". Lower case letters. 
#   If none, simply put ''.
custom_tokens=""

# List out any regex you want to clean in speeches (e.g. \n; \r; \uffd). 
#	REMEMBER TO ESCAPE ANY BACKSLASHES!!! e.g. if you want to remove the
#	"\\n" in a piece of text, you'll need to add "\\\\n" to the
#	custom_clean list below.
#    If none, simply put [].
custom_clean=[]

#Do you have a list of custom stopwords?
#    If True, you will need to define:
#        (1) a text file with custom stopwords.
#        (2) the directory of said file 
#		 (3) whether to treat these as "contains", too (e.g. remove "Israeli" if "Israel" in stopwords)
#		 	Warning: very powerful. Be careful. Also, could add a lot of time. Default = False.
#		 (4) a text file with any of your custom stopwords you DO NOT want to use as "contains". Place in "stoppath".
#    Note: stopwords will NOT be case sensitive.
custom_stopwords = True
stoplist_file = "namelist.txt"
stoppath = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/3_dtmprep/0_namelist/"
custom_stems = False
stem_exclude = ""
    
#########################
#Input and output directories
#########################

inpath = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/2_combined/"
refpath = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/3_dtmprep/1_multgen/"
outpath = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/3_dtmprep/1_multgen/"

assert "full-reflist.txt" in os.listdir(refpath)
###############################
#CSV file names 
#    (csvfilelist) a list of csv files (SAME HEADERS!!!) as inputs. If only one file, pass as ['filename']
#    (final_df_name) the name of your FULL dataframe output csv file
#   
###############################

csvfilelist = ["UNGANounsAdj.csv"]
final_df_name = "UNGANounsAdj_Full.csv"

#################
#Args
#################
year=sys.argv[1] #1982
assert str(year).isdigit()
assert len(str(year))==4,"System argument must be a year"
year=int(year)
pref=str(year)+"_"

###############################
######################
#CODE: NO MORE INPUTS PAST THIS POINT
######################
###############################

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
    
##############
#CODE
##############

#Read File
working_df = import_csvs(csvfilelist,inpath)

#Prep Working DF
working_df = working_df.reset_index()
working_df['index1'] = working_df.index
working_df=working_df[working_df["year"]==year]

#Prepare your toys for wordplay
snowball = nltk.stem.snowball.EnglishStemmer(ignore_stopwords=False)
final_token_set="[A-Za-z]{2,}"
if custom_tokens:
    final_token_set=final_token_set+"|"+custom_tokens
tokenizer = token_re(final_token_set) # group cites + words as tokens: ORDER MATTERS!!!!

print "CHECKPOINT 1: prepwork done"

####################################
#   1. Read in the reference list of ALL words
#   2. Assign numeric values to each word in vocabulary
#   3. Convert each speech to a vector of words WITHIN THE VOCABULARY
#   4. For each speech, get word count GIVEN PRESENCE IN VOCABULARY
#   5. For each speech, convert vector of words to sparse matrix
#   6. Write it all as a string in the dataframe
####################################

os.chdir(refpath)
ref_file=open("full-reflist.txt","r")
all_words_fin=ref_file.read().split("\n") #read the reflist text to a list of words
all_words_fin_set=set(all_words_fin) #SET is significantly faster!

assert len(all_words_fin)==len(all_words_fin_set)
assert all([i in all_words_fin_set] for i in all_words_fin) 

############################
#    2. Assign numeric values to each word in vocabulary
############################
all_sp_index=[i for i in range(0,len(all_words_fin))]
assert len(all_sp_index)==len(all_words_fin)
ind_word_dict=dict(zip(all_sp_index,all_words_fin))  
word_ind_dict=dict(zip(all_words_fin,all_sp_index))

def makemult(x):
    #Pre-process speech
    sp=x.lower()
    sp=sp.replace("-","")
    sp=sp.decode("utf8")
    
    #Tokenize words and keep only those in our vocab
    #SET IS SIGNIFICANTLY FASTER!!!
    vec_raw=tokenizer.tokenize(sp)
    vec=[word_ind_dict[i] for i in vec_raw if i in all_words_fin_set]
    
    #Prepare sparse matrix string
    wc=len(vec)
    multdict=dict(Counter(vec))
    multstr_raw=str(multdict)
    multstr=multstr_raw.replace("{","").replace("}","").replace(": ",":").replace(",","")
    outstr=str(wc)+" "+multstr
    return outstr
   
#LOOP here! Mapping/Applying is too memory intensive and won't work.
os.chdir(outpath)
for index1,row in working_df.iterrows():
	working_row=row.copy()
	sp=working_row["speech"]
	full_str=makemult(sp)
	working_df.loc[index1,"Full String"]=full_str
	if int(index1)%500==0:
		print "Processed through "+str(index1)
# working_df["Full String"]=working_df["speech"].map(makemult)

print "CHECKPOINT 5: Each speech converted to sparse matrix"

########################
#Write out:
#   1. final_meta.csv ["id","Full String","day","month","year","speaker"], no index, encoding="utf-8"
#   2. full-mult.dat
#   3. {final_df_name} [working_df], no index, encoding="utf-8"
########################
os.chdir(outpath)

#Write out metafile
final_meta=working_df[["id","Full String","day","month","year","speaker"]]
final_meta.to_csv(str(str(pref)+"final_meta.csv"),encoding="utf-8",index=False)

print "CHECKPOINT 6: meta file written"

#Write out your datfile
datfile=working_df[['Full String']]
datfile.to_csv(str(str(pref)+"full-mult.dat"),header=False,index=False)

print "CHECKPOINT 7: MULT file written"

#Write out full file, if applicable
if write_teh_big_one==True:
    working_df.to_csv(str(str(pref)+final_df_name),encoding="utf-8",index=False)

print "COMPLETE"