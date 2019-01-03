#! /usr/bin/env python

#############
#Written for python 2.7
#This script makes a unique vocabulary for DTM prep
#############

import nltk, re, sys, os, getopt, pandas, time
from collections import Counter
import numpy as np
from datetime import datetime
from nltk import word_tokenize as token_d
from nltk.tokenize import RegexpTokenizer as token_re
from collections import Counter
from nltk.corpus import stopwords

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
outpath = "/Volumes/Seagate Backup Plus Drive/Z/MSUgrad/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/3_dtmprep/1_multgen/"

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
styear=sys.argv[1] #1982
assert str(styear).isdigit()
assert len(str(styear))==4,"Start year must be a year"
styear=int(styear)

endyr=sys.argv[2] #2014
assert str(endyr).isdigit()
assert len(str(endyr))==4,"End year must be a year"
endyr=int(endyr)

assert styear<=endyr,"Start year must be prior to end year"

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
        
# tokenize all words into a list using the Porter Snowball Stemmer
def stem_list(a_list):
	list_out = []
	for item in a_list:
		list_out.append(snowball.stem(item))
	return list_out

# Adds items from a_list that are not already keys in master_dict to the list
# 	and makes their value equal to n as they are the nth term to enter the dict
# It is for compiling master lists of stems and words.
def add_to_master(master_dict, m_d_rev, a_list, file_obj):
	for item in a_list:
		if item not in master_dict:
			master_dict[item] = len(master_dict)
			m_d_rev[master_dict[item]] = item
			with open(file_obj,'a') as _f:
				_f.write(str(item)+"\n")
	return master_dict, m_d_rev

# Combines lists, keeping one copy of each word, and returning an appended first list1.
def combine_lists(list1,list2):
	for item in list2:
		if item not in list1:
			list1.append(item)
	return list1

# Counts words in a list, outputting a counter with items in the form wordindex: count, referencing a reference list
def count_words_counter(ref_dict, list_to_count):
	cnt_out = C_()
	for item in list_to_count:
		cnt_out[ref_dict[item]] += 1
	return cnt_out

# Removes all words from blacklist from input_list
def clean_list(blacklist,input_list):
	for item in blacklist:
		if item in input_list:
			for x in range(input_list.count(item)):
				input_list.remove(item)
	return input_list

#Removes any words CONTAINING words in blacklist from input_list (e.g. removes "Israeli" if "Israel" is in blacklist)
def clean_stems(blacklist,input_list):
	zstr=" ".join(input_list)
	blacklist_stems=[]
	rm_words=[]
	for item in blacklist:
		zre=re.search(str(item),zstr,re.I)
		if zre:
			blacklist_stems.append(item)
	for stem in blacklist_stems:
		for word in input_list:
			if stem.lower() in word.lower():
				rm_words.append(word)
	finlist=[item for item in input_list if item not in rm_words]
	return(finlist)

# Outputs file containing the wordlist with one word per row
def list_to_file(Counter_in,path_str,file_name):
	listfile = open(path_str + file_name, 'w', encoding = "utf-8")
	for item in Counter_in:
		listfile.write(item +'\n')
	listfile.close()

# Make a string in the multi.dat format from a counter
def make_multi(Counter_in):
	out_str = []
	out_str1 = []
	for item in Counter_in:
		item_v = '{0}'.format(item)
		count = '{0}'.format(Counter_in[item])
		out_str.append(item_v)
		out_str1.append(count)
	return out_str, out_str1

#creates a more streamlined .dat file: see 'wordcounts' file in hansard
def make_multi_full(Counter_in):
	out_str = str(len(Counter_in))
	for item in Counter_in:
		tmp_str = " {0}:{1}".format(item, Counter_in[item])
		out_str += tmp_str
	return out_str


#cleans a dataframe by removing NA values and exporting a clean version to csv
def clean_df(rawdf,rawname,headnamelist): 
    cldfraw=pandas.DataFrame(rawdf)
    cldf=pandas.DataFrame.dropna(cldfraw)
    cldf=cldf.reset_index()
    
    collist=list(cldf)
    if 'index' in collist:
        collist.remove('index')
    
    cldf.to_csv('cl'+rawname,sep=',',index=False,index_label=False,columns=collist,header=headnamelist)
    cldfcsv=pandas.read_csv('cl'+rawname)
    cldf=pandas.DataFrame(cldfcsv)
    return cldf


# Converts a printed counter back into a counter object
def remake_counter(counter_str):
	counter_out = C_()
	counter_str = re.sub("Counter\(\{", "", counter_str)
	counter_str = re.sub("\}\)$", "", counter_str)
	counter_str_list = re.split(", ", counter_str)
	for item in counter_str_list:
		counter_out[int(item[0:item.find(":")])] = int(item[item.find(":") + 2:])
	return counter_out

# Prints a counter to a file. Used to record the date, month, and year counts
def print_counter(a_counter, a_file):
    working_str = str(a_counter)[9:-2]
    item_list = sorted(working_str.split(","))
    for item in item_list:
        a_file.write(item.strip().replace("'", "") + '\n')

# Converts a specified text file into a list of stopwords
def custom_list(filename,location):
    curdir=str(os.getcwd())
    os.chdir(location)
    with open(filename,'rb') as f:
        lines=f.read().split('\n')
    os.chdir(curdir)
    finlist=[x.lower() for x in lines if len(x)>2] #incl words like "the"; "new"
    fin=[f for f in finlist if f]
    return fin

##############
#CODE
##############

#Read File
working_df = import_csvs(csvfilelist,inpath)

#Prep Working DF
working_df = working_df.reset_index()
working_df['index1'] = working_df.index
working_df = working_df[working_df["year"]>=styear]
working_df = working_df[working_df["year"]<=endyr]

#Prepare your toys for wordplay
snowball = nltk.stem.snowball.EnglishStemmer(ignore_stopwords=False)

final_token_set="[A-Za-z]{2,}"
if custom_tokens:
    final_token_set=final_token_set+"|"+custom_tokens
tokenizer = token_re(final_token_set) # group cites + words as tokens: ORDER MATTERS!!!!

word_dict    = {}			# Dict of all words in format {first_word_to_appear:0, ..., nth_word_to_appear:n}
w_d_rev		 = {}			# word_dict with keys and values reversed
stemmed_dict = {}			# Dict of all stems in format {first_stem_to_appear:0, ..., nth_stem_to_appear:n}
s_d_rev		 = {}			# stemmed_dict with keys and values reversed
s_blacklist  = []			# List of stems to remove
w_blacklist  = []			# List of words to remove
if exclude_stopwords == True:
	w_blacklist += stopwords.words('english')
	
if custom_stopwords == True:
        stoplist_directory = stoppath
        custom_stoplist=custom_list(stoplist_file,stoplist_directory)
        w_blacklist += custom_stoplist

#counter_full = C_({}) 	# Counter of all words (or stems) and their counts in format Counter({value_of_word_in_word_dict_or_stemmed_dict: count, ...})
#file_count = 1
#
#doc_grouper = ""				# Prepares for grouping of mem. cont. by metadata
#counter_to_print = C_()
#working_df['index1'] = working_df.index
#w_mc = []
#
##Prepare ref_file so you can write out words
#ref_file = outpath + 'full-reflist.txt'

print("CHECKPOINT 1: prepwork done")
###########
#Steps:
#   1. Compile a unique vocabulary 
#   2. Assign numeric values to each word in vocabulary
#   3. Convert each speech to a vector of words WITHIN THE VOCABULARY
#   4. For each speech, get word count GIVEN PRESENCE IN VOCABULARY
#   5. For each speech, convert vector of words to sparse matrix
#   6. Write it all as a string in the dataframe
############


#############################
#Function: takes as argument a string, outputs word list
#############################
def str2wordlist(string,custom_clean,w_blacklist,custom_stopwords,custom_stems,stem_exclude,stoplist_directory,custom_stoplist,unique=False):
    ########################
    #Cleans up an input string and returns a string vector
    #Default returns a FULL vocab list, not a unique list
    ########################
    all_sp=string.lower()
    all_sp=all_sp.replace("-","")
    
    for stuff_to_clean in custom_clean:
        all_sp=re.sub(str(stuff_to_clean),' ',all_sp)
    
    all_sp=all_sp.decode("utf8")
    
    
    #Tokenize words
    all_words=tokenizer.tokenize(all_sp)
    #if custom_tokens:
    #    all_words = tokenizer.tokenize(all_sp)
    #else:
    #    all_words = token_d(all_sp)
    
    #Clean up the tokenized wrds
    if unique==True:
        all_words = list(set(all_words))
    elif unique==False:
        pass
    else:
        sys.exit("'Unique' argument must be boolean")
        
    all_words = clean_list(w_blacklist, all_words)
    #Custom stoplist stemming
    if custom_stopwords == True:
        custom_stoplist_set=set(custom_stoplist)
        if custom_stems==True:
            excl_list=custom_list(stem_exclude,stoplist_directory)
        else:
            excl_list=[]
            custom_stemlist=[i for i in custom_stoplist_set if i not in excl_list]
            all_words = clean_stems(custom_stemlist,all_words)
    
    return all_words
    
###########################
#    1. Compile a unique vocabulary
###########################
all_sp=" ".join(working_df["speech"])
all_words=str2wordlist(all_sp,custom_clean,w_blacklist,custom_stopwords,custom_stems,stem_exclude,stoplist_directory,custom_stoplist,unique=True)

print ("CHECKPOINT 2: unique vocabulary compiled")

#Write out full-reflist.txt
os.chdir(outpath)
ascii_errs=[]
for i in all_words:
    try:
        with open("full-reflist.txt","a") as f:
            f.write(i)
            f.write("\n")
    except UnicodeEncodeError:
        ascii_errs.append(i)

print ("CHECKPOINT 3: unique vocabulary written")
print ("Script 1 complete: vocabulary cleaned and written out")