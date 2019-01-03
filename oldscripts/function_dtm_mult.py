###########
#Mult file generation for DTM. Written for Python 3.
#	Function() representation
#	Adopted from Will Issac and James Murray.
###########

# pandasDF_to_mult()

# '''This is the baseline mult generator for a pandas dataframe. There's no option for custom stopword FILE, but 
# it does include option for custom removals (regex patterns), which you can theoretically use to remove certain words.
# Includes option to exclude NLTK stopwords. Also includes option for custom tokens using regex patterns. 
# Words are defined by the regex '[A-Za-z]{min_chars_for_word,}', i.e. only including strings of letters longer than or equal to minimum.

# Requires header: ['id','day','month','year','speaker', 'speech']

# Outputs TO FILE in output path:
# 	# meta_output.csv = metadata without DAT info
# 	# full_reflist.txt = reference wordlist
# 	# full_mult.dat = DAT info
# 	# final_meta.csv = metadata with DAT info
# 	# [user defined name].csv = full dataframe, including speeches, metadata, and DAT info

# Returns:
# 	A pandas dataframe which includes all data.

# Parameters:
# (-) inputdf = a pandas dataframe with each row corresponding to a document
# (-) outpath = directory to write out the output files above

# (-) custom_tokens = list of regex patterns to keep as tokens. ORDER MATTERS! Regex catches from left to right, separate with '|'.
# (-) custom_clean = list of regex patterns to substitute with a space in text
# (-) exclude_stopwords = exclude NLTK stopwords
# (-) stem_mc = should I use the NLTK Snowball stemmer to stem words?
# (-) doc_col_name = column name in pandas dataframe of raw document text
# (-) min_chars_for_word = integer for minimum chars to consider something a word_tokenize
# '''

import nltk, re, sys, os, getopt, pandas, time
import numpy as np
from datetime import datetime
from nltk import word_tokenize as token_d
from nltk.tokenize import RegexpTokenizer as token_re
from collections import Counter as C_
from nltk.corpus import stopwords


##########
#Dependency functions
##########

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


#########
#Mult generator function
#########
def pandasDF_to_mult(inputdf,outpath,custom_tokens=[],custom_clean=[],exclude_stopwords=True,stem_mc=False,doc_col_name="speech",min_chars_for_word=2):
	'''This is the baseline mult generator for a pandas dataframe. There's no option for custom stopword FILE, but 
	it does include option for custom removals (regex patterns), which you can theoretically use to remove certain words.
	Includes option to exclude NLTK stopwords. Also includes option for custom tokens using regex patterns. 
	Words are defined by the regex '[A-Za-z]{min_chars_for_word,}', i.e. only including strings of letters longer than or equal to minimum.

	Requires header: ['id','day','month','year','speaker', 'speech']
	
	Outputs TO FILE in output path:
		# meta_output.csv = metadata without DAT info
		# full_reflist.txt = reference wordlist
		# full_mult.dat = DAT info
		# final_meta.csv = metadata with DAT info
		# [user defined name].csv = full dataframe, including speeches, metadata, and DAT info

	Returns:
		A pandas dataframe which includes all data.

	Parameters:
	(-) inputdf = a pandas dataframe with each row corresponding to a document
	(-) outpath = directory to write out the output files above

	(-) custom_tokens = list of regex patterns to keep as tokens. ORDER MATTERS! Regex catches from left to right, separate with '|'.
	(-) custom_clean = list of regex patterns to substitute with a space in text
	(-) exclude_stopwords = exclude NLTK stopwords
	(-) stem_mc = should I use the NLTK Snowball stemmer to stem words?
	(-) doc_col_name = column name in pandas dataframe of raw document text
	(-) min_chars_for_word = integer for minimum chars to consider something a word_tokenize
	'''

	#Prep Working DF
	working_df = inputdf
	working_df = working_df.reset_index()
	working_df['index1'] = working_df.index

	#Prepare your toys for wordplay
	snowball = nltk.stem.snowball.EnglishStemmer(ignore_stopwords=False)
	final_token_set=str(custom_tokens[0])+'|[A-Za-z]{'+str(min_chars_for_word)+',}'
	tokenizer = token_re(final_token_set) # group cites + words as tokens: ORDER MATTERS!!!!

	word_dict    = {}			# Dict of all words in format {first_word_to_appear:0, ..., nth_word_to_appear:n}
	w_d_rev		 = {}			# word_dict with keys and values reversed
	stemmed_dict = {}			# Dict of all stems in format {first_stem_to_appear:0, ..., nth_stem_to_appear:n}
	s_d_rev		 = {}			# stemmed_dict with keys and values reversed
	s_blacklist  = []			# List of stems to remove
	w_blacklist  = []			# List of words to remove
	if exclude_stopwords == True:
		w_blacklist += stopwords.words('english')

	#############
	#Currently does not support custom stopword option
	#############
	# if custom_stopwords == True:
	#         stoplist_directory = stoppath
	#         custom_stoplist=custom_list(stoplist_file,stoplist_directory)
	#         w_blacklist += custom_stoplist

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

	print('CHECKPOINT 2 - prep work complete')

	for index1, row in working_df.iterrows():
		working_row = row.copy()
		yr=working_row["year"]
		mem_cont_raw=str(working_row["speech"]).lower()

		#If there's custom stuff to remove, do it here
		for stuff_to_clean in custom_clean:
			mem_cont_raw=re.sub(str(stuff_to_clean),' ',mem_cont_raw)
		mem_cont=mem_cont_raw
		    
		#Tokenize words
		words_in_mc = tokenizer.tokenize(mem_cont)
		words_in_mc = clean_list(w_blacklist, words_in_mc)

		##########
		#Currently does not support custom stopwords/stems
		##########
		# #Custom stoplist stemming
		# if custom_stopwords == True and custom_stems == True:
		# 	if stem_exclude:
		# 		excl_list=custom_list(stem_exclude,stoplist_directory)
		# 	else:
		# 		excl_list=[]
		# 	custom_stemlist=[i for i in custom_stoplist if i not in excl_list]
		# 	words_in_mc = clean_stems(custom_stemlist,words_in_mc)

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
		if index1%500==0:
			print('Processing: '+ str(index1))
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
	final_result_meta.to_csv('final_meta.csv',encoding='utf-8',index=False)

	#Write out your datfile
	datfile=working_df[['Full String']]
	datfile.to_csv('full-mult.dat',header=False,index=False)

	#Close your ref file; you're done appending it.
	ref_file.close()

	return(final_result)