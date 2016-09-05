#! /usr/bin/env python

import nltk, re, sys, os, getopt, pandas, time
import numpy as np
from datetime import datetime
from nltk import word_tokenize as token_d
from nltk.tokenize import RegexpTokenizer as token_re
from collections import Counter as C_
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

# If True, the member contribution will be stemmed.
#   Truth be told, I'm not sure what this does. I leave it as it is, 
#   but for the UN project I set it as False and I don't remember why.
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
#    Note: stopwords will NOT be case sensitive.
custom_stopwords = False
stoplist_file = ""
stoppath = ""
    
#########################
#Input and output directories
#########################

inpath = ""
outpath = ""

###############################
#CSV file names 
#    (csvfilelist) a list of csv files (SAME HEADERS!!!) as inputs. If only one file, pass as ['filename']
#    (final_df_name) the name of your FULL dataframe output csv file
#   
###############################

csvfilelist = [""]
final_df_name = ""


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
    final_frame=frame.sort('id',ascending=1)
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
			file_obj.write(item + "\n")
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
def custom_stopword_list(filename,location):
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

#Prepare your toys for wordplay
snowball = nltk.stem.snowball.EnglishStemmer(ignore_stopwords=False)
final_token_set=custom_tokens+'|[A-Za-z]{2,}'
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
        custom_stoplist=custom_stopword_list(stoplist_file,stoplist_directory)
        w_blacklist += custom_stoplist

counter_full = C_({}) 	# Counter of all words (or stems) and their counts in format Counter({value_of_word_in_word_dict_or_stemmed_dict: count, ...})
file_count = 1

doc_grouper = ""				# Prepares for grouping of mem. cont. by metadata
counter_to_print = C_()
working_df['index1'] = working_df.index
w_mc = []

#Open ref_file so you can write out words
ref_file = open(outpath + 'full-reflist.txt', "w")

#######################################
#Begin iterating over rows
#######################################

print 'CHECKPOINT 2 - prep work complete'

for index1, row in working_df.iterrows():
	working_row = row.copy()
	yr=working_row["year"]
	print str(yr)+'_'+str(working_row[0])
        mem_cont_raw=str(working_row["speech"]).lower()
        
        #If there's custom stuff to remove, do it here
        for stuff_to_clean in custom_clean:
            mem_cont_raw=re.sub(str(stuff_to_clean),'',mem_cont_raw)
        mem_cont=mem_cont_raw
        
	#Tokenize words
	words_in_mc = tokenizer.tokenize(mem_cont)
	words_in_mc = clean_list(w_blacklist, words_in_mc)

	#Get wordcount
	if stem_mc == True:	
		ustemmed_in_mc        = []
		stemmed_in_mc         = stem_list(words_in_mc)
		stemmed_in_mc         = clean_list(s_blacklist, stemmed_in_mc)
		ustemmed_in_mc        = combine_lists(ustemmed_in_mc, stemmed_in_mc)
		stemmed_dict, s_d_rev = add_to_master(stemmed_dict, s_d_rev, ustemmed_in_mc, ref_file)
		counter_for_mc        = count_words_counter(stemmed_dict, stemmed_in_mc)

	elif stem_mc == False:
		unique_in_mc          = []
		unique_in_mc          = combine_lists(unique_in_mc, words_in_mc)
		word_dict, w_d_rev    = add_to_master(word_dict, w_d_rev, unique_in_mc, ref_file)
		counter_for_mc        = count_words_counter(word_dict, words_in_mc)
	counter_full += counter_for_mc

	multi_index, multi_count = make_multi(counter_for_mc)
	mc_str = make_multi_full(counter_for_mc)
	
	#Process the heck out of it
	mc = pandas.Series(multi_count, index=multi_index, dtype = 'int')
	mc_dict = mc.to_dict()
	print 'Processing: '+ str(index1)
	mc_str = str(mc_str)
	working_df.loc[index1,'Full String'] = mc_str       	           
	w_mc.append(mc_dict)
	file_count += 1

#######################
#Write out the outputs
#######################

os.chdir(outpath)
final_result = working_df

#Write out metafile
final_result_meta = working_df[['index1','id','Full String','day','month','year','speaker',]]
final_result_meta.to_csv('final_meta.csv',encoding='utf-8')

#Write out your datfile
datfile=working_df[['Full String']]
datfile.to_csv('full-mult.dat',header=False,index=False)

#Write out full dataframe, if applicable
if write_teh_big_one==True:
    final_result.to_csv(final_df_name, encoding='utf-8')
    
#This was here from before, not sure why but it looks important.
ref_file.close()
